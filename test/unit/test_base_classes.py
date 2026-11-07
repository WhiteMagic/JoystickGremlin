# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pytest

from action_plugins.run_command import (
    RunCommandData,
    RunCommandFunctor,
)
from gremlin.base_classes import Value
from gremlin.types import (
    ActionActivationMode,
    HatDirection,
    InputType,
    ModeType,
)

_BOTH = ActionActivationMode.Both
_PRESS = ActionActivationMode.Press
_RELEASE = ActionActivationMode.Release
_DEACTIVATED = ActionActivationMode.Deactivated
_NATIVE = ModeType.Native
_FOREIGN = ModeType.Foreign


def _functor(activation_mode: ActionActivationMode) -> RunCommandFunctor:
    # Any leaf works, the checks only read the activation mode and the value.
    action = RunCommandData(InputType.JoystickButton)
    action.activation_mode = activation_mode
    return RunCommandFunctor(action)


@pytest.mark.parametrize(
    ("activation_mode", "inverted", "current", "mode_type", "runs"),
    [
        pytest.param(_BOTH, False, True, _NATIVE, True, id="both_press"),
        pytest.param(_BOTH, False, False, _NATIVE, True, id="both_release"),
        pytest.param(_PRESS, False, True, _NATIVE, True, id="press_only"),
        pytest.param(_PRESS, False, False, _NATIVE, False, id="press_only_on_release"),
        pytest.param(_RELEASE, False, False, _NATIVE, True, id="release_only"),
        pytest.param(_RELEASE, False, True, _NATIVE, False, id="release_only_on_press"),
        pytest.param(_DEACTIVATED, False, True, _NATIVE, False, id="deactivated"),
        pytest.param(_BOTH, False, False, _FOREIGN, True, id="foreign_release"),
        pytest.param(_BOTH, False, True, _FOREIGN, False, id="foreign_press"),
        pytest.param(_BOTH, True, True, _FOREIGN, True, id="foreign_inverted_press"),
        pytest.param(
            _BOTH, True, False, _FOREIGN, False, id="foreign_inverted_release"
        ),
        pytest.param(
            _RELEASE, False, False, _FOREIGN, False, id="foreign_release_only"
        ),
        pytest.param(
            _BOTH, False, HatDirection.Center, _FOREIGN, True, id="foreign_hat_center"
        ),
        # 0.0 equals False, only the axis check keeps it from running.
        pytest.param(_BOTH, False, 0.0, _FOREIGN, False, id="foreign_axis"),
    ],
)
def test_should_execute(
    activation_mode: ActionActivationMode,
    inverted: bool,
    current: bool | float | HatDirection,
    mode_type: ModeType,
    runs: bool,
) -> None:
    functor = _functor(activation_mode)

    assert functor._should_execute(Value(current, mode_type), inverted) is runs


@pytest.mark.parametrize(
    ("activation_mode", "inverted", "current", "wants_next"),
    [
        pytest.param(_BOTH, False, True, True, id="press"),
        pytest.param(_BOTH, False, False, False, id="release"),
        pytest.param(_PRESS, False, True, False, id="not_both"),
        pytest.param(_BOTH, True, False, True, id="inverted_release"),
        pytest.param(_BOTH, True, True, False, id="inverted_press"),
        pytest.param(_BOTH, False, HatDirection.North, True, id="hat_direction"),
        pytest.param(_BOTH, False, HatDirection.Center, False, id="hat_center"),
        pytest.param(_BOTH, False, 0.5, False, id="axis"),
    ],
)
def test_requires_paired_event(
    activation_mode: ActionActivationMode,
    inverted: bool,
    current: bool | float | HatDirection,
    wants_next: bool,
) -> None:
    functor = _functor(activation_mode)

    assert (
        functor._requires_paired_event(Value(current, _NATIVE), inverted) is wants_next
    )
