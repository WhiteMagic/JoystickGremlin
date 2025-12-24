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

from gremlin.types import (
    HatDirection,
    InputType,
)
from gremlin.macro import MacroManager

from .conftest import (
    JoystickGremlinBot,
    EventSpec
)
from .input_definitions import *


def test_simple(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    expected_event_sequence = [
        EventSpec(InputType.JoystickHat, OUT_HAT_1, HatDirection.NorthEast),
        EventSpec(InputType.JoystickHat, OUT_HAT_2, HatDirection.East),
        EventSpec(InputType.JoystickButton, OUT_BUTTON_3, True),
        EventSpec(InputType.JoystickAxis, OUT_AXIS_2, 0.7),
        EventSpec(InputType.JoystickAxis, OUT_AXIS_3, -0.5),
        EventSpec(InputType.JoystickAxis, OUT_AXIS_1, 0.2),
        EventSpec(InputType.JoystickAxis, OUT_AXIS_4, -0.1),
    ]

    # Trigger action execution and ensure the sequence is sent as expected.
    jgbot.press_button(IN_BUTTON_1)
    jgbot.wait(0.05)
    for entry in expected_event_sequence:
        assert entry == jgbot.next_event()

def test_repeat(
    jgbot: JoystickGremlinBot,
    profile_dir: Path,
    subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.05

    expected_event_sequence = [
        EventSpec(InputType.JoystickButton, OUT_BUTTON_1, True),
        EventSpec(InputType.JoystickHat, OUT_HAT_1, HatDirection.North),
        EventSpec(InputType.JoystickButton, OUT_BUTTON_1, False),
        EventSpec(InputType.JoystickHat, OUT_HAT_1, HatDirection.Center),
    ]

    # Trigger action execution and ensure the sequence is repeated correctly.
    jgbot.press_button(IN_BUTTON_2)
    for loop in range(3):
        with subtests.test("Repeat iteration", i=loop):
            for entry in expected_event_sequence:
                assert entry == jgbot.next_event()


def test_trigger_on_release(
    jgbot: JoystickGremlinBot,
    profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    jgbot.press_button(IN_BUTTON_3)
    # Ensure no events are generated before releasing the button.
    jgbot.wait(0.05)
    assert jgbot.event_count() == 0

    # Ensure macro is executed upon button release.
    jgbot.release_button(IN_BUTTON_3)
    jgbot.wait(0.05)
    assert EventSpec(
        InputType.JoystickButton, OUT_BUTTON_1, True) == jgbot.next_event()
    assert EventSpec(
        InputType.JoystickButton, OUT_BUTTON_1, False) == jgbot.next_event()

    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_hat_single(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    jgbot.set_axis_absolute(OUT_AXIS_1, 0.12)
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.North)
    assert EventSpec(
        InputType.JoystickAxis, OUT_AXIS_1, 0.05) == jgbot.next_event()
    assert jgbot.axis(OUT_AXIS_1) == pytest.approx(0.17, abs=0.01)


def test_hat_count(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    jgbot.set_axis_absolute(OUT_AXIS_1, -0.15)
    jgbot.wait(0.05)
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.East)

    assert EventSpec(
        InputType.JoystickAxis, OUT_AXIS_1, 0.10) == jgbot.next_event()
    assert jgbot.axis(OUT_AXIS_1) == pytest.approx(-0.05, abs=0.01)
    assert EventSpec(
        InputType.JoystickAxis, OUT_AXIS_1, 0.10) == jgbot.next_event()
    assert jgbot.axis(OUT_AXIS_1) == pytest.approx(0.05, abs=0.01)


def test_hat_toggle(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    jgbot.set_axis_absolute(OUT_AXIS_1, -0.15)
    jgbot.wait(0.05)
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.South)
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.Center)

    expected_value = -0.15
    for _ in range(4):
        expected_value += 0.1
        assert EventSpec(
            InputType.JoystickAxis, OUT_AXIS_1, 0.1) == jgbot.next_event()
        assert jgbot.axis(OUT_AXIS_1) == pytest.approx(expected_value, abs=0.01)

    assert jgbot.event_count() == 0
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.South)
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.Center)
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_hat_hold(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.05

    # Set axis state and wait to ensure synchronization.
    jgbot.set_axis_absolute(OUT_AXIS_1, -0.15)
    jgbot.wait(0.05)
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.West)

    expected_value = -0.15
    for _ in range(4):
        expected_value += 0.1
        assert EventSpec(
            InputType.JoystickAxis, OUT_AXIS_1, 0.1) == jgbot.next_event()
        assert jgbot.axis(OUT_AXIS_1) == pytest.approx(expected_value, abs=0.01)

    assert jgbot.event_count() == 0
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.Center)
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()

