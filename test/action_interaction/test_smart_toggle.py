# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import InputType

from . import input_definitions as inout
from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_short_press(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "smart_toggle.xml")

    # Check that tapping the button toggles the output on and off.
    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.press_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.release_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.press_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.release_button(inout.IN_BUTTON_1)
    assert not jgbot.button(inout.OUT_BUTTON_1)

    # Ensure a short hold doesn't trigger the held behavior.
    jgbot.clear_events()
    jgbot.hold_button(inout.IN_BUTTON_1, 0.1)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_long_press(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "smart_toggle.xml")

    # Ensure holding and releasing the button after the threshold time
    # results in hold instead of toggle behavior.
    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.hold_button(inout.IN_BUTTON_1, 0.25)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()
