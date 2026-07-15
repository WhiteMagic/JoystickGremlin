# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.ui.backend import Backend

from .conftest import JoystickGremlinBot
from .input_definitions import *


def test_pause_resume(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "pause_resume.xml")

    assert Backend().gremlinPaused == False
    jgbot.press_button(IN_BUTTON_1)
    assert Backend().gremlinPaused == True
    jgbot.press_button(IN_BUTTON_2)
    assert Backend().gremlinPaused == False


def test_pause_resume_repeat(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "pause_resume.xml")

    assert Backend().gremlinPaused == False
    jgbot.press_button(IN_BUTTON_1)
    assert Backend().gremlinPaused == True
    jgbot.press_button(IN_BUTTON_1)
    assert Backend().gremlinPaused == True
    jgbot.press_button(IN_BUTTON_2)
    assert Backend().gremlinPaused == False


def test_toggle(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "pause_resume.xml")

    assert Backend().gremlinPaused == False
    jgbot.press_button(IN_BUTTON_3)
    assert Backend().gremlinPaused == True
    jgbot.press_button(IN_BUTTON_3)
    assert Backend().gremlinPaused == False
    jgbot.press_button(IN_BUTTON_3)
    assert Backend().gremlinPaused == True
    jgbot.press_button(IN_BUTTON_3)
    assert Backend().gremlinPaused == False
