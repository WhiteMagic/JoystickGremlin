# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

import sys
sys.path.append(".")

import pathlib

from gremlin.profile import Profile
from gremlin.action_analysis import _extract_sequences
from gremlin import shared_state


_PROFILE_FOR_ANALYSIS = "profile_for_analysis.xml"


def get_sequence_types(sequence: list) -> list[str]:
    return [action.tag for action in sequence]


def test_extract_sequences(xml_dir: pathlib.Path) -> None:
    p = Profile()
    shared_state.current_profile = p
    p.from_xml(str(xml_dir / _PROFILE_FOR_ANALYSIS))

    input_items = []
    for input_list in p.inputs.values():
        input_items.extend(input_list)

    axis_input = input_items[0]
    axis_root = axis_input.action_sequences[0].root_action
    assert axis_root is not None
    axis_sequences = _extract_sequences(axis_root)
    assert len(axis_sequences) == 1
    assert get_sequence_types(axis_sequences[0]) == [
        "root", "response-curve", "map-to-vjoy"
    ]

    button_input = input_items[1]
    button_root = button_input.action_sequences[0].root_action
    assert button_root is not None
    button_sequences = _extract_sequences(button_root)
    assert len(button_sequences) == 2
    assert get_sequence_types(button_sequences[0]) == [
        "root", "macro", "condition", "map-to-logical-device", "description", "change-mode"
    ]
    assert get_sequence_types(button_sequences[1]) == [
        "root", "macro", "condition", "map-to-vjoy", "change-mode"
    ]
