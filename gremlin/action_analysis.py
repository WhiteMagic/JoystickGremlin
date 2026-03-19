# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from collections.abc import Callable

from gremlin.base_classes import AbstractActionData, UserFeedback
from gremlin.types import InputType
from gremlin.profile import InputItemBinding


AnalysisFunction = Callable[[InputItemBinding, InputType], list[UserFeedback]]


# Definition of action tags. Actions are not imported due to their significant
# dependencies, especially on Qt.
TAG_DUAL_AXIS = "dual-axis-deadzone"
TAG_MAP_TO_MOUSE = "map-to-mouse"
TAG_RESPONSE_CURVE = "response-curve"
TAG_VJOY = "map-to-vjoy"


def action_sequence_feedback(binding: InputItemBinding) -> list[UserFeedback]:
    functions = [
        _map_to_mouse_analysis,
        _vjoy_analysis
    ]

    feedback = []
    if binding.root_action:
        paths = _extract_sequences(binding.root_action)
        for fn in functions:
            feedback.extend(fn(paths, binding.behavior))
    return feedback


def _map_to_mouse_analysis(
    paths: list[list[AbstractActionData]],
    behavior: InputType
) -> list[UserFeedback]:
    if behavior != InputType.JoystickAxis:
        return []

    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path)

        try:
            mm_index = path_tags.index(TAG_MAP_TO_MOUSE)
            rc_after = TAG_RESPONSE_CURVE in path_tags[mm_index:]
            darc_after = TAG_DUAL_AXIS in path_tags[mm_index:]

            if rc_after or darc_after:
                feedback.append(UserFeedback(
                    UserFeedback.FeedbackType.Warning,
                    "Actions are executed sequentially, the Map to Mouse action "
                    "will not be affected by actions after it."
                ))
        except ValueError:
            continue

    return feedback

def _vjoy_analysis(
    paths: list[list[AbstractActionData]],
    behavior: InputType
) -> list[UserFeedback]:
    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path)

        try:
            vjoy_index = path_tags.index(TAG_VJOY)

            rc_after = TAG_RESPONSE_CURVE in path_tags[vjoy_index:]
            darc_after = TAG_DUAL_AXIS in path_tags[vjoy_index:]
            # mm_before = TAG_MAP_TO_MOUSE in path_tags[:vjoy_index] \
            #     and behavior == InputType.JoystickAxis

            if rc_after or darc_after:
                feedback.append(UserFeedback(
                    UserFeedback.FeedbackType.Warning,
                    "Actions are executed sequentially, the Map to vJoy action "
                    "will not be affected by actions after it."
                ))
            # if mm_before:
            #     pass
        except ValueError:
            continue

    return feedback


def _path_as_tags(path: list[AbstractActionData]) -> list[str]:
    return [action.tag for action in path]


def _extract_sequences(
    root: AbstractActionData
) -> list[list[AbstractActionData]]:
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
                        stack.append(
                            (siblings[0], branch_path, siblings[1:])
                        )
                else:
                    stack.append(
                        (container[0], branch_path, container[1:] + siblings)
                    )

    return complete_paths
