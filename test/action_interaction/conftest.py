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
import pytest
from pytestqt.qtbot import QtBot
from pytestqt.wait_signal import SignalBlocker
import threading
from typing import Any, Generator, cast

from gremlin import code_runner
from gremlin import event_handler
from gremlin.logical_device import LogicalDevice
from gremlin import mode_manager
import gremlin.profile
from gremlin.types import InputType, HatDirection
from gremlin.util import clamp
import gremlin.ui.backend


LDIdentifier = LogicalDevice.Input.Identifier


class EventSpec:

    def __init__(self, event_type: InputType, input_id: int, expected_value: float | bool | HatDirection) -> None:
        self.event_type = event_type
        self.input_id = input_id
        self.expected_value = expected_value

    def __repr__(self) -> str:
        return f"EventSpec({self.event_type}, {self.input_id}, {self.expected_value})"

    def _repr_compare(self, other: Any) -> list[str]:
        return [
            "comparison failed",
            f"Obtained: {other}",
            f"Expected: {self}",
        ]

    def __eq__(self, event: Any) -> bool:
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


class GremlinBot:

    def __init__(self, qtbot: QtBot) -> None:
        self._qtbot = qtbot
        self._profile = gremlin.profile.Profile()
        self._runner = code_runner.CodeRunner()
        self._event_listener = event_handler.EventListener()
        self._logical_device = LogicalDevice()
        self._logical_device.reset()
        self._mode_manager = mode_manager.ModeManager()

        self._logged_data = []
        self._ignore_data = []
        self._event_listener.joystick_event.connect(self._data_logger)

    def load_profile(self, profile_path: str | Path) -> None:
        self._logical_device.reset()
        self._profile = gremlin.profile.Profile()
        self._profile.from_xml(str(profile_path))
        self.start()

    def start(self) -> None:
        self._runner.start(self._profile, self._profile.modes.first_mode)

    def stop(self) -> None:
        self._runner.stop()
        self._event_listener.terminate()

    def wait(self, duration: float) -> None:
        self._qtbot.wait(int(duration * 1000))

    def next_event(self) -> event_handler.Event:
        # Wait to receive a new event, if we timeout the test will fail.
        if not self._logged_data:
            self._qtbot.waitSignal(
                self._event_listener.joystick_event,
                timeout=500
            ).wait()
        return self._logged_data.pop(0)

    def _data_logger(self, event: event_handler.Event) -> None:
        for evt in self._ignore_data:
            if evt == event:
                self._ignore_data.remove(evt)
                return
        self._logged_data.append(event)

    def send_button(self, button_id: int, pressed: bool) -> None:
        self.emit_event(InputType.JoystickButton, button_id, pressed)

    def press_button(self, button_id: int) -> None:
        self.send_button(button_id, True)

    def release_button(self, button_id: int) -> None:
        self.send_button(button_id, False)

    def hold_button(self, button_id: int, duration: float) -> None:
        self.press_button(button_id)
        threading.Timer(
            duration, lambda: self.release_button(button_id)).start()

    def tap_button(self, button_id: int) -> None:
        self.send_button(button_id, True)
        self._qtbot.wait(50)
        self.send_button(button_id, False)

    def set_axis_absolute(self, axis_id: int, value: float) -> None:
        self.emit_event(InputType.JoystickAxis, axis_id, value)

    def set_axis_relative(self, axis_id: int, delta: float) -> None:
        input = cast(
            LogicalDevice.Axis,
            self._logical_device[LDIdentifier(InputType.JoystickAxis, axis_id)]
        )
        new_value = clamp(input.value + delta, -1.0, 1.0)
        self.emit_event(InputType.JoystickAxis, axis_id, new_value)

    def set_hat_direction(self, hat_id: int, direction: HatDirection) -> None:
        self.emit_event(InputType.JoystickHat, hat_id, direction)

    def emit_event(
        self,
        input_type: InputType,
        input_id: int,
        value: float | int | HatDirection
    ) -> None:
        # Update the state of the logical device.
        self._logical_device[LDIdentifier(input_type, input_id)].update(value)

        # Create event to emit.
        evt = event_handler.Event(
            input_type,
            input_id,
            LogicalDevice.device_guid,
            self._mode_manager.current.name,
            value=value if input_type != InputType.JoystickButton else None,
            is_pressed=value if input_type == InputType.JoystickButton else None,
            raw_value=value
        )
        self._ignore_data.append(evt)
        self._event_listener.joystick_event.emit(evt)


@pytest.fixture
def jgbot(qtbot: QtBot) -> Generator[GremlinBot]:
    hg = GremlinBot(qtbot)
    gremlin.ui.backend.Backend().minimize()
    yield hg
    hg.stop()


@pytest.fixture
def ldev() -> Generator[LogicalDevice]:
    device = LogicalDevice()
    device.reset()
    yield device


@pytest.fixture(scope="session")
def profile_dir() -> Path:
    return Path(__file__).parent / "profiles"
