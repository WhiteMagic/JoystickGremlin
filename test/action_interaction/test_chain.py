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
import pytestqt.qtbot

from gremlin.types import HatDirection, InputType
from gremlin.macro import MacroManager

from .conftest import GremlinBot, EventSpec
from .input_definitions import *


def test_cycling_option1(jgbot: GremlinBot, profile_dir: Path, subtests: pytest.Subtests) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")
    MacroManager().default_delay = 0.0

    with subtests.test("Chain 1"):
        jgbot.press_button(IN_BUTTON_1)
        assert EventSpec(InputType.JoystickButton, OUT_BUTTON_1, True) == jgbot.next_event()
        jgbot.release_button(IN_BUTTON_1)
        assert EventSpec(InputType.JoystickButton, OUT_BUTTON_1, False) == jgbot.next_event()

    with subtests.test("Chain 2"):
        jgbot.press_button(IN_BUTTON_1)
        assert EventSpec(InputType.JoystickButton, OUT_BUTTON_2, True) == jgbot.next_event()
        jgbot.release_button(IN_BUTTON_1)
        assert EventSpec(InputType.JoystickButton, OUT_BUTTON_2, False) == jgbot.next_event()

    with subtests.test("Chain 3"):
        jgbot.press_button(IN_BUTTON_1)
        assert EventSpec(InputType.JoystickButton, OUT_BUTTON_3, True) == jgbot.next_event()
        jgbot.release_button(IN_BUTTON_1)
        assert EventSpec(InputType.JoystickButton, OUT_BUTTON_3, False) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(pytestqt.qtbot.TimeoutError):
        jgbot.next_event()


def test_cycling_option2(jgbot: GremlinBot, profile_dir: Path, subtests: pytest.Subtests) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")
    MacroManager().default_delay = 0.0

    with subtests.test("Chain 1"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == False

    with subtests.test("Chain 2"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_2) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_2) == False

    with subtests.test("Chain 3"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_3) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_3) == False


def test_timeout_reset(jgbot: GremlinBot, profile_dir: Path, subtests: pytest.Subtests) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == False

    # Wait for timeout to expire
    jgbot.wait(0.3)

    with subtests.test("Chain 1 after timeout"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == False