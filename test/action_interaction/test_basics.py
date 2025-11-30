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


def test_simple(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "remap_basic.xml")

    jgbot.press_button(IN_BUTTON_1)
    assert button_state(OUT_BUTTON_1) == True
    jgbot.release_button(IN_BUTTON_1)
    assert button_state(OUT_BUTTON_1) == False

    jgbot.set_axis_absolute(IN_AXIS_1, 0.5)
    assert axis_value(OUT_AXIS_1) == 0.5
    jgbot.set_axis_absolute(IN_AXIS_1, -0.5)
    assert axis_value(OUT_AXIS_1) == -0.5

    jgbot.set_hat_direction(IN_HAT_1, HatDirection.NorthWest)
    assert hat_direction(OUT_HAT_1) == HatDirection.NorthWest
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.SouthEast)
    assert hat_direction(OUT_HAT_1) == HatDirection.SouthEast


def test_button_advanced(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "remap_basic.xml")

    jgbot.tap_button(IN_BUTTON_1)
    assert button_state(OUT_BUTTON_1) == False

    jgbot.hold_button(IN_BUTTON_1, 0.5)
    assert button_state(OUT_BUTTON_1) == True
    jgbot.wait(0.4)
    assert button_state(OUT_BUTTON_1) == True
    jgbot.wait(0.2)
    assert button_state(OUT_BUTTON_1) == False


def test_remap_inverse(jgbot: GremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "remap_invert.xml")

    jgbot.press_button(IN_BUTTON_1)
    assert button_state(OUT_BUTTON_1) == False
    jgbot.release_button(IN_BUTTON_1)
    assert button_state(OUT_BUTTON_1) == True
