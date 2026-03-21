# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from collections.abc import Callable
import time
import uuid

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


_CACHE_TTL = 0.1
_feedback_cache : dict[uuid.UUID, tuple[float, list[UserFeedback]]] = {}


def action_sequence_feedback(binding: InputItemBinding) -> list[UserFeedback]:
    functions = [
        _dual_axis_response_curve_analysis,
        _map_to_mouse_analysis,
        _vjoy_analysis
    ]

    cache_key = binding.root_action.id
    if cache_key in _feedback_cache:
        cache_time, cached_feedback = _feedback_cache[cache_key]
        if time.time() - cache_time < _CACHE_TTL:
            _feedback_cache[cache_key] = (time.time(), cached_feedback)
            print("Using cached feedback")
            return cached_feedback

    feedback = []
    if binding.root_action:
        paths = _extract_sequences(binding.root_action)
        for fn in functions:
            feedback.extend(fn(paths, binding.behavior))
    feedback = list(set(feedback))
    _feedback_cache[cache_key] = (time.time(), feedback)
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

            if rc_after or darc_after:
                feedback.append(UserFeedback(
                    UserFeedback.FeedbackType.Warning,
                    "Actions are executed sequentially, the Map to vJoy action "
                    "will not be affected by actions after it."
                ))
        except ValueError:
            continue

    return feedback


def _dual_axis_response_curve_analysis(
    paths: list[list[AbstractActionData]],
    behavior: InputType
) -> list[UserFeedback]:
    if behavior != InputType.JoystickAxis:
        return []

    feedback = []
    for path in paths:
        path_tags = _path_as_tags(path)

        if TAG_RESPONSE_CURVE in path_tags and TAG_DUAL_AXIS in path_tags:
            feedback.append(UserFeedback(
                UserFeedback.FeedbackType.Info,
                "Applying deadzones both in \"Response Curve\" and "
                "\"Dual Axis Deadzone\" actions may lead to unexpected results."
            ))

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
