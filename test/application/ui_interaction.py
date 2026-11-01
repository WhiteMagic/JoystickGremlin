# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import contextlib
import pathlib
from collections.abc import (
    Callable,
    Generator,
)

import pytest
import pytestqt.exceptions
import shiboken6
from PySide6 import (
    QtCore,
    QtGui,
    QtQuick,
)

import dill
import gremlin.ui.backend
from gremlin import common
from gremlin.logical_device import LogicalDevice
from gremlin.types import (
    HatDirection,
    InputType,
)
from gremlin.ui.util import InputListenerModel
from test.application.fakes import (
    STICK,
    PhysicalInjector,
)
from test.application.ui_driver import UiDriver

INPUT_TYPE_NAMES = ["Axis", "Button", "Hat"]
# Input each input type name's tests use, on the stick and on the vJoy device.
INPUTS = {
    "Axis": (InputType.JoystickAxis, 2),
    "Button": (InputType.JoystickButton, 3),
    "Hat": (InputType.JoystickHat, 1),
}


def add_logical_input(ui: UiDriver, input_type_name: str) -> str:
    """Adds a logical input of the given input type name and returns its label."""
    existing_labels = set(LogicalDevice().labels_of_type())
    ui.click(ui.find_item("logicalDeviceTab"))
    ui.choose_menu_item(ui.find_item("logicalAddInputButton"), input_type_name)
    ui.wait_until(lambda: len(LogicalDevice().labels_of_type()) > len(existing_labels))
    (label,) = set(LogicalDevice().labels_of_type()) - existing_labels
    return label


def select_logical_input(ui: UiDriver, label: str) -> None:
    """Selects the logical input with the given label."""
    logical_input = LogicalDevice()[label]
    ui_state = gremlin.ui.backend.Backend().ui_state

    def is_selected() -> bool:
        return (
            ui_state.currentTab == "logical"
            and ui_state.currentInput.input_type == logical_input.type
            and ui_state.currentInput.input_id == logical_input.id
        )

    if is_selected():
        return

    ui.click(ui.find_item("logicalDeviceTab"))
    row = ui.find_one_where(
        lambda item: (
            item.objectName() == "logicalInput"
            and item.property("name").endswith(f" - {label}")
        ),
        f"listing logical input '{label}'",
    )
    ui.click(row)
    wait_for_input_debounce(ui, is_selected)


def add_and_select_logical_input(ui: UiDriver, input_type_name: str) -> str:
    """Adds a logical input of the given input type name and selects it."""
    label = add_logical_input(ui, input_type_name)
    select_logical_input(ui, label)
    return label


def wait_for_input_debounce(ui: UiDriver, condition: Callable[[], bool]) -> None:
    """Waits until condition holds and the input debounce timer has fired."""
    # The configuration panel shows the input once the timer fired.
    debounce_timer = ui.find_object("inputDebounceTimer")
    ui.wait_until(lambda: condition() and not debounce_timer.property("running"))


def select_physical_input(
    ui: UiDriver, device: dill.DeviceSummary, input_type: InputType, input_id: int
) -> None:
    """Selects the physical input of the given type and id on the given device."""
    ui_state = gremlin.ui.backend.Backend().ui_state

    def is_device_shown() -> bool:
        return (
            ui_state.currentTab == "physical"
            and ui_state.currentDevice == str(device.device_guid.uuid).upper()
        )

    def is_selected() -> bool:
        return (
            is_device_shown()
            and ui_state.currentInput.input_type == input_type
            and ui_state.currentInput.input_id == input_id
        )

    if is_selected():
        return

    tab = ui.find_one_where(
        lambda item: (
            item.objectName() == "physicalDeviceTab"
            and item.property("text") == device.name
        ),
        f"showing device '{device.name}'",
    )
    ui.click(tab)
    ui.wait_until(is_device_shown)
    input_name = common.input_to_ui_string(input_type, input_id)
    row = ui.find_one_where(
        lambda item: (
            item.objectName() == "physicalInput" and item.property("name") == input_name
        ),
        f"listing physical input '{input_name}'",
    )
    ui.click(row)
    wait_for_input_debounce(ui, is_selected)


@contextlib.contextmanager
def open_dialog(
    ui: UiDriver, entry: str, content_name: str
) -> Generator[QtQuick.QQuickItem]:
    """Opens the Tools menu and opens a dialog from it, closing it afterward."""
    ui.open_menu("Tools", entry)
    dialog = ui.find_item(content_name)
    try:
        yield dialog
    finally:
        ui.close_window(dialog)


def manage_modes(ui: UiDriver) -> contextlib.AbstractContextManager[QtQuick.QQuickItem]:
    return open_dialog(ui, "Manage Modes", "manageModesContent")


def add_mode(ui: UiDriver, name: str, parent: str | None = None) -> None:
    with manage_modes(ui) as dialog:
        ui.click(ui.find_item("addModeButton", dialog))
        ui.type_text(ui.find_item("textInputField"), name)
        row = ui.find_item(f"modeRow_{name}", dialog)
        if parent is not None:
            ui.select(ui.find_item("parentModeCombo", row), parent)


def add_action(ui: UiDriver, name: str) -> QtQuick.QQuickItem:
    """Adds an action to the selected input's sequence and returns its node."""
    _add_action(ui, name)
    return find_action(ui, name)


def add_logical_input_with_action(
    ui: UiDriver, input_type_name: str, action_name: str
) -> tuple[str, QtQuick.QQuickItem]:
    """Adds a logical input, selects it and adds an action, returning label and node."""
    label = add_and_select_logical_input(ui, input_type_name)
    return label, add_action(ui, action_name)


def find_action(
    ui: UiDriver, name: str, parent: QtQuick.QQuickItem | None = None
) -> QtQuick.QQuickItem:
    return ui.find_item(f"actionNode_{name}", parent)


def find_rebuilt_action(
    ui: UiDriver, name: str, previous_node: QtQuick.QQuickItem
) -> QtQuick.QQuickItem:
    """Waits for the node of the action called name that replaced previous_node."""
    # Replaced nodes may outlive the rebuild briefly.
    return ui.find_one_where(
        lambda item: (
            item.objectName() == f"actionNode_{name}" and item is not previous_node
        ),
        f"showing rebuilt action '{name}'",
    )


def add_child_action(
    ui: UiDriver, parent: QtQuick.QQuickItem, slot: str, name: str
) -> QtQuick.QQuickItem:
    """Adds an action to the parent's slot labelled slot.

    Adding an action rebuilds every action node of the binding, so this returns the
    parent's new node.
    """
    parent_name = parent.objectName().removeprefix("actionNode_")
    _add_action(ui, name, parent, slot)
    return find_rebuilt_action(ui, parent_name, parent)


def _add_action(
    ui: UiDriver, name: str, parent: QtQuick.QQuickItem | None = None, slot: str = ""
) -> None:
    """Adds an action to the selected input's sequence, or to the parent's slot."""
    if parent is None:
        if ui.find_all("newActionSequenceButton"):
            ui.click(ui.find_item("newActionSequenceButton"))
        ui.choose_menu_item(ui.find_item("addActionButton"), name)
    else:
        header = ui.find_item(f"slotHeader_{slot}", parent)
        ui.choose_menu_item(ui.find_item("slotAddActionButton", header), name)


def find_child_action(
    ui: UiDriver, parent: QtQuick.QQuickItem, container: str, name: str
) -> QtQuick.QQuickItem:
    """Returns the a specified action from a parent's action container."""
    return ui.find_item(
        f"actionNode_{name}", ui.find_item(f"actionList_{container}", parent)
    )


def add_description(
    ui: UiDriver, text: str, parent: QtQuick.QQuickItem | None = None, slot: str = ""
) -> None:
    """Adds a description action and set its text to the parent's slot."""
    _add_action(ui, "Description", parent, slot)
    set_description(ui, find_description(ui, ""), text)


def find_description(ui: UiDriver, text: str) -> QtQuick.QQuickItem:
    """Returns the description action that contains the specified text."""
    return ui.find_one_where(
        lambda item: (
            item.objectName() == "actionNode_Description"
            and any(
                field.property("text") == text
                for field in ui.find_all("descriptionField", item)
            )
        ),
        f"describing '{text}'",
    )


def find_action_list(
    ui: UiDriver,
    container: str,
    owner: QtQuick.QQuickItem | None = None,
    previous: QtQuick.QQuickItem | None = None,
) -> QtQuick.QQuickItem:
    """Returns the owner's list for container, or the sequence's top-level list."""
    return ui.find_one_where(
        lambda item: (
            item.objectName() == f"actionList_{container}" and item is not previous
        ),
        f"listing container '{container}'",
        owner,
        stop_at=_is_action_list,
    )


def action_order(ui: UiDriver, action_list: QtQuick.QQuickItem) -> list[str]:
    """Returns the list's own actions top to bottom.

    Descriptions are identified by their text.
    """
    nodes = sorted(
        ui.find_where(
            lambda item: item.objectName().startswith("actionNode_"),
            action_list,
            stop_at=_is_action_list,
        ),
        key=lambda node: node.mapToScene(QtCore.QPointF()).y(),
    )
    labels = []
    for node in nodes:
        name = node.objectName().removeprefix("actionNode_")
        if name == "Description":
            name = ui.find_item("descriptionField", node).property("text")
        labels.append(name)
    return labels


def drag_action(
    ui: UiDriver,
    node: QtQuick.QQuickItem,
    action_list: QtQuick.QQuickItem,
    position: int,
) -> None:
    """Drags the action by its handle to the boundary position of action_list."""
    handle = ui.find_one_where(
        lambda item: item.objectName() == "dragHandle",
        "being the action's drag handle",
        node,
        stop_at=_is_action_list,
    )
    # The handle is centred on the header, as is the drag's hotspot.
    center = QtCore.QPointF(handle.width() / 2, handle.height() / 2)
    ui.press(handle, center)
    threshold = QtGui.QGuiApplication.styleHints().startDragDistance()
    ui.drag_by(QtCore.QPointF(0, threshold + 1))

    target_y = None

    # Starting the drag and opening indicators moves every target, thus target positions
    # need to be recomputed each step.
    def is_target_open() -> bool:
        nonlocal target_y
        indicators = ui.find_where(
            lambda item: item.objectName() == f"dropIndicator_{position}",
            action_list,
            stop_at=_is_action_list,
        )
        if len(indicators) != 1:
            return False
        (indicator,) = indicators
        # An end target's centre lies under the enclosing list's end target. The top
        # drop target does not have this quirk.
        target_y = indicator.mapToScene(QtCore.QPointF()).y()
        # The node trails the mouse by the drag threshold, so work off the handle's
        # position.
        ui.drag_by(QtCore.QPointF(0, target_y - handle.mapToScene(center).y()))
        return bool(indicator.property("isOpen"))

    try:
        ui.wait_until(is_target_open)
    except pytestqt.exceptions.TimeoutError:
        pass
    assert is_target_open(), (
        f"Drop indicator {position} did not open, its target is at scene y "
        f"{target_y}, the dragged handle at {handle.mapToScene(center).y()}, "
        f"open instead: {_open_indicators(ui)}"
    )
    ui.release()
    try:
        ui.wait_until(lambda: not shiboken6.isValid(node))
    except pytestqt.exceptions.TimeoutError:
        pass
    assert not shiboken6.isValid(node), (
        f"Dropping at indicator {position} did not rebuild the action nodes"
    )


def _is_action_list(item: QtQuick.QQuickItem) -> bool:
    return item.objectName().startswith("actionList_")


def _open_indicators(ui: UiDriver) -> list[str]:
    """Describes each open drop indicator by its list and scene y."""
    return [
        f"{action_list.objectName()}/{indicator.objectName()} at "
        f"{indicator.mapToScene(QtCore.QPointF()).y()}"
        for action_list in ui.find_where(_is_action_list)
        for indicator in ui.find_where(
            lambda item: (
                item.objectName().startswith("dropIndicator_")
                and bool(item.property("isOpen"))
            ),
            action_list,
            stop_at=_is_action_list,
        )
    ]


def typed_number(value: float) -> str:
    """Formats the value the way the controls parse it using the default locale."""
    locale = QtCore.QLocale()
    locale.setNumberOptions(QtCore.QLocale.NumberOption.OmitGroupSeparator)
    return locale.toString(value)


def set_spin_box_value(
    ui: UiDriver, spin_box: QtQuick.QQuickItem, value: float
) -> None:
    ui.type_text(spin_box, typed_number(value))
    ui.wait_for_value(lambda: spin_box.property("value"), pytest.approx(value))


def set_description(ui: UiDriver, action: QtQuick.QQuickItem, text: str) -> None:
    field = ui.find_item("descriptionField", action)
    ui.type_text(field, text)
    ui.wait_for_value(lambda: field.property("text"), text)


def assigned_input_text(label: str) -> str:
    """Returns the text an InputAssignButton shows for a logical input."""
    logical_input = LogicalDevice()[label]
    input_name = common.input_to_ui_string(logical_input.type, logical_input.id)
    return f"Logical Device - {input_name}"


def rename_instance(ui: UiDriver, action: QtQuick.QQuickItem, text: str) -> None:
    """Renames the instance shown by a Merge Axis or Dual Axis Deadzone action."""
    ui.click(ui.find_item("renameInstanceButton", action))
    ui.type_text(ui.find_item("textInputField"), text)
    combo = ui.find_item("instanceCombo", action)
    ui.wait_for_value(lambda: combo.property("currentText"), text)


def select_vjoy_input(
    ui: UiDriver, action: QtQuick.QQuickItem, input_type: InputType, input_id: int
) -> None:
    ui.select(ui.find_item("vjoyDeviceCombo", action), "vJoy Device 1")
    ui.select(
        ui.find_item("vjoyInputCombo", action),
        common.input_to_ui_string(input_type, input_id),
    )


def record_inputs(
    ui: UiDriver, capture_button: QtQuick.QQuickItem, inject: Callable[[], None]
) -> None:
    """Records the inputs generated by the inject callable through.

    The inject callable produces faked input events the InputListener captures.
    """
    ui.click(capture_button)
    listener = capture_button.findChild(InputListenerModel)
    ui.wait_until(lambda: listener.enabled)
    inject()
    ui.wait_until(lambda: not listener.enabled)


def record_stick_input(
    ui: UiDriver,
    capture_button: QtQuick.QQuickItem,
    inject_physical: PhysicalInjector,
    input_type_name: str,
) -> None:
    """Records the joystick input for the given type.

    The inject_physical instance produces events of the specified type that an
    InputListener captures."""
    _, input_id = INPUTS[input_type_name]

    def inject() -> None:
        match input_type_name:
            case "Axis":
                inject_physical.axis(STICK, input_id, 0.0)
                inject_physical.axis(STICK, input_id, 1.0)
            case "Button":
                inject_physical.button(STICK, input_id, True)
                inject_physical.button(STICK, input_id, False)
            case "Hat":
                inject_physical.hat(STICK, input_id, HatDirection.North)

    record_inputs(ui, capture_button, inject)

    # Reset the joystick's stored state after the recording is finished.
    match input_type_name:
        case "Axis":
            inject_physical.axis(STICK, input_id, 0.0)
        case "Hat":
            inject_physical.hat(STICK, input_id, HatDirection.Center)


@contextlib.contextmanager
def gremlin_active(ui: UiDriver) -> Generator[None]:
    """Context that enables Gremlin and disables it at the end."""
    backend = gremlin.ui.backend.Backend()
    ui.click(ui.find_item("activateButton"))
    ui.wait_until(lambda: backend.gremlinActive)
    try:
        yield
    finally:
        ui.click(ui.find_item("activateButton"))
        ui.wait_until(lambda: not backend.gremlinActive)


def save_and_reload(ui: UiDriver, path: pathlib.Path) -> None:
    """Saves through the toolbar and loads the file again via File > Recent."""
    backend = gremlin.ui.backend.Backend()
    ui.click(ui.find_item("saveProfileButton"))
    ui.wait_until(lambda: not backend.profileContainsUnsavedChanges)

    previous_profile = backend.profile
    ui.open_menu("File", "Recent")
    entry = ui.find_one_where(
        lambda item: (
            item.objectName() == "recentProfileItem"
            and pathlib.Path(item.property("text")) == path
        ),
        f"listing recent profile {path}",
    )
    ui.click(entry)
    ui.wait_until(lambda: backend.profile is not previous_profile)


def reload_action(
    ui: UiDriver, path: pathlib.Path, label: str, name: str
) -> QtQuick.QQuickItem:
    """Saves and loads the profile and returns the reloaded action's node."""
    previous_node = find_action(ui, name)
    save_and_reload(ui, path)
    select_logical_input(ui, label)
    return find_rebuilt_action(ui, name, previous_node)
