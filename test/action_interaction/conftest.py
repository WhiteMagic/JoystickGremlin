# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys
import threading
from collections.abc import Generator
from pathlib import Path
from typing import (
    cast,
)

import pytest
import pytestqt.qtbot
from PySide6 import QtCore

import dill
import gremlin.profile
import joystick_gremlin
from gremlin import (
    audio_player,
    code_runner,
    config,
    event_handler,
    mode_manager,
    tts,
)
from gremlin.error import GremlinError
from gremlin.input_refresh import RefreshPhysicalInputs
from gremlin.logical_device import LogicalDevice
from gremlin.types import (
    Event,
    HatDirection,
    InputType,
)
from gremlin.util import clamp
from vjoy import vjoy


class EventSpec:
    """Encapsulates information about an expected event and supports
    comparison with an actual Event instance."""

    def __init__(
        self,
        label: str,
        expected_value: float | bool | HatDirection,
    ) -> None:
        """Creates a new EventSpec instance.

        Args:
            label: The label of the input generating the event.
            expected_value: The expected value of the event.
        """
        self.label = label
        self.expected_value = expected_value

    def __repr__(self) -> str:
        """Returns a string representation of the EventSpec instance.

        Returns:
            A string representation of the EventSpec instance.
        """
        return f"EventSpec('{self.label}', {self.expected_value})"

    def _repr_compare(self, other: Event) -> list[str]:
        """Returns information used when the comparison fails.

        Returns:
            A list of strings describing the comparison failure.
        """
        return [
            "comparison failed",
            f"Obtained: {other}",
            f"Expected: {self}",
        ]

    def __eq__(self, event: Event) -> bool:
        """Compares the EventSpec instance with an Event instance.

        Args:
            event: The Event instance to compare with.

        Returns:
            True if the Event instance matches the EventSpec, False otherwise.
        """
        # Resolved here as specs can be built before the profile is loaded.
        input = LogicalDevice()[self.label]
        if input.type != event.event_type or input.id != event.identifier:
            return False
        match input.type:
            case InputType.JoystickAxis:
                return self.expected_value == pytest.approx(event.value)
            case InputType.JoystickButton:
                return self.expected_value == event.is_pressed
            case InputType.JoystickHat:
                return self.expected_value == event.raw_value
        return False

    def __ne__(self, event: Event) -> bool:
        return not (event == self)


class EventLogger(QtCore.QObject):
    """Helper class which logs all events received from Gremlin."""

    receivedValidSignal = QtCore.Signal()

    def __init__(self, qtbot: pytestqt.qtbot.QtBot) -> None:
        """Creates a new EventLogger instance.

        Args:
            qtbot: The QtBot instance used for timing and event processing.
        """
        super().__init__()
        self._qtbot = qtbot
        self.logged_events: list[Event] = []
        self.emitted_events: list[Event] = []

        event_handler.EventListener().joystick_event.connect(self._process_event)

    def clear(self) -> None:
        """Clears all logged events."""
        self.logged_events.clear()
        self.emitted_events.clear()

    def pop(self) -> Event:
        """Returns the next logged event.

        If no event is stored the method waits for the next event. If none is
        received within a timeout period, a TimeoutError exception is raised.

        Returns:
            The next logged event.
        """
        # Wait until the next event not emitted by the user (directly or
        # delayed) is received.
        while len(self.logged_events) == 0:
            self._qtbot.waitSignal(
                self.receivedValidSignal, timeout=500, raising=True
            ).wait()
        return self.logged_events.pop(0)

    def _timeout(self) -> None:
        sys.exit(1)
        # raise Exception("Timeout waiting for event")

    def _process_event(self, event: Event) -> None:
        """Record all events we receive unless they were actively emitted.

        Args:
            event: The event to process.
        """
        # Ignore any physical device events.
        if event.device_guid not in [dill.UUID_LogicalDevice, dill.UUID_Virtual]:
            return

        # If the event is one that we've emitted ourselves, ignore it.
        for evt in self.emitted_events:
            if evt == event:
                self.emitted_events.remove(evt)
                return
        self.logged_events.append(event)
        self.receivedValidSignal.emit()


class JoystickGremlinBot:
    """Helper class which allows interfacing with Gremlin for input simulation
    and output verification."""

    def __init__(self, qtbot: pytestqt.qtbot.QtBot) -> None:
        """Creates a new GremlinBot instance.

        Args:
            qtbot: The QtBot instance used for timing and event processing.
        """
        self._qtbot = qtbot
        self._profile = gremlin.profile.Profile()
        self._runner = code_runner.CodeRunner()
        self._event_listener = event_handler.EventListener()
        self._logical_device = LogicalDevice()
        self._logical_device.reset()
        self._mode_manager = mode_manager.ModeManager()
        self._event_logger = EventLogger(self._qtbot)

    @property
    def qtbot(self) -> pytestqt.qtbot.QtBot:
        """The QtBot instance used for timing and event processing."""
        return self._qtbot

    def load_profile(self, profile_path: str | Path) -> None:
        """Loads the specified profile and starts listening for events.

        Args:
            profile_path: The path to the profile XML file to load.
        """
        self._logical_device.reset()
        self._profile = gremlin.profile.Profile()
        self._profile.from_xml(str(profile_path))
        self.start()

    def start(self) -> None:
        """Starts the profile execution."""
        self._runner.start(self._profile)
        self._event_logger.clear()

    def stop(self) -> None:
        """Stops the profile execution."""
        # EventListener is session-wide; terminating it breaks later packages.
        self._runner.stop()
        vjoy.VJoyProxy.reset()
        audio_player.AudioPlayer().stop()
        tts.TTSManager().stop()

    def wait(self, duration: float) -> None:
        """Blocking wait for the specified duration while processing events in
        the background.

        Args:
            duration: The duration in seconds to wait.
        """
        self._qtbot.wait(int(duration * 1000))

    def next_event(self) -> Event:
        """Waits for and retrieves the next logged event.

        If no event is stored by the event logger, the method waits for the
        next event. If none is received within a timeout period, a
        TimeoutError exception is raised.

        Returns:
            The next logged event.
        """
        return self._event_logger.pop()

    def clear_events(self) -> None:
        """Clears all logged events."""
        self._event_logger.clear()

    def event_count(self) -> int:
        """Returns the number of logged events.

        Returns:
            The number of logged events.
        """
        return len(self._event_logger.logged_events)

    def current_mode(self) -> str:
        """Retrieves the name of the current mode.

        Returns:
            The name of the current mode.
        """
        return self._mode_manager.current.name

    def axis(self, label: str) -> float:
        """Retrieves the current value of the specified axis.

        Args:
            label: The label of the axis input.

        Returns:
            The current value of the specified axis.
        """
        input = cast(
            LogicalDevice.Axis,
            self._input(InputType.JoystickAxis, label),
        )
        return input.value

    def button(self, label: str) -> bool:
        """Retrieves the current state of the specified button.

        Args:
            label: The label of the button input.

        Returns:
            The current state of the specified button.
        """
        input = cast(
            LogicalDevice.Button,
            self._input(InputType.JoystickButton, label),
        )
        return input.is_pressed

    def hat(self, label: str) -> HatDirection:
        """Retrieves the current direction of the specified hat.

        Args:
            label: The label of the hat input.

        Returns:
            The current direction of the specified hat.
        """
        input = cast(
            LogicalDevice.Hat,
            self._input(InputType.JoystickHat, label),
        )
        return input.direction

    def send_button(self, label: str, pressed: bool) -> None:
        """Sends a button press or release event.

        Args:
            label: The label of the button input.
            pressed: True to press the button, False to release it.
        """
        self._emit_event(InputType.JoystickButton, label, pressed)

    def press_button(self, label: str) -> None:
        """Sends a button press event.

        Args:
            label: The label of the button input.
        """
        self.send_button(label, True)

    def release_button(self, label: str) -> None:
        """Sends a button release event.

        Args:
            label: The label of the button input.
        """
        self.send_button(label, False)

    def hold_button(self, label: str, duration: float) -> None:
        """Holds a button pressed for the specified duration.

        This returns immediately after pressing the button. The release event
        is emitted after the specified delay in the background while other
        interactions with Gremlin can happen.

        Args:
            label: The label of the button input.
            duration: The duration in seconds to hold the button pressed.
        """
        self.press_button(label)
        threading.Timer(duration, lambda: self.release_button(label)).start()

    def tap_button(self, label: str) -> None:
        """Taps a button (press and release) quickly.

        This is a blocking call that returns only after the button has been
        released. This is for convenience purposes.

        Args:
            label: The label of the button input.
        """
        self.send_button(label, True)
        self._qtbot.wait(50)
        self.send_button(label, False)

    def set_axis_absolute(self, label: str, value: float) -> None:
        """Sets the specified axis to the given absolute value.

        Args:
            label: The label of the axis input.
            value: The absolute value to set the axis to.
        """
        self._emit_event(InputType.JoystickAxis, label, value)

    def set_axis_relative(self, label: str, delta: float) -> None:
        """Changes the specified axis by the given delta value.

        Changes the current value of the specified axis by the given amount.
        Note that the axis value cannot go outside the range [-1.0, 1.0].

        Args:
            label: The label of the axis input.
            delta: The delta value to change the axis by.
        """
        input = cast(
            LogicalDevice.Axis,
            self._input(InputType.JoystickAxis, label),
        )
        new_value = clamp(input.value + delta, -1.0, 1.0)
        self._emit_event(InputType.JoystickAxis, label, new_value)

    def set_hat_direction(self, label: str, direction: HatDirection) -> None:
        """Sets the specified hat to the given direction.

        Args:
            label: The label of the hat input.
            direction: The direction to set the hat to.
        """
        self._emit_event(InputType.JoystickHat, label, direction)

    def tap_hat_direction(self, label: str, direction: HatDirection) -> None:
        """Taps the specified hat in the given direction quickly.

        This is a blocking call that returns only after the hat has been
        returned to the center position. This is for convenience purposes.

        Args:
            label: The label of the hat input.
            direction: The direction to tap the hat to.
        """
        self.set_hat_direction(label, direction)
        self._qtbot.wait(50)
        self.set_hat_direction(label, HatDirection.Center)

    def _input(self, input_type: InputType, label: str) -> LogicalDevice.Input:
        """Returns the logical device input with the given label.

        Args:
            input_type: The type the input is expected to have.
            label: The label of the input.

        Returns:
            The matching logical device input.
        """
        input = self._logical_device[label]
        if input.type != input_type:
            raise GremlinError(f"Input '{label}' is not of type {input_type}")
        return input

    def _emit_event(
        self, input_type: InputType, label: str, value: float | HatDirection
    ) -> None:
        """Creates an Event instance based on the given information and then
        emits it.

        Args:
            input_type: The type of the input generating the event.
            label: The label of the input generating the event.
            value: The value associated with the event.
        """
        # Update the state of the logical device.
        input = self._input(input_type, label)
        input.update(value)

        # Prepare event parameters to keep type checkers happy.
        is_pressed = None
        evt_value = None
        match input_type:
            case InputType.JoystickAxis:
                evt_value = cast(float, value)
            case InputType.JoystickButton:
                is_pressed = cast(bool, value)
            case InputType.JoystickHat:
                evt_value = cast(HatDirection, value)

        # Create event to emit.
        evt = Event(
            input_type,
            input.id,
            LogicalDevice.device_guid,
            self._mode_manager.current.name,
            value=evt_value,
            is_pressed=is_pressed,
            raw_value=value,
        )

        # Inform the event logger about the event we're about to emit, then
        # emit the event. PySide6 routes @Slot exceptions to sys.excepthook
        # instead of propagating them, so we capture and re-raise here.
        self._event_logger.emitted_events.append(evt)
        captured: list[BaseException] = []
        original_hook = sys.excepthook
        sys.excepthook = lambda _t, exc_value, _tb: captured.append(exc_value)
        try:
            self._event_listener.joystick_event.emit(evt)
        finally:
            sys.excepthook = original_hook
        if captured:
            raise captured[0]


@pytest.fixture
def jgbot(
    qtbot: pytestqt.qtbot.QtBot,
    qapp: joystick_gremlin.JoystickGremlinApp,
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[JoystickGremlinBot]:
    bot = JoystickGremlinBot(qtbot)
    cfg = config.Configuration()
    cfg.set("global", "behavior", "refresh-axis-on-activation", False)
    if not request.node.get_closest_marker("axis_refresh_on_mode_change"):
        monkeypatch.setattr(RefreshPhysicalInputs, "refresh_axes", lambda: None)
    qapp.minimize()
    yield bot
    bot.stop()


@pytest.fixture
def ldev() -> Generator[LogicalDevice]:
    device = LogicalDevice()
    device.reset()
    yield device


@pytest.fixture(scope="session")
def profile_dir() -> Path:
    return Path(__file__).parent / "profiles"
