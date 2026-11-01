# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest

from gremlin import keyboard
from test.application.fakes import KeyboardInjector
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    action_order,
    add_child_action,
    add_logical_input_with_action,
    find_action_list,
    find_child_action,
    record_inputs,
    reload_action,
    set_spin_box_value,
)

ACTION = "Axis Delta"
KEYBOARD_ACTION = "Map to Keyboard"


def test_settings(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Axis", ACTION)
    set_spin_box_value(ui, ui.find_item("thresholdSpinBox", action), 0.25)
    action = add_child_action(ui, action, "Positive change", "Description")
    action = add_child_action(ui, action, "Negative change", "Description")

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("thresholdSpinBox", action).property("value") == pytest.approx(
        0.25
    )
    find_child_action(ui, action, "positive", "Description")
    find_child_action(ui, action, "negative", "Description")


def test_child_actions(
    ui: UiDriver, empty_profile: pathlib.Path, inject_keyboard: KeyboardInjector
) -> None:
    label, action = add_logical_input_with_action(ui, "Axis", ACTION)
    keys = {"positive": "a", "negative": "b"}
    for container, key_name in keys.items():
        action = add_child_action(
            ui, action, f"{container.title()} change", KEYBOARD_ACTION
        )
        child = find_child_action(ui, action, container, KEYBOARD_ACTION)

        def press_key(key_name: str = key_name) -> None:
            inject_keyboard.key(key_name, True)
            inject_keyboard.key(key_name, False)

        record_inputs(ui, ui.find_item("keyCombinationButton", child), press_key)

    action = reload_action(ui, empty_profile, label, ACTION)
    for container, key_name in keys.items():
        assert action_order(ui, find_action_list(ui, container, action)) == [
            KEYBOARD_ACTION
        ]
        child = find_child_action(ui, action, container, KEYBOARD_ACTION)
        assert (
            ui.find_item("keyCombinationButton", child).property("text")
            == keyboard.key_from_name(key_name).name
        )
