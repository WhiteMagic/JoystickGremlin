# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.input_cache import Keyboard

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_hold_macro_restarts_after_release(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    hold = "Hold pulse every 5s [out_button_1]"

    jgbot.press_button(hold)
    assert EventSpec("out_button_1", True) == jgbot.next_event()
    assert EventSpec("out_button_1", False) == jgbot.next_event()

    # Released during the 5s repeat delay.
    jgbot.release_button(hold)
    jgbot.press_button(hold)
    assert EventSpec("out_button_1", True) == jgbot.next_event()


def test_hold_macro_finishes_repetition_before_restarting(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    hold = "Hold pulse every 5s [out_button_1]"

    jgbot.press_button(hold)
    assert EventSpec("out_button_1", True) == jgbot.next_event()

    # Released and pressed again during the repetition's pause.
    jgbot.release_button(hold)
    jgbot.press_button(hold)
    jgbot.wait(0)
    assert jgbot.event_count() == 0
    assert EventSpec("out_button_1", False) == jgbot.next_event()
    assert EventSpec("out_button_1", True) == jgbot.next_event()


def test_hold_macro_never_runs_during_exclusive_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    hold = "Hold pulse every 5s [out_button_1]"

    jgbot.press_button("Exclusive pulse [out_button_3]")
    assert EventSpec("out_button_3", True) == jgbot.next_event()

    # Expect this not to run as the hold macro stops before it ever started.
    jgbot.press_button(hold)
    jgbot.release_button(hold)
    assert EventSpec("out_button_3", False) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_hold_macro_runs_after_exclusive_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")

    jgbot.press_button("Exclusive pulse [out_button_3]")
    assert EventSpec("out_button_3", True) == jgbot.next_event()

    jgbot.press_button("Hold pulse every 5s [out_button_1]")
    assert EventSpec("out_button_3", False) == jgbot.next_event()
    assert EventSpec("out_button_1", True) == jgbot.next_event()
    assert EventSpec("out_button_1", False) == jgbot.next_event()


def test_toggle_macro_never_runs_during_exclusive_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    toggle = "Toggle pulse every 5s [out_button_2]"

    jgbot.press_button("Exclusive pulse [out_button_3]")
    assert EventSpec("out_button_3", True) == jgbot.next_event()

    jgbot.tap_button(toggle)
    jgbot.tap_button(toggle)
    assert EventSpec("out_button_3", False) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_toggle_macro_runs_after_exclusive_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")

    jgbot.press_button("Exclusive pulse [out_button_3]")
    assert EventSpec("out_button_3", True) == jgbot.next_event()

    jgbot.tap_button("Toggle pulse every 5s [out_button_2]")
    assert EventSpec("out_button_3", False) == jgbot.next_event()
    assert EventSpec("out_button_2", True) == jgbot.next_event()
    assert EventSpec("out_button_2", False) == jgbot.next_event()


def test_toggle_macro_restarts_after_toggling_off(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    toggle = "Toggle pulse every 5s [out_button_2]"

    jgbot.tap_button(toggle)
    assert EventSpec("out_button_2", True) == jgbot.next_event()
    assert EventSpec("out_button_2", False) == jgbot.next_event()

    # Toggled off and on again during the 5s repeat delay.
    jgbot.tap_button(toggle)
    jgbot.tap_button(toggle)
    assert EventSpec("out_button_2", True) == jgbot.next_event()


def test_toggle_macro_finishes_repetition_before_restarting(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    toggle = "Toggle pulse every 5s [out_button_2]"

    jgbot.tap_button(toggle)
    assert EventSpec("out_button_2", True) == jgbot.next_event()

    # Toggled off and on again during the repetition's pause.
    jgbot.tap_button(toggle)
    jgbot.tap_button(toggle)
    assert jgbot.event_count() == 0
    assert EventSpec("out_button_2", False) == jgbot.next_event()
    assert EventSpec("out_button_2", True) == jgbot.next_event()


def test_release_macro_runs_in_parallel_with_hold_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    hold = "Hold pulse [out_button_6], release macro [out_button_7]"

    jgbot.press_button(hold)
    assert EventSpec("out_button_6", True) == jgbot.next_event()

    jgbot.release_button(hold)
    assert EventSpec("out_button_7", True) == jgbot.next_event()
    assert EventSpec("out_button_6", False) == jgbot.next_event()


def test_map_to_keyboard_runs_during_exclusive_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    assert not Keyboard().is_pressed("k")

    jgbot.press_button("Exclusive pulse [out_button_3]")
    assert EventSpec("out_button_3", True) == jgbot.next_event()

    jgbot.press_button("Map to K")
    try:
        jgbot.wait(0.05)
        assert Keyboard().is_pressed("k")
        # The exclusive macro has not ended yet.
        assert jgbot.event_count() == 0
    finally:
        jgbot.release_button("Map to K")


def test_hold_macro_activated_on_press_and_release_stops_on_release(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    hold = "Hold on press and release every 0.2s [out_axis_1]"

    jgbot.press_button(hold)
    assert EventSpec("out_axis_1", 0.1) == jgbot.next_event()

    jgbot.release_button(hold)
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_empty_macro_does_not_block_next_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    assert not jgbot.button("out_button_8")

    jgbot.press_button("Empty macro, Macro [out_button_8]")
    assert EventSpec("out_button_8", True) == jgbot.next_event()


def test_macro_runs_twice_when_triggered_while_running(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    pulse = "Exclusive pulse [out_button_3]"

    jgbot.tap_button(pulse)
    jgbot.tap_button(pulse)
    assert EventSpec("out_button_3", True) == jgbot.next_event()
    assert EventSpec("out_button_3", False) == jgbot.next_event()
    assert EventSpec("out_button_3", True) == jgbot.next_event()


def test_count_macro_restarts_after_finishing(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")
    count = "Count 1 every 5s [out_button_9]"

    jgbot.tap_button(count)
    assert EventSpec("out_button_9", True) == jgbot.next_event()

    jgbot.tap_button(count)
    assert EventSpec("out_button_9", True) == jgbot.next_event()


def test_macro_waits_for_exclusive_macro_after_preemptive_macro_ends(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")

    jgbot.press_button("Exclusive pulse [out_button_3]")
    assert EventSpec("out_button_3", True) == jgbot.next_event()
    jgbot.press_button("Preemptive pulse [out_button_4]")
    assert EventSpec("out_button_4", True) == jgbot.next_event()

    jgbot.press_button("Empty macro, Macro [out_button_8]")
    assert EventSpec("out_button_4", False) == jgbot.next_event()
    assert EventSpec("out_button_3", False) == jgbot.next_event()
    assert EventSpec("out_button_8", True) == jgbot.next_event()


def test_waiting_macro_is_dropped_on_profile_stop(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")

    jgbot.press_button("Exclusive pulse [out_button_3]")
    assert EventSpec("out_button_3", True) == jgbot.next_event()
    jgbot.press_button("Empty macro, Macro [out_button_8]")

    jgbot.stop()
    assert EventSpec("out_button_3", False) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_running_macro_finishes_on_profile_stop(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")

    jgbot.press_button("Exclusive pulse [out_button_3]")
    assert EventSpec("out_button_3", True) == jgbot.next_event()

    jgbot.stop()
    assert EventSpec("out_button_3", False) == jgbot.next_event()


def test_running_macro_aborted_after_stop_grace_period(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro_scheduling.xml")

    jgbot.press_button("Long pause [out_button_10]")
    assert EventSpec("out_button_10", True) == jgbot.next_event()

    jgbot.stop()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()
