# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_exclusive_single(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap.xml")

    # Hold duration shorter than double tap time.
    jgbot.tap_button(
        "Double Tap 0.1 exclusive - single: out_single, double: out_double"
    )
    assert EventSpec("out_single", True) == jgbot.next_event()
    assert EventSpec("out_single", False) == jgbot.next_event()

    # Wait out the touble tap time.
    jgbot.wait(0.2)

    # Hold duration longer than double tap time.
    jgbot.hold_button(
        "Double Tap 0.1 exclusive - single: out_single, double: out_double", 0.15
    )
    assert EventSpec("out_single", True) == jgbot.next_event()
    assert EventSpec("out_single", False) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_exclusive_double(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap.xml")

    jgbot.tap_button(
        "Double Tap 0.1 exclusive - single: out_single, double: out_double"
    )
    jgbot.tap_button(
        "Double Tap 0.1 exclusive - single: out_single, double: out_double"
    )
    assert EventSpec("out_double", True) == jgbot.next_event()
    assert EventSpec("out_double", False) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_combined_single(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap.xml")

    # Hold duration shorter than double tap time.
    jgbot.tap_button("Double Tap 0.1 combined - single: out_single, double: out_double")
    assert EventSpec("out_single", True) == jgbot.next_event()
    assert EventSpec("out_single", False) == jgbot.next_event()

    # Wait out the touble tap time.
    jgbot.wait(0.2)

    # Hold duration longer than double tap time.
    jgbot.hold_button(
        "Double Tap 0.1 combined - single: out_single, double: out_double", 0.15
    )
    assert EventSpec("out_single", True) == jgbot.next_event()
    assert EventSpec("out_single", False) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_combined_double(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap.xml")

    jgbot.tap_button("Double Tap 0.1 combined - single: out_single, double: out_double")
    jgbot.tap_button("Double Tap 0.1 combined - single: out_single, double: out_double")
    assert EventSpec("out_single", True) == jgbot.next_event()
    assert EventSpec("out_single", False) == jgbot.next_event()
    assert EventSpec("out_single", True) == jgbot.next_event()
    assert EventSpec("out_double", True) == jgbot.next_event()
    assert EventSpec("out_single", False) == jgbot.next_event()
    assert EventSpec("out_double", False) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()
