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

from typing import Any, List, Optional, TYPE_CHECKING
import uuid

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from gremlin import shared_state
from gremlin.error import MissingImplementationError, GremlinError
from gremlin.plugin_manager import PluginManager
from gremlin.profile import InputItemBinding
from gremlin.signal import signal
from gremlin.types import InputType


if TYPE_CHECKING:
    from gremlin.base_classes import AbstractActionData


QML_IMPORT_NAME = "Gremlin.Profile"
QML_IMPORT_MAJOR_VERSION = 1



@QtQml.QmlElement
class ActionModel(QtCore.QObject):

    """QML model representing a single action instance."""

    actionChanged = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding: InputItemBinding,
            parent: QtCore.QObject
    ):
        super().__init__(parent)

        self._data = data
        self._binding = binding

    def _add_action_impl(self, action: AbstractActionData, options: Any) -> None:
        raise MissingImplementationError(
            "ActionModel._add_action_impl not implemented in subclass"
        )

    def _qml_path_impl(self) -> str:
        raise MissingImplementationError(
            "ActionModel._qml_path_impl not implemented in subclass"
        )

    @property
    def input_type(self) -> InputType:
        return self._binding.behavior

    @Property(type=InputType, notify=actionChanged)
    def inputType(self) -> InputType:
        return self._binding.behavior

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

    @Slot(str, result=list)
    def getActions(self, selector: Optional[Any]=None) -> List[ActionModel]:
        action_list = self._data.get_actions(None if selector == "" else selector)
        action_models = [a.model(a, self._binding, self) for a in action_list]
        return action_models

    @Slot(str, str)
    def addAction(self, action_name: str, options: Optional[Any]=None):
        """Adds a new action to the action of this model.

        Args:
            action_name: name of the action to add
            options: optional information used to manage action addition
        """
        action = PluginManager().create_instance(
            action_name,
            self._binding.behavior
        )

        self._add_action_impl(action, options)
        self._signal_change()

    @Slot(str, str, str)
    def dropAction(self, source: str, target: str, method: str) -> None:
        """Handles dropping an action on an UI item.

        Args:
            source: identifier of the acion being dropped
            target: identifier of the location on which the source is dropped
            method: type of drop action to perform
        """
        # Force a UI refresh without performing any model changes if both
        # source and target item are identical, i.e. an invalid drag&drop
        if source == target:
            self.actionChanged.emit()
            self._signal_change()
            return

        if method == "append":
            self._append_drop_action(source, target)
        else:
            try:
                # Retrieve tree nodes corresponding to the actions
                source_node = self._find_node_with_id(uuid.UUID(source))
                target_node = self._find_node_with_id(uuid.UUID(target))

                # Handle action level reordering
                source_node.parent.value.remove_action(source_node.value)
                target_node.value.insert_action(method, source_node.value)

                # Handle tree level reodering
                source_node.detach()
                target_node.insert_child(source_node, 0)

                # Redraw UI
                self.actionChanged.emit()
                self._signal_change()
            except GremlinError:
                signal.reloadUi.emit()

    def _append_drop_action(self, source: str, target: str) -> None:
        """Positions the source node after the target node.

        Args:
            source: string uuid value of the source node
            target: string uuid valiue of the target node
        """
        try:
            # Retrieve nodes
            source_node = self._find_node_with_id(uuid.UUID(source))
            target_node = self._find_node_with_id(uuid.UUID(target))

            # Reorder nodes, first action level then profile level
            if source_node != target_node:
                # Perform reordering on the parent node level if needed
                source_node.parent.value.remove_action(source_node.value)
                target_node.parent.value.add_action_after(
                    target_node.value,
                    source_node.value
                )

                # Perform reordering on the logical tree level
                source_node.detach()
                target_node.insert_sibling_after(source_node)

            self.actionChanged.emit()
            self._signal_change()
        except GremlinError:
            signal.reloadUi.emit()

    # @Slot(str)
    # def createChildAction(self, action_name: str) -> None:
    #     """Creates a new action as a child of the current action.

    #     Args:
    #         action_name: name of the action to add
    #     """
    #     action = plugin_manager.ActionPlugins().get_class(action_name)(
    #         self._binding.behavior
    #     )
    #     if self._action.parent is None:
    #         TreeNode(action, self._action)
    #     else:
    #         TreeNode(action, self._action.parent)

    #     self._signal_change()

    @Slot()
    def remove(self) -> None:
        shared_state.current_profile.remove_action(self._data, self._binding)
        self._signal_change()

    # @Property(type=bool, notify=actionChanged)
    # def isFirstSibling(self) -> bool:
    #     if self._action.parent is None:
    #         return True
    #     else:
    #         return self._action.parent.children[0] == self._action

    # @Property(type=bool, notify=actionChanged)
    # def isLastSibling(self) -> bool:
    #     if self._action.parent is None:
    #         return True
    #     else:
    #         return self._action.parent.children[-1] == self._action

    @Property(type=bool, notify=actionChanged)
    def hasChildren(self) -> bool:
        return len(self._data.children) > 0

    @Property(type=list, notify=actionChanged)
    def compatibleActions(self) -> List[str]:
        action_list = PluginManager().type_action_map[self._binding.behavior]
        return [a.name for a in sorted(action_list, key=lambda x: x.name)]

    # @Property(type=bool, notify=actionChanged)
    # def isRootNode(self) -> bool:
    #     return isinstance(self._action, RootAction)

    def _signal_change(self) -> None:
        """Emits signals causing a refresh of the actin's input binding."""
        self.actionChanged.emit()
        signal.reloadCurrentInputItem.emit()

    # def _find_node_with_id(self, uuid: uuid.UUID) -> tree.TreeNode:
    #     """Returns the node with the desired id from the action tree.

    #     Args:
    #         uuid: uuid of the node to retrieve

    #     Returns:
    #         The TreeNode corresponding to the given uuid
    #     """
    #     predicate = lambda x: True if x.value and x.value.id == uuid else False
    #     nodes = self._action_tree.root.nodes_matching(predicate)

    #     if len(nodes) != 1:
    #         raise error.GremlinError(f"Unable to retrieve node with id {uuid}")
    #     return nodes[0]
