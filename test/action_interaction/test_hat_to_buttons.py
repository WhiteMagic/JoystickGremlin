# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import HatDirection

from . import input_definitions as inout
from .conftest import JoystickGremlinBot


def test_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.North)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.Center)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.East)
    assert jgbot.button(inout.OUT_BUTTON_2)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.Center)
    assert not jgbot.button(inout.OUT_BUTTON_2)

    # Ensure no additional events are generated.
    jgbot.clear_events()
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.West)
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_transition(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.North)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.East)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_2)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.Center)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    assert not jgbot.button(inout.OUT_BUTTON_2)


def test_transition_multiple(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.North)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.South)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.East)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_2)
