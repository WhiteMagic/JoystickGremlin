# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_on_press_short(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    jgbot.press_button("Default: Tempo 0.2 on press - short: out_short, long: out_long")
    assert EventSpec("out_short", True) == jgbot.next_event()
    assert jgbot.button("out_short")
    jgbot.wait(0.1)
    jgbot.release_button(
        "Default: Tempo 0.2 on press - short: out_short, long: out_long"
    )
    assert EventSpec("out_short", False) == jgbot.next_event()
    assert not jgbot.button("out_short")

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_on_press_long(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    jgbot.press_button("Default: Tempo 0.2 on press - short: out_short, long: out_long")
    assert EventSpec("out_short", True) == jgbot.next_event()
    jgbot.wait(0.15)
    assert jgbot.button("out_short")
    assert not jgbot.button("out_long")
    assert EventSpec("out_long", True) == jgbot.next_event()

    jgbot.release_button(
        "Default: Tempo 0.2 on press - short: out_short, long: out_long"
    )
    assert EventSpec("out_long", False) == jgbot.next_event()
    assert EventSpec("out_short", False) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_on_release_short_tap(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    assert not jgbot.button("out_short")
    jgbot.tap_button("Default: Tempo 0.2 on release - short: out_short, long: out_long")

    assert EventSpec("out_short", True) == jgbot.next_event()
    assert EventSpec("out_short", False) == jgbot.next_event()
    assert not jgbot.button("out_short")

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_on_release_short_hold(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    assert not jgbot.button("out_short")
    jgbot.press_button(
        "Default: Tempo 0.2 on release - short: out_short, long: out_long"
    )
    jgbot.wait(0.15)
    jgbot.release_button(
        "Default: Tempo 0.2 on release - short: out_short, long: out_long"
    )

    assert EventSpec("out_short", True) == jgbot.next_event()
    assert EventSpec("out_short", False) == jgbot.next_event()

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        print(jgbot.next_event())


def test_on_release_long(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    jgbot.press_button(
        "Default: Tempo 0.2 on release - short: out_short, long: out_long"
    )
    jgbot.wait(0.22)
    assert EventSpec("out_long", True) == jgbot.next_event()
    assert jgbot.button("out_long")

    jgbot.wait(0.05)
    jgbot.release_button(
        "Default: Tempo 0.2 on release - short: out_short, long: out_long"
    )
    assert EventSpec("out_long", False) == jgbot.next_event()
    assert not jgbot.button("out_long")


def test_release_out_of_rder(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "tempo.xml")

    assert jgbot.current_mode() == "Default"
    jgbot.press_button(
        "Default: [Tempo 0.2 on release - long: Switch to Second], "
        "Second: [Tempo 0.2 on release - long: Switch to Default]"
    )
    jgbot.wait(0.25)
    jgbot.release_button(
        "Default: [Tempo 0.2 on release - long: Switch to Second], "
        "Second: [Tempo 0.2 on release - long: Switch to Default]"
    )
    assert jgbot.current_mode() == "Second"
    jgbot.press_button(
        "Default: [Tempo 0.2 on release - long: Switch to Second], "
        "Second: [Tempo 0.2 on release - long: Switch to Default]"
    )
    jgbot.wait(0.25)
    jgbot.release_button(
        "Default: [Tempo 0.2 on release - long: Switch to Second], "
        "Second: [Tempo 0.2 on release - long: Switch to Default]"
    )
    assert jgbot.current_mode() == "Default"
