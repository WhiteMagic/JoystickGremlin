# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest
from PySide6 import QtQuick

from action_plugins.common import joystick_label
from gremlin import (
    common,
    keyboard,
)
from gremlin.types import (
    InputType,
    MouseButton,
)
from test.application.fakes import (
    STICK,
    KeyboardInjector,
    LogicalInjector,
    MouseInjector,
    Outputs,
    PhysicalInjector,
)
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    INPUT_TYPE_NAMES,
    INPUTS,
    add_action,
    add_logical_input,
    add_logical_input_with_action,
    click_and_validate,
    gremlin_active,
    record_inputs,
    record_stick_input,
    reload_action,
    select_logical_input,
    select_vjoy_input,
    set_spin_box_value,
)

ACTION = "Macro"
STEP_KINDS = [
    "Joystick",
    "Keyboard",
    "Logical device",
    "Mouse button",
    "Mouse motion",
    "Pause",
    "vJoy",
]


def _add_macro(ui: UiDriver) -> tuple[str, QtQuick.QQuickItem]:
    """Adds a Macro to a new logical button."""
    return add_logical_input_with_action(ui, "Button", ACTION)


def _add_step(
    ui: UiDriver, action: QtQuick.QQuickItem, step_kind: str, index: int = 0
) -> QtQuick.QQuickItem:
    """Adds a step of the given kind and returns its row."""
    ui.choose_menu_item(ui.find_item("addStepButton", action), step_kind)
    return ui.find_item(f"macroStep_{index}", action)


def _single_row(ui: UiDriver, action: QtQuick.QQuickItem) -> QtQuick.QQuickItem:
    row = ui.find_item("macroStep_0", action)
    assert not ui.find_all("macroStep_1", action)
    return row


def _set_value(ui: UiDriver, row: QtQuick.QQuickItem, input_type_name: str) -> object:
    """Sets the step's value of the given input type name and returns it as shown."""
    match input_type_name:
        case "Axis":
            set_spin_box_value(ui, ui.find_item("axisValueSpinBox", row), 0.5)
            return pytest.approx(0.5)
        case "Button":
            combo = ui.find_item("pressedStateCombo", row)
            assert combo.property("currentText") == "Press"
            ui.select(combo, "Release")
            return "Release"
        case "Hat":
            ui.select(ui.find_item("hatDirectionCombo", row), "South West")
            return "South West"


def _shown_value(ui: UiDriver, row: QtQuick.QQuickItem, input_type_name: str) -> object:
    match input_type_name:
        case "Axis":
            return ui.find_item("axisValueSpinBox", row).property("value")
        case "Button":
            return ui.find_item("pressedStateCombo", row).property("currentText")
        case "Hat":
            return ui.find_item("hatDirectionCombo", row).property("currentText")


def _set_relative(ui: UiDriver, row: QtQuick.QQuickItem) -> None:
    click_and_validate(ui, ui.find_item("relativeModeRadio", row))


def _record_key(
    ui: UiDriver, row: QtQuick.QQuickItem, inject_keyboard: KeyboardInjector
) -> None:
    def press_key() -> None:
        inject_keyboard.key("a", True)
        inject_keyboard.key("a", False)

    record_inputs(ui, ui.find_item("recordInputButton", row), press_key)


@pytest.mark.parametrize("mode", ["Single", "Count", "Toggle", "Hold"])
def test_repeat_mode(ui: UiDriver, empty_profile: pathlib.Path, mode: str) -> None:
    label, action = _add_macro(ui)
    _add_step(ui, action, "Pause")
    ui.select(ui.find_item("repeatModeCombo", action), mode)
    if mode != "Single":
        set_spin_box_value(ui, ui.find_item("repeatDelaySpinBox", action), 1.5)
    if mode == "Count":
        set_spin_box_value(ui, ui.find_item("repeatCountSpinBox", action), 5)
    # Pre-emptive only shows for exclusive macros.
    for name in ["exclusiveCheckBox", "preemptiveCheckBox"]:
        click_and_validate(ui, ui.find_item(name, action))

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("repeatModeCombo", action).property("currentText") == mode
    if mode != "Single":
        delay = ui.find_item("repeatDelaySpinBox", action).property("value")
        assert delay == pytest.approx(1.5)
    if mode == "Count":
        assert ui.find_item("repeatCountSpinBox", action).property("value") == 5
    assert ui.find_item("exclusiveCheckBox", action).property("checked")
    assert ui.find_item("preemptiveCheckBox", action).property("checked")


@pytest.mark.parametrize("input_type_name", INPUT_TYPE_NAMES)
def test_joystick(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_physical: PhysicalInjector,
    input_type_name: str,
) -> None:
    label, action = _add_macro(ui)
    row = _add_step(ui, action, "Joystick")
    record_stick_input(
        ui, ui.find_item("recordInputButton", row), inject_physical, input_type_name
    )
    value = _set_value(ui, row, input_type_name)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert ui.find_item("recordInputButton", row).property("text") == joystick_label(
        STICK.device_guid.uuid, *INPUTS[input_type_name]
    )
    assert _shown_value(ui, row, input_type_name) == value


@pytest.mark.parametrize("input_type_name", INPUT_TYPE_NAMES)
def test_logical_device(
    ui: UiDriver, empty_profile: pathlib.Path, input_type_name: str
) -> None:
    label = add_logical_input(ui, "Button")
    target = add_logical_input(ui, input_type_name)
    select_logical_input(ui, label)
    action = add_action(ui, ACTION)
    row = _add_step(ui, action, "Logical device")
    ui.select(ui.find_item("logicalDeviceCombo", row), target)
    value = _set_value(ui, row, input_type_name)
    if input_type_name == "Axis":
        _set_relative(ui, row)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert ui.find_item("logicalDeviceCombo", row).property("currentText") == target
    assert _shown_value(ui, row, input_type_name) == value
    if input_type_name == "Axis":
        assert ui.find_item("relativeModeRadio", row).property("checked")


def test_logical_device_change_to_button_starts_at_press(ui: UiDriver) -> None:
    label = add_logical_input(ui, "Button")
    add_logical_input(ui, "Axis")
    select_logical_input(ui, label)
    action = add_action(ui, ACTION)
    # The step starts on the axis, as axes sort before buttons.
    row = _add_step(ui, action, "Logical device")
    ui.select(ui.find_item("logicalDeviceCombo", row), label)

    assert _shown_value(ui, row, "Button") == "Press"


@pytest.mark.parametrize("input_type_name", INPUT_TYPE_NAMES)
def test_vjoy(ui: UiDriver, empty_profile: pathlib.Path, input_type_name: str) -> None:
    label, action = _add_macro(ui)
    row = _add_step(ui, action, "vJoy")
    input_type, input_id = INPUTS[input_type_name]
    select_vjoy_input(ui, row, input_type, input_id)
    value = _set_value(ui, row, input_type_name)
    if input_type_name == "Axis":
        _set_relative(ui, row)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert ui.find_item("vjoyInputCombo", row).property(
        "currentText"
    ) == common.input_to_ui_string(input_type, input_id)
    assert _shown_value(ui, row, input_type_name) == value
    if input_type_name == "Axis":
        assert ui.find_item("relativeModeRadio", row).property("checked")


def test_vjoy_change_to_button_starts_at_press(ui: UiDriver) -> None:
    _, action = _add_macro(ui)
    row = _add_step(ui, action, "vJoy")
    select_vjoy_input(ui, row, *INPUTS["Axis"])
    select_vjoy_input(ui, row, *INPUTS["Button"])

    assert _shown_value(ui, row, "Button") == "Press"


def test_keyboard(
    ui: UiDriver, empty_profile: pathlib.Path, inject_keyboard: KeyboardInjector
) -> None:
    label, action = _add_macro(ui)
    row = _add_step(ui, action, "Keyboard")
    _record_key(ui, row, inject_keyboard)
    state = _set_value(ui, row, "Button")

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert (
        ui.find_item("recordInputButton", row).property("text")
        == keyboard.key_from_name("a").name
    )
    assert _shown_value(ui, row, "Button") == state


def test_mouse_button(
    ui: UiDriver, empty_profile: pathlib.Path, inject_mouse: MouseInjector
) -> None:
    label, action = _add_macro(ui)
    row = _add_step(ui, action, "Mouse button")

    def press_button() -> None:
        inject_mouse.button(MouseButton.Middle, True)
        inject_mouse.button(MouseButton.Middle, False)

    record_inputs(ui, ui.find_item("recordInputButton", row), press_button)
    state = _set_value(ui, row, "Button")

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert ui.find_item("recordInputButton", row).property(
        "text"
    ) == MouseButton.to_string(MouseButton.Middle)
    assert _shown_value(ui, row, "Button") == state


def test_mouse_motion(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = _add_macro(ui)
    row = _add_step(ui, action, "Mouse motion")
    set_spin_box_value(ui, ui.find_item("dxSpinBox", row), 25)
    set_spin_box_value(ui, ui.find_item("dySpinBox", row), -40)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert ui.find_item("dxSpinBox", row).property("value") == 25
    assert ui.find_item("dySpinBox", row).property("value") == -40


def test_pause(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = _add_macro(ui)
    row = _add_step(ui, action, "Pause")
    set_spin_box_value(ui, ui.find_item("durationSpinBox", row), 1.5)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert ui.find_item("durationSpinBox", row).property("value") == pytest.approx(1.5)


def test_multiple_steps(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_physical: PhysicalInjector,
    inject_keyboard: KeyboardInjector,
) -> None:
    label, action = _add_macro(ui)
    # The step deleted below, told apart from the kept Pause by its duration.
    deleted_row = _add_step(ui, action, "Pause")
    set_spin_box_value(ui, ui.find_item("durationSpinBox", deleted_row), 2.5)
    for index, step_kind in enumerate(STEP_KINDS, start=1):
        row = _add_step(ui, action, step_kind, index)
        # The other steps are valid with their defaults.
        match step_kind:
            case "Joystick":
                record_stick_input(
                    ui,
                    ui.find_item("recordInputButton", row),
                    inject_physical,
                    "Button",
                )
            case "Keyboard":
                _record_key(ui, row, inject_keyboard)
    ui.click(ui.find_item("deleteStepButton", deleted_row))
    ui.wait_until(lambda: not ui.find_all(f"macroStep_{len(STEP_KINDS)}", action))

    action = reload_action(ui, empty_profile, label, ACTION)
    rows = [
        ui.find_item(f"macroStep_{index}", action) for index in range(len(STEP_KINDS))
    ]
    assert [row.property("stepLabel") for row in rows] == STEP_KINDS
    assert not ui.find_all(f"macroStep_{len(STEP_KINDS)}", action)
    pause_row = rows[STEP_KINDS.index("Pause")]
    assert ui.find_item("durationSpinBox", pause_row).property(
        "value"
    ) == pytest.approx(0)


def test_recording(
    ui: UiDriver, empty_profile: pathlib.Path, inject_physical: PhysicalInjector
) -> None:
    label, action = _add_macro(ui)
    # Which inputs are recorded is a setting of the configuration, not the profile.
    assert ui.find_item("recordButtonCheckBox", action).property("checked")
    assert not ui.find_item("recordTimingsCheckBox", action).property("checked")
    _, button_id = INPUTS["Button"]

    ui.click(ui.find_item("startRecordingButton", action))
    inject_physical.button(STICK, button_id, True)
    inject_physical.button(STICK, button_id, False)
    # Each recorded event is queued to the event loop.
    ui.find_item("macroStep_1", action)
    ui.click(ui.find_item("stopRecordingButton", action))
    ui.find_item("startRecordingButton", action)

    action = reload_action(ui, empty_profile, label, ACTION)
    rows = [ui.find_item(f"macroStep_{index}", action) for index in range(2)]
    assert not ui.find_all("macroStep_2", action)
    assert [row.property("stepLabel") for row in rows] == ["Joystick", "Joystick"]
    assert {
        ui.find_item("recordInputButton", row).property("text") for row in rows
    } == {joystick_label(STICK.device_guid.uuid, *INPUTS["Button"])}
    assert [
        ui.find_item("pressedStateCombo", row).property("currentText") for row in rows
    ] == ["Press", "Release"]


def test_saved_macro_presses_vjoy_button(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    outputs: Outputs,
) -> None:
    label, action = _add_macro(ui)
    row = _add_step(ui, action, "vJoy")
    select_vjoy_input(ui, row, InputType.JoystickButton, 5)
    assert ui.find_item("pressedStateCombo", row).property("currentText") == "Press"

    reload_action(ui, empty_profile, label, ACTION)
    with gremlin_active(ui):
        inject_logical.button(label, True)
        # Macros run on the macro manager's thread.
        ui.wait_until(lambda: outputs.vjoy[1].button(5).is_pressed)
        inject_logical.button(label, False)
