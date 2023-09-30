# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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

import time
import uuid
from typing import Any, Dict, List, Tuple

from PySide6 import QtCharts, QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

import dill

from gremlin import common, event_handler, joystick_handling
from gremlin.error import GremlinError
from gremlin.intermediate_output import IntermediateOutput
from gremlin.types import InputType
from gremlin.util import parse_guid

from gremlin.ui import backend


QML_IMPORT_NAME = "Gremlin.Device"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class InputIdentifier(QtCore.QObject):

    """Stores the identifier of a single input item."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.device_guid = None
        self.input_type = None
        self.input_id = None

    @Property(bool)
    def isValid(self) -> bool:
        return self.device_guid is not None \
            and self.input_type is not None \
            and self.input_id is not None


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
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices = joystick_handling.physical_devices()

        event_handler.EventListener().device_change_event.connect(
            self.update_model
        )

    def update_model(self) -> None:
        """Updates the model if the connected devices change."""
        old_count = len(self._devices)
        self._devices = joystick_handling.joystick_devices()
        new_count = len(self._devices)

        # Remove everything and then add it back to force a model update
        self.rowsRemoved.emit(self.parent(), 0, new_count)
        self.rowsInserted.emit(self.parent(), 0, new_count)

    def rowCount(self, parent:QtCore.QModelIndex=...) -> int:
        return len(self._devices)

    def data(self, index:QtCore.QModelIndex, role:int=...) -> Any:
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
            self._devices = joystick_handling.physical_devices()
        elif types == "virtual":
            self._devices = joystick_handling.vjoy_devices()
        elif types == "all":
            self._devices = joystick_handling.joystick_devices()

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
    }

    deviceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._device = None

    def _get_guid(self) -> str:
        if self._device is None:
            return "Unknown"
        else:
            return str(self._device.device_guid)

    def _set_guid(self, guid: str) -> None:
        if self._device is not None and guid == str(self._device.device_guid):
            return

        self._device = dill.DILL.get_device_information_by_guid(
            parse_guid(guid)
        )
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
        if role_name == "name":
            return self._name(self._convert_index(index.row()))
        elif role_name == "actionCount":
            profile = backend.Backend().profile
            input_info = self._convert_index(index.row())
            return profile.get_input_count(
                self._device.device_guid,
                input_info[0],
                input_info[1],
            )

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
        identifier = InputIdentifier(self)
        identifier.device_guid = self._device.device_guid
        input_info = self._convert_index(index)
        identifier.input_type = input_info[0]
        identifier.input_id = input_info[1]

        return identifier

    def _name(self, identifier: Tuple[InputType, int]) -> str:
        return "{} {:d}".format(
            InputType.to_string(identifier[0]).capitalize(),
            identifier[1]
        )

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
        fset=_set_guid
    )


@QtQml.QmlElement
class IODeviceManagementModel(QtCore.QAbstractListModel):

    """Model providing information about the intermedia output device."""

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("actionCount".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("label".encode()),
    }

    deviceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._io = IntermediateOutput()

    @Slot(str)
    def createInput(self, type_str: str) -> None:
        self._io.create(InputType.to_enum(type_str))
        self.modelReset.emit()

    @Slot(str, str)
    def changeName(self, old_labele: str, new_label: str) -> None:
        try:
            self._io.set_label(old_labele, new_label)
        except GremlinError:
            # FIXME: Somehow needs to reset the text field to the previous value
            pass

    @Slot(str)
    def deleteInput(self, label: str) -> None:
        self._io.delete(label)
        self.modelReset.emit()

    def _get_guid(self) -> str:
        return str(self._io.device_guid)

    def rowCount(self, parent:QtCore.QModelIndex=...) -> int:
        return len(self._io.labels_of_type())

    def data(self, index: QtCore.QModelIndex, role:int=...) -> Any:
        if role not in IODeviceManagementModel.roles:
            return "Unknown"

        role_name = IODeviceManagementModel.roles[role].data().decode()
        input = self._index_to_input(index.row())
        if role_name == "name":
            return f"{InputType.to_string(input.type).capitalize()} " \
                f"{input.suffix}"
        elif role_name == "actionCount":
            return backend.Backend().profile.get_input_count(
                self._io.device_guid,
                input.type,
                input.guid
            )
        elif role_name == "label":
            return input.label

    @Slot(str, result=List[str])
    def validLabels(self, type_str: str) -> List[str]:
        """Returns a list of valid labels for a given input."""
        type = InputType.to_enum(type_str)
        if len(self._io.keys_of_type([type])) == 0:
            self._io.create(type)
        return self._io.keys_of_type([type])

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
            return InputIdentifier(self)

        input = self._index_to_input(index)
        identifier = InputIdentifier(self)
        identifier.device_guid = self._io.device_guid
        identifier.input_type = input.type
        identifier.input_id = input.guid

        return identifier

    def _name(self, identifier: Tuple[InputType, int]) -> str:
        return "{} {:d}".format(
            InputType.to_string(identifier[0]).capitalize(),
            identifier[1]
        )

    def _index_to_input(self, index: int) -> IntermediateOutput.Input:
        """Returns the label corresponding to the provided linear index.

        Args:
            index: the linear index into the list of inputs

        Returns:
            The input corresponding to the given index
        """
        return self._io[self._io.labels_of_type()[index]]

    def roleNames(self) -> Dict:
        return IODeviceManagementModel.roles

    guid = Property(str, fget=_get_guid)


@QtQml.QmlElement
class IODeviceInputsModel(QtCore.QAbstractListModel):

    inputsChanged = Signal()
    selectionChanged = Signal()

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("label".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("guid".encode())
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self._io = IntermediateOutput()
        self._valid_types = None
        self._current_index = 0
        self._current_guid = None

    def rowCount(self, parent) -> int:
        return len(self._io.labels_of_type(self._valid_types))

    def data(
            self,
            index: PySide6.QtCore.QModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role not in self.roleNames():
            raise GremlinError(f"Invalid role {role} in IODeviceInputsModel")

        input = self._io.inputs_of_type(self._valid_types)[index.row()]
        if role == QtCore.Qt.UserRole + 1:
            return input.label
        elif role == QtCore.Qt.UserRole + 2:
            return str(input.guid)

    def roleNames(self) -> Dict:
        return IODeviceInputsModel.roles

    def _set_valid_types(self, valid_types: List[str]) -> None:
        type_list = sorted([InputType.to_enum(entry) for entry in valid_types])
        if type_list != self._valid_types:
            self._valid_types = type_list
            self.inputsChanged.emit()

    def _get_current_selection_index(self) -> int:
        return self._current_index

    def _get_current_guid(self) -> str:
        return str(self._current_guid)

    def _set_current_guid(self, guid_str: str) -> None:
        guid = uuid.UUID(guid_str)
        if guid != self._current_guid:
            self._current_guid = guid
            self._current_index = 0
            for i, input in enumerate(self._io.inputs_of_type(self._valid_types)):
                if input.guid == guid:
                    self._current_index = i
            self.selectionChanged.emit()

    validTypes = Property(
        "QVariantList",
        fset=_set_valid_types,
        notify=inputsChanged
    )

    currentSelectionIndex = Property(
        int,
        fget=_get_current_selection_index,
        notify=selectionChanged
    )

    currentGuid = Property(
        str,
        fget=_get_current_guid,
        fset=_set_current_guid,
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
            joystick_handling.vjoy_devices(),
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
            raise GremlinError(f"No input named \"{input_label}\" present")

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
        type_list = sorted([InputType.to_enum(entry) for entry in valid_types])
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
        self._state = []

    def _event_callback(self, event: event_handler.Event):
        if event.device_guid != self._device.device_guid:
            return

        self._event_handler_impl(event)

    def _event_handler_impl(self, event: event_handler.Event) -> None:
        raise GremlinError(
            "AbstractDeviceState._event_handler_impl not implemented"
        )

    def _set_guid(self, guid: str) -> None:
        if self._device is not None and guid == str(self._device.device_guid):
            return

        self._device = dill.DILL.get_device_information_by_guid(parse_guid(guid))
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

        role_name = DeviceButtonState.roles[role].data().decode()
        return self._state[index.row()][role_name]

    def roleNames(self) -> Dict:
        return DeviceButtonState.roles

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
            pt = QtCore.QPoint(event.value[0], event.value[1])
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
        self._state = []
        self._identifier_map = {}
        self._window_size = 20

    def _set_guid(self, guid: str) -> None:
        if self._device is not None and guid == str(self._device.device_guid):
            return

        self._device = dill.DILL.get_device_information_by_guid(parse_guid(guid))

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
        if event.device_guid != self._device.device_guid:
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
        while now - data[0][0] > self._window_size:
            data.pop(0)

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