# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import InputType

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)
from .input_definitions import (
    IN_AXIS_1,
    OUT_BUTTON_1,
    OUT_BUTTON_2,
)


def test_positive_trigger(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "axis_delta.xml")

    # Initialize last_value without accumulating.
    jgbot.set_axis_absolute(IN_AXIS_1, 0.0)

    # Move past the positive threshold (0.3).
    jgbot.set_axis_absolute(IN_AXIS_1, 0.35)

    assert EventSpec(InputType.JoystickButton, OUT_BUTTON_1, True) == jgbot.next_event()
    assert (
        EventSpec(InputType.JoystickButton, OUT_BUTTON_1, False) == jgbot.next_event()
    )

    # OUT_BUTTON_2 must not have fired.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_negative_trigger(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "axis_delta.xml")

    jgbot.set_axis_absolute(IN_AXIS_1, 0.0)
    jgbot.set_axis_absolute(IN_AXIS_1, -0.35)

    assert EventSpec(InputType.JoystickButton, OUT_BUTTON_2, True) == jgbot.next_event()
    assert (
        EventSpec(InputType.JoystickButton, OUT_BUTTON_2, False) == jgbot.next_event()
    )

    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_no_trigger_below_threshold(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "axis_delta.xml")

    jgbot.set_axis_absolute(IN_AXIS_1, 0.0)

    # Small movements in both directions — accumulator never reaches ±0.3.
    jgbot.set_axis_absolute(IN_AXIS_1, 0.1)
    jgbot.set_axis_absolute(IN_AXIS_1, -0.1)
    jgbot.set_axis_absolute(IN_AXIS_1, 0.1)

    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_accumulation_positive(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "axis_delta.xml")

    jgbot.set_axis_absolute(IN_AXIS_1, 0.0)

    # Three steps of +0.11 each: 0.11 + 0.11 + 0.11 = 0.33 > 0.3.
    jgbot.set_axis_absolute(IN_AXIS_1, 0.11)
    jgbot.set_axis_absolute(IN_AXIS_1, 0.22)
    jgbot.set_axis_absolute(IN_AXIS_1, 0.33)

    assert EventSpec(InputType.JoystickButton, OUT_BUTTON_1, True) == jgbot.next_event()
    assert (
        EventSpec(InputType.JoystickButton, OUT_BUTTON_1, False) == jgbot.next_event()
    )

    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_accumulation_negative(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "axis_delta.xml")

    jgbot.set_axis_absolute(IN_AXIS_1, 0.0)

    jgbot.set_axis_absolute(IN_AXIS_1, -0.11)
    jgbot.set_axis_absolute(IN_AXIS_1, -0.22)
    jgbot.set_axis_absolute(IN_AXIS_1, -0.33)

    assert EventSpec(InputType.JoystickButton, OUT_BUTTON_2, True) == jgbot.next_event()
    assert (
        EventSpec(InputType.JoystickButton, OUT_BUTTON_2, False) == jgbot.next_event()
    )

    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_accumulator_resets_after_trigger(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "axis_delta.xml")

    jgbot.set_axis_absolute(IN_AXIS_1, 0.0)
    jgbot.set_axis_absolute(IN_AXIS_1, 0.35)

    # Consume the first pulse.
    jgbot.next_event()
    jgbot.next_event()
    jgbot.clear_events()

    # After reset the accumulator is 0.0; a small move should not trigger.
    jgbot.set_axis_absolute(IN_AXIS_1, 0.45)

    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()
