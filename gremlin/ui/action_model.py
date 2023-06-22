# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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

from typing import List, Optional, TYPE_CHECKING

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from gremlin.base_classes import DataInsertionMode
from gremlin.error import MissingImplementationError, GremlinError
from gremlin.plugin_manager import PluginManager
from gremlin.signal import signal
from gremlin.types import InputType

if TYPE_CHECKING:
    from gremlin.base_classes import AbstractActionData
    from gremlin.ui.profile import InputItemBindingModel


QML_IMPORT_NAME = "Gremlin.Profile"
QML_IMPORT_MAJOR_VERSION = 1


class SequenceIndex:

    def __init__(
            self,
            parent_index: int | None,
            container_name: str | None,
            index: int,
    ):
        """Creates a new action index instance.
        This models the QModelIndex class.
        Args:
            parent_index: index assigned to the parent action
            container_name: name of the parent's container
            index: index assigned to this action
        """
        self._parent_index = parent_index
        self._container_name = container_name
        self._index = index

    @property
    def index(self) -> int:
        return self._index

    @property
    def parent_index(self) -> int:
        return self._parent_index

    @property
    def container_name(self) -> str:
        return self._container_name


@QtQml.QmlElement
class ActionModel(QtCore.QObject):

    """QML model representing a single action instance."""

    actionChanged = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ):
        super().__init__(parent)

        self._data = data
        self._binding_model = binding_model
        self._sequence_index = action_index
        self._parent_sequence_index = parent_index

    def _qml_path_impl(self) -> str:
        raise MissingImplementationError(
            "ActionModel._qml_path_impl not implemented in subclass"
        )

    @property
    def input_type(self) -> InputType:
        return self._binding_model.behavior_type

    @Property(type=InputType, notify=actionChanged)
    def inputType(self) -> InputType:
        return self._binding_model.behavior_type

    @Property(type="QVariant", notify=actionChanged)
    def actionData(self) -> AbstractActionData:
        return self._data

    @Property(type=str, notify=actionChanged)
    def name(self) -> str:
        return self._data.name

    @Property(type=str, notify=actionChanged)
    def qmlPath(self) -> str:
        return self._qml_path_impl()

    @Property(type=str, notify=actionChanged)
    def id(self) -> str:
        return str(self._data.id)

    @Property(type=int, notify=actionChanged)
    def sequenceIndex(self) -> int:
        return self._sequence_index.index

    @Property(type=str, notify=actionChanged)
    def rootActionId(self) -> str:
        return str(self._binding_model.root_action.id)

    @Slot(str, result=list)
    def getActions(self, selector: str) -> List[ActionModel]:
        """Returns the collection of actions corresponding to the selector.

        Args:
            selector: name of the container to return

        Returns:
            List of actions corresponding to the given container
        """
        return self._binding_model.get_action_models(
            self._sequence_index,
            selector
        )

    @Slot(str, str)
    def appendAction(self, action_name: str, selector: Optional[str]=None):
        """Adds a new action to the end of the specified container.

        Args:
            action_name: name of the action to add
            selector: name of the container into which to add the action
        """
        action = PluginManager().create_instance(
            action_name,
            self._binding.behavior
        )
        self._data.insert_action(action, selector)
        self._signal_change()

    @Slot(int, int, str)
    def dropAction(self, source: int, target: int, method: str) -> None:
        """Handles dropping an action on an UI item.

        Args:
            source: sequence id of the acion being dropped
            target: sequence id of the action on which the source is dropped
            method: type of drop action to perform
        """
        print(source, target, method)

        # Force a UI refresh without performing any model changes if both
        # source and target item are identical, i.e. an invalid drag&drop
        if source == target:
            self.actionChanged.emit()
            self._signal_change()
            return

        if method == "append":
            self._append_drop_action(source, target)
        else:
            self._append_drop_action(source, target, method)

    def _append_drop_action(
            self,
            source: int,
            target: int,
            container: Optional[str]=None
        ) -> None:
        """Positions the source node after the target node.

        Args:
            source: sequence id of the source action
            target: sequence id of the target action
            container: name of the container to insert the action into
        """
        try:
            # Find parent actions of the source and target actions
            s_container, s_action, s_parent = self._binding.find_action(source)
            t_container, t_action, t_parent = self._binding.find_action(target)

            print(s_container, s_parent, s_action)
            print(t_container, t_parent, t_action)

            # Remove source from it's current parent
            s_parent.remove_action(s_action, s_container)

            # Insert source in the target's parent after the target action
            if container is None:
                t_parent.insert_action(
                    s_action,
                    t_container,
                    DataInsertionMode.Append,
                    t_action
                )
            else:
                t_parent.insert_action(
                    s_action,
                    container,
                    DataInsertionMode.Prepend,
                    t_action
                )

            self.actionChanged.emit()
            self._signal_change()
        except GremlinError:
            signal.reloadUi.emit()

    @Slot("QVariant", str)
    def removeAction(self, action: AbstractActionData, selector: str) -> None:
        """Removes the given action from the specified container.

        Args:
            action: the action to remove
            selector: specifies the container from which to remove the action
        """
        self._data.remove_action(action, selector)
        self._signal_change()

    @Property(type=list, notify=actionChanged)
    def compatibleActions(self) -> List[str]:
        action_list = PluginManager().type_action_map[
            self._binding_model.behavior_type
        ]
        action_list = [entry for entry in action_list if entry.tag != "root"]
        return [a.name for a in sorted(action_list, key=lambda x: x.name)]

    def _signal_change(self) -> None:
        """Emits signals causing a refresh of the actin's input binding."""
        self.actionChanged.emit()
        signal.reloadCurrentInputItem.emit()
