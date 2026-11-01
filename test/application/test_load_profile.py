# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    reload_action,
)

ACTION = "Load Profile"


def test_settings(
    ui: UiDriver, empty_profile: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    # Loading fails for a missing profile file.
    profile_path = tmp_path / "Flight Sim.xml"
    profile_path.touch()
    profile_file = str(profile_path)

    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.type_text(ui.find_item("profileFileField", action), profile_file)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("profileFileField", action).property("text") == profile_file
