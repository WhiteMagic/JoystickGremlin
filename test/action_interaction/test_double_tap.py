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


def test_exclusive_single(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap.xml")

    # Hold duration shorter than double tap time.
    jgbot.tap_button(inout.IN_BUTTON_1)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )

    # Wait out the touble tap time.
    jgbot.wait(0.2)

    # Hold duration longer than double tap time.
    jgbot.hold_button(inout.IN_BUTTON_1, 0.15)
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


def test_exclusive_double(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap.xml")

    jgbot.tap_button(inout.IN_BUTTON_1)
    jgbot.tap_button(inout.IN_BUTTON_1)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, False)
        == jgbot.next_event()
    )

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_combined_single(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap.xml")

    # Hold duration shorter than double tap time.
    jgbot.tap_button(inout.IN_BUTTON_2)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )

    # Wait out the touble tap time.
    jgbot.wait(0.2)

    # Hold duration longer than double tap time.
    jgbot.hold_button(inout.IN_BUTTON_2, 0.15)
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


def test_combined_double(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap.xml")

    jgbot.tap_button(inout.IN_BUTTON_2)
    jgbot.tap_button(inout.IN_BUTTON_2)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, False)
        == jgbot.next_event()
    )

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()
