# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

from test.application.fakes import (
    LogicalInjector,
    Outputs,
)
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    gremlin_active,
    reload_action,
)

ACTION = "Run Command"
EXECUTABLE = r"C:\Program Files\Tool\Run.exe"
ARGUMENTS = '--profile "My Profile.xml" -v'


def test_saved_settings_start_command(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    outputs: Outputs,
) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.type_text(ui.find_item("executableField", action), EXECUTABLE)
    ui.type_text(ui.find_item("argumentsField", action), ARGUMENTS)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("executableField", action).property("text") == EXECUTABLE
    assert ui.find_item("argumentsField", action).property("text") == ARGUMENTS

    with gremlin_active(ui):
        inject_logical.button(label, True)
        outputs.start_detached.assert_called_once_with(
            EXECUTABLE, ["--profile", "My Profile.xml", "-v"]
        )
