# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.macro import MacroManager
from gremlin.types import (
    HatDirection,
    InputType,
)

from . import input_definitions as inout
from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_simple(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    expected_event_sequence = [
        EventSpec(InputType.JoystickHat, inout.OUT_HAT_1, HatDirection.NorthEast),
        EventSpec(InputType.JoystickHat, inout.OUT_HAT_2, HatDirection.East),
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_3, True),
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_2, 0.7),
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_3, -0.5),
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_1, 0.2),
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_4, -0.1),
    ]

    # Trigger action execution and ensure the sequence is sent as expected.
    jgbot.press_button(inout.IN_BUTTON_1)
    jgbot.wait(0.05)
    for entry in expected_event_sequence:
        assert entry == jgbot.next_event()


def test_repeat(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.05

    expected_event_sequence = [
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True),
        EventSpec(InputType.JoystickHat, inout.OUT_HAT_1, HatDirection.North),
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False),
        EventSpec(InputType.JoystickHat, inout.OUT_HAT_1, HatDirection.Center),
    ]

    # Trigger action execution and ensure the sequence is repeated correctly.
    jgbot.press_button(inout.IN_BUTTON_2)
    for loop in range(3):
        with subtests.test("Repeat iteration", i=loop):
            for entry in expected_event_sequence:
                assert entry == jgbot.next_event()


def test_trigger_on_release(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    jgbot.press_button(inout.IN_BUTTON_3)
    # Ensure no events are generated before releasing the button.
    jgbot.wait(0.05)
    assert jgbot.event_count() == 0

    # Ensure macro is executed upon button release.
    jgbot.release_button(inout.IN_BUTTON_3)
    jgbot.wait(0.05)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
        == jgbot.next_event()
    )

    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_hat_single(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    jgbot.set_axis_absolute(inout.OUT_AXIS_1, 0.12)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.North)
    jgbot.wait(0.05)
    assert (
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_1, 0.17) == jgbot.next_event()
    )
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(0.17, abs=0.01)


def test_hat_count(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    jgbot.set_axis_absolute(inout.OUT_AXIS_1, -0.15)
    jgbot.wait(0.05)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.East)

    assert (
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_1, -0.05) == jgbot.next_event()
    )
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(-0.05, abs=0.01)
    assert (
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_1, 0.05) == jgbot.next_event()
    )
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(0.05, abs=0.01)


@pytest.mark.flaky(reruns=5)
def test_hat_toggle(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    jgbot.set_axis_absolute(inout.OUT_AXIS_1, -0.15)
    jgbot.wait(0.05)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.South)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.Center)

    expected_value = -0.15
    for _ in range(4):
        expected_value += 0.1
        assert (
            EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_1, expected_value)
            == jgbot.next_event()
        )

    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(expected_value, abs=0.01)
    assert jgbot.event_count() == 0
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.South)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.Center)
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_preemptive_exclusive_pauses_and_resumes_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    # Start a continuously repeating, non-exclusive macro.
    jgbot.press_button(inout.IN_BUTTON_4)
    assert (
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_2, 0.1) == jgbot.next_event()
    )

    # Trigger a preemptive, exclusive macro while the previous one is still
    # running. It must dispatch immediately rather than being queued behind it.
    jgbot.set_hat_direction(inout.IN_HAT_2, HatDirection.North)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_3, True)
        == jgbot.next_event()
    )

    # While the preemptive macro is still executing (it pauses for 0.3s
    # between its two actions), the interrupted macro must produce no further
    # events even though its own repeat delay (0.1s) has already elapsed.
    jgbot.wait(0.15)
    assert jgbot.event_count() == 0

    # Once the preemptive macro finishes, the interrupted macro must resume.
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_3, False)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_2, 0.2) == jgbot.next_event()
    )

    jgbot.release_button(inout.IN_BUTTON_4)


def test_non_preemptive_exclusive_waits_for_running_macro(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.0

    # Start a continuously repeating, non-exclusive macro.
    jgbot.press_button(inout.IN_BUTTON_4)
    assert (
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_2, 0.1) == jgbot.next_event()
    )

    # Trigger a non-preemptive exclusive macro. Unlike the preemptive case, it
    # must wait for the running macro to finish rather than interrupting it.
    jgbot.set_hat_direction(inout.IN_HAT_2, HatDirection.East)
    jgbot.wait(0.25)
    assert (
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_2, 0.2) == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_2, 0.3) == jgbot.next_event()
    )

    # Terminate the running macro, allowing the exclusive one to dispatch.
    jgbot.release_button(inout.IN_BUTTON_4)
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_4, True)
        == jgbot.next_event()
    )
    assert (
        EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_4, False)
        == jgbot.next_event()
    )


def test_hat_hold(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "macro.xml")
    MacroManager().default_delay = 0.05

    # Set axis state and wait to ensure synchronization.
    jgbot.set_axis_absolute(inout.OUT_AXIS_1, -0.15)
    jgbot.wait(0.05)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.West)

    expected_value = -0.15
    for _ in range(4):
        expected_value += 0.1
        assert (
            EventSpec(InputType.JoystickAxis, inout.OUT_AXIS_1, expected_value)
            == jgbot.next_event()
        )
        assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(expected_value, abs=0.01)

    assert jgbot.event_count() == 0
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.Center)
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()
