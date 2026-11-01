# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    reload_action,
    set_description,
)

ACTION = "Description"


def test_description(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    set_description(ui, action, "left engine 2")

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("descriptionField", action).property("text") == "left engine 2"
