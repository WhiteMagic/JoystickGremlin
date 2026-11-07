# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.event_handler import EventHandler
from gremlin.types import HatDirection

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_release_reaches_press_mode_only(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    assert jgbot.current_mode() == "A"
    jgbot.press_button("A: Map to out_button_mode_a, B: Map to out_button_mode_b")
    assert EventSpec("out_button_mode_a", True) == jgbot.next_event()
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert not jgbot.button("out_button_mode_b")
    jgbot.release_button("A: Map to out_button_mode_a, B: Map to out_button_mode_b")

    # Expect the release of A's press but no additional mappins from B are triggered.
    assert EventSpec("out_button_mode_a", False) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_smart_toggle_remains_latched_on_press_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_activation.xml")
    button = "A: Smart Toggle 0.2: out_latched_mode_a, B: Map to out_button_mode_b"
    # A tap is shorter than the 0.2 s toggle delay, so it latches.
    jgbot.tap_button(button)
    assert jgbot.button("out_latched_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    jgbot.press_button(button)
    assert jgbot.button("out_button_mode_b")
    jgbot.release_button(button)
    assert not jgbot.button("out_button_mode_b")
    assert jgbot.button("out_latched_mode_a")

    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"
    jgbot.tap_button(button)
    assert not jgbot.button("out_latched_mode_a")


def test_inverted_mapping_remains_off_on_release_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")
    hat_buttons = (
        "A: Hat Button N: Map inverted to out_shared_mode_a, "
        "B: Hat Button N: Map to out_shared_mode_b"
    )
    jgbot.set_hat_direction(hat_buttons, HatDirection.North)
    assert not jgbot.button("out_shared_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    jgbot.set_hat_direction(hat_buttons, HatDirection.Center)

    assert not jgbot.button("out_shared_mode_a")


def test_inverted_mapping_activates_on_press_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")
    hat_buttons = (
        "A: Hat Button N: Map inverted to out_shared_mode_a, "
        "B: Hat Button N: Map to out_shared_mode_b"
    )
    jgbot.set_hat_direction(hat_buttons, HatDirection.North)
    jgbot.set_hat_direction(hat_buttons, HatDirection.Center)
    assert jgbot.button("out_shared_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    jgbot.set_hat_direction(hat_buttons, HatDirection.North)

    assert not jgbot.button("out_shared_mode_a")
    assert jgbot.button("out_shared_mode_b")


def test_hat_centers_first_on_direction_change_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.North
    )
    assert EventSpec("out_hat_mode_a", HatDirection.North) == jgbot.next_event()
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.East
    )

    assert EventSpec("out_hat_mode_a", HatDirection.Center) == jgbot.next_event()
    assert EventSpec("out_hat_mode_b", HatDirection.East) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


@pytest.mark.axis_refresh_on_mode_change
def test_relative_axis_stops_in_other_mode_and_restarts_on_return(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_axes.xml")

    # Get the axis moving, then switch which should force the axis to stop moving.
    jgbot.set_axis_absolute("A: Map relative scale 5.0 to out_relative_mode_a", 1.0)
    jgbot.wait(0.1)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    stopped_value = jgbot.axis("out_relative_mode_a")
    jgbot.wait(0.1)

    # Make sure the axis has moved and that it hasn't kept moving.
    # Scale 5.0 moves 0.005 per 10 ms step, about 0.03-0.05 per 0.1 s wait.
    assert stopped_value > 0.0
    assert jgbot.axis("out_relative_mode_a") == pytest.approx(stopped_value, abs=0.01)

    # Switch back to A, which refreshes the deflected axis and thus restarts motion.
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"
    restarted_value = jgbot.axis("out_relative_mode_a")
    jgbot.wait(0.1)

    assert jgbot.axis("out_relative_mode_a") > restarted_value + 0.02


@pytest.mark.axis_refresh_on_mode_change
def test_virtual_button_activates_on_mode_entry_with_axis_in_range(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert jgbot.button("out_button_mode_b")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.0)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")

    assert jgbot.current_mode() == "B"
    assert jgbot.button("out_button_mode_b")


@pytest.mark.axis_refresh_on_mode_change
def test_virtual_button_releases_on_leaving_range_after_in_foreign_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert jgbot.button("out_button_mode_b")

    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.0)

    assert not jgbot.button("out_button_mode_b")


@pytest.mark.axis_refresh_on_mode_change
def test_inverted_virtual_button_turns_output_on_on_leaving_range_after_mode_entry(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")
    virtual_button = "B: Axis Button 0.5-1.0: Map inverted to out_inverted_mode_b"
    jgbot.set_axis_absolute(virtual_button, 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert not jgbot.button("out_inverted_mode_b")

    jgbot.set_axis_absolute(virtual_button, 0.0)

    assert jgbot.button("out_inverted_mode_b")


@pytest.mark.axis_refresh_on_mode_change
def test_directional_virtual_button_remains_off_on_entry_after_move_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")
    virtual_button = "B: Axis Button 0.5-1.0 from below: Map to out_directional_mode_b"
    jgbot.set_axis_absolute(virtual_button, 0.0)
    jgbot.set_axis_absolute(virtual_button, 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert not jgbot.button("out_directional_mode_b")

    jgbot.set_axis_absolute(virtual_button, 0.8)

    assert jgbot.button("out_directional_mode_b")


@pytest.mark.axis_refresh_on_mode_change
def test_directional_virtual_button_remains_off_on_entry_after_release_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")
    virtual_button = "B: Axis Button 0.5-1.0 from below: Map to out_directional_mode_b"
    jgbot.set_axis_absolute(virtual_button, 0.0)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    jgbot.set_axis_absolute(virtual_button, 0.75)
    assert jgbot.button("out_directional_mode_b")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    jgbot.set_axis_absolute(virtual_button, 0.0)
    assert not jgbot.button("out_directional_mode_b")

    jgbot.set_axis_absolute(virtual_button, 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")

    assert jgbot.current_mode() == "B"
    assert not jgbot.button("out_directional_mode_b")


def test_press_and_release_action_runs_on_release_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_containers.xml")
    run_macro = "A: Macro on both [out_axis_macro_both]"

    jgbot.press_button(run_macro)
    assert EventSpec("out_axis_macro_both", 0.1) == jgbot.next_event()
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.release_button(run_macro)

    assert EventSpec("out_axis_macro_both", 0.2) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_held_smart_toggle_turns_off_on_release_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_containers.xml")
    smart_toggle = "A: Smart Toggle 0.3: out_toggle_mode_a"

    jgbot.press_button(smart_toggle)
    # Longer than the 0.3 s delay, so the toggle counts as held.
    jgbot.wait(0.35)
    assert jgbot.button("out_toggle_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.release_button(smart_toggle)

    assert not jgbot.button("out_toggle_mode_a")


def test_tempo_runs_short_action_on_release_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_containers.xml")
    run_tempo = "A: [Tempo 0.3 on release - short: out_short, long: out_long]"

    # Tap is shorter than the tempo threshold.
    jgbot.press_button(run_tempo)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.release_button(run_tempo)

    assert EventSpec("out_short", True) == jgbot.next_event()
    assert EventSpec("out_short", False) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_condition_action_turns_off_on_release_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_containers.xml")
    test_button = "A: Condition condition_button pressed - true: out_condition"

    jgbot.press_button("condition_button")
    jgbot.press_button(test_button)
    assert jgbot.button("out_condition")
    jgbot.release_button("condition_button")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.release_button(test_button)

    assert not jgbot.button("out_condition")


def test_chain_advances_on_release_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_containers.xml")
    chain_button = "A: Chain 1: out_chain_1 2: out_chain_2"

    jgbot.press_button(chain_button)
    assert jgbot.button("out_chain_1")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.release_button(chain_button)
    assert not jgbot.button("out_chain_1")

    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"
    jgbot.press_button(chain_button)
    assert jgbot.button("out_chain_2")


def test_macro_hold_stops_on_release_in_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_containers.xml")
    macro_button = "A: Macro hold [out_axis_macro]"

    jgbot.press_button(macro_button)
    assert EventSpec("out_axis_macro", 0.1) == jgbot.next_event()
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    # Two 0.1 s repeat delays, so the switch alone didn't stop the macro.
    value_after_switch = jgbot.axis("out_axis_macro")
    jgbot.wait(0.2)
    assert jgbot.axis("out_axis_macro") > value_after_switch

    jgbot.release_button(macro_button)
    # One repeat delay lets a step already in flight land before the check.
    jgbot.wait(0.1)
    jgbot.clear_events()

    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_temporary_mode_change_ignores_release_in_non_temporary_other_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_temporary.xml")

    jgbot.press_button("A: Temporary to T1")
    jgbot.press_button("T1: Temporary to T2")
    assert jgbot.current_mode() == "T2"

    jgbot.release_button("A: Temporary to T1")
    assert jgbot.current_mode() == "T2"

    jgbot.release_button("T1: Temporary to T2")
    assert jgbot.current_mode() == "T1"


def test_button_pressed_during_pause_remains_off_on_resume(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a button pressed during a pause and still held at resume doesn't activate.
    # Why: a pause drops events, resume doesn't replay them. Queuing them would fire
    # actions the user pressed while Gremlin was paused.
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    EventHandler().pause()
    jgbot.press_button("A: Map to out_button_mode_a, B: Map to out_button_mode_b")
    EventHandler().resume()

    assert not jgbot.button("out_button_mode_a")
