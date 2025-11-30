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

from gremlin.types import HatDirection

from test.action_interaction.conftest import axis_value, button_state, hat_direction, GremlinBot
from test.action_interaction.input_definitions import *

def test_button_basic(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert button_state(IN_BUTTON_1) == False
    assert button_state(IN_BUTTON_2) == False

    jgbot.press_button(IN_BUTTON_1)
    assert button_state(IN_BUTTON_1) == True
    assert button_state(IN_BUTTON_2) == False
    jgbot.release_button(IN_BUTTON_1)
    assert button_state(IN_BUTTON_1) == False
    assert button_state(IN_BUTTON_2) == False


def test_button_hold(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert button_state(IN_BUTTON_1) == False
    assert button_state(IN_BUTTON_2) == False

    jgbot.hold_button(IN_BUTTON_1, 0.5)
    assert button_state(IN_BUTTON_1) == True
    assert button_state(IN_BUTTON_2) == False
    jgbot.wait(0.4)
    assert button_state(IN_BUTTON_1) == True
    assert button_state(IN_BUTTON_2) == False
    jgbot.wait(0.2)
    assert button_state(IN_BUTTON_1) == False
    assert button_state(IN_BUTTON_2) == False

def test_button_tap(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert button_state(IN_BUTTON_1) == False
    assert button_state(IN_BUTTON_2) == False

    # The duration of a tap is 0.1 seconds, thus the following checks ensure
    # that the button is held for approximately that long.
    jgbot.tap_button(IN_BUTTON_1)
    assert button_state(IN_BUTTON_1) == False
    assert button_state(IN_BUTTON_2) == False


def test_axis_basic(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert axis_value(IN_AXIS_1) == 0.0
    assert axis_value(IN_AXIS_2) == 0.0
    jgbot.set_axis_absolute(IN_AXIS_1, 0.5)
    assert axis_value(IN_AXIS_1) == 0.5
    assert axis_value(IN_AXIS_2) == 0.0


def test_axis_relative(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert axis_value(IN_AXIS_1) == 0.0
    assert axis_value(IN_AXIS_2) == 0.0
    jgbot.set_axis_relative(IN_AXIS_1, 0.3)
    assert axis_value(IN_AXIS_1) == 0.3
    assert axis_value(IN_AXIS_2) == 0.0
    jgbot.set_axis_relative(IN_AXIS_1, -0.5)
    assert axis_value(IN_AXIS_1) == -0.2
    assert axis_value(IN_AXIS_2) == 0.0
    jgbot.set_axis_relative(IN_AXIS_1, -0.9)
    assert axis_value(IN_AXIS_1) == -1.0
    assert axis_value(IN_AXIS_2) == 0.0


def test_hat_basic(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert hat_direction(IN_HAT_1) == HatDirection.Center
    assert hat_direction(IN_HAT_2) == HatDirection.Center
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.North)
    assert hat_direction(IN_HAT_1) == HatDirection.North
    assert hat_direction(IN_HAT_2) == HatDirection.Center
