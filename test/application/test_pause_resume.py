# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    reload_action,
)

ACTION = "Pause and Resume"
OPERATIONS = ["pauseRadio", "resumeRadio", "toggleRadio"]


@pytest.mark.parametrize("operation", ["resumeRadio", "toggleRadio"])
def test_operation(ui: UiDriver, empty_profile: pathlib.Path, operation: str) -> None:
    # Pause is the default, so a lost setting would still show it and we thus don't
    # test for it here.
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.click(ui.find_item(operation, action))

    action = reload_action(ui, empty_profile, label, ACTION)
    checked_radios = [
        radio for radio in OPERATIONS if ui.find_item(radio, action).property("checked")
    ]
    assert checked_radios == [operation]
