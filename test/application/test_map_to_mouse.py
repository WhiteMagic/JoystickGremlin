# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest
from PySide6 import QtQuick

from gremlin import sendinput
from gremlin.types import MouseButton
from test.application.fakes import (
    LogicalInjector,
    MouseInjector,
    Outputs,
)
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    gremlin_active,
    record_inputs,
    reload_action,
    set_spin_box_value,
)

ACTION = "Map to Mouse"


def _set_speeds(ui: UiDriver, action: QtQuick.QQuickItem) -> None:
    # The minimum value has to be less or equal to the maximum.
    set_spin_box_value(ui, ui.find_item("maxSpeedSpinBox", action), 400)
    set_spin_box_value(ui, ui.find_item("minSpeedSpinBox", action), 100)


def _assert_speeds(ui: UiDriver, action: QtQuick.QQuickItem) -> None:
    assert ui.find_item("minSpeedSpinBox", action).property("value") == 100
    assert ui.find_item("maxSpeedSpinBox", action).property("value") == 400


def test_button_mode(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    inject_logical: LogicalInjector,
    inject_mouse: MouseInjector,
    outputs: Outputs,
) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)

    def press_button() -> None:
        inject_mouse.button(MouseButton.Middle, True)
        inject_mouse.button(MouseButton.Middle, False)

    record_inputs(ui, ui.find_item("mouseButtonCaptureButton", action), press_button)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("buttonModeRadio", action).property("checked")
    assert ui.find_item("mouseButtonCaptureButton", action).property(
        "text"
    ) == MouseButton.to_string(MouseButton.Middle)

    with gremlin_active(ui):
        inject_logical.button(label, True)
        assert outputs.send_input.call_count == 1
        (sent_input,) = outputs.send_input.call_args.args
        assert sent_input.union.mi.dwFlags == sendinput.MOUSEEVENTF_MIDDLEDOWN


def test_button_motion(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.click(ui.find_item("motionModeRadio", action))
    _set_speeds(ui, action)
    set_spin_box_value(ui, ui.find_item("timeToMaxSpeedSpinBox", action), 2.5)
    set_spin_box_value(ui, ui.find_item("directionSpinBox", action), 45)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("motionModeRadio", action).property("checked")
    _assert_speeds(ui, action)
    assert ui.find_item("timeToMaxSpeedSpinBox", action).property(
        "value"
    ) == pytest.approx(2.5)
    assert ui.find_item("directionSpinBox", action).property("value") == 45


def test_axis_motion(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Axis", ACTION)
    ui.click(ui.find_item("xAxisRadio", action))
    _set_speeds(ui, action)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("xAxisRadio", action).property("checked")
    assert not ui.find_item("yAxisRadio", action).property("checked")
    _assert_speeds(ui, action)


def test_hat_motion(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = add_logical_input_with_action(ui, "Hat", ACTION)
    _set_speeds(ui, action)
    set_spin_box_value(ui, ui.find_item("timeToMaxSpeedSpinBox", action), 2.5)

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_speeds(ui, action)
    assert ui.find_item("timeToMaxSpeedSpinBox", action).property(
        "value"
    ) == pytest.approx(2.5)
