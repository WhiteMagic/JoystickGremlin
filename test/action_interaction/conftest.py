# -*- coding: utf-8; -*-

# Copyright (C) 2025 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from pathlib import Path
import threading
from typing import (
    cast,
    Any,
    Generator,
)

import pytest
from pytestqt.qtbot import QtBot

from gremlin import code_runner
from gremlin import event_handler
from gremlin.logical_device import LogicalDevice
from gremlin import mode_manager
import gremlin.profile
from gremlin.types import (
    InputType,
    HatDirection,
)
from gremlin.util import clamp
import gremlin.ui.backend


LDIdentifier = LogicalDevice.Input.Identifier


class EventSpec:

    """Encapsulates information about an expected event and supports
    comparison with an actual Event instance."""

    def __init__(
        self,
        event_type: InputType,
        input_id: int,
        expected_value: float | bool | HatDirection
    ) -> None:
        """Creates a new EventSpec instance.
        
        Args:
            event_type: The type of the event.
            input_id: The identifier of the input generating the event.
            expected_value: The expected value of the event.
        """
        self.event_type = event_type
        self.input_id = input_id
        self.expected_value = expected_value

    def __repr__(self) -> str:
        """Returns a string representation of the EventSpec instance.
        
        Returns:
            A string representation of the EventSpec instance.
        """
        return f"EventSpec({self.event_type}, {self.input_id}, " \
            f"{self.expected_value})"

    def _repr_compare(self, other: Any) -> list[str]:
        """Returns information used when the comparison fails.
        
        Returns:
            A list of strings describing the comparison failure.
        """
        return [
            "comparison failed",
            f"Obtained: {other}",
            f"Expected: {self}",
        ]

    def __eq__(self, event: Any) -> bool:
        """Compares the EventSpec instance with an Event instance.
        
        Args:
            event: The Event instance to compare with.
        
        Returns:
            True if the Event instance matches the EventSpec, False otherwise.
        """
        if self.event_type != event.event_type:
            return False
        if self.input_id != event.identifier:
            return False
        match self.event_type:
            case InputType.JoystickAxis:
                return self.expected_value == event.value
            case InputType.JoystickButton:
                return self.expected_value == event.is_pressed
            case InputType.JoystickHat:
                return self.expected_value == event.raw_value
        return False

    def __ne__(self, event: Any) -> bool:
        return not (event == self)


class EventLogger:

    """Helper class which logs all events received from Gremlin."""

    def __init__(self, qtbot: QtBot) -> None:
        """Creates a new EventLogger instance.
        
        Args:
            qtbot: The QtBot instance used for timing and event processing.
        """
        self._qtbot = qtbot
        self.logged_events: list[event_handler.Event] = []
        self.emitted_events: list[event_handler.Event] = []

        event_handler.EventListener().joystick_event.connect(
            self._process_event
        )

    def pop(self) -> event_handler.Event:
        """Returns the next logged event.

        If no event is stored the method waits for the next event. If none is
        received within a timeout period, a TimeoutError exception is raised.

        Returns:
            The next logged event.
        """
        # Wait to receive a new event, if we timeout an exception is raised.
        if not self.logged_events:
            self._qtbot.waitSignal(
                event_handler.EventListener().joystick_event,
                timeout=500
            ).wait()
        return self.logged_events.pop(0)

    def _process_event(self, event: event_handler.Event) -> None:
        """Record all events we receive unless they were actively emitted.
        
        Args:
            event: The event to process.
        """
        # If the event is one that we've emitted ourselves, ignore it.
        for evt in self.emitted_events:
            if evt == event:
                self.emitted_events.remove(evt)
                return
        self.logged_events.append(event)


class JoystickGremlinBot:

    """Helper class which allows interfacing with Gremlin for input simulation
    and output verification."""

    def __init__(self, qtbot: QtBot) -> None:
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
        self._runner.start(self._profile, self._profile.modes.first_mode)

    def stop(self) -> None:
        """Stops the profile execution."""
        self._runner.stop()
        self._event_listener.terminate()

    def wait(self, duration: float) -> None:
        """Blocking wait for the specified duration while processing events in
        the background.

        Args:
            duration: The duration in seconds to wait.
        """
        self._qtbot.wait(int(duration * 1000))

    def next_event(self) -> event_handler.Event:
        """Waits for and retrieves the next logged event.

        If no event is stored by the event logger, the method waits for the
        next event. If none is received within a timeout period, a
        TimeoutError exception is raised.

        Returns:
            The next logged event.
        """
        return self._event_logger.pop()

    def axis(self, input_id: int) -> float:
        """Retrieves the current value of the specified axis.
        
        Args:
            input_id: The identifier of the axis input.
        
        Returns:
            The current value of the specified axis.
        """
        input = cast(
            LogicalDevice.Axis,
            self._logical_device[LDIdentifier(InputType.JoystickAxis, input_id)]
        )
        return input.value

    def button(self, input_id: int) -> bool:
        """Retrieves the current state of the specified button.
        
        Args:
            input_id: The identifier of the button input.

        Returns:
            The current state of the specified button.
        """
        input = cast(
            LogicalDevice.Button,
            self._logical_device[LDIdentifier(InputType.JoystickButton, input_id)]
        )
        return input.is_pressed

    def hat(self, input_id: int) -> HatDirection:
        """Retrieves the current direction of the specified hat.

        Args:
            input_id: The identifier of the hat input.

        Returns:
            The current direction of the specified hat.
        """
        input = cast(
            LogicalDevice.Hat,
            self._logical_device[LDIdentifier(InputType.JoystickHat, input_id)]
        )
        return input.direction

    def send_button(self, button_id: int, pressed: bool) -> None:
        """Sends a button press or release event.
        
        Args:
            button_id: The identifier of the button input.
            pressed: True to press the button, False to release it.
        """
        self._emit_event(InputType.JoystickButton, button_id, pressed)

    def press_button(self, button_id: int) -> None:
        """Sends a button press event.
        
        Args:
            button_id: The identifier of the button input.
        """
        self.send_button(button_id, True)

    def release_button(self, button_id: int) -> None:
        """Sends a button release event.
        
        Args:
            button_id: The identifier of the button input.
        """
        self.send_button(button_id, False)

    def hold_button(self, button_id: int, duration: float) -> None:
        """Holds a button pressed for the specified duration.
        
        This returns immediately after pressing the button. The release event
        is emitted after the specified delay in the background while other
        interactions with Gremlin can happen.

        Args:
            button_id: The identifier of the button input.
            duration: The duration in seconds to hold the button pressed.
        """
        self.press_button(button_id)
        threading.Timer(
            duration, lambda: self.release_button(button_id)).start()

    def tap_button(self, button_id: int) -> None:
        """Taps a button (press and release) quickly.
        
        This is a blocking call that returns only after the button has been
        released. This is for convenience purposes.

        Args:
            button_id: The identifier of the button input.
        """
        self.send_button(button_id, True)
        self._qtbot.wait(50)
        self.send_button(button_id, False)

    def set_axis_absolute(self, axis_id: int, value: float) -> None:
        """Sets the specified axis to the given absolute value.

        Args:
            axis_id: The identifier of the axis input.
            value: The absolute value to set the axis to.
        """        
        self._emit_event(InputType.JoystickAxis, axis_id, value)

    def set_axis_relative(self, axis_id: int, delta: float) -> None:
        """Changes the specified axis by the given delta value.

        Changes the current value of the specified axis by the given amount.
        Note that the axis value cannot go outside the range [-1.0, 1.0].

        Args:
            axis_id: The identifier of the axis input.
            delta: The delta value to change the axis by.
        """
        input = cast(
            LogicalDevice.Axis,
            self._logical_device[LDIdentifier(InputType.JoystickAxis, axis_id)]
        )
        new_value = clamp(input.value + delta, -1.0, 1.0)
        self._emit_event(InputType.JoystickAxis, axis_id, new_value)

    def set_hat_direction(self, hat_id: int, direction: HatDirection) -> None:
        """Sets the specified hat to the given direction.
        
        Args:
            hat_id: The identifier of the hat input.
            direction: The direction to set the hat to.
        """
        self._emit_event(InputType.JoystickHat, hat_id, direction)

    def _emit_event(
        self,
        input_type: InputType,
        input_id: int,
        value: float | int | HatDirection
    ) -> None:
        """Creates an Event instance based on the given information and then
        emits it.
        
        Args:
            input_type: The type of the input generating the event.
            input_id: The identifier of the input generating the event.
            value: The value associated with the event.
        """
        # Update the state of the logical device.
        self._logical_device[LDIdentifier(input_type, input_id)].update(value)

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
        evt = event_handler.Event(
            input_type,
            input_id,
            LogicalDevice.device_guid,
            self._mode_manager.current.name,
            value=evt_value,
            is_pressed=is_pressed,
            raw_value=value
        )

        # Inform the event logger about the event we're about to emit, then
        # emit the event.
        self._event_logger.emitted_events.append(evt)
        self._event_listener.joystick_event.emit(evt)


@pytest.fixture
def jgbot(qtbot: QtBot) -> Generator[JoystickGremlinBot]:
    bot = JoystickGremlinBot(qtbot)
    gremlin.ui.backend.Backend().minimize()
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
