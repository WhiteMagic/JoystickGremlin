# -*- coding: utf-8; -*-

# Copyright (C) 2025 Lionel Ott
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


from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from gremlin.error import GremlinError
from gremlin.profile import Script, ScriptManager, ScriptVariable

QML_IMPORT_NAME = "Gremlin.Plugin"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class ScriptModel(QtCore.QAbstractListModel):

    """List of all loaded scripts."""

    instancesChanged = Signal()

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("path".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("variables".encode()),
    }

    def __init__(self, script_manager: ScriptManager, parent=None):
        super().__init__(parent)

        self._script_manager = script_manager

    @Slot(str)
    def addScript(self, path: str) -> None:
        self.beginInsertRows(
            QtCore.QModelIndex(),
            self.rowCount(),
            self.rowCount()
        )
        self._script_manager.add_script(Path(path))
        self.endInsertRows()

    @Slot(str, str)
    def removeScript(self, path: str, name: str) -> None:
        index = self._script_manager.index_of(Path(path), name)
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self._script_manager.remove_script(Path(path), name)
        self.endRemoveRows()

    @Slot(str, str, str)
    def renameScript(
            self,
            path: str,
            old_name: str,
            new_name: str
    ) -> None:
        self._script_manager.rename_script(Path(path), old_name, new_name)
        self.modelReset.emit()

    def rowCount(self, parent=QtCore.QModelIndex) -> int:
        return len(self._script_manager.scripts)

    def data(self, index: QtCore.QModelIndex, role: int=...) -> Any:
        if role not in self.roleNames():
            raise GremlinError(f"Invalid role {role} in ScriptModel")

        role_name = ScriptModel.roles[role].data().decode()
        script = self._script_manager.scripts[index.row()]
        match role_name:
            case "path":
                return str(script.path)
            case "name":
                return script.name
            case "variables":
                return  [ScriptVariableModel(var) for var in script.variables]

    def roleNames(self) -> dict[int, QtCore.QByteArray]:
        return ScriptModel.roles


@QtQml.QmlElement
class ScriptVariableModel(QtCore.QObject):

    """Exposes a single variable to the QML UI."""

    changed = Signal()

    def __init__(self, variable: ScriptVariable, parent=None):
        super().__init__(parent)

        self._variable = variable


    def _get_name(self) -> str:
        return self._variable.name

    def _set_name(self, new_name: str) -> None:
        if new_name != self._variable.name:
            self._variable.name = new_name
            self.changed.emit()

    name = Property(
        str,
        fget=_get_name,
        fset=_set_name,
        notify=changed
    )