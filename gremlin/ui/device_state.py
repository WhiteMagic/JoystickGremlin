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

"""Device state tracking for real-time input monitoring."""

from __future__ import annotations

import uuid
from typing import Any, Dict

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal

import dill

from gremlin import event_handler
from gremlin.error import GremlinError
from gremlin.types import InputType


QML_IMPORT_NAME = "Gremlin.DeviceState"
QML_IMPORT_MAJOR_VERSION = 1


class AbstractDeviceState(QtCore.QAbstractListModel):
    """Abstract base class for device state tracking."""

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

    def _initialize_state(self) -> None:
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
    """Tracks axis state for a device."""

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
    """Tracks button state for a device."""

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
    """Tracks hat state for a device."""

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
