# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from gremlin.base_classes import (
    AbstractActionData,
    UserFeedback,
)
from gremlin.types import InputType

if TYPE_CHECKING:
    from action_plugins.root import RootData

AnalysisFunction = Callable[
    [list[list[AbstractActionData]], InputType], list[UserFeedback]
]


# Definition of action tags. Actions are not imported due to their significant
# dependencies, especially on Qt.
TAG_DUAL_AXIS_DEADZONE = "dual-axis-deadzone"
TAG_MAP_TO_MOUSE = "map-to-mouse"
TAG_RESPONSE_CURVE = "response-curve"
TAG_VJOY = "map-to-vjoy"


_CACHE_TTL = 0.25
_feedback_cache: dict[uuid.UUID, tuple[float, list[UserFeedback]]] = {}


def action_sequence_feedback(
    root_action: RootData, input_type: InputType
) -> list[UserFeedback]:
    analysis_functions: list[AnalysisFunction] = [
        _dual_axis_response_curve_analysis,
        _map_to_mouse_analysis,
        _vjoy_analysis,
    ]

    if root_action.id in _feedback_cache:
        cache_time, cached_feedback = _feedback_cache[root_action.id]
        if time.time() - cache_time < _CACHE_TTL:
            return cached_feedback

    feedback = []
    paths = _extract_sequences(root_action)
    for fn in analysis_functions:
        feedback.extend(fn(paths, input_type))
    feedback = list(set(feedback))
    _feedback_cache[root_action.id] = (time.time(), feedback)
    return feedback


def _map_to_mouse_analysis(
    paths: list[list[AbstractActionData]], behavior: InputType
) -> list[UserFeedback]:
    """Verifies the following aspects relating to the Map to Mouse action:

    - Warn when a joystick axis maps to a mouse movement and an axis value
      modifying action appears afterward.
    """
    if behavior != InputType.JoystickAxis:
        return []

    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path)

        try:
            mm_index = path_tags.index(TAG_MAP_TO_MOUSE)
            rc_after = TAG_RESPONSE_CURVE in path_tags[mm_index:]
            dadz_after = TAG_DUAL_AXIS_DEADZONE in path_tags[mm_index:]

            if rc_after or dadz_after:
                feedback.append(
                    UserFeedback(
                        UserFeedback.FeedbackType.Warning,
                        "Actions are executed sequentially, the Map to Mouse action "
                        "will not be affected by actions after it.",
                    )
                )
        except ValueError:
            continue

    return feedback


def _vjoy_analysis(
    paths: list[list[AbstractActionData]], behavior: InputType
) -> list[UserFeedback]:
    """Verifies the following aspects relating to the Map to vJoy action:

    - Warn when a Map to vJoy action is used with an axis value modifying action
      appearing afterward.
    """
    if behavior != InputType.JoystickAxis:
        return []

    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path)

        try:
            vjoy_index = path_tags.index(TAG_VJOY)

            rc_after = TAG_RESPONSE_CURVE in path_tags[vjoy_index:]
            dadz_after = TAG_DUAL_AXIS_DEADZONE in path_tags[vjoy_index:]

            if rc_after or dadz_after:
                feedback.append(
                    UserFeedback(
                        UserFeedback.FeedbackType.Warning,
                        "Actions are executed sequentially, the Map to vJoy action "
                        "will not be affected by actions after it.",
                    )
                )
        except ValueError:
            continue

    return feedback


def _dual_axis_response_curve_analysis(
    paths: list[list[AbstractActionData]], behavior: InputType
) -> list[UserFeedback]:
    """Verifies the following aspects relating to the Dual Axis Deadzone action:

    - Warn when both a response curve and a dual axis deadzone action
      are present.
    """
    if behavior != InputType.JoystickAxis:
        return []

    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path)

        if TAG_RESPONSE_CURVE in path_tags and TAG_DUAL_AXIS_DEADZONE in path_tags:
            feedback.append(
                UserFeedback(
                    UserFeedback.FeedbackType.Info,
                    'Applying deadzones both in "Response Curve" and '
                    '"Dual Axis Deadzone" actions may lead to unexpected results.',
                )
            )

    return feedback


def _path_as_tags(path: list[AbstractActionData]) -> list[str]:
    return [action.tag for action in path]


def _extract_sequences(root: AbstractActionData) -> list[list[AbstractActionData]]:
    complete_paths = []

    # Each entry in the stack has the following information:
    # (action, current path, remaining siblings)
    stack = [(root, [], [])]
    while stack:
        action, path, siblings = stack.pop()
        path.append(action)
        selectors = action._valid_selectors()

        if not selectors:
            if siblings:
                stack.append((siblings[0], path, siblings[1:]))
            else:
                complete_paths.append(path)
        else:
            for container in [action._get_container(s) for s in selectors]:
                branch_path = path.copy()
                if not container:
                    if not siblings:
                        complete_paths.append(branch_path)
                    else:
                        stack.append((siblings[0], branch_path, siblings[1:]))
                else:
                    stack.append((container[0], branch_path, container[1:] + siblings))

    return complete_paths
