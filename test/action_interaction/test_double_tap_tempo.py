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


def test_single_tap_short(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap_tempo.xml")

    jgbot.tap_button(inout.IN_BUTTON_1)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )

    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())


def test_single_tap_long(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap_tempo.xml")

    jgbot.hold_button(inout.IN_BUTTON_1, 0.3)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, False)
        == jgbot.next_event()
    )

    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())


def test_double_tap_short(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap_tempo.xml")

    jgbot.tap_button(inout.IN_BUTTON_1)
    jgbot.tap_button(inout.IN_BUTTON_1)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_3, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_3, False)
        == jgbot.next_event()
    )

    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())


def test_double_tap_long(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap_tempo.xml")

    jgbot.tap_button(inout.IN_BUTTON_1)
    jgbot.hold_button(inout.IN_BUTTON_1, 0.3)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_4, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_4, False)
        == jgbot.next_event()
    )

    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())
