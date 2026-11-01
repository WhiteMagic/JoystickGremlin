# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

from PySide6 import QtQuick

import gremlin.ui.backend
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_and_select_logical_input,
    add_description,
    add_mode,
    find_description,
    manage_modes,
    save_and_reload,
    select_logical_input,
    wait_for_input_debounce,
)


def _select_mode(ui: UiDriver, name: str) -> None:
    """Selects the mode being configured and waits for its bindings to show."""
    ui.select(ui.find_item("modeSelectorCombo"), name)
    ui_state = gremlin.ui.backend.Backend().ui_state
    wait_for_input_debounce(ui, lambda: ui_state.currentMode == name)


def _mode_names(ui: UiDriver, dialog: QtQuick.QQuickItem) -> list[str]:
    return sorted(
        row.objectName().removeprefix("modeRow_")
        for row in ui.find_where(
            lambda item: item.objectName().startswith("modeRow_"), dialog
        )
    )


def _parent_combo(
    ui: UiDriver, dialog: QtQuick.QQuickItem, name: str
) -> QtQuick.QQuickItem:
    return ui.find_item("parentModeCombo", ui.find_item(f"modeRow_{name}", dialog))


def _rename_mode(
    ui: UiDriver, dialog: QtQuick.QQuickItem, name: str, new_name: str
) -> None:
    # Wrappers found within a row are removed with the row's wrapper.
    row = ui.find_item(f"modeRow_{name}", dialog)
    ui.click(ui.find_item("renameModeButton", row))
    ui.type_text(ui.find_item("textInputField"), new_name)
    ui.find_item(f"modeRow_{new_name}", dialog)


def _delete_mode(ui: UiDriver, dialog: QtQuick.QQuickItem, name: str) -> None:
    row = ui.find_item(f"modeRow_{name}", dialog)
    ui.click(ui.find_item("deleteModeButton", row))
    ui.wait_until(lambda: not ui.find_all(f"modeRow_{name}", dialog))


def _assert_modes(ui: UiDriver, dialog: QtQuick.QQuickItem) -> None:
    # A new dialog creates all but the first row at its first polish.
    ui.find_item("modeRow_Third", dialog)
    assert _mode_names(ui, dialog) == [
        "Cleared",
        "Default",
        "Moved",
        "Renamed",
        "Third",
    ]
    assert _parent_combo(ui, dialog, "Cleared").property("currentText") == ""
    assert _parent_combo(ui, dialog, "Default").property("currentText") == ""
    assert _parent_combo(ui, dialog, "Moved").property("currentText") == "Default"
    assert _parent_combo(ui, dialog, "Renamed").property("currentText") == ""
    assert _parent_combo(ui, dialog, "Third").property("currentText") == "Renamed"


def _assert_only_description(ui: UiDriver, text: str) -> None:
    find_description(ui, text)
    # Nodes of the previous mode may outlive the rebuild briefly.
    ui.find_item("actionNode_Description")


def _assert_selected_mode(ui: UiDriver, name: str) -> None:
    combo = ui.find_item("modeSelectorCombo")
    ui.wait_for_value(lambda: combo.property("currentText"), name)
    assert gremlin.ui.backend.Backend().ui_state.currentMode == name


def test_mode_changes_survive_reload(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    add_mode(ui, "Second")
    add_mode(ui, "Third", parent="Second")
    add_mode(ui, "Cleared", parent="Second")
    add_mode(ui, "Moved", parent="Second")
    add_mode(ui, "Doomed")
    with manage_modes(ui) as dialog:
        ui.select(_parent_combo(ui, dialog, "Cleared"), "")
        ui.select(_parent_combo(ui, dialog, "Moved"), "Default")
        _rename_mode(ui, dialog, "Second", "Renamed")
        _delete_mode(ui, dialog, "Doomed")
        _assert_modes(ui, dialog)

    save_and_reload(ui, empty_profile)
    with manage_modes(ui) as dialog:
        _assert_modes(ui, dialog)


def test_last_mode_cannot_be_deleted(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    with manage_modes(ui) as dialog:
        row = ui.find_item("modeRow_Default", dialog)
        assert not ui.find_item("deleteModeButton", row).isEnabled()

    add_mode(ui, "Second")
    with manage_modes(ui) as dialog:
        row = ui.find_item("modeRow_Default", dialog)
        assert ui.find_item("deleteModeButton", row).isEnabled()


def test_duplicate_name_rejected(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    with manage_modes(ui) as dialog:
        ui.click(ui.find_item("addModeButton", dialog))
        field = ui.find_item("textInputField")
        ui.type_text(field, "Default")
        ui.find_item("textInputErrorIcon")
        assert _mode_names(ui, dialog) == ["Default"]
        ui.close_window(field)


def test_bindings_stay_in_their_mode(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    add_mode(ui, "Second")
    add_mode(ui, "Unbound")
    label = add_and_select_logical_input(ui, "Button")
    add_description(ui, "default")
    _select_mode(ui, "Second")
    add_description(ui, "second")

    save_and_reload(ui, empty_profile)
    assert ui.find_item("modeSelectorCombo").property("currentText") == "Default"
    select_logical_input(ui, label)
    _assert_only_description(ui, "default")
    _select_mode(ui, "Second")
    _assert_only_description(ui, "second")
    _select_mode(ui, "Unbound")
    ui.wait_for_value(lambda: ui.find_all("actionNode_Description"), [])


def test_rename_selected_mode(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    add_mode(ui, "Second")
    _select_mode(ui, "Second")
    first_label = add_and_select_logical_input(ui, "Button")
    add_description(ui, "before rename")

    with manage_modes(ui) as dialog:
        _rename_mode(ui, dialog, "Second", "Renamed")
    _assert_selected_mode(ui, "Renamed")
    # Only a newly selected input looks its bindings up by the mode's name.
    second_label = add_and_select_logical_input(ui, "Button")
    add_description(ui, "after rename")

    save_and_reload(ui, empty_profile)
    _select_mode(ui, "Renamed")
    select_logical_input(ui, first_label)
    _assert_only_description(ui, "before rename")
    select_logical_input(ui, second_label)
    _assert_only_description(ui, "after rename")


def test_delete_selected_mode(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    add_mode(ui, "Second")
    _select_mode(ui, "Second")

    with manage_modes(ui) as dialog:
        _delete_mode(ui, dialog, "Second")
    _assert_selected_mode(ui, "Default")
    label = add_and_select_logical_input(ui, "Button")
    add_description(ui, "after delete")

    save_and_reload(ui, empty_profile)
    select_logical_input(ui, label)
    _assert_only_description(ui, "after delete")


def test_selector_keeps_mode_when_list_reorders(
    ui: UiDriver, empty_profile: pathlib.Path
) -> None:
    add_mode(ui, "Second")
    _select_mode(ui, "Second")

    # Sorts before the selected mode, shifting its row.
    add_mode(ui, "Alpha")
    _assert_selected_mode(ui, "Second")
    label = add_and_select_logical_input(ui, "Button")
    add_description(ui, "second")

    save_and_reload(ui, empty_profile)
    _select_mode(ui, "Second")
    select_logical_input(ui, label)
    _assert_only_description(ui, "second")
