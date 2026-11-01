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

ACTION = "Smart Toggle"


def test_settings(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    set_spin_box_value(ui, ui.find_item("delaySpinBox", action), 0.75)
    action = add_child_action(ui, action, "Actions", "Description")

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("delaySpinBox", action).property("value") == pytest.approx(0.75)
    find_child_action(ui, action, "children", "Description")
