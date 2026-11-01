# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest

from gremlin.tts import TTSQueueMode
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

ACTION = "Text to Speech"
TEXT = "Hello, World!"


def test_saved_settings_speak_text(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    outputs: Outputs,
) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.type_text(ui.find_item("speechTextField", action), TEXT)
    ui.select(ui.find_item("queueModeCombo", action), "Interrupt")
    set_spin_box_value(ui, ui.find_item("volumeSpinBox", action), 0.5)
    set_spin_box_value(ui, ui.find_item("rateSpinBox", action), -0.5)
    set_spin_box_value(ui, ui.find_item("pitchSpinBox", action), 0.25)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("speechTextField", action).property("text") == TEXT
    assert ui.find_item("queueModeCombo", action).property("currentText") == "Interrupt"
    for name, value in [
        ("volumeSpinBox", 0.5),
        ("rateSpinBox", -0.5),
        ("pitchSpinBox", 0.25),
    ]:
        assert ui.find_item(name, action).property("value") == pytest.approx(value)

    with gremlin_active(ui):
        inject_logical.button(label, True)
        outputs.tts["enqueue"].assert_called_once()
        request, mode = outputs.tts["enqueue"].call_args.args
        assert request.text == TEXT
        assert mode == TTSQueueMode.Interrupt
