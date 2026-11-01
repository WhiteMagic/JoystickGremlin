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

ACTION = "Tempo"


def test_settings(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    set_spin_box_value(ui, ui.find_item("thresholdSpinBox", action), 0.75)
    # Release is the default, so only press shows the setting surviving.
    ui.click(ui.find_item("pressRadio", action))
    action = add_child_action(ui, action, "Short press", "Description")
    action = add_child_action(ui, action, "Long press", "Description")

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("thresholdSpinBox", action).property("value") == pytest.approx(
        0.75
    )
    assert ui.find_item("pressRadio", action).property("checked")
    assert not ui.find_item("releaseRadio", action).property("checked")
    find_child_action(ui, action, "short", "Description")
    find_child_action(ui, action, "long", "Description")
