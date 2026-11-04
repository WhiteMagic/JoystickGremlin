# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_short_press(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "smart_toggle.xml")

    # Check that tapping the button toggles the output on and off.
    assert not jgbot.button("out_button")
    jgbot.press_button("Smart Toggle 0.2: out_button")
    assert jgbot.button("out_button")
    jgbot.release_button("Smart Toggle 0.2: out_button")
    assert jgbot.button("out_button")
    jgbot.press_button("Smart Toggle 0.2: out_button")
    assert jgbot.button("out_button")
    jgbot.release_button("Smart Toggle 0.2: out_button")
    assert not jgbot.button("out_button")

    # Ensure a short hold doesn't trigger the held behavior.
    jgbot.clear_events()
    jgbot.hold_button("Smart Toggle 0.2: out_button", 0.1)
    assert EventSpec("out_button", True) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_long_press(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "smart_toggle.xml")

    # Ensure holding and releasing the button after the threshold time
    # results in hold instead of toggle behavior.
    assert not jgbot.button("out_button")
    jgbot.hold_button("Smart Toggle 0.2: out_button", 0.25)
    assert EventSpec("out_button", True) == jgbot.next_event()
    assert EventSpec("out_button", False) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()
