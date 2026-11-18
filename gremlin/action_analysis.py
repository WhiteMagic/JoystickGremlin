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

# Actions along one path through an action tree, each with the behavior it runs under.
type ActionPath = list[tuple[AbstractActionData, InputType]]

AnalysisFunction = Callable[[list[ActionPath], InputType], list[UserFeedback]]


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
    paths = _extract_sequences(root_action, input_type)
    for fn in analysis_functions:
        feedback.extend(fn(paths, input_type))
    feedback = list(set(feedback))
    _feedback_cache[root_action.id] = (time.time(), feedback)
    return feedback


def _map_to_mouse_analysis(
    paths: list[ActionPath], behavior: InputType
) -> list[UserFeedback]:
    """Verifies the following aspects relating to the Map to Mouse action:

    - Warn when a joystick axis maps to a mouse movement and an axis value
      modifying action appears afterward.
    """
    if behavior != InputType.JoystickAxis:
        return []

    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path, behavior)

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


def _vjoy_analysis(paths: list[ActionPath], behavior: InputType) -> list[UserFeedback]:
    """Verifies the following aspects relating to the Map to vJoy action:

    - Warn when a Map to vJoy action is used with an axis value modifying action
      appearing afterward.
    """
    if behavior != InputType.JoystickAxis:
        return []

    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path, behavior)

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
    paths: list[ActionPath], behavior: InputType
) -> list[UserFeedback]:
    """Verifies the following aspects relating to the Dual Axis Deadzone action:

    - Warn when both a response curve and a dual axis deadzone action
      are present.
    """
    if behavior != InputType.JoystickAxis:
        return []

    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path, behavior)

        if TAG_RESPONSE_CURVE in path_tags and TAG_DUAL_AXIS_DEADZONE in path_tags:
            feedback.append(
                UserFeedback(
                    UserFeedback.FeedbackType.Info,
                    'Applying deadzones both in "Response Curve" and '
                    '"Dual Axis Deadzone" actions may lead to unexpected results.',
                )
            )

    return feedback


def _path_as_tags(path: ActionPath, behavior: InputType) -> list[str]:
    return [action.tag for action, entry_behavior in path if entry_behavior == behavior]


def _action_behaviors(
    action: AbstractActionData, behavior: InputType
) -> dict[uuid.UUID, InputType]:
    """Returns the behaviors of all actions in this action subtree.

    Args:
        action: root of the action tree
        behavior: behavior the action operates under

    Returns:
        Behavior of each action in the tree, keyed by action id
    """
    behaviors = {action.id: behavior}
    child_behavior = action.child_behavior_type or behavior
    for child in action.get_actions()[0]:
        behaviors.update(_action_behaviors(child, child_behavior))
    return behaviors


def _extract_sequences(
    root: AbstractActionData, input_type: InputType
) -> list[ActionPath]:
    behaviors = _action_behaviors(root, input_type)
    complete_paths = []

    # Each entry in the stack has the following information:
    # (action, current path, remaining siblings)
    stack = [(root, [], [])]
    while stack:
        action, path, siblings = stack.pop()
        path.append((action, behaviors[action.id]))
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
