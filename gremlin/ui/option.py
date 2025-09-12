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

from typing import Any, Dict, Optional, TYPE_CHECKING

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal

import gremlin.config
from gremlin.types import PropertyType

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.Config"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class ConfigSectionModel(QtCore.QAbstractListModel):

    """Exposes the sections present in the configuration as a list model."""

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"name"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"groupModel"),
    }

    def __init__(self, parent: Optional[QtCore.QObject]=None) -> None:
        super().__init__(parent)

        self._config = gremlin.config.Configuration()

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._config.sections())

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role not in self.roles:
            return None

        sections = self._config.sections()
        if index.row() >= len(sections):
            return None

        match self.roles[role]:
            case "name":
                return sections[index.row()]
            case "groupModel":
                return ConfigGroupModel(sections[index.row()])

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles


@QtQml.QmlElement
class ConfigGroupModel(QtCore.QAbstractListModel):

    """Exposes the groups present in a specific configuration section as a
    list model.
    """

    changed = Signal()

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"groupName"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"entryModel"),
    }

    def __init__(self, section: str, parent: Optional[QtCore.QObject]=None) -> None:
        super().__init__(parent)

        self._config = gremlin.config.Configuration()
        self._section_name = section

    @Property(str, notify=changed) # type: ignore
    def sectionName(self) -> str:
        return self._section_name

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._config.groups(self._section_name))

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        groups = self._config.groups(self._section_name)
        if index.row() < len(groups):
            match self.roles[role]:
                case "entryModel":
                    return ConfigEntryModel(
                        self._section_name, groups[index.row()]
                    )
                case "groupName":
                    return groups[index.row()]
        else:
            return None

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles


@QtQml.QmlElement
class ConfigEntryModel(QtCore.QAbstractListModel):

    """Exposes the entries in a section's group as a list model."""

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"data_type"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"value"),
        QtCore.Qt.ItemDataRole.UserRole + 3: QtCore.QByteArray(b"description"),
        QtCore.Qt.ItemDataRole.UserRole + 4: QtCore.QByteArray(b"properties"),
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

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._config.entries(self._section_name, self._group_name))

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        entries = self._config.entries(self._section_name, self._group_name)
        if not index.isValid() or index.row() >= len(entries):
            return None

        if role in self.roles:
            role_name = bytes(self.roles[role].data()).decode()

            # Special handling
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

    def setData(
            self,
            index: ta.ModelIndex,
            value: Any,
            role: int=QtCore.Qt.ItemDataRole.EditRole
    ) -> bool:
        entries = self._config.entries(self._section_name, self._group_name)
        if not index.isValid() or index.row() >= len(entries):
            return False

        if self.roles[role] == "value":
            self._config.set(
                self._section_name,
                self._group_name,
                entries[index.row()],
                value
            )

            self.dataChanged.emit(index, index, {role})
            return True
        return False

    def flags(self, index: ta.ModelIndex) -> QtCore.Qt.ItemFlag:
        return super().flags(index) | QtCore.Qt.ItemFlag.ItemIsEditable

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles


class MetaConfigOption:

    def register_meta_option(
        self,
        section: str,
        group: str,
        name: str,
        description: str,
        qml_element: str
    ) -> None:
        """Registers an option that does not directly contain a value.

        This allows register option items of a more complex nature that have a
        dedicate QML UI element to them which handles the UI configuring the
        content and also the logic to persist the data to the Configuration
        class.

        Args:
            section: overall section this option is associated with
            group: grouping into which the option belongs
            name: name by which the new option is shown
            description: description of the parameter's purpose
            qml_element: path to the QML to load for this option
        """
        pass

