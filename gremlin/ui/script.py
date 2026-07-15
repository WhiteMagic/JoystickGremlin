# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path
from typing import cast

from PySide6 import QtCore

import gremlin.ui.type_aliases as ta
from gremlin import (
    event_handler,
    keyboard,
    user_script,
)
from gremlin.error import GremlinError
from gremlin.logical_device import LogicalDevice
from gremlin.profile import ScriptManager
from gremlin.types import InputType
from gremlin.ui.device import InputIdentifier
from gremlin.ui.util import to_local_path

QML_IMPORT_NAME = "Gremlin.Script"
QML_IMPORT_MAJOR_VERSION = 1


@ta.QmlElement
class AbstractVariableModel(QtCore.QObject):
    """Exposes a single variable to the QML UI."""

    validityChanged = QtCore.Signal()

    def __init__(
        self, variable: user_script.AbstractVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(parent)

        self._variable = variable

    @QtCore.Property(str, constant=True)
    def description(self) -> str:
        return self._variable.description

    @QtCore.Property(str, constant=True)
    def name(self) -> str:
        return self._variable.name

    @QtCore.Property(str, constant=True)
    def type(self) -> str:
        return self._variable.xml_tag

    @QtCore.Property(bool, constant=True)
    def isOptional(self) -> bool:
        return self._variable.is_optional

    @QtCore.Property(bool, notify=validityChanged)
    def isValid(self) -> bool:
        return self._variable.is_valid()

    def evaluate_validity(self) -> None:
        self.validityChanged.emit()


@ta.QmlElement
class BoolVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.BoolVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    def _get_value(self) -> bool:
        return self._variable.value

    def _set_value(self, new_value: bool) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()
            self.evaluate_validity()

    value = QtCore.Property(bool, fget=_get_value, fset=_set_value, notify=changed)


@ta.QmlElement
class FloatVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.FloatVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    def _get_value(self) -> float:
        return self._variable.value

    def _set_value(self, new_value: float) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()
            self.evaluate_validity()

    @QtCore.Property(float, constant=True)
    def maxValue(self) -> float:
        return self._variable.max_value

    @QtCore.Property(float, constant=True)
    def minValue(self) -> float:
        return self._variable.min_value

    value = QtCore.Property(float, fget=_get_value, fset=_set_value, notify=changed)


@ta.QmlElement
class IntegerVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.IntegerVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    def _get_value(self) -> int:
        return self._variable.value

    def _set_value(self, new_value: int) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()
            self.evaluate_validity()

    @QtCore.Property(float, constant=True)
    def maxValue(self) -> float:
        return self._variable.max_value

    @QtCore.Property(float, constant=True)
    def minValue(self) -> float:
        return self._variable.min_value

    value = QtCore.Property(int, fget=_get_value, fset=_set_value, notify=changed)


@ta.QmlElement
class KeyboardVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.KeyboardVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    @QtCore.Property(str, notify=changed)
    def label(self) -> str:
        return "Record" if self._variable.value is None else self._variable.value.name

    @QtCore.Slot(list)
    def updateKeyboard(self, data: list[event_handler.Event]) -> None:
        """Receives the events corresponding to joystick events.

        We only expect to receive a single input item, thus only store
        the first element of the list.

        Args:
            data: list of joystick events
        """
        self._variable.value = keyboard.key_from_code(*data[0].identifier)
        self.changed.emit()
        self.evaluate_validity()


@ta.QmlElement
class LogicalDeviceModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.LogicalDeviceVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    @QtCore.Property(str, notify=changed)
    def label(self) -> str:
        return self._variable.value.label

    @QtCore.Property(list, constant=True)
    def validTypes(self) -> list[str]:
        return [InputType.to_string(v) for v in self._variable.valid_types]

    def _get_logical_input_identifier(self) -> InputIdentifier:
        return InputIdentifier(
            LogicalDevice.device_guid,
            self._variable.value.type,
            self._variable.value.id,
            parent=self,
        )

    def _set_logical_input_identifier(self, identifier: InputIdentifier) -> None:
        if identifier.input_type not in self._variable.valid_types:
            return

        self._variable.value = LogicalDevice.Input.Identifier(
            identifier.input_type, identifier.input_id
        )
        self.changed.emit()

    logicalInputIdentifier = QtCore.Property(
        type=InputIdentifier,
        fget=_get_logical_input_identifier,
        fset=_set_logical_input_identifier,
        notify=changed,
    )


@ta.QmlElement
class ModeVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.ModeVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    def _get_value(self) -> str:
        return self._variable.value

    def _set_value(self, new_value: str) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()
            self.evaluate_validity()

    value = QtCore.Property(str, fget=_get_value, fset=_set_value, notify=changed)


@ta.QmlElement
class SelectionVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.SelectionVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    def _get_value(self) -> str:
        return self._variable.value

    def _set_value(self, new_value: str) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()
            self.evaluate_validity()

    @QtCore.Property(list, constant=True)
    def options(self) -> list:
        return self._variable.options

    value = QtCore.Property(str, fget=_get_value, fset=_set_value, notify=changed)


@ta.QmlElement
class StringVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.StringVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    def _get_value(self) -> str:
        return self._variable.value

    def _set_value(self, new_value: str) -> None:
        if new_value != self._variable.value:
            self._variable.value = new_value
            self.changed.emit()
            self.evaluate_validity()

    value = QtCore.Property(str, fget=_get_value, fset=_set_value, notify=changed)


@ta.QmlElement
class PhysicalInputVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.PhysicalInputVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    @QtCore.Property(str, notify=changed)
    def label(self) -> str:
        return InputIdentifier(*self._variable.value).label

    @QtCore.Property(list, constant=True)
    def validTypes(self) -> list[str]:
        return [InputType.to_string(v) for v in self._variable.valid_types]

    @QtCore.Slot(list)
    def updateJoystick(self, data: list[event_handler.Event]) -> None:
        """Receives the events corresponding to joystick events.

        We only expect to receive a single input item, thus only store
        the first element of the list.

        Args:
            data: list of joystick events
        """
        self._variable.value = (
            data[0].device_guid,
            data[0].event_type,
            data[0].identifier,
        )
        self.changed.emit()
        self.evaluate_validity()


@ta.QmlElement
class VirtualInputVariableModel(AbstractVariableModel):
    changed = QtCore.Signal()

    def __init__(
        self, variable: user_script.PhysicalInputVariable, parent: ta.OQO = None
    ) -> None:
        super().__init__(variable, parent)

    @QtCore.Property(str, notify=changed)
    def label(self) -> str:
        return "Bla 123"

    @QtCore.Property(list, constant=True)
    def validTypes(self) -> list[str]:
        return [InputType.to_string(v) for v in self._variable.valid_types]

    def _get_input_type(self) -> str:
        return InputType.to_string(self._variable._input_type)

    def _set_input_type(self, value: str) -> None:
        input_type = InputType.to_enum(value)
        if self._variable.input_type != input_type:
            self._variable._input_type = input_type
            self.changed.emit()
            self.evaluate_validity()

    def _get_input_id(self) -> int:
        return self._variable.input_id

    def _set_input_id(self, index: int) -> None:
        if self._variable.input_id != index:
            self._variable._input_id = index
            self.changed.emit()
            self.evaluate_validity()

    def _get_vjoy_id(self) -> int:
        return self._variable.vjoy_id

    def _set_vjoy_id(self, index: int) -> None:
        if self._variable.vjoy_id != index:
            self._variable._vjoy_id = index
            self.changed.emit()
            self.evaluate_validity()

    inputType = QtCore.Property(
        str, fget=_get_input_type, fset=_set_input_type, notify=changed
    )

    inputId = QtCore.Property(
        int, fget=_get_input_id, fset=_set_input_id, notify=changed
    )

    vjoyId = QtCore.Property(int, fget=_get_vjoy_id, fset=_set_vjoy_id, notify=changed)


@ta.QmlElement
class ScriptListModel(QtCore.QAbstractListModel):
    """List of all loaded scripts."""

    instancesChanged = QtCore.Signal()

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray("path".encode()),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray("name".encode()),
        QtCore.Qt.ItemDataRole.UserRole + 3: QtCore.QByteArray("variables".encode()),
    }

    data_class_lookup = {
        user_script.BoolVariable: BoolVariableModel,
        user_script.FloatVariable: FloatVariableModel,
        user_script.IntegerVariable: IntegerVariableModel,
        user_script.KeyboardVariable: KeyboardVariableModel,
        user_script.LogicalDeviceVariable: LogicalDeviceModel,
        user_script.ModeVariable: ModeVariableModel,
        user_script.SelectionVariable: SelectionVariableModel,
        user_script.StringVariable: StringVariableModel,
        user_script.PhysicalInputVariable: PhysicalInputVariableModel,
        user_script.VirtualInputVariable: VirtualInputVariableModel,
    }

    def __init__(self, script_manager: ScriptManager, parent: ta.OQO = None) -> None:
        super().__init__(parent)

        self._script_manager = script_manager

    @QtCore.Slot(str)
    def addScript(self, qml_url: str) -> None:
        self.layoutAboutToBeChanged.emit()
        self._script_manager.add_script(to_local_path(qml_url))
        self.layoutChanged.emit()

    @QtCore.Slot(str, str)
    def removeScript(self, path: str, name: str) -> None:
        index = self._script_manager.index_of(Path(path), name)
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self._script_manager.remove_script(Path(path), name)
        self.endRemoveRows()

    @QtCore.Slot(str, str, str)
    def renameScript(self, path: str, old_name: str, new_name: str) -> None:
        self._script_manager.rename_script(Path(path), old_name, new_name)
        self.dataChanged.emit(
            self.createIndex(0, 0), self.createIndex(self.rowCount(), 0)
        )

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._script_manager.scripts)

    def data(
        self, index: ta.ModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole
    ) -> str | list[AbstractVariableModel] | None:
        if role not in self.roles:
            raise GremlinError(f"Invalid role {role} in ScriptListModel")

        script = self._script_manager.scripts[index.row()]
        match cast(str, self.roles[role]):
            case "path":
                return str(script.path)
            case "name":
                return script.name
            case "variables":
                return [
                    ScriptListModel.data_class_lookup[type(var)](var, self)
                    for var in script.variables.values()
                ]
            case _:
                return None

    def roleNames(self) -> dict[int, QtCore.QByteArray]:
        return ScriptListModel.roles
