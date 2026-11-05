# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from gremlin.event_handler import EventHandler
from gremlin.types import HatDirection

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)

type InputChange = Callable[[JoystickGremlinBot], None]


def _set_hat(label: str, direction: HatDirection) -> InputChange:
    return lambda jgbot: jgbot.set_hat_direction(label, direction)


def _set_axis_absolute(label: str, value: float) -> InputChange:
    return lambda jgbot: jgbot.set_axis_absolute(label, value)


_INDIRECT_INVERTED_INPUTS = [
    pytest.param(
        _set_hat(
            "A: Hat Buttons - N: Map inverted to out_shared_mode_a, "
            "B: Hat Buttons - N: Map to out_shared_mode_b",
            HatDirection.North,
        ),
        _set_hat(
            "A: Hat Buttons - N: Map inverted to out_shared_mode_a, "
            "B: Hat Buttons - N: Map to out_shared_mode_b",
            HatDirection.Center,
        ),
        id="hat_buttons",
    ),
    pytest.param(
        _set_hat(
            "A: Hat Button N: Map inverted to out_shared_mode_a, "
            "B: Hat Button N: Map to out_shared_mode_b",
            HatDirection.North,
        ),
        _set_hat(
            "A: Hat Button N: Map inverted to out_shared_mode_a, "
            "B: Hat Button N: Map to out_shared_mode_b",
            HatDirection.Center,
        ),
        id="hat_virtual_button",
    ),
    pytest.param(
        _set_axis_absolute(
            "A: Axis Button 0.5-1.0: Map inverted to out_shared_mode_a, "
            "B: Axis Button 0.5-1.0: Map to out_shared_mode_b",
            0.75,
        ),
        _set_axis_absolute(
            "A: Axis Button 0.5-1.0: Map inverted to out_shared_mode_a, "
            "B: Axis Button 0.5-1.0: Map to out_shared_mode_b",
            0.0,
        ),
        id="axis_virtual_button",
    ),
]


def test_release_reaches_press_mode_only(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    assert jgbot.current_mode() == "A"
    jgbot.press_button("A: Map to out_button_mode_a, B: Map to out_button_mode_b")
    assert jgbot.button("out_button_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert not jgbot.button("out_button_mode_b")
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()
    jgbot.release_button("A: Map to out_button_mode_a, B: Map to out_button_mode_b")

    # Expect the release of A's press but no additional mappins from B are triggered.
    assert EventSpec("out_button_mode_a", False) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_inverted_release_activates_only_binding_of_release_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: with inverted outputs in both modes, a press in A and release in B turns on
    # B's output and leaves A's off.
    # Why: the release is the inverted output's activation, so it belongs to the mode it
    # happens in, as a normal button's press does.
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")

    jgbot.press_button(
        "A: Map inverted to out_shared_mode_a, B: Map inverted to out_shared_mode_b"
    )
    assert not jgbot.button("out_shared_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.release_button(
        "A: Map inverted to out_shared_mode_a, B: Map inverted to out_shared_mode_b"
    )

    assert not jgbot.button("out_shared_mode_a")
    assert jgbot.button("out_shared_mode_b")

    # B's release was the last one, so the next press in A has to reset B.
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"
    jgbot.press_button(
        "A: Map inverted to out_shared_mode_a, B: Map inverted to out_shared_mode_b"
    )
    assert not jgbot.button("out_shared_mode_b")


def test_inverted_press_in_other_binding_resets_release_binding(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: an inverted output left on by a release in A goes off on the next press in
    # B, and stays off back in A until the next press and release there.
    # Why: the press is the inverted output's deactivation, so it has to reach A as a
    # normal button's release does. Buttons get no refresh, so it can't restore.
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.tap_button(
        "A: Map inverted to out_inverted_mode_a, B: Map to out_plain_mode_b"
    )
    assert jgbot.button("out_inverted_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    jgbot.press_button(
        "A: Map inverted to out_inverted_mode_a, B: Map to out_plain_mode_b"
    )
    assert not jgbot.button("out_inverted_mode_a")
    assert jgbot.button("out_plain_mode_b")

    jgbot.release_button(
        "A: Map inverted to out_inverted_mode_a, B: Map to out_plain_mode_b"
    )
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"
    assert not jgbot.button("out_inverted_mode_a")
    jgbot.tap_button(
        "A: Map inverted to out_inverted_mode_a, B: Map to out_plain_mode_b"
    )
    assert jgbot.button("out_inverted_mode_a")


def test_release_activated_action_fires_only_in_release_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: X pressed in A and released in B runs only B's release-activated switch to
    # D, so unwinding from D returns to B rather than to A's target C.
    # Why: we decided that for a release-activated action the release is the
    # activation, which only happens in the active mode.
    jgbot.load_profile(profile_dir / "mode_change_activation.xml")
    label = "A: On release Switch to C, B: On release Switch to D"

    jgbot.press_button(label)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.release_button(label)
    assert jgbot.current_mode() == "D"

    # A firing first also ends in D, so the unwind shows whether C was entered.
    jgbot.tap_button("D: Unwind")
    assert jgbot.current_mode() == "B"


def test_both_edge_action_ignores_release_without_press(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: X pressed in A and released in B doesn't run B's switch to C, which fires
    # on press and release, and a press in B afterwards does.
    # Why: we decided the release only deactivates, and B's action was never activated.
    # A switch stands in for a sound or command, which a test can't observe.
    jgbot.load_profile(profile_dir / "mode_change_activation.xml")
    label = "A: Map to out_button_mode_a, B: On both Switch to C"

    jgbot.press_button(label)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    jgbot.release_button(label)
    assert jgbot.current_mode() == "B"

    jgbot.press_button(label)
    assert jgbot.current_mode() == "C"


def test_latched_output_survives_press_in_other_binding(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: an output latched by a smart toggle tap in A stays on while X is pressed and
    # released in B, and a tap back in A turns it off.
    # Why: we decided a latch is deliberate, so unlike an inverted output the next press
    # elsewhere doesn't end it.
    jgbot.load_profile(profile_dir / "mode_change_activation.xml")
    label = "A: Smart Toggle 0.2: out_latched_mode_a, B: Map to out_button_mode_b"
    # A tap is shorter than the 0.2 s toggle delay, so it latches.
    jgbot.tap_button(label)
    assert jgbot.button("out_latched_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    jgbot.press_button(label)
    assert jgbot.button("out_button_mode_b")
    jgbot.release_button(label)
    assert not jgbot.button("out_button_mode_b")
    assert jgbot.button("out_latched_mode_a")

    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"
    jgbot.tap_button(label)
    assert not jgbot.button("out_latched_mode_a")


@pytest.mark.parametrize(
    ("activate", "deactivate"),
    _INDIRECT_INVERTED_INPUTS,
)
def test_deactivation_in_other_binding_leaves_inverted_output_off(
    jgbot: JoystickGremlinBot,
    profile_dir: Path,
    activate: InputChange,
    deactivate: InputChange,
) -> None:
    # What: an inverted output driven by a hat or virtual button stays off when the
    # input is let go in another binding.
    # Why: these reach the action through a different path than a direct button.
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")

    # An axis virtual button can only press after the axis was outside its range.
    deactivate(jgbot)
    activate(jgbot)
    assert not jgbot.button("out_shared_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    deactivate(jgbot)

    assert not jgbot.button("out_shared_mode_a")


@pytest.mark.parametrize(
    ("activate", "deactivate"),
    _INDIRECT_INVERTED_INPUTS,
)
def test_activation_in_other_binding_resets_inverted_output(
    jgbot: JoystickGremlinBot,
    profile_dir: Path,
    activate: InputChange,
    deactivate: InputChange,
) -> None:
    # What: the inverted output reset also works when a hat or virtual button drives it.
    # Why: we decided all input types get it, and these reach the action through a
    # different path than a direct button.
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")

    # An axis virtual button can only press after the axis was outside its range.
    deactivate(jgbot)
    activate(jgbot)
    deactivate(jgbot)
    assert jgbot.button("out_shared_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    activate(jgbot)

    assert not jgbot.button("out_shared_mode_a")
    assert jgbot.button("out_shared_mode_b")


def test_inverted_logical_reset_reaches_bindings_of_output(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: when reset turns off an inverted logical button, an action bound to that
    # logical button sees the release (out_inverted_mode_a drives out_shared_mode_a
    # in A).
    # Why: without the event, that action's own output stays on with no way to clear it.
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")

    jgbot.tap_button(
        "A: Map inverted to out_inverted_mode_a, B: Map to out_plain_mode_b"
    )
    assert jgbot.button("out_inverted_mode_a")
    assert jgbot.button("out_shared_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    jgbot.press_button(
        "A: Map inverted to out_inverted_mode_a, B: Map to out_plain_mode_b"
    )

    assert not jgbot.button("out_inverted_mode_a")
    assert not jgbot.button("out_shared_mode_a")


def test_inverted_virtual_button_goes_off_only_on_own_range(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: A's inverted output, left on by a release in A, stays on through the switch
    # and B's own button on a different range, and goes off when the axis enters A's
    # range in B.
    # Why: we decided only A's own press turns it off, as with a direct button.
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")
    label = (
        "A: Axis Button 0.5-1.0: Map inverted to out_inverted_mode_a, "
        "B: Axis Button -1.0--0.5: Map to out_plain_mode_b"
    )
    # An axis virtual button can only press after the axis was outside its range.
    jgbot.set_axis_absolute(label, 0.0)
    jgbot.set_axis_absolute(label, 0.75)
    jgbot.set_axis_absolute(label, 0.0)
    assert jgbot.button("out_inverted_mode_a")

    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert jgbot.button("out_inverted_mode_a")

    jgbot.set_axis_absolute(label, -0.75)
    assert jgbot.button("out_plain_mode_b")
    assert jgbot.button("out_inverted_mode_a")

    jgbot.set_axis_absolute(label, 0.75)
    assert not jgbot.button("out_inverted_mode_a")


@pytest.mark.parametrize(
    "label",
    [
        pytest.param(
            "A: Hat Buttons - N: Map inverted to out_shared_mode_a, "
            "B: Hat Buttons - N: Map to out_shared_mode_b",
            id="hat_buttons",
        ),
        pytest.param(
            "A: Hat Button N: Map inverted to out_shared_mode_a, "
            "B: Hat Button N: Map to out_shared_mode_b",
            id="hat_virtual_button",
        ),
    ],
)
def test_other_hat_direction_in_other_binding_leaves_inverted_output_on(
    jgbot: JoystickGremlinBot, profile_dir: Path, label: str
) -> None:
    # What: A's inverted output, left on by North then centre in A, stays on when the
    # hat is pushed East in B.
    # Why: we decided only A's own direction turns it off, as only a press of the same
    # button does for a direct button.
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")
    jgbot.set_hat_direction(label, HatDirection.North)
    jgbot.set_hat_direction(label, HatDirection.Center)
    assert jgbot.button("out_shared_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    jgbot.set_hat_direction(label, HatDirection.East)

    assert jgbot.button("out_shared_mode_a")


def test_hat_center_reaches_direction_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a hat held in A isn't activated in B by the switch, and its centre reaches
    # A's output only.
    # Why: this is the hat form of the release routing and uses separate code.
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.North
    )
    assert jgbot.hat("out_hat_mode_a") == HatDirection.North
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert jgbot.hat("out_hat_mode_b") == HatDirection.Center
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()
    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.Center
    )

    assert EventSpec("out_hat_mode_a", HatDirection.Center) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_hat_direction_in_new_binding_centers_old_first(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a new direction in another binding centres the old output, then sets the
    # new one.
    # Why: the hat never passes through centre physically, so without the generated
    # centre the old output stays stuck. The order keeps both from being active at once.
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.North
    )
    assert jgbot.hat("out_hat_mode_a") == HatDirection.North
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()
    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.East
    )

    assert EventSpec("out_hat_mode_a", HatDirection.Center) == jgbot.next_event()
    assert EventSpec("out_hat_mode_b", HatDirection.East) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_hat_direction_in_same_binding_has_no_center(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.North
    )
    assert jgbot.hat("out_hat_mode_a") == HatDirection.North
    jgbot.tap_button("A: Switch to C")
    assert jgbot.current_mode() == "C"
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()
    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.East
    )

    assert EventSpec("out_hat_mode_a", HatDirection.East) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_absolute_axis_refreshes_on_mode_change(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: after a switch B's output has the current axis value through B's inverting
    # response curve without any movement, A's output keeps its value, and further
    # moves reach only B.
    # Why: the refresh is mandatory since the setting was removed, and only unit tests
    # check that it's called, not what the new binding ends up with.
    jgbot.load_profile(profile_dir / "mode_change_axes.xml")

    jgbot.set_axis_absolute(
        "A: Map to out_absolute_mode_a, B: Inverting curve to out_inverted_mode_b", 0.5
    )
    assert jgbot.axis("out_absolute_mode_a") == pytest.approx(0.5)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert jgbot.axis("out_inverted_mode_b") == pytest.approx(-0.5)
    assert jgbot.axis("out_absolute_mode_a") == pytest.approx(0.5)

    jgbot.set_axis_absolute(
        "A: Map to out_absolute_mode_a, B: Inverting curve to out_inverted_mode_b", 0.25
    )

    assert jgbot.axis("out_inverted_mode_b") == pytest.approx(-0.25)
    assert jgbot.axis("out_absolute_mode_a") == pytest.approx(0.5)


def test_mode_change_stops_axis_motion_and_return_restarts_it(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: relative axis motion stops on a switch to a mode without the binding, and
    # restarts on return while the axis is still deflected.
    # Why: a rate output keeps moving by itself, and reset ends its thread, so the
    # refresh on return has to start it again.
    jgbot.load_profile(profile_dir / "mode_change_axes.xml")

    # Get the axis moving, then switch which should force the axis to stop moving.
    jgbot.set_axis_absolute("A: Map relative scale 5.0 to out_relative_mode_a", 1.0)
    jgbot.wait(0.1)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    stopped_value = jgbot.axis("out_relative_mode_a")
    jgbot.wait(0.1)

    # Make sure the axis has moved and that it hasn't kept moving.
    assert stopped_value > 0.0
    assert jgbot.axis("out_relative_mode_a") == pytest.approx(stopped_value, abs=0.01)

    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"
    restarted_value = jgbot.axis("out_relative_mode_a")
    jgbot.wait(0.1)

    assert jgbot.axis("out_relative_mode_a") > restarted_value + 0.02


def test_mode_change_keeps_inherited_axis_binding(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    jgbot.load_profile(profile_dir / "mode_change_axes.xml")

    jgbot.set_axis_absolute("A: Map relative scale 5.0 to out_relative_mode_a", 1.0)
    jgbot.wait(0.1)
    jgbot.tap_button("A: Switch to C")
    assert jgbot.current_mode() == "C"
    switched_value = jgbot.axis("out_relative_mode_a")
    jgbot.wait(0.1)

    assert jgbot.axis("out_relative_mode_a") > switched_value + 0.02

    # Switching to B resets the binding, which stops the motion thread.
    jgbot.tap_button("A: Switch to B, B: Switch to A")


def test_axis_virtual_button_releases_after_mode_change(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a virtual button held across a switch stays pressed while the axis moves in
    # range, releases once on leaving it, and then no longer reacts to the axis in B.
    # Why: the old binding is only meant to get axis events until it releases. Today it
    # keeps them forever, so re-entering the range in B fires A's action.
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")

    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.0)
    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.75)
    assert jgbot.button("out_button_mode_a")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()

    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.8)
    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.85)
    assert jgbot.event_count() == 0

    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.0)
    assert EventSpec("out_button_mode_a", False) == jgbot.next_event()
    assert jgbot.event_count() == 0

    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.75)
    assert not jgbot.button("out_button_mode_a")
    assert jgbot.event_count() == 0


def test_axis_virtual_button_held_across_return_releases_once(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a virtual button held through A→B→A sends no extra press or release, and
    # leaving the range in A releases it once.
    # Why: back in A the binding gets axis events normally again, so it must not also
    # get them through the path that serves held buttons of inactive modes.
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")

    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.0)
    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "A"
    assert jgbot.button("out_button_mode_a")
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()

    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.8)
    assert jgbot.event_count() == 0
    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Map to out_button_mode_a", 0.0)

    assert EventSpec("out_button_mode_a", False) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_axis_virtual_button_temporary_mode_ends_on_leaving_range(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a virtual button that is itself Temporary enters T1 in range and returns to
    # A on leaving the range.
    # Why: the mode changes during the axis event that presses the button, which is the
    # one case where the held button is registered mid-dispatch. A throttle detent
    # switching modes is a real use of this.
    jgbot.load_profile(profile_dir / "mode_change_temporary.xml")

    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Temporary to T1", 0.0)
    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Temporary to T1", 0.75)
    assert jgbot.current_mode() == "T1"

    jgbot.set_axis_absolute("A: Axis Button 0.5-1.0: Temporary to T1", 0.0)

    assert jgbot.current_mode() == "A"


def test_axis_virtual_button_no_press_on_mode_entry(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: entering B with the axis already in range doesn't press B's virtual button,
    # on the first entry or a later one.
    # Why: we decided entry never presses. Today the first entry stays silent but a
    # later one presses, because the stored value makes the refresh look like a move.
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"
    assert not jgbot.button("out_button_mode_b")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.0)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")

    assert jgbot.current_mode() == "B"
    assert not jgbot.button("out_button_mode_b")


def test_axis_virtual_button_presses_on_first_move_after_entry(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: after entering B with the axis in range, the first move inside the range
    # presses the virtual button, and leaving the range releases it.
    # Why: this is the other half of the entry decision. The button stays up on entry
    # but must respond as soon as the user moves the axis.
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert not jgbot.button("out_button_mode_b")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.8)
    assert jgbot.button("out_button_mode_b")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.0)
    assert not jgbot.button("out_button_mode_b")


def test_axis_virtual_button_leaving_range_after_entry_sends_nothing(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: after entering B with the axis in range, leaving the range without a move
    # inside it sends no event.
    # Why: the button never pressed, so a release would fire release-activated actions
    # and turn on inverted outputs for a press that didn't happen.
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    # Drop the axis refresh events every mode change emits.
    jgbot.clear_events()

    jgbot.set_axis_absolute("B: Axis Button 0.5-1.0: Map to out_button_mode_b", 0.0)

    assert jgbot.event_count() == 0


def test_inverted_virtual_button_stays_off_leaving_range_after_entry(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: entering B with the axis inside the range of B's inverted virtual button,
    # then leaving the range without a move inside it, leaves the output off.
    # Why: the button never pressed, so nothing may activate the output. The test above
    # can't see a stray release, as its plain output is already off.
    jgbot.load_profile(profile_dir / "mode_change_virtual_button.xml")
    label = "B: Axis Button 0.5-1.0: Map inverted to out_inverted_mode_b"
    jgbot.set_axis_absolute(label, 0.75)
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    assert jgbot.current_mode() == "B"

    jgbot.set_axis_absolute(label, 0.0)

    assert not jgbot.button("out_inverted_mode_b")


def test_tempo_long_action_fires_in_press_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a tempo pressed in Default and switched away from before its timeout still
    # fires its long action there, the release ends it, and Second's binding sees
    # nothing.
    # Why: the timer runs outside event dispatch, so the routing doesn't cover it. The
    # press belongs to the old mode, so its pending action must complete there.
    jgbot.load_profile(profile_dir / "tempo.xml")

    jgbot.press_button(
        "Default: [Tempo 0.2 on release - short: out_short, long: out_long], "
        "Second: Map to out_second"
    )
    jgbot.tap_button("Default: Switch to Second")
    assert jgbot.current_mode() == "Second"
    # Long enough to pass the 0.2 s threshold in tempo.xml.
    jgbot.wait(0.25)
    assert jgbot.button("out_long")
    assert not jgbot.button("out_short")

    jgbot.release_button(
        "Default: [Tempo 0.2 on release - short: out_short, long: out_long], "
        "Second: Map to out_second"
    )

    assert not jgbot.button("out_long")
    assert not jgbot.button("out_second")


def test_temporary_release_reaches_output_held_in_temporary_mode(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: an output pressed in T1 stays on after T1 ends, and its release in A turns
    # it off.
    # Why: leaving a temporary mode is the most common way a button ends up held across
    # a switch, and T1's binding must still get the release after T1 is gone.
    jgbot.load_profile(profile_dir / "mode_change_temporary.xml")

    jgbot.press_button("A: Temporary to T1")
    assert jgbot.current_mode() == "T1"
    jgbot.press_button("T1: Map to out_button_mode_t1")
    assert jgbot.button("out_button_mode_t1")

    jgbot.release_button("A: Temporary to T1")
    assert jgbot.current_mode() == "A"
    assert jgbot.button("out_button_mode_t1")

    jgbot.release_button("T1: Map to out_button_mode_t1")
    assert not jgbot.button("out_button_mode_t1")


def test_temporary_only_undoes_own_transition(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: with X→T1 and Y→T2, releasing X in T2 changes nothing and releasing Y
    # returns to T1, which stays active with nothing held.
    # Why: we decided a Temporary only undoes its transition from the mode it entered.
    # Ending up in T1 is the accepted result of letting go after moving elsewhere.
    jgbot.load_profile(profile_dir / "mode_change_temporary.xml")

    jgbot.press_button("A: Temporary to T1")
    jgbot.press_button("T1: Temporary to T2")
    assert jgbot.current_mode() == "T2"

    jgbot.release_button("A: Temporary to T1")
    assert jgbot.current_mode() == "T2"

    jgbot.release_button("T1: Temporary to T2")
    assert jgbot.current_mode() == "T1"


def test_release_during_pause_applies_on_resume(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a release during a pause leaves A's output on until resume, which turns it
    # off, also when the mode changed before the pause.
    # Why: we decided resume syncs state. Today the release is lost and the output stays
    # stuck, a regression from R16 in this case. A switch has to come before the pause
    # because a change-mode binding is blocked during one.
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.press_button("A: Map to out_button_mode_a, B: Map to out_button_mode_b")
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    EventHandler().pause()
    jgbot.release_button("A: Map to out_button_mode_a, B: Map to out_button_mode_b")
    assert jgbot.button("out_button_mode_a")

    EventHandler().resume()

    assert not jgbot.button("out_button_mode_a")
    assert not jgbot.button("out_button_mode_b")


def test_hat_center_during_pause_applies_on_resume(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a hat centred during a pause leaves A's output set until resume, which
    # centres it.
    # Why: the hat form of the resume sync, using its own state and routing.
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.North
    )
    jgbot.tap_button("A: Switch to B, B: Switch to A")
    EventHandler().pause()
    jgbot.set_hat_direction(
        "A: Map to out_hat_mode_a, B: Map to out_hat_mode_b", HatDirection.Center
    )
    assert jgbot.hat("out_hat_mode_a") == HatDirection.North

    EventHandler().resume()

    assert jgbot.hat("out_hat_mode_a") == HatDirection.Center


def test_axis_move_during_pause_applies_on_resume(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: an axis moved during a pause leaves the output unchanged until resume, which
    # gives it the current value.
    # Why: we decided resume syncs state. Today the output stays stale until the axis
    # next moves.
    jgbot.load_profile(profile_dir / "mode_change_axes.xml")

    jgbot.set_axis_absolute(
        "A: Map to out_absolute_mode_a, B: Inverting curve to out_inverted_mode_b", 0.5
    )
    EventHandler().pause()
    jgbot.set_axis_absolute(
        "A: Map to out_absolute_mode_a, B: Inverting curve to out_inverted_mode_b", 0.25
    )
    assert jgbot.axis("out_absolute_mode_a") == pytest.approx(0.5)

    EventHandler().resume()

    assert jgbot.axis("out_absolute_mode_a") == pytest.approx(0.25)


def test_press_during_pause_stays_inactive_on_resume(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: a button pressed during a pause and still held at resume doesn't activate.
    # Why: the resume sync only sends releases and centres. A sync that also replayed
    # presses would fire actions the user pressed while Gremlin was paused.
    jgbot.load_profile(profile_dir / "mode_change_buttons.xml")

    EventHandler().pause()
    jgbot.press_button("A: Map to out_button_mode_a, B: Map to out_button_mode_b")

    EventHandler().resume()

    assert not jgbot.button("out_button_mode_a")


def test_inverted_release_during_pause_stays_off_after_resume(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: an inverted output pressed before a pause and released during it stays off
    # after resume, until the next press and release.
    # Why: we decided resume only deactivates, and the release is this output's
    # activation.
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")
    label = "A: Map inverted to out_inverted_mode_a, B: Map to out_plain_mode_b"
    jgbot.press_button(label)
    EventHandler().pause()
    jgbot.release_button(label)

    EventHandler().resume()

    assert not jgbot.button("out_inverted_mode_a")
    jgbot.tap_button(label)
    assert jgbot.button("out_inverted_mode_a")


def test_inverted_press_during_pause_turns_off_on_resume(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: an inverted output that is on stays on when its button is pressed during a
    # pause, and goes off at resume with the button still held.
    # Why: we decided resume only deactivates, and the press is this output's
    # deactivation.
    jgbot.load_profile(profile_dir / "mode_change_inverted.xml")
    label = "A: Map inverted to out_inverted_mode_a, B: Map to out_plain_mode_b"
    jgbot.tap_button(label)
    assert jgbot.button("out_inverted_mode_a")
    EventHandler().pause()
    jgbot.press_button(label)
    assert jgbot.button("out_inverted_mode_a")

    EventHandler().resume()

    assert not jgbot.button("out_inverted_mode_a")


def test_release_activated_action_does_not_fire_on_resume(
    jgbot: JoystickGremlinBot, profile_dir: Path
) -> None:
    # What: X held before a pause and released during it doesn't run A's
    # release-activated switch at resume, and a later tap still does.
    # Why: we decided resume only deactivates, otherwise the action would fire long
    # after the release. The tap shows the binding works, so the first check isn't
    # passing on a dead profile.
    jgbot.load_profile(profile_dir / "mode_change_activation.xml")
    label = "A: On release Switch to C, B: On release Switch to D"
    jgbot.press_button(label)
    EventHandler().pause()
    jgbot.release_button(label)

    EventHandler().resume()

    assert jgbot.current_mode() == "A"
    jgbot.tap_button(label)
    assert jgbot.current_mode() == "C"
