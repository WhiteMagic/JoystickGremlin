# SPDX-License-Identifier: GPL-3.0-only

"""Measures latency from a physical button press to the mapped vJoy button.

Maps every button of the first physical device 1:1 onto the first vJoy output
device, runs that profile through the real CodeRunner, and times each physical
button event against the matching vJoy button event reported back by DILL.

Usage:
    poetry run python scripts/benchmark_latency.py [--samples N] [--match-timeout S]
"""

from __future__ import annotations

import argparse
import atexit
import ctypes
import math
import signal
import statistics
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import cast

# The repo root isn't an installed package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6 import QtCore, QtWidgets

import dill
import gremlin.code_runner
import gremlin.config
import gremlin.config_registry
import gremlin.device_initialization
import gremlin.event_handler
import gremlin.event_helpers
import gremlin.shared_state
from action_plugins.map_to_vjoy import MapToVjoyData
from action_plugins.root import RootData
from gremlin.event_handler import Event
from gremlin.profile import InputItemBinding, Profile
from gremlin.types import InputType

MAX_BUTTONS = 32
AXIS_REFRESH_OPTIONS = ("refresh-axis-on-activation", "refresh-axis-on-mode-change")


@dataclass(frozen=True)
class Sample:
    """Latency of one matched physical and vJoy button event pair."""

    button_id: int
    is_pressed: bool
    latency_s: float


class LatencyRecorder(QtCore.QObject):
    """Pairs each physical button event with the vJoy event it produces.

    Events are timestamped and paired on the DILL callback thread, while samples
    are reported on the main thread via `sample_recorded`.
    """

    sample_recorded = QtCore.Signal(object)

    def __init__(
        self,
        physical_guid: uuid.UUID,
        output_guid: uuid.UUID,
        button_count: int,
        sample_target: int | None,
        match_timeout_s: float,
    ) -> None:
        """Creates a new instance.

        Args:
            physical_guid: device whose button events start a measurement
            output_guid: vJoy device whose button events end a measurement
            button_count: number of mapped buttons, starting at button 1
            sample_target: quit after this many samples, None runs indefinitely
            match_timeout_s: seconds after which a pending event is unmatched
        """
        super().__init__()
        self._physical_guid = physical_guid
        self._output_guid = output_guid
        self._button_count = button_count
        self._sample_target = sample_target
        self._match_timeout_s = match_timeout_s
        self._pending: dict[tuple[int, bool], float] = {}
        self.samples: list[Sample] = []
        self.unmatched_count = 0

        self.sample_recorded.connect(self._report_sample)

    def on_joystick_event(self, event: Event) -> None:
        """Records a button event, completing a sample if it matches.

        Runs on the DILL callback thread, anything slow delays event delivery.

        Args:
            event: joystick event emitted by the EventListener
        """
        now = time.perf_counter()
        if event.event_type != InputType.JoystickButton:
            return
        button_id = cast(int, event.identifier)
        is_pressed = cast(bool, event.is_pressed)
        if not 1 <= button_id <= self._button_count:
            return

        self._expire_pending(now)
        key = (button_id, is_pressed)
        if event.device_guid == self._physical_guid:
            self._pending[key] = now
        elif event.device_guid == self._output_guid and key in self._pending:
            sample = Sample(button_id, is_pressed, now - self._pending.pop(key))
            self.samples.append(sample)
            self.sample_recorded.emit(sample)

    def finish(self) -> None:
        """Counts all events still awaiting a match as unmatched."""
        self.unmatched_count += len(self._pending)
        self._pending.clear()

    def _expire_pending(self, now: float) -> None:
        """Counts pending events older than the match timeout as unmatched.

        Args:
            now: current `time.perf_counter()` value
        """
        stale = [
            key
            for key, pressed_at in self._pending.items()
            if now - pressed_at > self._match_timeout_s
        ]
        for key in stale:
            del self._pending[key]
        self.unmatched_count += len(stale)

    def _report_sample(self, sample: Sample) -> None:
        """Prints a sample and quits once the sample target is reached.

        Args:
            sample: the newly recorded sample
        """
        edge = "press" if sample.is_pressed else "release"
        print(
            f"button {sample.button_id:>2} {edge:<7} {sample.latency_s * 1000:7.2f} ms"
        )

        # MapToVjoy registers an auto-release per press; one mode never consumes it.
        gremlin.event_helpers.ButtonReleaseActions().reset()

        if self._sample_target and len(self.samples) >= self._sample_target:
            QtWidgets.QApplication.quit()


def build_profile(physical_guid: uuid.UUID, vjoy_id: int, button_count: int) -> Profile:
    """Creates a profile mapping each physical button to the same vJoy button.

    Args:
        physical_guid: device providing the input buttons
        vjoy_id: vJoy device receiving the output buttons
        button_count: number of buttons to map, starting at button 1

    Returns:
        Single-mode profile containing the button mappings
    """
    profile = Profile()
    mode_name = profile.modes.first_mode
    for button_id in range(1, button_count + 1):
        item = profile.get_input_item(
            physical_guid,
            InputType.JoystickButton,
            button_id,
            mode_name,
            create_if_missing=True,
        )
        assert item is not None

        root_action = RootData(InputType.JoystickButton)
        map_action = MapToVjoyData(InputType.JoystickButton)
        map_action.vjoy_device_id = vjoy_id
        map_action.vjoy_input_id = button_id
        map_action.button_inverted = False
        root_action.insert_action(map_action, "children")

        binding = InputItemBinding(item)
        binding.root_action = root_action
        binding.behavior = InputType.JoystickButton
        item.action_sequences.append(binding)

        profile.library.add_action(root_action)
        profile.library.add_action(map_action)
    return profile


def pick_device(
    label: str, devices: list[dill.DeviceSummary]
) -> dill.DeviceSummary | None:
    """Lists the devices and returns the first one with buttons.

    Args:
        label: device category shown in the listing
        devices: devices to list and pick from

    Returns:
        First device with at least one button, None if there is none
    """
    print(f"{label} devices:")
    for device in devices:
        print(
            f"  {device.name}: {device.button_count} buttons, {device.axis_count} axes"
        )
    return next((device for device in devices if device.button_count > 0), None)


def percentile(sorted_values: list[float], fraction: float) -> float:
    """Returns the nearest-rank percentile.

    Args:
        sorted_values: values in ascending order, must not be empty
        fraction: percentile as a fraction in [0, 1]

    Returns:
        Value at the requested percentile
    """
    return sorted_values[max(0, math.ceil(fraction * len(sorted_values)) - 1)]


def print_summary(
    samples: list[Sample], unmatched_count: int, match_timeout_s: float
) -> None:
    """Prints latency statistics and a warning for unmatched events.

    Args:
        samples: recorded samples
        unmatched_count: number of physical events without a vJoy match
        match_timeout_s: match timeout used, shown in the warning
    """
    print("\n--- summary ---")
    if samples:
        latencies_ms = sorted(sample.latency_s * 1000 for sample in samples)
        print(f"samples:  {len(latencies_ms)}")
        print(f"min:      {latencies_ms[0]:.2f} ms")
        print(f"mean:     {statistics.mean(latencies_ms):.2f} ms")
        print(f"median:   {statistics.median(latencies_ms):.2f} ms")
        print(f"p95:      {percentile(latencies_ms, 0.95):.2f} ms")
        print(f"p99:      {percentile(latencies_ms, 0.99):.2f} ms")
        print(f"max:      {latencies_ms[-1]:.2f} ms")
    else:
        print("No completed round trips recorded.")

    if unmatched_count:
        print(
            f"\nWARNING: {unmatched_count} physical button event(s) had no "
            f"matching vJoy event within {match_timeout_s:g}s. Either the button "
            "wasn't pressed or DILL doesn't report this vJoy device's state changes."
        )


def run_benchmark(
    app: QtWidgets.QApplication,
    physical: dill.DeviceSummary,
    output: dill.DeviceSummary,
    args: argparse.Namespace,
) -> None:
    """Runs the benchmark until the sample target is reached or Ctrl+C.

    Args:
        app: application whose event loop drives the benchmark
        physical: device whose buttons are pressed
        output: vJoy device the buttons are mapped to
        args: parsed command line arguments
    """
    button_count = min(physical.button_count, output.button_count, MAX_BUTTONS)
    print(
        f"\nMapping {button_count} buttons of {physical.name} "
        f"onto vJoy {output.vjoy_id}."
    )

    event_listener = gremlin.event_handler.EventListener()
    profile = build_profile(physical.device_guid.uuid, output.vjoy_id, button_count)
    gremlin.shared_state.current_profile = profile
    runner = gremlin.code_runner.CodeRunner()
    recorder = LatencyRecorder(
        physical.device_guid.uuid,
        output.device_guid.uuid,
        button_count,
        args.samples,
        args.match_timeout,
    )
    # Direct so timestamps aren't delayed by the main thread's event queue.
    event_listener.joystick_event.connect(
        recorder.on_joystick_event, QtCore.Qt.ConnectionType.DirectConnection
    )

    # Python signal handlers only run once Qt's C++ event loop yields.
    # https://docs.python.org/3/library/signal.html#execution-of-python-signal-handlers
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    wake_timer = QtCore.QTimer()
    wake_timer.timeout.connect(lambda: None)
    wake_timer.start(200)

    try:
        runner.start(profile)
        print("Press physical buttons now. Ctrl+C to stop.\n")
        app.exec()
    finally:
        runner.stop()
        # EventListener's non-daemon threads keep the process alive otherwise.
        event_listener.terminate()

    recorder.finish()
    print_summary(recorder.samples, recorder.unmatched_count, args.match_timeout)


def main() -> int:
    """Sets up DILL and the devices, then runs the benchmark.

    Returns:
        Process exit code
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples",
        type=int,
        help="stop after this many round trips (default: until Ctrl+C)",
    )
    parser.add_argument(
        "--match-timeout",
        type=float,
        default=2.0,
        help="seconds to wait for the vJoy event before a press counts as unmatched",
    )
    args = parser.parse_args()

    # 1 ms timer resolution for the whole process, including dill.dll.
    ctypes.windll.winmm.timeBeginPeriod(1)
    atexit.register(ctypes.windll.winmm.timeEndPeriod, 1)

    app = QtWidgets.QApplication(sys.argv)

    gremlin.config_registry.register_config_options()
    config = gremlin.config.Configuration()
    dill.DILL.load(config.value("global", "general", "use-legacy-dill"))
    print(f"Using DILL library {dill.DILL._dll_path}")
    dill.DILL.init()
    gremlin.device_initialization.joystick_devices_initialization()

    physical = pick_device("Physical", gremlin.device_initialization.physical_devices())
    output = pick_device(
        "vJoy output", gremlin.device_initialization.output_vjoy_devices()
    )
    if physical is None or output is None:
        print(
            "Need a physical and a vJoy output device with at least one button each.",
            file=sys.stderr,
        )
        return 1

    # Configuration.set() saves to disk, so restore the user's values afterwards.
    saved = {
        name: config.value("global", "behavior", name) for name in AXIS_REFRESH_OPTIONS
    }
    try:
        for name in AXIS_REFRESH_OPTIONS:
            config.set("global", "behavior", name, False)
        run_benchmark(app, physical, output, args)
    finally:
        for name, value in saved.items():
            config.set("global", "behavior", name, value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
