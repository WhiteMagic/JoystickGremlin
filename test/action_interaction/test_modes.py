# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.types import HatDirection

from . import input_definitions as inout
from .conftest import JoystickGremlinBot


def test_simple(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "modes.xml")

    assert jgbot.current_mode() == "Default"

    # Switch modes directly.
    jgbot.tap_button(inout.IN_BUTTON_1)
    assert jgbot.current_mode() == "Parent"
    jgbot.tap_button(inout.IN_BUTTON_1)
    assert jgbot.current_mode() == "Child 1"
    jgbot.tap_button(inout.IN_BUTTON_2)
    # Traverse back up via unwinding uses inheritance.
    assert jgbot.current_mode() == "Parent"
    jgbot.tap_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Default"

    # Ensure no action exists in un-parented mode.
    jgbot.tap_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Default"


def test_cycling(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "modes.xml")

    jgbot.tap_button(inout.IN_BUTTON_1)
    assert jgbot.current_mode() == "Parent"

    sequence = ["Child 1", "Child Child 1", "Child 2", "Parent"]

    for i in range(10):
        jgbot.tap_button(inout.IN_BUTTON_3)
        expected_mode = sequence[i % len(sequence)]
        assert jgbot.current_mode() == expected_mode


def test_previous(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "modes.xml")

    jgbot.tap_button(inout.IN_BUTTON_1)
    assert jgbot.current_mode() == "Parent"
    jgbot.tap_hat_direction(inout.IN_HAT_1, HatDirection.North)
    assert jgbot.current_mode() == "Child 2"

    for i in range(4):
        jgbot.tap_hat_direction(inout.IN_HAT_1, HatDirection.East)
        assert jgbot.current_mode() == "Parent"
        jgbot.tap_hat_direction(inout.IN_HAT_1, HatDirection.East)
        assert jgbot.current_mode() == "Child 2"


def test_temporary_inheritance(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "modes.xml")

    jgbot.tap_button(inout.IN_BUTTON_1)
    assert jgbot.current_mode() == "Parent"

    jgbot.press_button(inout.IN_BUTTON_4)
    assert jgbot.current_mode() == "Child Child 1"
    jgbot.release_button(inout.IN_BUTTON_4)
    assert jgbot.current_mode() == "Parent"


def test_temporary_no_inheritance(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "modes.xml")

    jgbot.press_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Independant"
    jgbot.release_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Default"


def test_temporary_tricky(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "modes.xml")

    jgbot.press_button(inout.IN_BUTTON_3)
    assert jgbot.current_mode() == "Parent"
    jgbot.tap_button(inout.IN_BUTTON_1)
    assert jgbot.current_mode() == "Child 1"
    jgbot.tap_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "Parent"
    jgbot.release_button(inout.IN_BUTTON_3)
    assert jgbot.current_mode() == "Default"
