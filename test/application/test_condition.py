# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import dataclasses
import pathlib

import pytest
from PySide6 import QtQuick

from gremlin import (
    common,
    keyboard,
)
from gremlin.types import InputType
from test.application.fakes import (
    STICK,
    KeyboardInjector,
    LogicalInjector,
    Outputs,
    PhysicalInjector,
)
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    INPUT_TYPE_NAMES,
    INPUTS,
    action_order,
    add_action,
    add_child_action,
    add_description,
    add_logical_input,
    add_logical_input_with_action,
    click_and_validate,
    find_action,
    find_action_list,
    find_child_action,
    gremlin_active,
    record_inputs,
    record_stick_input,
    reload_action,
    select_logical_input,
    select_vjoy_input,
    set_spin_box_value,
)

ACTION = "Condition"
HAT_DIRECTIONS = [
    "north",
    "northEast",
    "east",
    "southEast",
    "south",
    "southWest",
    "west",
    "northWest",
]


@dataclasses.dataclass(frozen=True)
class Comparator:
    """Comparator settings applied to, and expected back from, a condition."""

    lower_limit: float
    upper_limit: float
    pressed_state: str
    hat_directions: frozenset[str]


DEFAULT_COMPARATOR = Comparator(
    lower_limit=-0.5,
    upper_limit=0.5,
    pressed_state="Release",
    hat_directions=frozenset({"north", "southWest"}),
)


def _add_condition_action(
    ui: UiDriver, input_type_name: str = "Button"
) -> tuple[str, QtQuick.QQuickItem]:
    """Adds a Condition to a new logical input of the given type."""
    return add_logical_input_with_action(ui, input_type_name, ACTION)


def _add_condition(
    ui: UiDriver, action: QtQuick.QQuickItem, condition_type: str, index: int = 0
) -> QtQuick.QQuickItem:
    """Adds a condition of the given type and returns its item."""
    ui.choose_menu_item(ui.find_item("addConditionButton", action), condition_type)
    return ui.find_item(f"condition_{index}", action)


def _single_row(ui: UiDriver, action: QtQuick.QQuickItem) -> QtQuick.QQuickItem:
    row = ui.find_item("condition_0", action)
    assert not ui.find_all("condition_1", action)
    return row


def _recorded_inputs(ui: UiDriver, row: QtQuick.QQuickItem) -> set[str]:
    return set(ui.find_item("recordInputsButton", row).property("text").split(", "))


def _stick_input_name(input_type_name: str) -> str:
    return f"{STICK.name} - {common.input_to_ui_string(*INPUTS[input_type_name])}"


def _set_comparator(
    ui: UiDriver,
    row: QtQuick.QQuickItem,
    input_type_name: str,
    comparator: Comparator,
) -> None:
    """Sets the comparator of the given input type to the given values."""
    match input_type_name:
        case "Axis":
            set_spin_box_value(
                ui, ui.find_item("lowerLimitSpinBox", row), comparator.lower_limit
            )
            set_spin_box_value(
                ui, ui.find_item("upperLimitSpinBox", row), comparator.upper_limit
            )
        case "Button":
            ui.select(ui.find_item("pressedStateCombo", row), comparator.pressed_state)
        case "Hat":
            for direction in sorted(comparator.hat_directions):
                click_and_validate(
                    ui, ui.find_item(f"hatDirectionButton_{direction}", row)
                )


def _assert_comparator(
    ui: UiDriver,
    row: QtQuick.QQuickItem,
    input_type_name: str,
    comparator: Comparator,
) -> None:
    match input_type_name:
        case "Axis":
            lower_limit = ui.find_item("lowerLimitSpinBox", row).property("value")
            upper_limit = ui.find_item("upperLimitSpinBox", row).property("value")
            assert lower_limit == pytest.approx(comparator.lower_limit)
            assert upper_limit == pytest.approx(comparator.upper_limit)
        case "Button":
            combo = ui.find_item("pressedStateCombo", row)
            assert combo.property("currentText") == comparator.pressed_state
        case "Hat":
            checked_directions = {
                direction
                for direction in HAT_DIRECTIONS
                if ui.find_item(f"hatDirectionButton_{direction}", row).property(
                    "checked"
                )
            }
            assert checked_directions == comparator.hat_directions


@pytest.mark.parametrize("input_type_name", INPUT_TYPE_NAMES)
def test_joystick(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_physical: PhysicalInjector,
    input_type_name: str,
) -> None:
    label, action = _add_condition_action(ui)
    row = _add_condition(ui, action, "Joystick")
    record_stick_input(
        ui, ui.find_item("recordInputsButton", row), inject_physical, input_type_name
    )
    # The recording replaces the comparator's controls thus it has to be set again.
    _set_comparator(ui, row, input_type_name, DEFAULT_COMPARATOR)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert _recorded_inputs(ui, row) == {_stick_input_name(input_type_name)}
    _assert_comparator(ui, row, input_type_name, DEFAULT_COMPARATOR)


def test_joystick_multiple_buttons(
    ui: UiDriver, empty_profile: pathlib.Path, inject_physical: PhysicalInjector
) -> None:
    label, action = _add_condition_action(ui)
    row = _add_condition(ui, action, "Joystick")

    # The first release ends the recording.
    def press_buttons() -> None:
        inject_physical.button(STICK, 1, True)
        inject_physical.button(STICK, 2, True)
        inject_physical.button(STICK, 1, False)
        inject_physical.button(STICK, 2, False)

    record_inputs(ui, ui.find_item("recordInputsButton", row), press_buttons)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert _recorded_inputs(ui, row) == {
        f"{STICK.name} - {common.input_to_ui_string(InputType.JoystickButton, 1)}",
        f"{STICK.name} - {common.input_to_ui_string(InputType.JoystickButton, 2)}",
    }


def test_keyboard(
    ui: UiDriver, empty_profile: pathlib.Path, inject_keyboard: KeyboardInjector
) -> None:
    label, action = _add_condition_action(ui)
    row = _add_condition(ui, action, "Keyboard")

    # Multiple keys are accepted and the first release ends the recording but all
    # pressed keys are recorded.
    def press_keys() -> None:
        inject_keyboard.key("a", True)
        inject_keyboard.key("leftshift", True)
        inject_keyboard.key("a", False)
        inject_keyboard.key("leftshift", False)

    record_inputs(ui, ui.find_item("recordInputsButton", row), press_keys)
    _set_comparator(ui, row, "Button", DEFAULT_COMPARATOR)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert _recorded_inputs(ui, row) == {
        keyboard.key_from_name(name).name for name in ["a", "leftshift"]
    }
    _assert_comparator(ui, row, "Button", DEFAULT_COMPARATOR)


@pytest.mark.parametrize("input_type_name", INPUT_TYPE_NAMES)
def test_current_input(
    ui: UiDriver, empty_profile: pathlib.Path, input_type_name: str
) -> None:
    # The comparator follows the type of the bound input.
    label, action = _add_condition_action(ui, input_type_name)
    row = _add_condition(ui, action, "Current Input")
    _set_comparator(ui, row, input_type_name, DEFAULT_COMPARATOR)

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_comparator(ui, _single_row(ui, action), input_type_name, DEFAULT_COMPARATOR)


@pytest.mark.parametrize("input_type_name", INPUT_TYPE_NAMES)
def test_vjoy(ui: UiDriver, empty_profile: pathlib.Path, input_type_name: str) -> None:
    label, action = _add_condition_action(ui)
    row = _add_condition(ui, action, "vJoy")
    input_type, input_id = INPUTS[input_type_name]
    select_vjoy_input(ui, row, input_type, input_id)
    _set_comparator(ui, row, input_type_name, DEFAULT_COMPARATOR)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert ui.find_item("vjoyInputCombo", row).property(
        "currentText"
    ) == common.input_to_ui_string(input_type, input_id)
    _assert_comparator(ui, row, input_type_name, DEFAULT_COMPARATOR)


@pytest.mark.parametrize("input_type_name", INPUT_TYPE_NAMES)
def test_logical_device(
    ui: UiDriver, empty_profile: pathlib.Path, input_type_name: str
) -> None:
    label = add_logical_input(ui, "Button")
    target = add_logical_input(ui, input_type_name)
    select_logical_input(ui, label)
    action = add_action(ui, ACTION)
    row = _add_condition(ui, action, "Logical Device")
    ui.select(ui.find_item("logicalDeviceCombo", row), target)
    _set_comparator(ui, row, input_type_name, DEFAULT_COMPARATOR)

    action = reload_action(ui, empty_profile, label, ACTION)
    row = _single_row(ui, action)
    assert ui.find_item("logicalDeviceCombo", row).property("currentText") == target
    _assert_comparator(ui, row, input_type_name, DEFAULT_COMPARATOR)


def test_multiple_conditions(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = _add_condition_action(ui)
    for index, condition_type in enumerate(
        ["Current Input", "Keyboard", "Logical Device"]
    ):
        _add_condition(ui, action, condition_type, index)
    # Wrappers found within a row are removed with the row's wrapper.
    keyboard_row = ui.find_item("condition_1", action)
    ui.click(ui.find_item("deleteConditionButton", keyboard_row))
    ui.wait_until(lambda: not ui.find_all("condition_2", action))
    ui.select(ui.find_item("logicalOperatorCombo", action), "Any")
    # Adding an action rebuilds every action node of the binding.
    add_description(ui, "when true", action, "When true")
    add_description(ui, "when false", find_action(ui, ACTION), "When false")

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("logicalOperatorCombo", action).property("currentText") == "Any"
    rows = [ui.find_item(f"condition_{index}", action) for index in range(2)]
    assert [row.property("conditionName") for row in rows] == [
        "Current input",
        "Logical device",
    ]
    assert not ui.find_all("condition_2", action)
    for container, text in [("true", "when true"), ("false", "when false")]:
        assert action_order(ui, find_action_list(ui, container, action)) == [text]


def test_true_condition_runs_child_action(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    inject_physical: PhysicalInjector,
    outputs: Outputs,
) -> None:
    label, action = _add_condition_action(ui)
    row = _add_condition(ui, action, "Joystick")
    record_stick_input(
        ui, ui.find_item("recordInputsButton", row), inject_physical, "Button"
    )
    action = add_child_action(ui, action, "When true", "Map to vJoy")
    select_vjoy_input(
        ui,
        find_child_action(ui, action, "true", "Map to vJoy"),
        InputType.JoystickButton,
        5,
    )

    reload_action(ui, empty_profile, label, ACTION)
    _, button_id = INPUTS["Button"]
    with gremlin_active(ui):
        inject_physical.button(STICK, button_id, True)
        inject_logical.button(label, True)
        assert outputs.vjoy[1].button(5).is_pressed
        inject_logical.button(label, False)
        inject_physical.button(STICK, button_id, False)


def test_smart_toggle_in_condition(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = _add_condition_action(ui)
    action = add_child_action(ui, action, "When true", "Smart Toggle")
    smart_toggle = find_child_action(ui, action, "true", "Smart Toggle")
    set_spin_box_value(ui, ui.find_item("delaySpinBox", smart_toggle), 0.75)
    add_child_action(ui, smart_toggle, "Actions", "Description")

    action = reload_action(ui, empty_profile, label, ACTION)
    smart_toggle = find_child_action(ui, action, "true", "Smart Toggle")
    delay = ui.find_item("delaySpinBox", smart_toggle).property("value")
    assert delay == pytest.approx(0.75)
    find_child_action(ui, smart_toggle, "children", "Description")
