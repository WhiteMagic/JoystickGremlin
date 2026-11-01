# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest
from PySide6 import QtQuick

from gremlin.logical_device import LogicalDevice
from gremlin.types import HatDirection
from test.application.fakes import LogicalInjector
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_action,
    add_logical_input,
    gremlin_active,
    reload_action,
    select_logical_input,
    set_spin_box_value,
)

ACTION = "Map to Logical Device"


def _add_mapping(
    ui: UiDriver, input_type_name: str
) -> tuple[str, str, QtQuick.QQuickItem]:
    """Maps a new logical input to another new one of the same input type."""
    source = add_logical_input(ui, input_type_name)
    target = add_logical_input(ui, input_type_name)
    select_logical_input(ui, source)
    action = add_action(ui, ACTION)
    # The action starts out mapped to the first input of its type, the source.
    ui.select(ui.find_item("logicalDeviceCombo", action), target)
    return source, target, action


def _assert_target(ui: UiDriver, action: QtQuick.QQuickItem, target: str) -> None:
    assert ui.find_item("logicalDeviceCombo", action).property("currentText") == target


def test_axis_absolute(
    ui: UiDriver, empty_profile: pathlib.Path, inject_logical: LogicalInjector
) -> None:
    source, target, _ = _add_mapping(ui, "Axis")

    action = reload_action(ui, empty_profile, source, ACTION)
    _assert_target(ui, action, target)
    assert ui.find_item("absoluteModeRadio", action).property("checked")

    with gremlin_active(ui):
        inject_logical.axis(source, 0.75)
        assert LogicalDevice()[target].value == pytest.approx(0.75)


def test_axis_relative(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    source, target, action = _add_mapping(ui, "Axis")
    ui.click(ui.find_item("relativeModeRadio", action))
    set_spin_box_value(ui, ui.find_item("axisScalingSpinBox", action), 2.5)

    action = reload_action(ui, empty_profile, source, ACTION)
    _assert_target(ui, action, target)
    assert ui.find_item("relativeModeRadio", action).property("checked")
    assert not ui.find_item("absoluteModeRadio", action).property("checked")
    assert ui.find_item("axisScalingSpinBox", action).property(
        "value"
    ) == pytest.approx(2.5)


def test_button_remap(
    ui: UiDriver, empty_profile: pathlib.Path, inject_logical: LogicalInjector
) -> None:
    source, target, _ = _add_mapping(ui, "Button")

    action = reload_action(ui, empty_profile, source, ACTION)
    _assert_target(ui, action, target)

    with gremlin_active(ui):
        inject_logical.button(source, True)
        assert LogicalDevice()[target].is_pressed


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
    source, _, action = _add_mapping(ui, "Button")
    ui.click(ui.find_item("invertActivationCheckBox", action))
    ui.click(ui.find_item(unchecked_activation, action))

    action = reload_action(ui, empty_profile, source, ACTION)
    assert ui.find_item("invertActivationCheckBox", action).property("checked")
    assert not ui.find_item(unchecked_activation, action).property("checked")
    assert ui.find_item(checked_activation, action).property("checked")


def test_hat_remap(
    ui: UiDriver, empty_profile: pathlib.Path, inject_logical: LogicalInjector
) -> None:
    source, target, _ = _add_mapping(ui, "Hat")

    action = reload_action(ui, empty_profile, source, ACTION)
    _assert_target(ui, action, target)

    with gremlin_active(ui):
        inject_logical.hat(source, HatDirection.NorthEast)
        assert LogicalDevice()[target].direction == HatDirection.NorthEast
