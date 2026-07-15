# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import HatDirection

from .conftest import JoystickGremlinBot
from .input_definitions import *


def test_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(IN_HAT_1, HatDirection.North)
    assert jgbot.button(OUT_BUTTON_1) == True
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.Center)
    assert jgbot.button(OUT_BUTTON_1) == False
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.East)
    assert jgbot.button(OUT_BUTTON_2) == True
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.Center)
    assert jgbot.button(OUT_BUTTON_2) == False

    # Ensure no additional events are generated.
    jgbot.clear_events()
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.West)
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_transition(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(IN_HAT_1, HatDirection.North)
    assert jgbot.button(OUT_BUTTON_1) == True
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.East)
    assert jgbot.button(OUT_BUTTON_1) == False
    assert jgbot.button(OUT_BUTTON_2) == True
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.Center)
    assert jgbot.button(OUT_BUTTON_1) == False
    assert jgbot.button(OUT_BUTTON_2) == False


def test_transition_multiple(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(IN_HAT_1, HatDirection.North)
    assert jgbot.button(OUT_BUTTON_1) == True
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.South)
    assert jgbot.button(OUT_BUTTON_1) == True
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.East)
    assert jgbot.button(OUT_BUTTON_1) == False
    assert jgbot.button(OUT_BUTTON_2) == True
