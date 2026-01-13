# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from PySide6 import (
    QtCore,
    QtQml,
)

import dill
from gremlin import (
    event_handler,
    swap_devices,
)
from gremlin.error import GremlinError
from gremlin.ui import backend

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.Tools"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class ProfileDeviceListModel222(QtCore.QAbstractListModel):

    # TODO: Make this obsolete by augmenting the existing DeviceListModel.

    """Model listing devices with bindings in the profile."""

    selectedIndexChanged = QtCore.Signal()

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("uuid".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("numBindings".encode())
    }

    def __init__(self, parent: ta.OQO = None) -> None:
        super().__init__(parent)
        self._selected_index = -1
        self._devices: list[swap_devices.ProfileDeviceInfo] = []
        self.update_model()
        event_handler.EventListener().device_change_event.connect(self.update_model)

    def update_model(self) -> None:
        """Updates the model if the connected devices change."""
        self._devices = \
            swap_devices.get_profile_devices(backend.Backend().profile)
        # Ensure the entire model is refreshed
        self.modelReset.emit()

    def rowCount(self, parent: ta.MI = QtCore.QModelIndex()) -> int:
        return len(self._devices)

    def data(
        self, index: ta.MI, role: int = QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._devices)):
            return None

        device = self._devices[index.row()]
        if role in self.roles:
            match self.roles[role]:
                case "name":
                    return device.name
                case "uuid":
                    return str(device.device_uuid)
                case "numBindings":
                    return device.num_bindings
        raise ValueError(f"Unknown {role=}")

    def roleNames(self) -> dict[int, QtCore.QByteArray]:
        return self.roles

    @QtCore.Slot(int, result=str)
    def uuidAtIndex(self, index: int) -> str:
        if len(self._devices) == 0:
            return str(dill.UUID_Invalid)
        if not (0 <= index < len(self._devices)):
            raise GremlinError(f"Provided {index=} out of range")

        return str(self._devices[index].device_uuid)

    @QtCore.Property(int, notify=selectedIndexChanged)
    def selectedIndex(self) -> int:
        return self._selected_index

    @selectedIndex.setter
    def selectedIndex(self, index: int) -> None:
        if 0 <= index < len(self._devices) and index != self._selected_index:
            self._selected_index = index
            self.selectedIndexChanged.emit()
