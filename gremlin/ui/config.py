# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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

from typing import Any, Dict, Optional

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

import gremlin.config
from gremlin.types import PropertyType


QML_IMPORT_NAME = "Gremlin.Config"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class ConfigSectionModel(QtCore.QAbstractListModel):

    """Exposes the sections present in the configuration as a list model."""

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("groupModel".encode()),
    }

    def __init__(self, parent: Optional[QtCore.QObject]=None) -> None:
        super().__init__(parent)

        self._config = gremlin.config.Configuration()

    def rowCount(self, parent: Optional[QtCore.QModelIndex]) -> int:
        return len(self._config.sections())

    def data(self, index: QtCore.QModelIndex, role: int) -> Any:
        if role not in ConfigSectionModel.roles:
            return None

        sections = self._config.sections()
        if index.row() >= len(sections):
            return None

        role_name = ConfigSectionModel.roles[role].data().decode()
        if role_name == "name":
            return sections[index.row()]
        elif role_name == "groupModel":
            return ConfigGroupModel(sections[index.row()])

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return ConfigSectionModel.roles


@QtQml.QmlElement
class ConfigGroupModel(QtCore.QAbstractListModel):

    """Exposes the groups present in a specific configuration section as a
    list model.
    """

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("groupName".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("entryModel".encode()),
    }

    def __init__(self, section: str, parent: Optional[QtCore.QObject]=None) -> None:
        super().__init__(parent)

        self._config = gremlin.config.Configuration()
        self._section_name = section

    def rowCount(self, parent: Optional[QtCore.QModelIndex]) -> int:
        return len(self._config.groups(self._section_name))

    def data(self, index: QtCore.QModelIndex, role: int) -> Any:
        groups = self._config.groups(self._section_name)
        if index.row() < len(groups):
            role_name = ConfigGroupModel.roles[role].data().decode()
            if role_name == "entryModel":
                return ConfigEntryModel(self._section_name, groups[index.row()])
            elif role_name == "groupName":
                return groups[index.row()]
        else:
            return None

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return ConfigGroupModel.roles


@QtQml.QmlElement
class ConfigEntryModel(QtCore.QAbstractListModel):

    """Exposes the entries in a section's group as a list model."""

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("data_type".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("value".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("description".encode()),
        QtCore.Qt.UserRole + 4: QtCore.QByteArray("properties".encode()),
    }

    def __init__(
        self,
        section: str,
        group: str,
        parent: Optional[QtCore.QObject]=None
    ) -> None:
        super().__init__(parent)

        self._config = gremlin.config.Configuration()
        self._section_name = section
        self._group_name = group

    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        return len(self._config.entries(self._section_name, self._group_name))

    def data(self, index: QtCore.QModelIndex, role: int) -> Any:
        entries = self._config.entries(self._section_name, self._group_name)
        if not index.isValid() or index.row() >= len(entries):
            return None

        if role in ConfigEntryModel.roles:
            role_name = ConfigEntryModel.roles[role].data().decode()
            value = self._config.get(
                self._section_name,
                self._group_name,
                entries[index.row()],
                role_name
            )
            if isinstance(value, PropertyType):
                value = PropertyType.to_string(value)
            return value
        return None

    def setData(self, index: QtCore.QModelIndex, value: Any, role: int) -> bool:
        entries = self._config.entries(self._section_name, self._group_name)
        if not index.isValid() or index.row() >= len(entries):
            return False

        role_name = ConfigEntryModel.roles[role].data().decode()
        if role_name == "value":
            self._config.set(
                self._section_name,
                self._group_name,
                entries[index.row()],
                value
            )

            self.dataChanged.emit(index, index, {role})
            return True
        return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return ConfigEntryModel.roles
