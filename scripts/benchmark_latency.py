# SPDX-License-Identifier: GPL-3.0-only

"""Measures round-trip latency from a physical button press to the mapped vJoy button.

Requires a real, connected physical input device and a configured vJoy output
device. Builds a profile mapping every button of the physical device 1:1 to
the same-numbered button on the vJoy device, activates it through the real
CodeRunner, then listens for DILL-reported state changes on both devices to
time the round trip: physical press observed -> vJoy button change observed.

Usage: poetry run python scripts/benchmark_latency.py [--samples N] [--timeout SECONDS]
"""

from __future__ import annotations

import argparse
import atexit
import ctypes
import statistics
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

# dill/gremlin/vjoy/action_plugins live at the repo root and aren't an
# installed package; running this script from scripts/ needs the root added
# to sys.path explicitly (same fix test/unit/conftest.py, test/integration/
# conftest.py apply for the same reason).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6 import QtCore, QtWidgets

import dill
import gremlin.code_runner
import gremlin.config
import gremlin.device_initialization
import gremlin.event_handler
import gremlin.event_helpers
import gremlin.shared_state
import joystick_gremlin
from action_plugins.map_to_vjoy import MapToVjoyData
from action_plugins.root import RootData
from gremlin.event_handler import Event
from gremlin.profile import InputItemBinding, Profile
from gremlin.types import InputType

MAX_BUTTONS = 32
DEFAULT_UNMATCHED_TIMEOUT_S = 2.0


@dataclass
class Sample:
    button_id: int
    is_pressed: bool
    latency_s: float


def build_profile(
    physical_guid: uuid.UUID, output_vjoy_id: int, button_count: int
) -> Profile:
    prof = Profile()
    mode_name = prof.modes.first_mode
    for button_id in range(1, button_count + 1):
        item = prof.get_input_item(
            physical_guid,
            InputType.JoystickButton,
            button_id,
            mode_name,
            create_if_missing=True,
        )
        assert item is not None

        root_action = RootData(InputType.JoystickButton)
        map_action = MapToVjoyData(InputType.JoystickButton)
        map_action.vjoy_device_id = output_vjoy_id
        map_action.vjoy_input_id = button_id
        map_action.button_inverted = False
        root_action.insert_action(map_action, "children")

        binding = InputItemBinding(item)
        binding.root_action = root_action
        binding.behavior = InputType.JoystickButton
        item.action_sequences.append(binding)

        prof.library.add_action(root_action)
        prof.library.add_action(map_action)
    return prof


class LatencyRecorder(QtCore.QObject):
    """Pairs physical/vJoy button events observed on the same DILL callback stream."""

    def __init__(
        self,
        physical_guid: uuid.UUID,
        output_guid: uuid.UUID,
        button_count: int,
        sample_target: int | None,
        unmatched_timeout_s: float,
    ) -> None:
        super().__init__()
        self._physical_guid = physical_guid
        self._output_guid = output_guid
        self._button_count = button_count
        self._sample_target = sample_target
        self._unmatched_timeout_s = unmatched_timeout_s
        self._pending: dict[tuple[int, bool], float] = {}
        self.samples: list[Sample] = []
        self.unmatched_count = 0

    @QtCore.Slot(Event)
    def on_joystick_event(self, event: Event) -> None:
        if event.event_type != InputType.JoystickButton:
            return
        button_id, is_pressed = event.identifier, event.is_pressed
        if not isinstance(button_id, int) or is_pressed is None:
            return
        if not (1 <= button_id <= self._button_count):
            return

        now = time.perf_counter()
        self._expire_stale(now)
        key = (button_id, is_pressed)

        if event.device_guid == self._physical_guid:
            self._pending[key] = now
        elif event.device_guid == self._output_guid:
            start = self._pending.pop(key, None)
            if start is None:
                return
            latency = now - start
            self.samples.append(Sample(button_id, is_pressed, latency))
            edge = "press" if is_pressed else "release"
            print(f"button {button_id:>2} {edge:<7} {latency * 1000:7.2f} ms")

            # MapToVjoyFunctor unconditionally registers a "different mode"
            # auto-release entry per press (gremlin/event_helpers.py) that
            # never gets consumed in a single-mode profile, so it grows
            # forever and adds O(n) scan overhead to every later event on
            # this button. Our profile doesn't rely on that safety net
            # (press/release are both handled directly), so keep it empty.
            gremlin.event_helpers.ButtonReleaseActions().reset()

            if self._sample_target and len(self.samples) >= self._sample_target:
                app = QtWidgets.QApplication.instance()
                assert app is not None
                app.quit()

    def finalize(self) -> None:
        """Counts any presses still awaiting a match as unmatched."""
        self.unmatched_count += len(self._pending)
        self._pending.clear()

    def _expire_stale(self, now: float) -> None:
        stale = [
            key
            for key, started_at in self._pending.items()
            if now - started_at > self._unmatched_timeout_s
        ]
        for key in stale:
            del self._pending[key]
            self.unmatched_count += 1
            edge = "press" if key[1] else "release"
            print(f"button {key[0]:>2} {edge:<7} unmatched (timed out)")


def print_summary(
    samples: list[Sample], unmatched_count: int, unmatched_timeout_s: float
) -> None:
    print("\n--- summary ---")
    if not samples:
        print("No completed round trips recorded.")
    else:
        latencies_ms = sorted(s.latency_s * 1000 for s in samples)

        def percentile(p: float) -> float:
            return latencies_ms[min(len(latencies_ms) - 1, int(len(latencies_ms) * p))]

        print(f"samples:  {len(latencies_ms)}")
        print(f"min:      {latencies_ms[0]:.2f} ms")
        print(f"mean:     {statistics.mean(latencies_ms):.2f} ms")
        print(f"median:   {statistics.median(latencies_ms):.2f} ms")
        print(f"p95:      {percentile(0.95):.2f} ms")
        print(f"p99:      {percentile(0.99):.2f} ms")
        print(f"max:      {latencies_ms[-1]:.2f} ms")

    if unmatched_count:
        print(
            f"\nWARNING: {unmatched_count} physical press(es)/release(s) had no "
            f"matching vJoy output event within {unmatched_timeout_s:.0f}s. Either "
            "a button wasn't actually pressed, or DILL may not deliver events for "
            "this vJoy device's own state changes."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="Stop after this many completed round trips (default: run until Ctrl+C)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_UNMATCHED_TIMEOUT_S,
        help="Seconds to wait for a matching vJoy event before a press is unmatched",
    )
    args = parser.parse_args()

    # Windows' default system timer resolution is ~15.6ms, and dill.dll (a
    # native DLL loaded into this process) is affected by it just like any
    # other in-process code if its internal wait/poll loop relies on it.
    # timeBeginPeriod is a per-process request but the finer resolution it
    # asks for applies process-wide for as long as it's held, so requesting
    # it here also sharpens dill.dll's own timing.
    ctypes.windll.winmm.timeBeginPeriod(1)
    atexit.register(ctypes.windll.winmm.timeEndPeriod, 1)

    app = QtWidgets.QApplication(sys.argv)

    joystick_gremlin.register_config_options()
    dill.DILL.init()
    gremlin.device_initialization.joystick_devices_initialization()

    physical_devices = gremlin.device_initialization.physical_devices()
    print("Physical devices found:")
    for dev in physical_devices:
        print(f"  {dev.name}: {dev.button_count} button(s), {dev.axis_count} axis(es)")
    physical = next((d for d in physical_devices if d.button_count > 0), None)
    if physical is None:
        print(
            "No physical (non-vJoy) device with at least one button found.",
            file=sys.stderr,
        )
        return 1

    output_devices = gremlin.device_initialization.output_vjoy_devices()
    print("vJoy output devices found:")
    for dev in output_devices:
        buttons, axes = dev.button_count, dev.axis_count
        print(f"  vjoy id {dev.vjoy_id}: {buttons} button(s), {axes} axis(es)")
    output = next((d for d in output_devices if d.button_count > 0), None)
    if output is None:
        print("No vJoy output device with at least one button found.", file=sys.stderr)
        return 1

    button_count = min(physical.button_count, output.button_count, MAX_BUTTONS)

    print(f"\nPhysical device: {physical.name} ({physical.device_guid.uuid})")
    print(f"vJoy output device: {output.name} (vjoy id {output.vjoy_id})")
    print(f"Mapping {button_count} button(s) 1:1.\n")

    event_listener = gremlin.event_handler.EventListener()

    prof = build_profile(physical.device_guid.uuid, output.vjoy_id, button_count)
    gremlin.shared_state.current_profile = prof

    cfg = gremlin.config.Configuration()
    cfg.set("global", "general", "refresh-axis-on-activation", False)
    cfg.set("global", "general", "refresh-axis-on-mode-change", False)

    runner = gremlin.code_runner.CodeRunner()
    runner.start(prof, prof.modes.first_mode)

    recorder = LatencyRecorder(
        physical.device_guid.uuid,
        output.device_guid.uuid,
        button_count,
        args.samples,
        args.timeout,
    )
    event_listener.joystick_event.connect(recorder.on_joystick_event)

    # Qt's C++ event loop never returns control to the interpreter, so a
    # plain Ctrl+C only registers once another event wakes it up. A no-op
    # timer keeps handing control back so KeyboardInterrupt actually fires.
    keepalive_timer = QtCore.QTimer()
    keepalive_timer.timeout.connect(lambda: None)
    keepalive_timer.start(200)

    print("Press physical buttons now. Ctrl+C to stop.\n")
    try:
        app.exec()
    except KeyboardInterrupt:
        pass

    runner.stop()
    recorder.finalize()
    print_summary(recorder.samples, recorder.unmatched_count, args.timeout)

    # EventListener owns non-daemon threads (the DILL callback thread, the
    # keyboard hook); without terminating it the process hangs after main()
    # returns instead of exiting.
    event_listener.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
