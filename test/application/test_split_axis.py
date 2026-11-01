# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_child_action,
    add_logical_input_with_action,
    find_child_action,
    reload_action,
    set_spin_box_value,
)

ACTION = "Split Axis"


def test_settings(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Axis", ACTION)
    set_spin_box_value(ui, ui.find_item("splitValueSpinBox", action), 0.3)
    action = add_child_action(ui, action, "Lower / left", "Description")
    action = add_child_action(ui, action, "Upper / right", "Description")

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("splitValueSpinBox", action).property("value") == pytest.approx(
        0.3
    )
    find_child_action(ui, action, "lower", "Description")
    find_child_action(ui, action, "upper", "Description")
