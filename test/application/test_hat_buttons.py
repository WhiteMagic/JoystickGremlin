# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_child_action,
    add_logical_input_with_action,
    find_child_action,
    find_rebuilt_action,
    reload_action,
)

ACTION = "Hat as Buttons"


def test_settings(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Hat", ACTION)
    ui.click(ui.find_item("eightWayRadio", action))
    action = find_rebuilt_action(ui, ACTION, action)
    # Only the 8 way mode has diagonal directions.
    action = add_child_action(ui, action, "North-East", "Description")

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("eightWayRadio", action).property("checked")
    assert not ui.find_item("fourWayRadio", action).property("checked")
    find_child_action(ui, action, "North-East", "Description")
