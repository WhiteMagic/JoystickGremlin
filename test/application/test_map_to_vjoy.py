# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest
from PySide6 import QtQuick

from gremlin import common
from gremlin.types import (
    HatDirection,
    InputType,
)
from test.application.fakes import (
    LogicalInjector,
    Outputs,
)
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    gremlin_active,
    reload_action,
    select_vjoy_input,
    set_spin_box_value,
)

ACTION = "Map to vJoy"


def _assert_vjoy_input(
    ui: UiDriver, action: QtQuick.QQuickItem, input_type: InputType, input_id: int
) -> None:
    assert (
        ui.find_item("vjoyDeviceCombo", action).property("currentText")
        == "vJoy Device 1"
    )
    assert ui.find_item("vjoyInputCombo", action).property(
        "currentText"
    ) == common.input_to_ui_string(input_type, input_id)


def test_axis_absolute(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    outputs: Outputs,
) -> None:
    label, action = add_logical_input_with_action(ui, "Axis", ACTION)
    select_vjoy_input(ui, action, InputType.JoystickAxis, 2)

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_vjoy_input(ui, action, InputType.JoystickAxis, 2)
    assert ui.find_item("absoluteModeRadio", action).property("checked")

    with gremlin_active(ui):
        inject_logical.axis(label, 0.75)
        assert outputs.vjoy[1].axis(2).value == pytest.approx(0.75)


def test_axis_relative(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Axis", ACTION)
    ui.click(ui.find_item("relativeModeRadio", action))
    set_spin_box_value(ui, ui.find_item("axisScalingSpinBox", action), 2.5)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("relativeModeRadio", action).property("checked")
    assert not ui.find_item("absoluteModeRadio", action).property("checked")
    assert ui.find_item("axisScalingSpinBox", action).property(
        "value"
    ) == pytest.approx(2.5)


def test_button_remap(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    outputs: Outputs,
) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    select_vjoy_input(ui, action, InputType.JoystickButton, 5)

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_vjoy_input(ui, action, InputType.JoystickButton, 5)

    with gremlin_active(ui):
        inject_logical.button(label, True)
        assert outputs.vjoy[1].button(5).is_pressed


@pytest.mark.parametrize(
    ("unchecked_activation", "checked_activation"),
    [
        ("activationPress", "activationRelease"),
        ("activationRelease", "activationPress"),
    ],
)
def test_button_settings(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    unchecked_activation: str,
    checked_activation: str,
) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.click(ui.find_item("invertActivationCheckBox", action))
    ui.click(ui.find_item(unchecked_activation, action))

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("invertActivationCheckBox", action).property("checked")
    assert not ui.find_item(unchecked_activation, action).property("checked")
    assert ui.find_item(checked_activation, action).property("checked")


def test_hat_remap(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    outputs: Outputs,
) -> None:
    label, action = add_logical_input_with_action(ui, "Hat", ACTION)
    select_vjoy_input(ui, action, InputType.JoystickHat, 2)

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_vjoy_input(ui, action, InputType.JoystickHat, 2)

    with gremlin_active(ui):
        inject_logical.hat(label, HatDirection.NorthEast)
        assert outputs.vjoy[1].hat(2).direction == HatDirection.NorthEast
