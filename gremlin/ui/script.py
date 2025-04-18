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

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from gremlin import user_script
from gremlin.error import GremlinError
from gremlin.profile import ScriptManager
from gremlin.types import InputType
from gremlin.ui.device import InputIdentifier


QML_IMPORT_NAME = "Gremlin.Plugin"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class AbstractVariableModel(QtCore.QObject):

    """Exposes a single variable to the QML UI."""

    # changed = Signal()

    def __init__(self, variable: user_script.AbstractVariable, parent=None):
        super().__init__(parent)

        self._variable = variable

    @Property(str, constant=True)
    def description(self) -> str:
        return self._variable.description

    @Property(str, constant=True)
    def name(self) -> str:
        return self._variable.name

    @Property(str, constant=True)
    def type(self) -> str:
        return self._variable.xml_tag


@QtQml.QmlElement
class BoolVariableModel(AbstractVariableModel):

    changed = Signal()

    def __init__(self, variable: user_script.BoolVariable, parent=None):
        super().__init__(variable, parent)

    def _get_value(self) -> bool:
        return self._variable.value

    def _set_value(self, new_value: bool) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()

    value = Property(
        bool,
        fget=_get_value,
        fset=_set_value,
        notify=changed
    )


@QtQml.QmlElement
class FloatVariableModel(AbstractVariableModel):

    changed = Signal()

    def __init__(self, variable: user_script.FloatVariable, parent=None):
        super().__init__(variable, parent)

    def _get_value(self) -> float:
        return self._variable.value

    def _set_value(self, new_value: float) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()

    @Property(float, constant=True)
    def maxValue(self) -> float:
        return self._variable.max_value

    @Property(float, constant=True)
    def minValue(self) -> float:
        return self._variable.min_value

    value = Property(
        float,
        fget=_get_value,
        fset=_set_value,
        notify=changed
    )


@QtQml.QmlElement
class IntegerVariableModel(AbstractVariableModel):

    changed = Signal()

    def __init__(self, variable: user_script.IntegerVariable, parent=None):
        super().__init__(variable, parent)

    def _get_value(self) -> int:
        return self._variable.value

    def _set_value(self, new_value: int) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()

    @Property(float, constant=True)
    def maxValue(self) -> float:
        return self._variable.max_value

    @Property(float, constant=True)
    def minValue(self) -> float:
        return self._variable.min_value

    value = Property(
        int,
        fget=_get_value,
        fset=_set_value,
        notify=changed
    )


@QtQml.QmlElement
class ModeVariableModel(AbstractVariableModel):

    changed = Signal()

    def __init__(self, variable: user_script.ModeVariable, parent=None):
        super().__init__(variable, parent)

    def _get_value(self) -> str:
        return self._variable.value

    def _set_value(self, new_value: str) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()

    value = Property(
        str,
        fget=_get_value,
        fset=_set_value,
        notify=changed
    )


@QtQml.QmlElement
class SelectionVariableModel(AbstractVariableModel):

    changed = Signal()

    def __init__(self, variable: user_script.SelectionVariable, parent=None):
        super().__init__(variable, parent)

    def _get_value(self) -> str:
        return self._variable.value

    def _set_value(self, new_value: str) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()

    @Property(list, constant=True)
    def options(self) -> list:
        return self._variable.options

    value = Property(
        str,
        fget=_get_value,
        fset=_set_value,
        notify=changed
    )


@QtQml.QmlElement
class StringVariableModel(AbstractVariableModel):

    changed = Signal()

    def __init__(self, variable: user_script.StringVariable, parent=None):
        super().__init__(variable, parent)

    def _get_value(self) -> str:
        return self._variable.value

    def _set_value(self, new_value: str) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()

    value = Property(
        str,
        fget=_get_value,
        fset=_set_value,
        notify=changed
    )


@QtQml.QmlElement
class PhysicalInputVariableModel(AbstractVariableModel):

    changed = Signal()

    def __init__(
            self,
            variable: user_script.PhysicalInputVariable,
            parent=None
    ):
        super().__init__(variable, parent)

    @Property(str, notify=changed)
    def label(self) -> str:
        return InputIdentifier(*self._variable.value).label

    @Property(list, constant=True)
    def validTypes(self) -> list[str]:
        return [InputType.to_string(v) for v in self._variable.valid_types]

    @Slot(list)
    def updateJoystick(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to joystick events.

        We only expect to receive a single input item, thus only store
        the first element of the list.

        Args:
            data: list of joystick events
        """
        self._variable.value = (
            data[0].device_guid,
            data[0].event_type,
            data[0].identifier
        )
        self.changed.emit()


@QtQml.QmlElement
class VirtualInputVariableModel(AbstractVariableModel):

    changed = Signal()

    def __init__(
            self,
            variable: user_script.PhysicalInputVariable,
            parent=None
    ):
        super().__init__(variable, parent)

    @Property(str, notify=changed)
    def label(self) -> str:
        return "Bla 123"

    @Property(list, constant=True)
    def validTypes(self) -> list[str]:
        return [InputType.to_string(v) for v in self._variable.valid_types]

    def _get_input_type(self) -> str:
        return InputType.to_string(self._variable._input_type)

    def _set_input_type(self, value: str) -> None:
        input_type = InputType.to_enum(value)
        if self._variable.input_type != input_type:
            self._variable._input_type = input_type
            self.changed.emit()

    def _get_input_id(self) -> int:
        return self._variable.input_id

    def _set_input_id(self, index: int) -> None:
        if self._variable.input_id != index:
            self._variable._input_id = index
            self.changed.emit()

    def _get_vjoy_id(self) -> int:
        return self._variable.vjoy_id

    def _set_vjoy_id(self, index: int) -> None:
        if self._variable.vjoy_id != index:
            self._variable._vjoy_id = index
            self.changed.emit()

    inputType = Property(
        str,
        fget=_get_input_type,
        fset=_set_input_type,
        notify=changed
    )

    inputId = Property(
        int,
        fget=_get_input_id,
        fset=_set_input_id,
        notify=changed
    )

    vjoyId = Property(
        int,
        fget=_get_vjoy_id,
        fset=_set_vjoy_id,
        notify=changed
    )


@QtQml.QmlElement
class ScriptListModel(QtCore.QAbstractListModel):

    """List of all loaded scripts."""

    instancesChanged = Signal()

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("path".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("variables".encode()),
    }

    data_class_lookup = {
        user_script.BoolVariable: BoolVariableModel,
        user_script.FloatVariable: FloatVariableModel,
        user_script.IntegerVariable: IntegerVariableModel,
        user_script.ModeVariable: ModeVariableModel,
        user_script.SelectionVariable: SelectionVariableModel,
        user_script.StringVariable: StringVariableModel,
        user_script.PhysicalInputVariable: PhysicalInputVariableModel,
        user_script.VirtualInputVariable: VirtualInputVariableModel,
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
            raise GremlinError(f"Invalid role {role} in ScriptListModel")

        role_name = ScriptListModel.roles[role].data().decode()
        script = self._script_manager.scripts[index.row()]
        match role_name:
            case "path":
                return str(script.path)
            case "name":
                return script.name
            case "variables":
                return  [
                    ScriptListModel.data_class_lookup[type(var)](var, self) \
                    for var in script.variables.values()
                ]
            case _:
                return None

    def roleNames(self) -> dict[int, QtCore.QByteArray]:
        return ScriptListModel.roles