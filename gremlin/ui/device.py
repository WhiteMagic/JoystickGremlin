# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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

import random
import typing

from PySide2 import QtCore, QtQml
from PySide2.QtCore import Property, Signal, Slot

import dill

from gremlin import common
from gremlin import error
from gremlin import event_handler
from gremlin import input_devices
from gremlin import joystick_handling
from gremlin import profile
from gremlin.types import InputType
from gremlin.util import parse_guid
from gremlin.ui import backend



class InputIdentifier(QtCore.QObject):

    """Stores the identifier of a single input item."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.device_guid = None
        self.input_type = None
        self.input_id = None


class DeviceListModel(QtCore.QAbstractListModel):

    """Model containing absic information about all connected devices."""

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
        self._devices = joystick_handling.joystick_devices()

        event_handler.EventListener().device_change_event.connect(
            self.update_model
        )

    def update_model(self) -> None:
        """Updates the model if the connected devices change."""
        old_count = len(self._devices)
        self._devices = joystick_handling.joystick_devices()
        new_count = len(self._devices)

        # Remove everything and then add it back
        self.rowsRemoved.emit(self.parent(), 0, new_count)
        self.rowsInserted.emit(self.parent(), 0, new_count)

        # self.dataChanged.emit(
        #     self.index(0, 0),
        #     self.index(len(self._devices), 1),
        #     list(DeviceData.roles.keys())
        # )

    def rowCount(self, parent:QtCore.QModelIndex=...) -> int:
        return len(self._devices)

    def data(self, index:QtCore.QModelIndex, role:int=...) -> typing.Any:
        if role in DeviceListModel.roles:
            role_name = DeviceListModel.roles[role].data().decode()
            return DeviceListModel.role_query[role_name](
                self._devices[index.row()]
            )
        else:
            return "Unknown"

    def roleNames(self) -> typing.Dict:
        return DeviceListModel.roles

    @Slot(int, result=str)
    def guidAtIndex(self, index: int) -> str:
        if not(0 <= index < len(self._devices)):
            raise error.GremlinError("Provided index out of range")

        return str(self._devices[index].device_guid)


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

    def data(self, index: QtCore.QModelIndex, role:int=...) -> typing.Any:
        if role not in Device.roles:
            return "Unknown"

        role_name = Device.roles[role].data().decode()
        if role_name == "name":
            return self._name(self._convert_index(index.row()))
        elif role_name == "actionCount":
            try:
                profile = backend.Backend().profile
                input_info = self._convert_index(index.row())
                item = profile.get_input_item(
                    self._device.device_guid,
                    input_info[0],
                    input_info[1],
                    False
                )
                return len(item.action_configurations)
            except error.ProfileError as e:
                return 0

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

    def _name(self, identifier: typing.Tuple[InputType, int]) -> str:
        return "{} {:d}".format(
            InputType.to_string(identifier[0]).capitalize(),
            identifier[1]
        )

    def _convert_index(self, index: int) -> typing.Tuple[InputType, int]:
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

    def roleNames(self) -> typing.Dict:
        return Device.roles

    guid = Property(
        str,
        fget=_get_guid,
        fset=_set_guid
    )


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

    def _format_input(self) -> str:
        pass

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
            raise error.GremlinError(
                f"Could not find vJoy device with id {vjoy_id}"
            )

        # Find the index corresponding to the provided input_type and input_id
        input_label = common.input_to_ui_string(
            InputType.to_enum(input_type),
            input_id
        )
        try:
            self._set_input_index(self._input_items.index(input_label))
        except ValueError:
            raise error.GremlinError(f"No input named \"{input_label}\" present")

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

    def _get_valid_types(self) -> typing.List[str]:
        return [InputType.to_string(entry) for entry in self._valid_types]

    def _set_valid_types(self, valid_types: typing.List[str]) -> None:
        type_list = sorted([InputType.to_enum(entry) for entry in valid_types])
        if type_list != self._valid_types:
            self._valid_types = type_list

            # When changing the input type attempt to preserve the existing
            # selection if the input type is part of the new set of valid
            # types. If this is not possible set the selection to the first
            # entry of the available values.
            old_vjoy_input_id = self._get_vjoy_id()
            old_input_type = self._get_input_type()
            self.inputModel
            if self._current_input_type in self._valid_types and \
                    self._current_vjoy_index > 0:
                self.setSelection(
                    self._current_vjoy_index,
                    old_vjoy_input_id,
                    old_input_type
                )
            else:
                self._current_vjoy_index = self._devices[0].vjoy_id
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
            raise error.GremlinError(
                "Attempted to read from invalid VJoyDevices instance."
            )
        return self._devices[self._current_vjoy_index].vjoy_id

    def _get_vjoy_index(self) -> int:
        if not self._is_state_valid():
            raise error.GremlinError(
                "Attempted to read from invalid VJoyDevices instance."
            )
        return self._current_vjoy_index

    def _set_vjoy_index(self, index: int) -> None:
        if index != self._current_vjoy_index:
            if index > len(self._devices):
                raise error.GremlinError(
                    f"Invalid device index used device with index {index} "
                    f"does not exist"
                )
            self._current_vjoy_index = index
            self.vjoyIndexChanged.emit()
            self.inputModelChanged.emit()

    def _get_input_id(self) -> int:
        if not self._is_state_valid():
            raise error.GremlinError(
                "Attempted to read from invalid VJoyDevices instance."
            )
        return self._input_data[self._current_input_index][1]

    def _get_input_index(self) -> int:
        if not self._is_state_valid():
            raise error.GremlinError(
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