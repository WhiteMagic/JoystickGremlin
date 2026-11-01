# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

from PySide6 import QtQuick

from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    action_order,
    add_action,
    add_and_select_logical_input,
    add_description,
    add_logical_input_with_action,
    drag_action,
    find_action,
    find_action_list,
    find_description,
    save_and_reload,
    select_logical_input,
)

CONTAINER = "Tempo"


def reload_sequence(ui: UiDriver, path: pathlib.Path, label: str) -> QtQuick.QQuickItem:
    """Saves and loads the profile and returns the reloaded top-level list."""
    previous_list = find_action_list(ui, "children")
    save_and_reload(ui, path)
    select_logical_input(ui, label)
    return find_action_list(ui, "children", previous=previous_list)


def test_reorder(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label = add_and_select_logical_input(ui, "Button")
    for text in ["a", "b", "c"]:
        add_description(ui, text)
    drag_action(
        ui, find_description(ui, "c"), find_action_list(ui, "children"), position=0
    )
    drag_action(
        ui, find_description(ui, "a"), find_action_list(ui, "children"), position=3
    )

    top_level = reload_sequence(ui, empty_profile, label)
    assert action_order(ui, top_level) == ["c", "b", "a"]


def test_move_between_slots(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, container = add_logical_input_with_action(ui, "Button", CONTAINER)
    add_description(ui, "a", container, "Short press")
    add_description(ui, "b", find_action(ui, CONTAINER), "Short press")
    drag_action(
        ui,
        find_description(ui, "b"),
        find_action_list(ui, "long", find_action(ui, CONTAINER)),
        position=0,
    )
    drag_action(
        ui,
        find_description(ui, "a"),
        find_action_list(ui, "long", find_action(ui, CONTAINER)),
        position=1,
    )

    top_level = reload_sequence(ui, empty_profile, label)
    container = find_action(ui, CONTAINER, top_level)
    assert action_order(ui, find_action_list(ui, "short", container)) == []
    assert action_order(ui, find_action_list(ui, "long", container)) == ["b", "a"]


def test_move_into_and_out_of_nested(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label = add_and_select_logical_input(ui, "Button")
    add_description(ui, "a")
    container = add_action(ui, CONTAINER)
    add_description(ui, "b", container, "Short press")
    add_description(ui, "c")
    drag_action(
        ui,
        find_description(ui, "a"),
        find_action_list(ui, "short", find_action(ui, CONTAINER)),
        position=1,
    )
    drag_action(
        ui, find_description(ui, "b"), find_action_list(ui, "children"), position=2
    )

    top_level = reload_sequence(ui, empty_profile, label)
    assert action_order(ui, top_level) == [CONTAINER, "c", "b"]
    container = find_action(ui, CONTAINER, top_level)
    assert action_order(ui, find_action_list(ui, "short", container)) == ["a"]
