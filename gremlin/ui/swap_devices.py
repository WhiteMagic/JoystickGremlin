# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2025 Lionel Ott
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

import logging
from typing import Any
import uuid

from PySide6 import QtCore
from PySide6 import QtQml

import dill
from gremlin import event_handler, swap_devices
from gremlin.ui import backend

QML_IMPORT_NAME = "Gremlin.Tools"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class ProfileDeviceListModel(QtCore.QAbstractListModel):
    """Model listing devices with bindings in the profile."""
    selectedIndexChanged = QtCore.Signal()

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("uuid".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("numBindings".encode())
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_index = -1
        self._devices: list[swap_devices.ProfileDeviceInfo] = []
        self.update_model()
        event_handler.EventListener().device_change_event.connect(self.update_model)

    def update_model(self) -> None:
        """Updates the model if the connected devices change."""
        self._devices = swap_devices.get_profile_devices(backend.Backend().profile)
        # Ensure the entire model is refreshed
        self.modelReset.emit()

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._devices)

    def data(
        self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole
    ) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._devices)):
            return None

        device = self._devices[index.row()]
        if role in ProfileDeviceListModel.roles:
            role_name = ProfileDeviceListModel.roles[role].data().decode()
            match role_name:
                case "name":
                    return device.name
                case "uuid":
                    return str(device.device_uuid)
                case "numBindings":
                    return device.num_bindings
        raise ValueError(f"Unknown {role=}")
        
    def roleNames(self) -> dict[int, QtCore.QByteArray]:
        return ProfileDeviceListModel.roles

    @QtCore.Slot(int, result=str)
    def uuidAtIndex(self, index: int) -> str:
        if len(self._devices) == 0:
            return str(dill.UUID_Invalid)
        if not (0 <= index < len(self._devices)):
            raise GremlinError("Provided index out of range")

        return str(self._devices[index].device_uuid)
    
    @QtCore.Property(int)
    def selectedIndex(self):
        return self._selected_index
    
    @selectedIndex.setter
    def selectedIndex(self, index):
        if 0 <= index < len(self._devices):
            self._selected_index = index
            self.selectedIndexChanged.emit()


@QtQml.QmlElement
class SwapDevices(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    @QtCore.Slot(str, str, result=str)
    def swapDevices(self, source_device_uuid: str, target_device_uuid: str) -> str:
        """
        Swaps the specified two devices in the profile.

        Args:
            source_device_uuid: The UUID of the source (from profile) device.
            target_device_uuid: The UUID of the target (connected) device.

        Returns:
            The number of action and input swaps performed.
        """
        logging.getLogger("system").info(
            f"Swapping devices {source_device_uuid} and {target_device_uuid}"
        )
        result = swap_devices.swap_devices(
            backend.Backend().profile,
            uuid.UUID(source_device_uuid),
            uuid.UUID(target_device_uuid),
        )
        return result.as_string()
