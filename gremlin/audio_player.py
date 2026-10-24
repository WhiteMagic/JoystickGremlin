# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import array
import threading
import time
from collections.abc import Generator

import miniaudio

from gremlin.common import SingletonMetaclass
from gremlin.config import Configuration
from gremlin.types import PropertyType
from gremlin.util import clamp


class AudioSample:
    """Represents a single audiot sample to be played.

    Generates the audio samples from the given audio file while also exposing
    controls over the playback.

    TODO: An instance cannot be reused after playback has completed. This is
        fine for the play audio action, but may be limiting for other uses.
    """

    Generator_T = Generator[bytes | array.array[int], int]

    def __init__(self, sound_file: str, play_volume: int) -> None:
        """Creates an AudioSample instance.

        Args:
            sound_file: The path to the audio file to be played.
            play_volume: The volume of the playback, the value is in the range
                [0, 100] with 0 being mute and 100 maximum.
        """
        decoded = miniaudio.decode_file(sound_file)
        volume_factor = clamp(play_volume / 100.0, 0.0, 1.0)
        self._samples = array.array(
            "h", [int(sample * volume_factor) for sample in decoded.samples]
        )
        self._nchannels = decoded.nchannels

        self.device = miniaudio.PlaybackDevice(
            sample_rate=decoded.sample_rate,
            nchannels=decoded.nchannels,
            output_format=decoded.sample_format,
            buffersize_msec=50,
        )
        # Events to manage playback.
        self._stream_done = threading.Event()
        self._cancel_requested = threading.Event()
        self._playback_done = threading.Event()

    def block(self) -> None:
        """Blocks the calling thread until playback is complete."""
        self._playback_done.wait()

    def is_done(self) -> bool:
        """Returns whether playback has completed and the device is closed."""
        return self._playback_done.is_set()

    def cancel(self) -> None:
        """Stops the playback after the device's buffered audio drains."""
        self._cancel_requested.set()

    def play(self) -> None:
        """Starts playing the audio file.

        Starts the device with the sample generator and a thread that closes
        the device once all samples have been consumed.
        """
        self.device.start(self._build_sample_generator())
        threading.Thread(target=self._close_when_done).start()

    def _build_sample_generator(self) -> AudioSample.Generator_T:
        """Returns a started generator yielding the requested frames per callback."""

        def generate() -> AudioSample.Generator_T:
            try:
                frame_count = yield b""
                offset = 0
                while (
                    offset < len(self._samples) and not self._cancel_requested.is_set()
                ):
                    end = offset + frame_count * self._nchannels
                    frame_count = yield self._samples[offset:end]
                    offset = end
            finally:
                self._stream_done.set()

        generator = generate()
        next(generator)
        return generator

    def _close_when_done(self) -> None:
        """Closes the device once the sample generator has finished."""
        self._stream_done.wait()
        self.device.close()
        self._playback_done.set()


class AudioPlayer(metaclass=SingletonMetaclass):
    """Manages the playing of audio files."""

    def __init__(self) -> None:
        self._play_list: list[AudioSample] = []
        self._currently_playing: list[AudioSample] = []
        self._playback_mode = Configuration().value(
            "action", "play-sound", "playback-mode"
        )

        self._is_ready = False
        self._playback_thread = threading.Thread(target=self._playback)

    def refresh(self) -> None:
        """Refreshes the configuration by reading the playback-mode value."""
        self._playback_mode = Configuration().value(
            "action", "play-sound", "playback-mode"
        )

    def start(self) -> None:
        """Starts the audio playback thread if it is not already running."""
        if not self._is_ready:
            self._playback_thread = threading.Thread(target=self._playback)
            self._playback_thread.start()

    def stop(self) -> None:
        """Stops the audio playback thread."""
        self._is_ready = False
        self._play_list = []
        [s.cancel() for s in self._currently_playing]
        if self._playback_thread.is_alive():
            self._playback_thread.join()

    def enqueue(self, file_name: str, volume: int) -> None:
        """Queues the given sound with the specified volume to be played.

        The sound will be played according to the current playback mode.

        Args:
            sound_filename: The filename of the sound file to play.
            volume: The volume of the playback, the value is in the range
                [0, 100] with 0 being mute and 100 maximum
        """
        self._play_list.append(AudioSample(file_name, volume))

    def _playback(self) -> None:
        """Background thread which ensures audio is played."""
        self._is_ready = True
        while self._is_ready:
            self._currently_playing = [
                sample for sample in self._currently_playing if not sample.is_done()
            ]
            match self._playback_mode:
                case "Sequential":
                    if self._play_list:
                        sample = self._play_list.pop(0)
                        self._currently_playing.append(sample)
                        sample.play()
                        sample.block()
                case "Overlap":
                    if self._play_list:
                        sample = self._play_list.pop(0)
                        self._currently_playing.append(sample)
                        sample.play()
                case "Interrupt":
                    if self._play_list:
                        while self._currently_playing:
                            self._currently_playing.pop(0).cancel()
                        sample = self._play_list.pop(0)
                        self._currently_playing.append(sample)
                        sample.play()
            time.sleep(0.01)


Configuration().register(
    "action",
    "play-sound",
    "playback-mode",
    PropertyType.Selection,
    "Sequential",
    "When playing sound files wait for the previous sound to finish "
    "(Sequential) or interrupt current playback (Interrupt), or play sounds "
    "in parallel (Overlap).",
    {"valid_options": ["Sequential", "Interrupt", "Overlap"]},
    True,
)
