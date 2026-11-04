# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)

DOUBLE_TAP_TEMPOS = (
    "Double Tap 0.1 exclusive - "
    "single: Tempo 0.1 [out_single_short, out_single_long], "
    "double: Tempo 0.1 [out_double_short, out_double_long]"
)


def test_single_tap_short(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap_tempo.xml")

    jgbot.tap_button(DOUBLE_TAP_TEMPOS)
    assert EventSpec("out_single_short", True) == jgbot.next_event()
    assert EventSpec("out_single_short", False) == jgbot.next_event()

    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())


def test_single_tap_long(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap_tempo.xml")

    jgbot.hold_button(DOUBLE_TAP_TEMPOS, 0.3)
    assert EventSpec("out_single_long", True) == jgbot.next_event()
    assert EventSpec("out_single_long", False) == jgbot.next_event()

    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())


def test_double_tap_short(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap_tempo.xml")

    jgbot.tap_button(DOUBLE_TAP_TEMPOS)
    jgbot.tap_button(DOUBLE_TAP_TEMPOS)
    assert EventSpec("out_double_short", True) == jgbot.next_event()
    assert EventSpec("out_double_short", False) == jgbot.next_event()

    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())


def test_double_tap_long(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "double_tap_tempo.xml")

    jgbot.tap_button(DOUBLE_TAP_TEMPOS)
    jgbot.hold_button(DOUBLE_TAP_TEMPOS, 0.3)
    assert EventSpec("out_double_long", True) == jgbot.next_event()
    assert EventSpec("out_double_long", False) == jgbot.next_event()

    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())
