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
import threading
from typing import cast, Generator

from gremlin import code_runner
from gremlin import event_handler
from gremlin.logical_device import LogicalDevice
from gremlin import mode_manager
import gremlin.profile
from gremlin.types import InputType, HatDirection
from gremlin.util import clamp
import gremlin.ui.backend


LDIdentifier = LogicalDevice.Input.Identifier


class GremlinBot:

    def __init__(self, qtbot: QtBot) -> None:
        self._qtbot = qtbot
        self._profile = gremlin.profile.Profile()
        self._runner = code_runner.CodeRunner()
        self._event_listener = event_handler.EventListener()
        self._logical_device = LogicalDevice()
        self._logical_device.reset()
        self._mode_manager = mode_manager.ModeManager()

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


def axis_value(input_id: int) -> float:
    input = cast(
        LogicalDevice.Axis,
        LogicalDevice()[LDIdentifier(InputType.JoystickAxis, input_id)]
    )
    return input.value


def button_state(input_id: int) -> bool:
    input = cast(
        LogicalDevice.Button,
        LogicalDevice()[LDIdentifier(InputType.JoystickButton, input_id)]
    )
    return input.is_pressed


def hat_direction(input_id: int) -> HatDirection:
    input = cast(
        LogicalDevice.Hat,
        LogicalDevice()[LDIdentifier(InputType.JoystickHat, input_id)]
    )
    return input.direction
