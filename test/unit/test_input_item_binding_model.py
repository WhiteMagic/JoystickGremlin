# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

from action_plugins.description import DescriptionData
from action_plugins.root import RootData
from gremlin.profile import (
    InputItem,
    InputItemBinding,
    Profile,
)
from gremlin.types import InputType
from gremlin.ui.profile import InputItemBindingModel


def _make_binding_model(behavior: InputType) -> InputItemBindingModel:
    profile = Profile()
    input_item = InputItem(profile.library)
    binding = InputItemBinding(input_item)
    binding.root_action = RootData(behavior)
    binding.behavior = behavior
    profile.library.add_action(binding.root_action)

    child_one = DescriptionData(behavior)
    child_two = DescriptionData(behavior)
    profile.library.add_action(child_one)
    profile.library.add_action(child_two)
    binding.root_action.insert_action(child_one, "children")
    binding.root_action.insert_action(child_two, "children")

    return InputItemBindingModel(binding)


def test_behavior_switch_clears_children() -> None:
    iibm = _make_binding_model(InputType.JoystickButton)
    binding = iibm.input_item_binding
    root_id = binding.root_action.id
    child_ids = [child.id for child in binding.root_action.get_actions()[0]]

    assert len(child_ids) == 2
    assert all(binding.library.has_action(cid) for cid in child_ids)

    iibm.behavior = InputType.to_string(InputType.JoystickAxis)

    # Root action identity is preserved, but its contents are wiped.
    assert binding.root_action.id == root_id
    assert binding.root_action.get_actions()[0] == []
    assert binding.behavior == InputType.JoystickAxis
    assert all(not binding.library.has_action(cid) for cid in child_ids)


def test_behavior_switch_noop_keeps_children() -> None:
    iibm = _make_binding_model(InputType.JoystickButton)
    binding = iibm.input_item_binding
    child_ids = [child.id for child in binding.root_action.get_actions()[0]]

    iibm.behavior = InputType.to_string(InputType.JoystickButton)

    assert [child.id for child in binding.root_action.get_actions()[0]] == child_ids
    assert all(binding.library.has_action(cid) for cid in child_ids)
