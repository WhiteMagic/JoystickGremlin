# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

import pytest
from PySide6 import QtQuick

import gremlin.ui.backend
from test.application.fakes import LogicalInjector
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    add_mode,
    gremlin_active,
    reload_action,
)

ACTION = "Change Mode"


def _add_change_mode(ui: UiDriver, change_type: str) -> tuple[str, QtQuick.QQuickItem]:
    """Adds two modes and a change mode action to a specific mode."""
    add_mode(ui, "Second")
    add_mode(ui, "Third")
    label, action = add_logical_input_with_action(ui, "Button", ACTION)
    ui.select(ui.find_item("changeTypeCombo", action), change_type)
    return label, action


def _assert_change_type(
    ui: UiDriver, action: QtQuick.QQuickItem, change_type: str
) -> None:
    assert (
        ui.find_item("changeTypeCombo", action).property("currentText") == change_type
    )


def test_saved_switch_changes_mode(
    ui: UiDriver,
    empty_profile: pathlib.Path,
    backend: gremlin.ui.backend.Backend,
    inject_logical: LogicalInjector,
) -> None:
    label, action = _add_change_mode(ui, "Switch")
    ui.select(ui.find_item("switchModeCombo", action), "Second")

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_change_type(ui, action, "Switch")
    assert ui.find_item("switchModeCombo", action).property("currentText") == "Second"

    with gremlin_active(ui):
        inject_logical.button(label, True)
        ui.wait_for_value(lambda: backend.currentMode, "Second")
        inject_logical.button(label, False)


def test_temporary(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = _add_change_mode(ui, "Temporary")
    ui.select(ui.find_item("temporaryModeCombo", action), "Second")

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_change_type(ui, action, "Temporary")
    assert (
        ui.find_item("temporaryModeCombo", action).property("currentText") == "Second"
    )


def test_cycle(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = _add_change_mode(ui, "Cycle")
    # Every edit rebuilds the rows, so each step looks its row up again.
    for index in range(3):
        ui.click(ui.find_item("addCycleModeButton", action))
        ui.find_item(f"cycleModeCombo_{index}", action)
    ui.select(ui.find_item("cycleModeCombo_0", action), "Second")
    ui.select(ui.find_item("cycleModeCombo_2", action), "Third")
    ui.click(ui.find_item("deleteCycleModeButton_1", action))
    ui.wait_until(lambda: not ui.find_all("cycleModeCombo_2", action))

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_change_type(ui, action, "Cycle")
    assert [
        ui.find_item(f"cycleModeCombo_{index}", action).property("currentText")
        for index in range(2)
    ] == ["Second", "Third"]
    assert not ui.find_all("cycleModeCombo_2", action)


@pytest.mark.parametrize("change_type", ["Previous", "Unwind"])
def test_without_target(
    ui: UiDriver, empty_profile: pathlib.Path, change_type: str
) -> None:
    label, _ = _add_change_mode(ui, change_type)

    action = reload_action(ui, empty_profile, label, ACTION)
    _assert_change_type(ui, action, change_type)
