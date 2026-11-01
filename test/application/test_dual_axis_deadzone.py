# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_action,
    add_child_action,
    add_logical_input,
    assigned_input_text,
    find_action,
    find_child_action,
    find_rebuilt_action,
    reload_action,
    rename_instance,
    select_logical_input,
    set_spin_box_value,
)

ACTION = "Dual Axis Deadzone"


def test_settings(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    first_label = add_logical_input(ui, "Axis")
    second_label = add_logical_input(ui, "Axis")

    select_logical_input(ui, first_label)
    action = add_action(ui, ACTION)
    rename_instance(ui, action, "stick")
    set_spin_box_value(ui, ui.find_item("innerDeadzoneSpinBox", action), 0.2)
    set_spin_box_value(ui, ui.find_item("outerDeadzoneSpinBox", action), 0.8)
    ui.click(ui.find_item("firstAxisButton", action))
    action = add_child_action(ui, action, "First axis actions", "Description")
    action = add_child_action(ui, action, "Second axis actions", "Description")

    # Each input creates its own instance, so the second selects the first's.
    select_logical_input(ui, second_label)
    action = add_action(ui, ACTION)
    ui.select(ui.find_item("instanceCombo", action), "stick")
    action = find_rebuilt_action(ui, ACTION, action)
    assert ui.find_item("instanceCombo", action).property("currentText") == "stick"
    ui.click(ui.find_item("secondAxisButton", action))

    action = reload_action(ui, empty_profile, first_label, ACTION)
    assert ui.find_item("instanceCombo", action).property("currentText") == "stick"
    assert ui.find_item("innerDeadzoneSpinBox", action).property(
        "value"
    ) == pytest.approx(0.2)
    assert ui.find_item("outerDeadzoneSpinBox", action).property(
        "value"
    ) == pytest.approx(0.8)
    assert ui.find_item("firstAxisButton", action).property(
        "text"
    ) == assigned_input_text(first_label)
    assert ui.find_item("secondAxisButton", action).property(
        "text"
    ) == assigned_input_text(second_label)
    find_child_action(ui, action, "first", "Description")
    find_child_action(ui, action, "second", "Description")

    select_logical_input(ui, second_label)
    action = find_action(ui, ACTION)
    assert ui.find_item("instanceCombo", action).property("currentText") == "stick"
