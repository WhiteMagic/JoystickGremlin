# -*- coding: utf-8; -*-

# Copyright (C) 2019 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import math
import logging
import time
import uuid
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from PySide6 import QtCharts, QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

import dill

from gremlin import common, device_initialization, event_handler, \
    shared_state, util
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.input_cache import DeviceDatabase
from gremlin.logical_device import LogicalDevice
from gremlin.types import InputType, PropertyType

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.Device"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class InputIdentifier(QtCore.QObject):

    """Stores the identifier of a single input item."""

    changed = Signal()

    def __init__(
            self,
            device_guid: uuid.UUID | None=None,
            input_type: InputType | None=None,
            input_id: int | None=None,
            parent: ta.OQO=None
    ) -> None:
        super().__init__(parent)

        self.device_guid = device_guid
        self.input_type = input_type
        self.input_id = input_id

    @Property(str, notify=changed)
    def label(self) -> str:
        if self.isValid:
            if self.device_guid == dill.UUID_LogicalDevice:
                dev_name = "Logical Device"
            else:
                dev_name = dill.DILL.get_device_name(
                    dill.GUID.from_uuid(self.device_guid)
                )
            return f"{dev_name} - " + \
                   f"{InputType.to_string(self.input_type).capitalize()} " + \
                   f"{self.input_id}"
        else:
            return "No input"

    @Property(bool, notify=changed)
    def isValid(self) -> bool:
        return self.device_guid is not None \
            and self.input_type is not None \
            and self.input_id is not None

    def __eq__(self, other: InputIdentifier) -> bool:
        return self.device_guid == other.device_guid and \
            self.input_type == other.input_type and \
            self.input_id == other.input_id


@QtQml.QmlElement
class DeviceListModel(QtCore.QAbstractListModel):

    """Model containing basic information about all connected devices."""

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("axes".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("buttons".encode()),
        QtCore.Qt.UserRole + 4: QtCore.QByteArray("hats".encode()),
        QtCore.Qt.UserRole + 5: QtCore.QByteArray("pid".encode()),
        QtCore.Qt.UserRole + 6: QtCore.QByteArray("vid".encode()),
        QtCore.Qt.UserRole + 7: QtCore.QByteArray("guid".encode()),
        QtCore.Qt.UserRole + 8: QtCore.QByteArray("joy_id".encode()),
        QtCore.Qt.UserRole + 9: QtCore.QByteArray("vjoy_id".encode()),
    }

    role_query = {
        "name": lambda dev: dev.name,
        "axes": lambda dev: dev.axis_count,
        "buttons": lambda dev: dev.button_count,
        "hats": lambda dev: dev.hat_count,
        "pid": lambda dev: "{:04X}".format(dev.product_id),
        "vid": lambda dev: "{:04X}".format(dev.vendor_id),
        "guid": lambda dev: str(dev.device_guid),
        "joy_id": lambda dev: dev.joystick_id,
        "vjoy_id": lambda dev: dev.vjoy_id,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices = device_initialization.physical_devices()

        event_handler.EventListener().device_change_event.connect(
            self.update_model
        )

    def update_model(self) -> None:
        """Updates the model if the connected devices change."""
        old_count = len(self._devices)
        self._devices = device_initialization.physical_devices()
        new_count = len(self._devices)

        # Ensure the entire model is refreshed
        self.modelReset.emit()

    def rowCount(self, parent:QtCore.QModelIndex=...) -> int:
        return len(self._devices)

    def data(self, index: QtCore.QModelIndex, role: int=...) -> Any:
        if role in DeviceListModel.roles:
            role_name = DeviceListModel.roles[role].data().decode()
            return DeviceListModel.role_query[role_name](
                self._devices[index.row()]
            )
        else:
            return "Unknown"

    def roleNames(self) -> Dict:
        return DeviceListModel.roles

    @Slot(int, result=str)
    def guidAtIndex(self, index: int) -> str:
        if len(self._devices) == 0:
            return str(dill.UUID_Invalid)
        if not(0 <= index < len(self._devices)):
            raise GremlinError("Provided index out of range")

        return str(self._devices[index].device_guid)

    def _change_device_type(self, types: str) -> None:
        """Sets which device types are going to be used.

        Valid options are:
        - physical
        - virtual
        - all

        Args:
            types: the type of devices to list
        """
        if types == "physical":
            self._devices = device_initialization.physical_devices()
        elif types == "virtual":
            self._devices = device_initialization.vjoy_devices()
        elif types == "all":
            self._devices = device_initialization.joystick_devices()

        # Remove everything and then add it back to force a model update
        new_count = len(self._devices)
        self.rowsRemoved.emit(self.parent(), 0, new_count)
        self.rowsInserted.emit(self.parent(), 0, new_count)

    deviceType = Property(
        str,
        fset=_change_device_type
    )


@QtQml.QmlElement
class Device(QtCore.QAbstractListModel):

    """Model providing access to information about a single device."""

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("actionCount".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("description".encode()),
    }

    deviceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._device: dill.DeviceSummary | None = None
        self._device_mapping: Dict[str, str] | None = None
        self._mode = "Default"

    @Slot(int)
    def refreshInput(self, index: int) -> None:
        """Refreshes the input at the given index.

        Args:
            index: linear index of the device's inputs to refresh
        """
        self.dataChanged.emit(
            self.createIndex(index, 0),
            self.createIndex(index, 0)
        )

    @Slot(str)
    def setMode(self, mode: str) -> None:
        self.layoutAboutToBeChanged.emit()
        self._mode = mode
        self.layoutChanged.emit()

    def _get_guid(self) -> str:
        if self._device is None:
            return "Unknown"
        else:
            return str(self._device.device_guid)

    def _set_guid(self, guid: str) -> None:
        if self._device is not None and guid == str(self._device.device_guid):
            return

        self._device = dill.DILL.get_device_information_by_guid(
            dill.GUID.from_str(guid)
        )

        self._device_mapping = DeviceDatabase().get_mapping(self._device)
        self.deviceChanged.emit()
        self.layoutChanged.emit()

    def rowCount(self, parent:QtCore.QModelIndex=...) -> int:
        if self._device is None:
            return 0

        return self._device.axis_count + \
               self._device.button_count + \
               self._device.hat_count

    def data(self, index: QtCore.QModelIndex, role:int=...) -> Any:
        if role not in Device.roles:
            return "Unknown"

        role_name = Device.roles[role].data().decode()
        match role_name:
            case "name":
                return self._name(self._convert_index(index.row()))
            case "actionCount":
                input_info = self._convert_index(index.row())
                return shared_state.current_profile.get_input_count(
                    self._device.device_guid.uuid,
                    input_info[0],
                    input_info[1],
                    self._mode
                )
            case "description":
                input_info = self._convert_index(index.row())
                item = shared_state.current_profile.get_input_item(
                    self._device.device_guid.uuid,
                    input_info[0],
                    input_info[1],
                    self._mode
                )
                if item and len(item.action_sequences) > 0:
                    labels = filter(
                        lambda x: x != "Root",
                        [seq.root_action.action_label for seq in item.action_sequences]
                    )
                    return " / ".join(labels)
                else:
                    return ""
            case _:
                return ""

    @Slot(int, result=InputIdentifier)
    def inputIdentifier(self, index: int) -> InputIdentifier:
        """Returns the InputIdentifier for input with the specified index.

        Args:
            index: the index of the input for which to generate the
                InpuIdentifier instance

        Returns:
            An InputIdentifier instance referring to the input item with
            the given index.
        """
        identifier = InputIdentifier(parent=self)
        identifier.device_guid = self._device.device_guid.uuid
        input_info = self._convert_index(index)
        identifier.input_type = input_info[0]
        identifier.input_id = input_info[1]

        return identifier

    def _name(self, identifier: Tuple[InputType, int]) -> str:
        input_name = "{} {:d}".format(
            InputType.to_string(identifier[0]).capitalize(),
            identifier[1]
        )

        if self._device_mapping is not None:
            return self._device_mapping.input_name(input_name)
        else:
            return input_name

    def _convert_index(self, index: int) -> Tuple[InputType, int]:
        axis_count = self._device.axis_count
        button_count = self._device.button_count
        hat_count = self._device.hat_count

        if index < axis_count:
            return (
                InputType.JoystickAxis,
                self._device.axis_map[index].axis_index
            )
        elif index < axis_count + button_count:
            return (
                InputType.JoystickButton,
                index + 1 - axis_count
            )
        else:
            return (
                InputType.JoystickHat,
                index + 1 - axis_count - button_count
            )

    def roleNames(self) -> Dict:
        return Device.roles

    guid = Property(
        str,
        fget=_get_guid,
        fset=_set_guid,
        notify=deviceChanged
    )


@QtQml.QmlElement
class LogicalDeviceManagementModel(QtCore.QAbstractListModel):

    """Model providing information about the intermedia output device."""

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"name"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"actionCount"),
        QtCore.Qt.ItemDataRole.UserRole + 3: QtCore.QByteArray(b"label"),
    }

    def __init__(self, parent: None|QtCore.QObject=None) -> None:
        super().__init__(parent)

        self._logical = LogicalDevice()

    @Slot(str)
    def createInput(self, type_str: str) -> None:
        self.beginInsertRows(
            QtCore.QModelIndex(),
            self.rowCount(),
            self.rowCount()
        )
        self._logical.create(InputType.to_enum(type_str))
        self.endInsertRows()
        self.dataChanged.emit(
            self.createIndex(0, 0),
            self.createIndex(self.rowCount(), 0)
        )

    @Slot(str, str)
    def changeName(self, old_label: str, new_label: str) -> None:
        try:
            self._logical.set_label(old_label, new_label)
            self.dataChanged.emit(
                self.createIndex(0, 0),
                self.createIndex(self.rowCount(), 0)
            )
        except GremlinError:
            # FIXME: Somehow needs to reset the text field to the previous value
            pass

    @Slot(str)
    def deleteInput(self, label: str) -> None:
        item_index = self._label_to_index(label)
        self.beginRemoveRows(QtCore.QModelIndex(), item_index, item_index)
        self._logical.delete(label)
        self.endRemoveRows()
        self.dataChanged.emit(
            self.createIndex(0, 0),
            self.createIndex(self.rowCount(), 0)
        )

    def _get_guid(self) -> str:
        return str(self._logical.device_guid)

    def rowCount(self, parent : ta.ModelIndex=QtCore.QModelIndex()) -> int:
        return len(self._logical.labels_of_type())

    def data(
            self,
            index : ta.ModelIndex,
            role : int=QtCore.Qt.ItemDataRole.DisplayRole
     ) -> Any:
        if role not in self.roles:
            return "Unknown"

        input = self._index_to_input(index.row())
        match self.roles[role]:
            case "name":
                return f"{InputType.to_string(input.type).capitalize()} " \
                    f"{input.id}"
            case "actionCount":
                # FIXME: retrieve currently selected mode just as the other
                #   input devices do
                return shared_state.current_profile.get_input_count(
                    self._logical.device_guid,
                    input.type,
                    input.id,
                    "Default"
                )
            case "label":
                return input.label

    @Slot(str, result=List[str])
    def validLabels(self, type_str: str) -> List[str]:
        """Returns a list of valid labels for a given input."""
        type = InputType.to_enum(type_str)
        if len(self._logical.labels_of_type([type])) == 0:
            self._logical.create(type)
        return self._logical.labels_of_type([type])

    @Slot(int, result=InputIdentifier)
    def inputIdentifier(self, index: int) -> InputIdentifier:
        """Returns the InputIdentifier for input with the specified index.

        Args:
            index: the index of the input for which to generate the
                InpuIdentifier instance

        Returns:
            An InputIdentifier instance referring to the input item with
            the given index.
        """
        if index < 0:
            return InputIdentifier(parent=self)

        input = self._index_to_input(index)
        identifier = InputIdentifier(parent=self)
        identifier.device_guid = self._logical.device_guid
        identifier.input_type = input.type
        identifier.input_id = input.id

        return identifier

    def _name(self, identifier: Tuple[InputType, int]) -> str:
        return "{} {:d}".format(
            InputType.to_string(identifier[0]).capitalize(),
            identifier[1]
        )

    def _index_to_input(self, index: int) -> LogicalDevice.Input:
        """Returns the label corresponding to the provided linear index.

        Args:
            index: the linear index into the list of inputs

        Returns:
            The input corresponding to the given index
        """
        return self._logical[self._logical.labels_of_type()[index]]

    def _label_to_index(self, label: str) -> int:
        """Returns the index corresponding to the given label.

        Args:
            label: name of the input for which to determine the index

        Returns:
            Index of the given label in the backend data storage
        """
        all_labels = self._logical.labels_of_type()
        return all_labels.index(label)

    def roleNames(self) -> Dict:
        return self.roles

    guid = Property(str, fget=_get_guid)


@QtQml.QmlElement
class LogicalDeviceSelectorModel(QtCore.QAbstractListModel):

    inputsChanged = Signal()
    selectionChanged = Signal()

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"label"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"id"),
        QtCore.Qt.ItemDataRole.UserRole + 3: QtCore.QByteArray(b"type"),
    }

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        self._logical = LogicalDevice()
        self._valid_types = []
        self._current_index = -1
        self._current_identifier = InputIdentifier(parent=self)

    def rowCount(self, parent: ta.ModelIndex=QtCore.QModelIndex()) -> int:
        return len(self._logical.labels_of_type(self._valid_types))

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role not in self.roleNames():
            raise GremlinError(
                f"Invalid role {role} in LogicalDeviceSelectorModel"
            )

        input = self._logical.inputs_of_type(self._valid_types)[index.row()]
        match self.roles[role]:
            case "label":
                return input.label
            case "id":
                return input.id
            case "type":
                return InputType.to_string(input.type)

    def roleNames(self) -> Dict:
        return self.roles

    def _set_valid_types(self, valid_types: List[str]) -> None:
        type_list = sorted([InputType.to_enum(entry) for entry in valid_types])
        if type_list != self._valid_types:
            is_initialized = len(self._valid_types) > 0
            self._valid_types = type_list
            self.inputsChanged.emit()
            if is_initialized:
                self._set_current_index(0)

    def _get_current_identifier(self) -> InputIdentifier:
        return self._current_identifier

    def _set_current_identifier(self, identifier: InputIdentifier) -> None:
        if identifier != self._current_identifier:
            # Find the index that would correspond to the given identifier.
            for i, input in enumerate(
                self._logical.inputs_of_type(self._valid_types)
            ):
                if input.type == identifier.input_type and \
                        input.id == identifier.input_id:
                    self._set_current_index(i)

    def _get_current_index(self) -> int:
        return self._current_index

    def _set_current_index(self, index: int) -> None:
        if index != self._current_index:
            input = self._logical.inputs_of_type(self._valid_types)[index]
            self._current_identifier = InputIdentifier(
                LogicalDevice().device_guid,
                input.type,
                input.id,
                parent=self
            )
            self._current_index = index
            self.selectionChanged.emit()

    validTypes = Property(
        list,
        fset=_set_valid_types,
        notify=inputsChanged
    )

    currentIdentifier = Property(
        InputIdentifier,
        fget=_get_current_identifier,
        fset=_set_current_identifier,
        notify=selectionChanged
    )

    currentIndex = Property(
        int,
        fget=_get_current_index,
        fset=_set_current_index,
        notify=selectionChanged
    )


@QtQml.QmlElement
class VJoyDevices(QtCore.QObject):

    """vJoy model used together with the VJoySelector QML.

    The model provides setters and getters for UI selection index values while
    only providing getters for the equivalent id based values. Setting the
    state based on id values is supported via a slot method.
    """

    deviceModelChanged = Signal()
    inputModelChanged = Signal()
    validTypesChanged = Signal()

    vjoyIndexChanged = Signal()
    vjoyIdChanged = Signal()
    inputIdChanged = Signal()
    inputIndexChanged = Signal()
    inputTypeChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._devices = sorted(
            device_initialization.vjoy_devices(),
            key=lambda x: x.vjoy_id
        )

        # Information used to determine what to show in the UI
        self._valid_types = [
            InputType.JoystickAxis,
            InputType.JoystickButton,
            InputType.JoystickHat
        ]
        self._input_items = []
        self._input_data = []

        # Model state information to allow translation between UI index
        # values and model ids
        self._current_vjoy_index = 0
        # Force a refresh of internal state
        self.inputModel
        self._current_input_index = 0
        self._current_input_type = self._input_data[0][0]

        self._is_initialized = False

    def _device_name(self, device) -> str:
        return "vJoy Device {:d}".format(device.vjoy_id)

    def _is_state_valid(self) -> bool:
        """Returns if the state of the object is valid.

        Returns:
            True if the state is valid and consistent, False otherwise
        """
        return self._current_vjoy_index is not None and \
               self._current_input_index is not None and \
               self._current_input_type is not None

    @Slot(int, int, str)
    def setSelection(self, vjoy_id: int, input_id: int, input_type: str) -> None:
        """Sets the internal index state based on the model id data.

        Args:
            vjoy_id: id of the vjoy device
            input_id: id of the input item
            input_type: type of input being selected by the input_id
        """
        # Find vjoy_index corresponding to the provided id
        vjoy_index = -1
        for i, dev in enumerate(self._devices):
            if dev.vjoy_id == vjoy_id:
                vjoy_index = i
                self._set_vjoy_index(i)

        if vjoy_index == -1:
            raise GremlinError(f"Could not find vJoy device with id {vjoy_id}")

        # Find the index corresponding to the provided input_type and input_id
        input_label = common.input_to_ui_string(
            InputType.to_enum(input_type),
            input_id
        )
        try:
            self._set_input_index(self._input_items.index(input_label))
        except ValueError:
            logging.getLogger("system").warning(
                f"No input named \"{input_label}\" present"
            )
            self._set_input_index(0)

    @Property(type="QVariantList", notify=deviceModelChanged)
    def deviceModel(self):
        return [self._device_name(dev) for dev in self._devices]

    @Property(type="QVariantList", notify=inputModelChanged)
    def inputModel(self):
        input_count = {
            InputType.JoystickAxis: lambda x: x.axis_count,
            InputType.JoystickButton: lambda x: x.button_count,
            InputType.JoystickHat: lambda x: x.hat_count
        }

        self._input_items = []
        self._input_data = []
        device = self._devices[self._current_vjoy_index]
        # Add items based on the input type
        for input_type in self._valid_types:
            for i in range(input_count[input_type](device)):
                input_id = i+1
                if input_type == InputType.JoystickAxis:
                    input_id = device.axis_map[i].axis_index

                self._input_items.append(common.input_to_ui_string(
                    input_type,
                    input_id
                ))
                self._input_data.append((input_type, input_id))

        return self._input_items

    def _get_valid_types(self) -> List[str]:
        return [InputType.to_string(entry) for entry in self._valid_types]

    def _set_valid_types(self, valid_types: List[str]) -> None:
        type_list = [InputType.to_enum(entry) for entry in sorted(valid_types)]
        if type_list != self._valid_types:
            self._valid_types = type_list

            # When changing the input type attempt to preserve the existing
            # selection if the input type is part of the new set of valid
            # types. If this is not possible, the selection is set to the
            # first entry of the available values.
            old_vjoy_id = self._get_vjoy_id()
            old_input_type = self._get_input_type()

            # Refresh the UI elements
            self.inputModel

            input_label = common.input_to_ui_string(
                InputType.to_enum(old_input_type),
                old_vjoy_id
            )
            if input_label in self._input_items:
                self.setSelection(
                    self._get_vjoy_id(),
                    old_vjoy_id,
                    old_input_type
                )
            else:
                self._current_vjoy_index = 0
                self._current_input_index = 0
                self._current_input_type = self._input_data[0][0]

            # Prevent sending change of input indices and thus changing the
            # model if the model hadn't been initialized yet.
            if self._is_initialized:
                self.inputIndexChanged.emit()
            else:
                self._is_initialized = True
            self.validTypesChanged.emit()
            self.inputModelChanged.emit()

    def _get_vjoy_id(self) -> int:
        if not self._is_state_valid():
            raise GremlinError(
                "Attempted to read from invalid VJoyDevices instance."
            )
        return self._devices[self._current_vjoy_index].vjoy_id

    def _get_vjoy_index(self) -> int:
        if not self._is_state_valid():
            raise GremlinError(
                "Attempted to read from invalid VJoyDevices instance."
            )
        return self._current_vjoy_index

    def _set_vjoy_index(self, index: int) -> None:
        if index != self._current_vjoy_index:
            if index >= len(self._devices):
                raise GremlinError(
                    f"Invalid device index used device with index {index} "
                    f"does not exist"
                )
            self._current_vjoy_index = index
            self.vjoyIndexChanged.emit()
            self.inputModelChanged.emit()

    def _get_input_id(self) -> int:
        if not self._is_state_valid():
            raise GremlinError(
                "Attempted to read from invalid VJoyDevices instance."
            )
        return self._input_data[self._current_input_index][1]

    def _get_input_index(self) -> int:
        if not self._is_state_valid():
            raise GremlinError(
                "Attempted to read from invalid VJoyDevices instance."
            )
        return self._current_input_index

    def _set_input_index(self, index: int) -> None:
        if index != self._current_input_index:
            self._current_input_index = index
            self._current_input_type = self._input_data[index][0]
            self.inputIndexChanged.emit()

    def _get_input_type(self) -> str:
        return InputType.to_string(self._current_input_type)

    validTypes = Property(
        "QVariantList",
        fget=_get_valid_types,
        fset=_set_valid_types,
        notify=validTypesChanged
    )

    vjoyId = Property(
        int,
        fget=_get_vjoy_id,
        notify=vjoyIdChanged
    )

    vjoyIndex = Property(
        int,
        fget=_get_vjoy_index,
        fset=_set_vjoy_index,
        notify=vjoyIndexChanged
    )

    inputId = Property(
        int,
        fget=_get_input_id,
        notify=inputIdChanged
    )

    inputIndex = Property(
        int,
        fget=_get_input_index,
        fset=_set_input_index,
        notify=inputIndexChanged
    )

    inputType = Property(
        str,
        fget=_get_input_type,
        notify=inputTypeChanged
    )


class AbstractDeviceState(QtCore.QAbstractListModel):

    deviceChanged = Signal()

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("identifier".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("value".encode()),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        el = event_handler.EventListener()
        el.joystick_event.connect(self._event_callback)

        self._device = None
        self._device_uuid = None
        self._state = []

    def _event_callback(self, event: event_handler.Event):
        if event.device_guid != self._device_uuid:
            return

        self._event_handler_impl(event)

    def _event_handler_impl(self, event: event_handler.Event) -> None:
        raise GremlinError(
            "AbstractDeviceState._event_handler_impl not implemented"
        )

    def _set_guid(self, guid: str) -> None:
        if self._device is not None and guid == str(self._device.device_guid):
            return

        self._device = dill.DILL.get_device_information_by_guid(
            dill.GUID.from_str(guid)
        )
        self._device_uuid = uuid.UUID(guid)
        self._state = []
        self._initialize_state()
        self.deviceChanged.emit()

    def _initilize_state(self) -> None:
        raise GremlinError(
            "AbstractDeviceState._initialize_state not implemented"
        )

    def rowCount(self, parent:QtCore.QModelIndex=...) -> int:
        if self._device is None:
            return 0

        return len(self._state)

    def data(self, index: QtCore.QModelIndex, role:int=...) -> Any:
        if role not in AbstractDeviceState.roles:
            return False

        role_name = AbstractDeviceState.roles[role].data().decode()
        return self._state[index.row()][role_name]

    def roleNames(self) -> Dict:
        return AbstractDeviceState.roles

    guid = Property(
        str,
        fset=_set_guid,
        notify=deviceChanged
    )


@QtQml.QmlElement
class DeviceAxisState(AbstractDeviceState):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._identifier_map = {}

    def _event_handler_impl(self, event: event_handler.Event) -> None:
        if event.event_type == InputType.JoystickAxis:
            index = self._identifier_map[event.identifier]
            self._state[index]["value"] = event.value
            self.dataChanged.emit(self.index(index, 0), self.index(index, 0))

    def _initialize_state(self) -> None:
        for i in range(self._device.axis_count):
            self._identifier_map[self._device.axis_map[i].axis_index] = i
            self._state.append({
                "identifier": self._device.axis_map[i].axis_index,
                "value": 0.0
            })


@QtQml.QmlElement
class DeviceButtonState(AbstractDeviceState):

    def __init__(self, parent=None):
        super().__init__(parent)

    def _event_handler_impl(self, event):
        if event.event_type == InputType.JoystickButton:
            idx = event.identifier-1
            self._state[idx]["value"] = event.is_pressed
            self.dataChanged.emit(self.index(idx, 0), self.index(idx, 0))

    def _initialize_state(self) -> None:
        for i in range(self._device.button_count):
            self._state.append({
                "identifier": i+1,
                "value": False
            })


@QtQml.QmlElement
class DeviceHatState(AbstractDeviceState):

    def __init__(self, parent=None):
        super().__init__(parent)

    def _event_handler_impl(self, event):
        if event.event_type == InputType.JoystickHat:
            idx = event.identifier-1
            pt = QtCore.QPoint(event.value.value[0], event.value.value[1])
            if pt != self._state[idx]["value"]:
                self._state[idx]["value"] = pt
                self.dataChanged.emit(self.index(idx, 0), self.index(idx, 0))

    def _initialize_state(self) -> None:
        for i in range(self._device.hat_count):
            self._state.append({
                "identifier": i+1,
                "value": QtCore.QPoint(0, 0)
            })


@QtQml.QmlElement
class DeviceAxisSeries(QtCore.QObject):

    windowSizeChanged = Signal()
    deviceChanged = Signal()
    axisCountChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        el = event_handler.EventListener()
        el.joystick_event.connect(self._event_callback)

        self._device = None
        self._device_uuid = None
        self._state = []
        self._identifier_map = {}
        self._window_size = 20

    def _set_guid(self, guid: str) -> None:
        if self._device is not None and guid == str(self._device.device_guid):
            return

        self._device = dill.DILL.get_device_information_by_guid(
            dill.GUID.from_str(guid)
        )
        self._device_uuid = uuid.UUID(guid)

        self._state = []
        for i in range(self._device.axis_count):
            self._identifier_map[self._device.axis_map[i].axis_index] = i
            self._state.append({
                "identifier": self._device.axis_map[i].axis_index,
                "timeSeries": []
            })
        self.deviceChanged.emit()

    def _get_window_size(self) -> int:
        return self._window_size

    def _set_window_size(self, value: int) -> None:
        if value != self._window_size:
            self._window_size = value
            self.windowSizeChanged.emit()

    def _event_callback(self, event: event_handler.Event):
        if event.device_guid != self._device_uuid:
            return

        if event.event_type == InputType.JoystickAxis:
            index = self._identifier_map[event.identifier]
            self._state[index]["timeSeries"].append(
                (time.time(), event.value)
            )

    @Property(int, notify=axisCountChanged)
    def axisCount(self) -> int:
        return self._device.axis_count

    @Slot(QtCharts.QLineSeries, int)
    def updateSeries(self, series: QtCharts.QLineSeries, identifier: int):
        data = self._state[identifier]["timeSeries"]

        if len(data) == 0:
            series.replace([
                QtCore.QPointF(0.0, 0.0),
                QtCore.QPointF(self._window_size, 0.0),
            ])
            return

        now  = time.time()
        try:
            while now - data[0][0] > self._window_size:
                data.pop(0)
        except IndexError as e:
            logging.getLogger("system").warning(f"Unexpected exception: {e}")
            return

        time_series = []
        for pt in data:
            time_series.append(QtCore.QPointF(pt[0] - now, pt[1]))
        time_series.append(QtCore.QPointF(0, data[-1][1]))
        series.replace(time_series)

    @Slot(int, result=int)
    def axisIdentifier(self, index: int) -> int:
        return self._state[index]["identifier"]

    guid = Property(
        str,
        fset=_set_guid,
        notify=deviceChanged
    )

    windowSize = Property(
        int,
        fset=_set_window_size,
        fget=_get_window_size,
        notify=windowSizeChanged
    )


@QtQml.QmlElement
class AxisCalibration(QtCore.QAbstractListModel):

    deviceChanged = Signal()

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"identifier"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"calibratedValue"),
        QtCore.Qt.ItemDataRole.UserRole + 3: QtCore.QByteArray(b"rawValue"),
        QtCore.Qt.ItemDataRole.UserRole + 4: QtCore.QByteArray(b"low"),
        QtCore.Qt.ItemDataRole.UserRole + 5: QtCore.QByteArray(b"centerLow"),
        QtCore.Qt.ItemDataRole.UserRole + 6: QtCore.QByteArray(b"centerHigh"),
        QtCore.Qt.ItemDataRole.UserRole + 7: QtCore.QByteArray(b"high"),
        QtCore.Qt.ItemDataRole.UserRole + 8: QtCore.QByteArray(b"withCenter"),
        QtCore.Qt.ItemDataRole.UserRole + 9: QtCore.QByteArray(b"unsavedChanges"),
    }

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        self._event_listener = event_handler.EventListener()
        self._event_listener.joystick_event.connect(self._event_callback)

        self._device = None
        self._device_uuid = None
        self._state = []
        self._calibration_fn = []
        self._active_calibrations = []

        self._config = Configuration()
        self._device_db = DeviceDatabase()
        self._device_mapping = None

    def data(
        self,
        index: ta.ModelIndex,
        role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role not in self.roles:
            return None

        role_name = self.roles[role].data().decode()
        return self._state[index.row()][role_name]

    def setData(
        self,
        index: ta.ModelIndex,
        value: Any,
        role: int=QtCore.Qt.ItemDataRole.EditRole
    ) -> bool:
        if role not in self.roles:
            return False

        # Update internal representation
        role_name = self.roles[role].data().decode()
        self._state[index.row()][role_name] = value
        self._state[index.row()]["unsavedChanges"] = True
        self._update_calibration(index.row())

        # Signal that the model has changed for a UI update
        self.emit_update(index.row())
        return True

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        if self._device is None:
            return 0

        return len(self._state)

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles

    def emit_update(self, index: int) -> None:
        """Emits the data update signal for the given index."""
        self.dataChanged.emit(self.index(index, 0), self.index(index, 0))

    @Slot(int)
    def reset(self, index: int) -> None:
        """Resets the calibration data of the specified axis.

        Args:
            index: index of the axis to reset
        """
        if not (0 <= index < len(self._state)):
            return

        # Reset values to defaults
        self._state[index]["low"] = -32768
        self._state[index]["centerLow"] = 0
        self._state[index]["centerHigh"] = 0
        self._state[index]["high"] = 32767
        self._state[index]["unsavedChanges"] = True

        # Reset calibration tracking data to continue calibration after a
        # reset.
        self._active_calibrations[index]["cvalues"] = [0, 0]
        self._active_calibrations[index]["evalues"] = [0, 0]

        # Update models
        self._update_calibration(index)
        self.emit_update(index)

    @Slot(int, bool)
    def calibrateCenter(self, index: int, is_active: bool) -> None:
        self._active_calibrations[index]["center"] = is_active
        self._active_calibrations[index]["extrema"] = False
        self._active_calibrations[index]["cvalues"] = [0, 0]
        if is_active:
            self._state[index]["centerLow"] = 0
            self._state[index]["centerHigh"] = 0
            self.emit_update(index)

    @Slot(int, bool)
    def calibrateExtrema(self, index: int, is_active: bool) -> None:
        self._active_calibrations[index]["extrema"] = is_active
        self._active_calibrations[index]["center"] = False
        self._active_calibrations[index]["evalues"] = [0, 0]
        if is_active:
            self._state[index]["low"] = 0
            self._state[index]["high"] = 0
            self.emit_update(index)

    @Slot(int)
    def save(self, index: int) -> None:
        """Saves the current calibration data to the configuration system.

        Args:
            index: index of the axis whose data to save
        """
        if self._device_uuid is None or self._device is None:
            return

        self._config.set_calibration(
            self._device_uuid,
            self._device.axis_map[index].axis_index,
            (
                self._state[index]["low"],
                self._state[index]["centerLow"],
                self._state[index]["centerHigh"],
                self._state[index]["high"],
                self._state[index]["withCenter"]
            )
        )
        self._state[index]["unsavedChanges"] = False
        self._event_listener.reload_calibration(
            self._device.device_guid,
            self._device.axis_map[index].axis_index,
        )
        self.emit_update(index)

    def _update_calibration(self, index: int) -> None:
        """Creates the calibration function based on the stored values.

        Args:
            index: index of the axis to update the calibration function of
        """
        self._calibration_fn[index] = util.create_calibration_function(
            self._state[index]["low"],
            self._state[index]["centerLow"],
            self._state[index]["centerHigh"],
            self._state[index]["high"],
            self._state[index]["withCenter"]
        )

    def _set_guid(self, guid: str) -> None:
        if self._device is not None and guid == str(self._device.device_guid):
            return

        self.beginResetModel()
        self._device = dill.DILL.get_device_information_by_guid(
            dill.GUID.from_str(guid)
        )
        self._device_uuid = uuid.UUID(guid)
        self._device_mapping = self._device_db.get_mapping(self._device)
        self._state = []
        self._calibration_fn = []
        self._active_calibrations = []
        self._initialize_state()
        self.deviceChanged.emit()
        self.modelReset.emit()
        self.endResetModel()

    def _initialize_state(self) -> None:
        if self._device_uuid is None or self._device is None:
            return

        for i in range(self._device.axis_count):
            # Register the device in the configuration system, does not
            # change the calibration values if the device has previously been
            # calibrated.
            key = (self._device_uuid, self._device.axis_map[i].axis_index)
            self._config.init_calibration(*key)

            axis_name = "{} {:d}".format(
                InputType.to_string(InputType.JoystickAxis).capitalize(),
                key[1]
            )
            if self._device_mapping:
                axis_name = self._device_mapping.input_name(axis_name)

            calibration_data = self._config.get_calibration(*key)
            self._state.append({
                "identifier": axis_name,
                "rawValue": 0,
                "calibratedValue": 0,
                "low": calibration_data[0],
                "centerLow": calibration_data[1],
                "centerHigh": calibration_data[2],
                "high": calibration_data[3],
                "withCenter": calibration_data[4],
                "unsavedChanges": False
            })

            self._calibration_fn.append(None)
            self._active_calibrations.append({"center": False, "extrema": False})
            self._update_calibration(i)

    def _event_callback(self, event: event_handler.Event) -> None:
        if event.device_guid != self._device_uuid:
            return

        if self._device is None:
            return

        if event.event_type == InputType.JoystickAxis:
            index = self._device.axis_lookup[event.identifier] - 1
            state = self._state[index]

            # Update axis value information
            state["rawValue"] = event.raw_value
            state["calibratedValue"] = math.floor(
                self._calibration_fn[index](event.raw_value) * 65535 / 2
            )

            # Check if we're calibrating the axis and if so record possible
            # new calibration values
            calibration_changed = False
            if self._active_calibrations[index]["center"]:
                data = self._active_calibrations[index]["cvalues"]
                if data[0] > event.raw_value:
                    data[0] = event.raw_value
                    state["centerLow"] = event.raw_value
                    calibration_changed = True
                if data[1] < event.raw_value:
                    data[1] = event.raw_value
                    state["centerHigh"] = event.raw_value
                    calibration_changed = True
            elif self._active_calibrations[index]["extrema"]:
                data = self._active_calibrations[index]["evalues"]
                if data[0] > event.raw_value:
                    data[0] = event.raw_value
                    state["low"] = event.raw_value
                    calibration_changed = True
                if data[1] < event.raw_value:
                    data[1] = event.raw_value
                    state["high"] = event.raw_value
                    calibration_changed = True

            # Recompute the calibration function if we're actively calibrating
            if self._active_calibrations[index]["center"] or \
                    self._active_calibrations[index]["extrema"]:
                self._update_calibration(index)
                if calibration_changed == True:
                    self._state[index]["unsavedChanges"] = True

            # Signal that the model has changed for a UI update
            self.emit_update(index)

    guid = Property(
        str,
        fset=_set_guid,
        notify=deviceChanged
    )


Configuration().register(
    "global",
    "input-names",
    "input-name-display-mode",
    PropertyType.Selection,
    "Numerical & Label",
    "Defines how input name is displayed.",
    {
        "valid_options": ["Numerical", "Numerical + Label", "Label"]
    },
    True
)
