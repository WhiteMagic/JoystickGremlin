# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import contextlib
from collections.abc import Generator

import pytest
from PySide6 import QtQuick

from gremlin.config import Configuration
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    click_and_validate,
    open_dialog,
)

ENTRIES_KEY = ("profile", "automation", "entries-auto-loading")
FOCUS_LOSS_KEY = ("profile", "automation", "focus-loss-behavior")


@pytest.fixture(autouse=True)
def restore_auto_loading_config() -> Generator[None]:
    config = Configuration()
    entries = config.value(*ENTRIES_KEY)
    focus_loss_behavior = config.value(*FOCUS_LOSS_KEY)
    config.set(*ENTRIES_KEY, [])
    yield
    config.set(*ENTRIES_KEY, entries)
    config.set(*FOCUS_LOSS_KEY, focus_loss_behavior)


@contextlib.contextmanager
def _profile_options(ui: UiDriver) -> Generator[QtQuick.QQuickItem]:
    """Opens the Options dialog showing the profile section."""
    with open_dialog(ui, "Options", "optionsContent") as dialog:
        ui.click(ui.find_item("configSection_profile", dialog))
        yield dialog


def _find_auto_load_entry(
    ui: UiDriver, dialog: QtQuick.QQuickItem, profile: str
) -> QtQuick.QQuickItem:
    return ui.find_one_where(
        lambda item: (
            item.objectName() == "autoLoadEntry" and item.property("profile") == profile
        ),
        f"being the auto loading entry of '{profile}'",
        dialog,
    )


def _add_auto_load_entry(
    ui: UiDriver, dialog: QtQuick.QQuickItem, profile: str
) -> QtQuick.QQuickItem:
    ui.click(ui.find_item("newAutoLoadEntryButton", dialog))
    entry = _find_auto_load_entry(ui, dialog, "")
    # The field is read-only and the native file dialog writes to it like this.
    ui.find_item("autoLoadProfileField", entry).setProperty("text", profile)
    return entry


def _executable_controls_enabled(ui: UiDriver, entry: QtQuick.QQuickItem) -> list[bool]:
    return [
        ui.find_item(name, entry).isEnabled()
        for name in (
            "autoLoadExecutableField",
            "browseExecutableButton",
            "selectExecutableButton",
        )
    ]


def test_default_entry_settings(ui: UiDriver) -> None:
    profile = "C:/Profiles/Desktop.xml"

    # Open options add entry, enable auto loading and pick added entry as default.
    with _profile_options(ui) as dialog:
        entry = _add_auto_load_entry(ui, dialog, profile)
        assert _executable_controls_enabled(ui, entry) == [True, True, True]

        click_and_validate(ui, ui.find_item("autoLoadEnabledCheckBox", entry))
        click_and_validate(ui, ui.find_item("autoLoadDefaultCheckBox", entry))
        ui.wait_for_value(
            lambda: _executable_controls_enabled(ui, entry), [False, False, False]
        )

    # Reopen options and check state holds, deselecting default allows editing again.
    with _profile_options(ui) as dialog:
        entry = _find_auto_load_entry(ui, dialog, profile)
        assert ui.find_item("autoLoadEnabledCheckBox", entry).property("checked")
        assert ui.find_item("autoLoadDefaultCheckBox", entry).property("checked")
        assert _executable_controls_enabled(ui, entry) == [False, False, False]

        click_and_validate(ui, ui.find_item("autoLoadDefaultCheckBox", entry), False)
        ui.wait_for_value(
            lambda: _executable_controls_enabled(ui, entry), [True, True, True]
        )

    # Reopen again to verify the default profile still is not ticket.
    with _profile_options(ui) as dialog:
        entry = _find_auto_load_entry(ui, dialog, profile)
        assert not ui.find_item("autoLoadDefaultCheckBox", entry).property("checked")


def test_only_one_entry_can_be_default(ui: UiDriver) -> None:
    first_profile = "C:/Profiles/First.xml"
    second_profile = "C:/Profiles/Second.xml"

    with _profile_options(ui) as dialog:
        first_entry = _add_auto_load_entry(ui, dialog, first_profile)
        second_entry = _add_auto_load_entry(ui, dialog, second_profile)

        first_default = ui.find_item("autoLoadDefaultCheckBox", first_entry)
        second_default = ui.find_item("autoLoadDefaultCheckBox", second_entry)
        click_and_validate(ui, first_default)
        click_and_validate(ui, second_default)
        ui.wait_until(lambda: not first_default.property("checked"))
        # The replaced entry takes its executable controls back as well.
        ui.wait_for_value(
            lambda: _executable_controls_enabled(ui, first_entry), [True, True, True]
        )

    # Verify reopening the options doesn't change state.
    with _profile_options(ui) as dialog:
        first_entry = _find_auto_load_entry(ui, dialog, first_profile)
        second_entry = _find_auto_load_entry(ui, dialog, second_profile)
        assert not ui.find_item("autoLoadDefaultCheckBox", first_entry).property(
            "checked"
        )
        assert ui.find_item("autoLoadDefaultCheckBox", second_entry).property("checked")


def test_focus_loss_behavior_setting(ui: UiDriver) -> None:
    def find_combo(dialog: QtQuick.QQuickItem) -> QtQuick.QQuickItem:
        card = ui.find_one_where(
            lambda item: item.property("title") == "Focus loss behavior",
            "being the focus loss behavior option",
            dialog,
        )
        return ui.find_one_where(
            lambda item: item.inherits("QQuickComboBox"), "being a combo box", card
        )

    with _profile_options(ui) as dialog:
        ui.select(find_combo(dialog), "Load default")

    with _profile_options(ui) as dialog:
        assert find_combo(dialog).property("currentText") == "Load default"
