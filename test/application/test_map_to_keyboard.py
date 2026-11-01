# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest
from PySide6 import QtQuick

from gremlin import keyboard
from test.application.fakes import (
    KeyboardInjector,
    LogicalInjector,
    Outputs,
)
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    gremlin_active,
    record_inputs,
    reload_action,
)

ACTION = "Map to Keyboard"


def _record_keys(
    ui: UiDriver,
    action: QtQuick.QQuickItem,
    inject_keyboard: KeyboardInjector,
    presses: list[str],
    releases: list[str],
) -> None:
    def inject_keys() -> None:
        for name in presses:
            inject_keyboard.key(name, True)
        for name in releases:
            inject_keyboard.key(name, False)

    record_inputs(ui, ui.find_item("keyCombinationButton", action), inject_keys)


@pytest.mark.parametrize(
    ("presses", "releases", "expected_text"),
    [
        pytest.param(["a"], ["a"], "a", id="single_key"),
        pytest.param(
            ["a", "leftshift"],
            ["a", "leftshift"],
            "Left Shift + a",
            id="modifier_moved_to_front",
        ),
        pytest.param(["esc"], ["esc"], "Esc", id="esc_tap"),
        pytest.param(
            ["leftshift", "esc"],
            ["esc", "leftshift"],
            "Left Shift + Esc",
            id="esc_tap_with_modifier_esc_released_first",
        ),
        pytest.param(
            ["esc", "leftshift"],
            ["leftshift", "esc"],
            "Left Shift + Esc",
            id="esc_tap_with_modifier_modifier_released_first",
        ),
    ],
)
def test_records_keys(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_keyboard: KeyboardInjector,
    presses: list[str],
    releases: list[str],
    expected_text: str,
) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)

    _record_keys(ui, action, inject_keyboard, presses, releases)

    action = reload_action(ui, empty_profile, label, ACTION)
    button = ui.find_item("keyCombinationButton", action)
    assert button.property("text") == expected_text


def test_recorded_key_is_sent(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    inject_keyboard: KeyboardInjector,
    outputs: Outputs,
) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    _record_keys(ui, action, inject_keyboard, ["a"], ["a"])
    reload_action(ui, empty_profile, label, ACTION)

    with gremlin_active(ui):
        inject_logical.button(label, True)
        # Macros run on the MacroManager's thread.
        ui.wait_until(lambda: outputs.key_down.call_count == 1)
        outputs.key_down.assert_called_once_with(keyboard.key_from_name("a"))


@pytest.mark.parametrize(
    "held_keys",
    [
        pytest.param(["esc"], id="esc_only"),
        pytest.param(["leftshift", "esc"], id="esc_with_other_key_held"),
    ],
)
def test_holding_esc_aborts_and_clears_keys(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_keyboard: KeyboardInjector,
    held_keys: list[str],
) -> None:
    _, action = add_logical_input_with_action(ui, "Button", ACTION)
    _record_keys(ui, action, inject_keyboard, ["a"], ["a"])
    button = ui.find_item("keyCombinationButton", action)
    assert button.property("text") == "a"

    try:
        # The 2000 ms wait outlasts the 1000 ms abort timer in InputListenerModel.
        _record_keys(ui, action, inject_keyboard, presses=held_keys, releases=[])
    finally:
        # A key left down in the input cache drops the next test's press as a repeat.
        for name in held_keys:
            inject_keyboard.key(name, False)

    # Not reloaded, as saving discards an action without keys as invalid.
    assert button.property("text") == "Record keys"
