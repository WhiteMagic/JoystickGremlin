# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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

import typing

from PySide2 import QtCore
from PySide2.QtCore import Property, Signal, Slot

import dill
import gremlin.types

from gremlin.util import parse_guid
import gremlin.common
import gremlin.joystick_handling
import gremlin.event_handler
import gremlin.input_devices


class DeviceListModel(QtCore.QAbstractListModel):

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("axes".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("buttons".encode()),
        QtCore.Qt.UserRole + 4: QtCore.QByteArray("hats".encode()),
        QtCore.Qt.UserRole + 5: QtCore.QByteArray("pid".encode()),
        QtCore.Qt.UserRole + 6: QtCore.QByteArray("vid".encode()),
        QtCore.Qt.UserRole + 7: QtCore.QByteArray("guid".encode())
    }

    role_query = {
        "name": lambda dev: dev.name,
        "axes": lambda dev: dev.axis_count,
        "buttons": lambda dev: dev.button_count,
        "hats": lambda dev: dev.hat_count,
        "pid": lambda dev: "{:04X}".format(dev.product_id),
        "vid": lambda dev: "{:04X}".format(dev.vendor_id),
        "guid": lambda dev: str(dev.device_guid)
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices = gremlin.joystick_handling.joystick_devices()

        gremlin.event_handler.EventListener().device_change_event.connect(
            self.update_model
        )

    def update_model(self):
        old_count = len(self._devices)
        self._devices = gremlin.joystick_handling.joystick_devices()
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


class Device(QtCore.QAbstractListModel):

    deviceChanged = Signal()

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("index".encode()),
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self._device = None

    @Property(type=str)
    def guid(self) -> str:
        if self._device is None:
            return "Unknown"
        else:
            return str(self._device.device_guid)

    @guid.setter
    def set_guid(self, guid: str) -> None:
        if self._device is not None and guid == str(self._device.device_guid):
            return

        self._device = dill.DILL.get_device_information_by_guid(
            parse_guid(guid)
        )
        self.deviceChanged.emit()

    def rowCount(self, parent:QtCore.QModelIndex=...) -> int:
        if self._device is None:
            return 0

        return self._device.axis_count + \
               self._device.button_count + \
               self._device.hat_count

    def data(self, index: QtCore.QModelIndex, role:int=...) -> typing.Any:
        if role not in DeviceListModel.roles:
            return "Unknown"

        role_name = DeviceListModel.roles[role].data().decode()
        if role_name == "name":
            return self._name(self._convert_index(index))

    def roleNames(self) -> typing.Dict:
        return DeviceListModel.roles

    def _name(self, identifier: typing.Tuple[gremlin.types.InputType, int]) -> str:
        return "{} {:d}".format(
            gremlin.types.InputType.to_string(identifier[0]).capitalize(),
            identifier[1]
        )

    def _convert_index(self, index:QtCore.QModelIndex) \
            -> typing.Tuple[gremlin.types.InputType, int]:
        axis_count = self._device.axis_count
        button_count = self._device.button_count
        hat_count = self._device.hat_count

        if index.row() < axis_count:
            return (
                gremlin.types.InputType.JoystickAxis,
                self._device.axis_map[index.row()].axis_index
            )
        elif index.row() < axis_count + button_count:
            return (
                gremlin.types.InputType.JoystickButton,
                index.row() + 1 - axis_count
            )
        else:
            return (
                gremlin.types.InputType.JoystickHat,
                index.row() + 1 - axis_count - button_count
            )
