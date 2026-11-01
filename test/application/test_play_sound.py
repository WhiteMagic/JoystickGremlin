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
    set_spin_box_value,
)

ACTION = "Play Sound"


def test_saved_settings_play_sound(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    tmp_path: pathlib.Path,
    inject_logical: LogicalInjector,
    outputs: Outputs,
) -> None:
    # Loading fails for a missing sound file.
    sound_path = tmp_path / "Alert Tone.WAV"
    sound_path.touch()
    sound_file = str(sound_path)

    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.type_text(ui.find_item("soundFileField", action), sound_file)
    set_spin_box_value(ui, ui.find_item("volumeSpinBox", action), 75)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("soundFileField", action).property("text") == sound_file
    assert ui.find_item("volumeSpinBox", action).property("value") == 75

    with gremlin_active(ui):
        inject_logical.button(label, True)
        outputs.audio["enqueue"].assert_called_once_with(sound_file, 75)
