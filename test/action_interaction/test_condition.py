# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.types import InputType

from . import input_definitions as inout
from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "condition.xml")

    jgbot.press_button(inout.IN_BUTTON_1)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_2)
    jgbot.release_button(inout.IN_BUTTON_1)

    jgbot.press_button(inout.IN_BUTTON_2)
    jgbot.press_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    assert not jgbot.button(inout.OUT_BUTTON_2)
    jgbot.release_button(inout.IN_BUTTON_1)


def test_release_during(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "condition.xml")

    jgbot.press_button(inout.IN_BUTTON_2)
    jgbot.press_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    assert not jgbot.button(inout.OUT_BUTTON_2)
    jgbot.release_button(inout.IN_BUTTON_2)
    jgbot.release_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    assert not jgbot.button(inout.OUT_BUTTON_2)

    jgbot.press_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_2)
    jgbot.release_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    assert not jgbot.button(inout.OUT_BUTTON_2)


def test_current_input(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "condition.xml")

    jgbot.press_button(inout.IN_BUTTON_3)
    jgbot.wait(0.01)
    assert jgbot.button(inout.OUT_BUTTON_3)
    jgbot.release_button(inout.IN_BUTTON_3)
    jgbot.wait(0.01)
    assert not jgbot.button(inout.OUT_BUTTON_3)


def test_condition_with_tempo(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "condition.xml")

    jgbot.press_button(inout.IN_BUTTON_4)
    jgbot.press_button(inout.IN_BUTTON_2)
    jgbot.release_button(inout.IN_BUTTON_2)

    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )

    # Long press path.
    jgbot.press_button(inout.IN_BUTTON_4)
    jgbot.press_button(inout.IN_BUTTON_2)
    jgbot.wait(0.15)
    assert jgbot.button(inout.OUT_BUTTON_2)

    jgbot.release_button(inout.IN_BUTTON_4)
    jgbot.release_button(inout.IN_BUTTON_2)
