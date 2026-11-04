# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "condition.xml")

    jgbot.press_button("Condition condition_button pressed - true: out_a, false: out_b")
    assert not jgbot.button("out_a")
    assert jgbot.button("out_b")
    jgbot.release_button(
        "Condition condition_button pressed - true: out_a, false: out_b"
    )

    jgbot.press_button("condition_button")
    jgbot.press_button("Condition condition_button pressed - true: out_a, false: out_b")
    assert jgbot.button("out_a")
    assert not jgbot.button("out_b")
    jgbot.release_button(
        "Condition condition_button pressed - true: out_a, false: out_b"
    )


def test_release_during(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "condition.xml")

    jgbot.press_button("condition_button")
    jgbot.press_button("Condition condition_button pressed - true: out_a, false: out_b")
    assert jgbot.button("out_a")
    assert not jgbot.button("out_b")
    jgbot.release_button("condition_button")
    jgbot.release_button(
        "Condition condition_button pressed - true: out_a, false: out_b"
    )
    assert not jgbot.button("out_a")
    assert not jgbot.button("out_b")

    jgbot.press_button("Condition condition_button pressed - true: out_a, false: out_b")
    assert not jgbot.button("out_a")
    assert jgbot.button("out_b")
    jgbot.release_button(
        "Condition condition_button pressed - true: out_a, false: out_b"
    )
    assert not jgbot.button("out_a")
    assert not jgbot.button("out_b")


def test_current_input(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "condition.xml")

    jgbot.press_button(
        "Condition self pressed - true: Macro out_macro on, false: Macro out_macro off"
    )
    jgbot.wait(0.01)
    assert jgbot.button("out_macro")
    # Release follows the press into the true branch whose macro is press-only.
    jgbot.release_button(
        "Condition self pressed - true: Macro out_macro on, false: Macro out_macro off"
    )
    jgbot.wait(0.01)
    assert jgbot.button("out_macro")


def test_condition_with_tempo(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "condition.xml")

    jgbot.press_button("condition_button")
    jgbot.press_button("Condition condition_button pressed - Tempo 0.1 [out_a, out_b]")
    jgbot.release_button(
        "Condition condition_button pressed - Tempo 0.1 [out_a, out_b]"
    )

    assert EventSpec("out_a", True) == jgbot.next_event()
    assert EventSpec("out_a", False) == jgbot.next_event()

    # Long press path.
    jgbot.press_button("condition_button")
    jgbot.press_button("Condition condition_button pressed - Tempo 0.1 [out_a, out_b]")
    jgbot.wait(0.15)
    assert jgbot.button("out_b")

    jgbot.release_button("condition_button")
    jgbot.release_button(
        "Condition condition_button pressed - Tempo 0.1 [out_a, out_b]"
    )
    assert not jgbot.button("out_b")
