# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_action,
    add_child_action,
    add_logical_input,
    add_logical_input_with_action,
    assigned_input_text,
    find_action,
    find_child_action,
    find_rebuilt_action,
    reload_action,
    rename_instance,
    select_logical_input,
)

ACTION = "Merge Axis"


def test_settings(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    first_label = add_logical_input(ui, "Axis")
    second_label = add_logical_input(ui, "Axis")

    select_logical_input(ui, first_label)
    action = add_action(ui, ACTION)
    rename_instance(ui, action, "pedals")
    ui.select(ui.find_item("mergeOperationCombo", action), "Maximum")
    ui.click(ui.find_item("firstAxisButton", action))
    action = add_child_action(ui, action, "Actions", "Description")

    # The second input reuses the existing instance.
    select_logical_input(ui, second_label)
    action = add_action(ui, ACTION)
    assert ui.find_item("instanceCombo", action).property("currentText") == "pedals"
    ui.click(ui.find_item("secondAxisButton", action))

    action = reload_action(ui, empty_profile, first_label, ACTION)
    assert ui.find_item("instanceCombo", action).property("currentText") == "pedals"
    assert (
        ui.find_item("mergeOperationCombo", action).property("currentText") == "Maximum"
    )
    assert ui.find_item("firstAxisButton", action).property(
        "text"
    ) == assigned_input_text(first_label)
    assert ui.find_item("secondAxisButton", action).property(
        "text"
    ) == assigned_input_text(second_label)
    find_child_action(ui, action, "children", "Description")

    select_logical_input(ui, second_label)
    action = find_action(ui, ACTION)
    assert ui.find_item("instanceCombo", action).property("currentText") == "pedals"


def test_new_instance(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Axis", ACTION)
    ui.click(ui.find_item("newInstanceButton", action))
    ui.select(ui.find_item("instanceCombo", action), "New Merge Axis 123")
    action = find_rebuilt_action(ui, ACTION, action)
    assert (
        ui.find_item("instanceCombo", action).property("currentText")
        == "New Merge Axis 123"
    )
    # Saving drops instances without both axes assigned.
    ui.click(ui.find_item("firstAxisButton", action))
    ui.click(ui.find_item("secondAxisButton", action))

    action = reload_action(ui, empty_profile, label, ACTION)
    assert (
        ui.find_item("instanceCombo", action).property("currentText")
        == "New Merge Axis 123"
    )
