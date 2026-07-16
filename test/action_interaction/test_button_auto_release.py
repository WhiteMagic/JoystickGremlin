# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from . import input_definitions as inout
from .conftest import JoystickGremlinBot


def test_simple(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "button_auto_release.xml")

    assert jgbot.current_mode() == "Default"
    assert jgbot.button(inout.OUT_BUTTON_1) is False
    assert jgbot.button(inout.OUT_BUTTON_2) is False

    jgbot.press_button(inout.IN_BUTTON_1)
    assert jgbot.current_mode() == "Other"
    assert jgbot.button(inout.OUT_BUTTON_1) is False
    assert jgbot.button(inout.OUT_BUTTON_2) is False

    jgbot.press_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Other"
    assert jgbot.button(inout.OUT_BUTTON_1) is False
    assert jgbot.button(inout.OUT_BUTTON_2) is True

    jgbot.release_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Other"
    assert jgbot.button(inout.OUT_BUTTON_1) is False
    assert jgbot.button(inout.OUT_BUTTON_2) is False

    jgbot.press_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Other"
    assert jgbot.button(inout.OUT_BUTTON_1) is False
    assert jgbot.button(inout.OUT_BUTTON_2) is True

    jgbot.press_button(inout.IN_BUTTON_1)
    assert jgbot.current_mode() == "Default"
    assert jgbot.button(inout.OUT_BUTTON_1) is False
    assert jgbot.button(inout.OUT_BUTTON_2) is True

    jgbot.release_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Default"
    assert jgbot.button(inout.OUT_BUTTON_1) is False
    assert jgbot.button(inout.OUT_BUTTON_2) is False
