# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import HatDirection, InputType

from . import input_definitions as inout
from .conftest import EventSpec, JoystickGremlinBot


def test_release_reaches_press_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.press_button(inout.IN_BUTTON_1)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.tap_button(inout.IN_BUTTON_4)
    assert jgbot.current_mode() == "B"
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()
    jgbot.release_button(inout.IN_BUTTON_1)

    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )
    # The binding of mode B must not have seen the release.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_press_in_other_binding_resets_release_binding(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.press_button(inout.IN_BUTTON_3)
    assert not jgbot.button(inout.OUT_BUTTON_3)
    jgbot.tap_button(inout.IN_BUTTON_4)
    jgbot.release_button(inout.IN_BUTTON_3)
    assert jgbot.button(inout.OUT_BUTTON_3)

    jgbot.press_button(inout.IN_BUTTON_3)
    assert not jgbot.button(inout.OUT_BUTTON_3)
    assert jgbot.button(inout.OUT_BUTTON_4)


def test_hat_direction_in_new_binding_centers_old(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.North)
    assert jgbot.hat(inout.OUT_HAT_1) == HatDirection.North
    jgbot.tap_button(inout.IN_BUTTON_4)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.East)

    assert jgbot.hat(inout.OUT_HAT_1) == HatDirection.Center
    assert jgbot.hat(inout.OUT_HAT_2) == HatDirection.East


def test_hat_direction_in_same_binding_has_no_center(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.North)
    assert jgbot.hat(inout.OUT_HAT_1) == HatDirection.North
    jgbot.tap_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "C"
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.East)

    assert (
        EventSpec(InputType.JoystickHat, inout.OUT_HAT_1, HatDirection.East)
        == jgbot.next_event()
    )
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_mode_change_stops_continuous_axis_motions(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_axes.xml")

    # Get the axis moving, then switch which should force the axis to stop moving.
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 1.0)
    jgbot.wait(0.1)
    jgbot.tap_button(inout.IN_BUTTON_4)
    assert jgbot.current_mode() == "B"
    stopped_value = jgbot.axis(inout.OUT_AXIS_1)
    jgbot.wait(0.1)

    # Make sure the axis has moved and that it hasn't kept moving.
    assert stopped_value > 0.0
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(stopped_value, abs=0.01)


def test_mode_change_keeps_inherited_axis_binding(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_axes.xml")

    jgbot.set_axis_absolute(inout.IN_AXIS_1, 1.0)
    jgbot.wait(0.1)
    jgbot.tap_button(inout.IN_BUTTON_2)
    assert jgbot.current_mode() == "C"
    switched_value = jgbot.axis(inout.OUT_AXIS_1)
    jgbot.wait(0.1)

    assert jgbot.axis(inout.OUT_AXIS_1) > switched_value + 0.02

    # Switching to B resets the binding, which stops the motion thread.
    jgbot.tap_button(inout.IN_BUTTON_4)


def test_axis_virtual_button_releases_after_mode_change(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")

    jgbot.set_axis_absolute(inout.IN_AXIS_2, 0.0)
    jgbot.set_axis_absolute(inout.IN_AXIS_2, 0.75)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.tap_button(inout.IN_BUTTON_4)
    assert jgbot.current_mode() == "B"
    jgbot.set_axis_absolute(inout.IN_AXIS_2, 0.0)

    assert not jgbot.button(inout.OUT_BUTTON_1)
