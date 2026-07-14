# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""
This module provides text-to-speech support via the Qt WinRT TTS backend.
"""

from __future__ import annotations

import dataclasses
import enum
from collections import deque

from PySide6.QtTextToSpeech import (
    QTextToSpeech,
    QVoice,
)

from gremlin.common import SingletonMetaclass
from gremlin.config import Configuration
from gremlin.types import PropertyType


class TTSQueueMode(enum.StrEnum):
    QueueBack = "queue-back"
    QueueFront = "queue-front"
    Interrupt = "interrupt"


@dataclasses.dataclass
class TTSRequest:
    text: str
    rate: float
    volume: float
    pitch: float


class TTSManager(metaclass=SingletonMetaclass):
    """Singleton TTS manager with a self-managed playback queue."""

    def __init__(self) -> None:
        self._engine: QTextToSpeech | None = None
        self._queue: deque[TTSRequest] = deque()
        self._current_request: TTSRequest | None = None

    def start(self) -> None:
        """Initialise the engine and wire signals.  Safe to call repeatedly."""
        if self._engine is not None:
            return
        self._engine = QTextToSpeech("winrt")
        voice_name = Configuration().value("action", "text-to-speech", "voice")
        if voice_name:
            for voice in self._engine.availableVoices():
                if voice.name() == voice_name:
                    self._engine.setVoice(voice)
                    break
        self._engine.stateChanged.connect(self._on_state_changed)

    def stop(self) -> None:
        """Clear the queue and stop any ongoing speech."""
        self._queue.clear()
        if self._engine is not None:
            self._engine.stop()

    def enqueue(self, request: TTSRequest, mode: TTSQueueMode) -> None:
        """Add *request* to the queue according to *mode* and start speaking
        if the engine is currently idle."""
        force_speak = False
        match mode:
            case TTSQueueMode.QueueBack:
                self._queue.append(request)
            case TTSQueueMode.QueueFront:
                self._queue.appendleft(request)
            case TTSQueueMode.Interrupt:
                if self._engine is not None:
                    self._engine.stop()
                self._queue.appendleft(request)
                force_speak = True
        self._speak_next(force_speak)

    def available_voices(self) -> list[QVoice]:
        if self._engine is None:
            return []
        return self._engine.availableVoices()

    def update_voice(self, voice_name: str) -> None:
        if self._engine is None:
            return
        for voice in self._engine.availableVoices():
            if voice.name() == voice_name:
                self._engine.setVoice(voice)
                break

    def _on_state_changed(self, state: QTextToSpeech.State) -> None:
        if state == QTextToSpeech.State.Ready:
            self._speak_next()

    def _speak_next(self, force_speak: bool = False) -> None:
        """Pop and speak the next queued item."""
        if not self._queue or self._engine is None:
            return
        if self._engine.state() != QTextToSpeech.State.Ready and not force_speak:
            return

        self._current_request = self._queue.popleft()
        self._engine.setRate(self._current_request.rate)
        self._engine.setVolume(self._current_request.volume)
        self._engine.setPitch(self._current_request.pitch)
        self._engine.say(self._current_request.text)


Configuration().register(
    "action",
    "text-to-speech",
    "voice",
    PropertyType.String,
    "",
    "Name of the TTS voice to use for all Text to Speech actions.",
    {},
    False,
)
