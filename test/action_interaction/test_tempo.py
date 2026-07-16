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


def test_on_press_short(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    jgbot.press_button(inout.IN_BUTTON_2)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.wait(0.1)
    jgbot.release_button(inout.IN_BUTTON_2)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )
    assert not jgbot.button(inout.OUT_BUTTON_1)

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_on_press_long(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    jgbot.press_button(inout.IN_BUTTON_2)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    jgbot.wait(0.15)
    assert jgbot.button(inout.OUT_BUTTON_1)
    assert not jgbot.button(inout.OUT_BUTTON_2)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, True)
        == jgbot.next_event()
    )

    jgbot.release_button(inout.IN_BUTTON_2)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, False)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_on_release_short_tap(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.tap_button(inout.IN_BUTTON_1)

    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )
    assert not jgbot.button(inout.OUT_BUTTON_1)

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_on_release_short_hold(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.press_button(inout.IN_BUTTON_1)
    jgbot.wait(0.15)
    jgbot.release_button(inout.IN_BUTTON_1)

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
        print(jgbot.next_event())


def test_on_release_long(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    jgbot.press_button(inout.IN_BUTTON_1)
    jgbot.wait(0.22)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, True)
        == jgbot.next_event()
    )
    assert jgbot.button(inout.OUT_BUTTON_2)

    jgbot.wait(0.05)
    jgbot.release_button(inout.IN_BUTTON_1)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, False)
        == jgbot.next_event()
    )
    assert not jgbot.button(inout.OUT_BUTTON_2)


def test_release_out_of_rder(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    assert jgbot.current_mode() == "Default"
    jgbot.press_button(inout.IN_BUTTON_3)
    jgbot.wait(0.25)
    jgbot.release_button(inout.IN_BUTTON_3)
    assert jgbot.current_mode() == "Second"
    jgbot.press_button(inout.IN_BUTTON_3)
    jgbot.wait(0.25)
    jgbot.release_button(inout.IN_BUTTON_3)
    assert jgbot.current_mode() == "Default"
