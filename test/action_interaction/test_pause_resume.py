# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.ui.backend import Backend

from .conftest import JoystickGremlinBot


def test_pause_resume(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "pause_resume.xml")

    assert not Backend().gremlinPaused
    jgbot.press_button("Pause")
    assert Backend().gremlinPaused
    jgbot.press_button("Resume")
    assert not Backend().gremlinPaused


def test_pause_resume_repeat(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "pause_resume.xml")

    assert not Backend().gremlinPaused
    jgbot.press_button("Pause")
    assert Backend().gremlinPaused
    jgbot.press_button("Pause")
    assert Backend().gremlinPaused
    jgbot.press_button("Resume")
    assert not Backend().gremlinPaused


def test_toggle(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "pause_resume.xml")

    assert not Backend().gremlinPaused
    jgbot.press_button("Toggle pause")
    assert Backend().gremlinPaused
    jgbot.press_button("Toggle pause")
    assert not Backend().gremlinPaused
    jgbot.press_button("Toggle pause")
    assert Backend().gremlinPaused
    jgbot.press_button("Toggle pause")
    assert not Backend().gremlinPaused
