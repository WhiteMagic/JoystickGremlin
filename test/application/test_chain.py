# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    action_order,
    add_child_action,
    add_description,
    add_logical_input_with_action,
    drag_action,
    find_action,
    find_action_list,
    find_child_action,
    find_description,
    find_rebuilt_action,
    reload_action,
    set_description,
    set_spin_box_value,
)

ACTION = "Chain"


def test_settings(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    set_spin_box_value(ui, ui.find_item("timeoutSpinBox", action), 2.5)
    for _ in range(2):
        ui.click(ui.find_item("addSequenceButton", action))
    descriptions = ["first", "second", "third"]
    for index, description in enumerate(descriptions):
        action = add_child_action(ui, action, f"Sequence {index + 1}", "Description")
        child = find_child_action(ui, action, str(index), "Description")
        set_description(ui, child, description)
    ui.click(ui.find_item("removeSequenceButton_1", action))
    action = find_rebuilt_action(ui, ACTION, action)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("timeoutSpinBox", action).property("value") == pytest.approx(
        2.5
    )
    ui.find_item("slotHeader_Sequence 2", action)
    assert not ui.find_all("slotHeader_Sequence 3", action)
    for index, description in enumerate(["first", "third"]):
        child = find_child_action(ui, action, str(index), "Description")
        assert ui.find_item("descriptionField", child).property("text") == description


def test_drag_actions(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.click(ui.find_item("addSequenceButton", action))
    add_description(ui, "first", action, "Sequence 1")
    add_description(ui, "second", find_action(ui, ACTION), "Sequence 1")
    add_description(ui, "third", find_action(ui, ACTION), "Sequence 2")
    drag_action(
        ui,
        find_description(ui, "second"),
        find_action_list(ui, "0", find_action(ui, ACTION)),
        position=0,
    )
    drag_action(
        ui,
        find_description(ui, "first"),
        find_action_list(ui, "1", find_action(ui, ACTION)),
        position=1,
    )

    action = reload_action(ui, empty_profile, label, ACTION)
    assert action_order(ui, find_action_list(ui, "0", action)) == ["second"]
    assert action_order(ui, find_action_list(ui, "1", action)) == ["third", "first"]
