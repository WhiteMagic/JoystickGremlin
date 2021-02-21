# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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

import typing
from typing import List
import uuid

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import error, profile, profile_library, tree, util
from gremlin.base_classes import AbstractActionModel
from gremlin.types import AxisButtonDirection, HatDirection, InputType


# Hierarchy of the item related classed:
# InputItemModel -> LibraryItemListModel -> ActionTree


class InputItemModel(QtCore.QObject):

    """QML model class representing a LibraryItem instance."""

    def __init__(self, input_item: profile.InputItem, parent=None):
        super().__init__(parent)

        self._input_item = input_item

    @Property(QtCore.QObject)
    def actionConfigurations(self) -> ActionConfigurationListModel:
        return ActionConfigurationListModel(
            self._input_item.action_configurations,
            self
        )


class ActionConfigurationListModel(QtCore.QAbstractListModel):

    """List model of all ActionConfiguration instances of a single input item."""

    # This fake single role and the roleName function are needed to have the
    # modelData property available in the QML delegate
    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("fake".encode()),
    }

    def __init__(self, items: List[profile.ActionConfiguration], parent=None):
        super().__init__(parent)

        self._action_configurations = items

    def rowCount(self, parent: QtCore.QModelIndex=...) -> int:
        return len(self._action_configurations)

    def data(self, index: QtCore.QModelIndex, role: int=...) -> typing.Any:
        return ActionTreeModel(
            self._action_configurations[index.row()],
            parent=self
        )

    def roleNames(self) -> typing.Dict:
        return ActionConfigurationListModel.roles


class VirtualButtonModel(QtCore.QObject):

    """Represents both axis and hat virtual buttons."""

    lowerLimitChanged = Signal()
    upperLimitChanged = Signal()
    directionChanged = Signal()
    hatDirectionChanged = Signal()

    def __init__(self, virtual_button, parent=None):
        super().__init__(parent)

        self.virtual_button = virtual_button

    def _get_lower_limit(self) -> float:
        return self.virtual_button.lower_limit

    def _set_lower_limit(self, value: float) -> None:
        if value != self.virtual_button.lower_limit:
            self.virtual_button.lower_limit = util.clamp(value, -1.0, 1.0)
            self.lowerLimitChanged.emit()

    def _get_upper_limit(self) -> float:
        return self.virtual_button.upper_limit

    def _set_upper_limit(self, value: float) -> None:
        if value != self.virtual_button.upper_limit:
            self.virtual_button.upper_limit = util.clamp(value, -1.0, 1.0)
            self.upperLimitChanged.emit()

    def _get_direction(self) -> str:
        return AxisButtonDirection.to_string(self.virtual_button.direction)

    def _set_direction(self, value: str) -> None:
        direction = AxisButtonDirection.to_enum(value.lower())
        if direction != self.virtual_button.direction:
            self.virtual_button.direction = direction
            self.directionChanged.emit()

    def _get_hat_state(self, hat_direction):
        return hat_direction in self.virtual_button.directions

    def _set_hat_state(self, hat_direction, is_active):
        if is_active:
            if hat_direction not in self.virtual_button.directions:
                self.virtual_button.directions.append(hat_direction)
                self.hatDirectionChanged.emit()
        else:
            if hat_direction in self.virtual_button.directions:
                index = self.virtual_button.directions.index(hat_direction)
                del self.virtual_button.directions[index]
                self.hatDirectionChanged.emit()

    lowerLimit = Property(
        float,
        fget=_get_lower_limit,
        fset=_set_lower_limit,
        notify=lowerLimitChanged
    )
    upperLimit = Property(
        float,
        fget=_get_upper_limit,
        fset=_set_upper_limit,
        notify=upperLimitChanged
    )
    direction = Property(
        str,
        fget=_get_direction,
        fset=_set_direction,
        notify=directionChanged
    )

    hatNorth = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.North),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.North, x),
        notify=hatDirectionChanged
    )
    hatNorthEast = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.NorthEast),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.NorthEast, x),
        notify=hatDirectionChanged
    )
    hatEast = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.East),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.East, x),
        notify=hatDirectionChanged
    )
    hatSouthEast = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.SouthEast),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.SouthEast, x),
        notify=hatDirectionChanged
    )
    hatSouth = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.South),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.South, x),
        notify=hatDirectionChanged
    )
    hatSouthWest = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.SouthWest),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.SouthWest, x),
        notify=hatDirectionChanged
    )
    hatWest = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.West),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.West, x),
        notify=hatDirectionChanged
    )
    hatNorthWest = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.NorthWest),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.NorthWest, x),
        notify=hatDirectionChanged
    )


class ActionNodeModel(QtCore.QObject):

    actionChanged = Signal()

    def __init__(
            self,
            node: tree.TreeNode,
            action_configuration: profile.ActionConfiguration,
            parent=None
    ):
        super().__init__(parent)

        self._action_configuration = action_configuration
        self._node = node

    @property
    def action_configuration(self) -> profile.ActionConfiguration:
        return self._action_configuration

    @property
    def tree_node(self) -> tree.TreeNode:
        return self._node

    @Property(type="QVariant", notify=actionChanged)
    def actionModel(self) -> AbstractActionModel:
        return self._node.value

    @Property(type=str, notify=actionChanged)
    def name(self) -> str:
        return self._node.value.name

    @Property(type=int, notify=actionChanged)
    def depth(self) -> int:
        return self._node.depth

    @Property(type=str, notify=actionChanged)
    def qmlPath(self) -> str:
        return self._node.value.qml_path()

    @Property(type=str, notify=actionChanged)
    def id(self) -> str:
        return str(self._node.value.id)

    @Slot(str, str)
    def moveAfter(self, source: str, target: str) -> None:
        """Positions the source node after the target node.

        Args:
            source: string uuid value of the source node
            target: string uuid valiue of the target node
        """
        # Retrieve nodes
        source_node = self._find_node_with_id(uuid.UUID(source))
        target_node = self._find_node_with_id(uuid.UUID(target))

        # Reorder nodes
        if source_node != target_node:
            source_node.detach()
            target_node.insert_sibling_after(source_node)

        self.actionChanged.emit()
        self.parent().rootActionChanged.emit()

    @Slot(str, str)
    def moveBefore(self, source: str, target: str) -> None:
        """Positions the source node before the target node.

        Args:
            source: string uuid value of the source node
            target: string uuid valiue of the target node
        """
        # Retrieve nodes
        source_node = self._find_node_with_id(uuid.UUID(source))
        target_node = self._find_node_with_id(uuid.UUID(target))

        # Reorder nodes
        if source_node != target_node:
            source_node.detach()
            target_node.insert_sibling_before(source_node)

        self.actionChanged.emit()
        self.parent().rootActionChanged.emit()

    @Slot()
    def remove(self) -> None:
        self._node.detach()
        self.parent().rootActionChanged.emit()

    @Property(type=bool, notify=actionChanged)
    def isFirstSibling(self) -> bool:
        if self._node.parent is None:
            return True
        else:
            return self._node.parent.children[0] == self._node

    @Property(type=bool, notify=actionChanged)
    def isLastSibling(self) -> bool:
        if self._node.parent is None:
            return True
        else:
            return self._node.parent.children[-1] == self._node

    @Property(type=bool, notify=actionChanged)
    def isRootNode(self) -> bool:
        return isinstance(self._node.value, profile_library.RootAction)

    def _find_node_with_id(self, uuid: uuid.UUID) -> tree.TreeNode:
        """Returns the node with the desired id from the action tree.

        Args:
            uuid: uuid of the node to retrieve

        Returns:
            The TreeNode corresponding to the given uuid
        """
        predicate = lambda x: True if x.value and x.value.id == uuid else False
        nodes = self._action_tree.action_tree().root.nodes_matching(predicate)

        if len(nodes) != 1:
            raise error.GremlinError(f"Unable to retrieve node with id {uuid}")
        return nodes[0]


class ActionTreeModel(QtCore.QObject):

    """Model representing an ActionTree instance."""

    behaviorChanged = Signal()
    descriptionChanged = Signal()
    virtualButtonChanged = Signal()
    actionCountChanged = Signal()
    rootActionChanged = Signal()
    inputTypeChanged = Signal()

    def __init__(
            self,
            action_configuration: profile.ActionConfiguration,
            parent=None
    ):
        super().__init__(parent)

        self._action_configuration = action_configuration
        self._action_tree = action_configuration.library_reference.action_tree
        self._virtual_button_model = VirtualButtonModel(
            self._action_configuration.virtual_button
        )

    @Property(type=ActionNodeModel, notify=rootActionChanged)
    def rootAction(self) -> ActionNodeModel:
        return ActionNodeModel(
            self._action_tree.root,
            self._action_configuration,
            parent=self
        )

    @Property(type="QVariantList", notify=rootActionChanged)
    def rootNodes(self) -> List[ActionNodeModel]:
        return [
            ActionNodeModel(node, self._action_configuration, parent=self)
            for node in self._action_tree.root.children
        ]

    @Property(type=str, notify=inputTypeChanged)
    def inputType(self) -> str:
        return InputType.to_string(
            self._action_configuration.input_item.input_type
        )

    @Property(type=VirtualButtonModel, notify=virtualButtonChanged)
    def virtualButton(self) -> VirtualButtonModel:
        return self._virtual_button_model

    @Property(type=int, notify=actionCountChanged)
    def actionCount(self) -> int:
        return self._action_tree.root.node_count

    def _get_behavior(self) -> str:
        return InputType.to_string(self._input_item_binding.behavior)

    def _set_behavior(self, text: str) -> None:
        behavior = InputType.to_enum(text)
        if behavior != self._input_item_binding.behavior:
            self._input_item_binding.behavior = behavior

            # Ensure a virtual button instance exists of the correct type
            # if one is needed
            input_type = self._action_configuration.input_item.input_type
            if input_type == InputType.JoystickAxis and \
                    behavior == InputType.JoystickButton:
                if not isinstance(
                        self._action_configuration.virtual_button,
                        profile.VirtualAxisButton
                ):
                    self._action_configuration.virtual_button = \
                        profile.VirtualAxisButton()
                    self._virtual_button_model = VirtualButtonModel(
                        self._action_configuration.virtual_button
                    )
            elif input_type == InputType.JoystickHat and \
                    behavior == InputType.JoystickButton:
                if not isinstance(
                        self._action_configuration.virtual_button,
                        profile.VirtualHatButton
                ):
                    self._action_configuration.virtual_button = \
                        profile.VirtualHatButton()
                    self._virtual_button_model = VirtualButtonModel(
                        self._action_configuration.virtual_button
                    )

            self.behaviorChanged.emit()

    def _get_description(self) -> str:
        return self._action_configuration.description

    def _set_description(self, description: str) -> None:
        if description != self._action_configuration.description:
            self._action_configuration.description = description
            self.descriptionChanged.emit()

    @property
    def behavior_type(self):
        return self._input_item_binding.behavior

    @property
    def action_tree(self):
        return self._action_tree

    behavior = Property(
        str,
        fget=_get_behavior,
        fset=_set_behavior,
        notify=behaviorChanged
    )

    description = Property(
        str,
        fget=_get_description,
        fset=_set_description,
        notify=descriptionChanged
    )


# class ActionConfigurationModel(QtCore.QAbstractListModel):
#
#     """Model representing the ActionConfiguration structure for display via QML.
#
#     The index uses the depth first enumeration of the ActionTree instance
#     contained in this action configuration. Index 0 refers to the root node
#     which by construction contains no data.
#     """
#
#     roles = {
#         QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
#         QtCore.Qt.UserRole + 2: QtCore.QByteArray("depth".encode()),
#         QtCore.Qt.UserRole + 3: QtCore.QByteArray("profileData".encode()),
#         QtCore.Qt.UserRole + 4: QtCore.QByteArray("qmlPath".encode()),
#         QtCore.Qt.UserRole + 5: QtCore.QByteArray("id".encode()),
#         QtCore.Qt.UserRole + 6: QtCore.QByteArray("isLastSibling".encode()),
#         QtCore.Qt.UserRole + 7: QtCore.QByteArray("isFirstSibling".encode()),
#     }
#
#     behaviourChanged = Signal()
#     descriptionChanged = Signal()
#     virtualButtonChanged = Signal()
#
#     def __init__(
#             self,
#             action_configuration: profile.ActionConfiguration,
#             parent=None
#     ):
#         super().__init__(parent)
#
#         self._action_configuration = action_configuration
#         self._action_tree = action_configuration.library_reference.action_tree
#         self._virtual_button_model = VirtualButtonModel(
#             self._action_configuration.virtual_button
#         )
#
#     def rowCount(self, parent: QtCore.QModelIndex=...) -> int:
#         return self._action_tree.root.node_count - 1
#
#     def data(self, index: QtCore.QModelIndex, role: int=...) -> typing.Any:
#         if role not in ActionConfigurationModel.roles:
#             return "Unknown"
#
#         role_name = ActionConfigurationModel.roles[role].data().decode()
#         try:
#             node = self._action_tree.root.node_at_index(index.row() + 1)
#             if role_name == "depth":
#                 return node.depth
#             elif role_name == "name":
#                 return f"{node.value.name}"
#             elif role_name == "qmlPath":
#                 return node.value.qml_path()
#             elif role_name == "profileData":
#                 return node.value
#             elif role_name == "id":
#                 return str(node.value.id)
#             elif role_name == "isLastSibling":
#                 return node.parent.children[-1] == node
#             elif role_name == "isFirstSibling":
#                 return node.parent.children[0] == node
#         except error.GremlinError as e:
#             print(f"Invalid index: {e}")
#
#     def roleNames(self) -> typing.Dict:
#         return ActionConfigurationModel.roles
#
#     @Property(type=str, constant=True)
#     def inputType(self) -> str:
#         return InputType.to_string(
#             self._action_configuration.input_item.input_type
#         )
#
#     @Property(type=VirtualButtonModel, notify=virtualButtonChanged)
#     def virtualButton(self) -> VirtualButtonModel:
#         return self._virtual_button_model
#
#     @Slot(str, str)
#     def moveAfter(self, source: str, target: str) -> None:
#         """Positions the source node after the target node.
#
#         Args:
#             source: string uuid value of the source node
#             target: string uuid valiue of the target node
#         """
#         # Retrieve nodes
#         source_node = self._find_node_with_id(uuid.UUID(source))
#         target_node = self._find_node_with_id(uuid.UUID(target))
#
#         # Reorder nodes
#         if source_node != target_node:
#             source_node.detach()
#             target_node.insert_sibling_after(source_node)
#
#         self.layoutChanged.emit()
#
#     @Slot(str, str)
#     def moveBefore(self, source: str, target: str) -> None:
#         """Positions the source node before the target node.
#
#         Args:
#             source: string uuid value of the source node
#             target: string uuid valiue of the target node
#         """
#         # Retrieve nodes
#         source_node = self._find_node_with_id(uuid.UUID(source))
#         target_node = self._find_node_with_id(uuid.UUID(target))
#
#         # Reorder nodes
#         if source_node != target_node:
#             source_node.detach()
#             target_node.insert_sibling_before(source_node)
#
#         self.layoutChanged.emit()
#
#     @Slot(str)
#     def remove(self, item):
#         node = self._find_node_with_id(uuid.UUID(item))
#         node.detach()
#         self.layoutChanged.emit()
#
#     def _get_behaviour(self) -> str:
#         return InputType.to_string(self._action_configuration.behaviour)
#
#     def _set_behaviour(self, text: str) -> None:
#         behaviour = InputType.to_enum(text)
#         if behaviour != self._action_configuration.behaviour:
#             self._action_configuration.behaviour = behaviour
#
#             # Ensure a virtual button instance exists of the correct type
#             # if one is needed
#             input_type = self._action_configuration.input_item.input_type
#             if input_type == InputType.JoystickAxis and \
#                     behaviour == InputType.JoystickButton:
#                 if not isinstance(
#                         self._action_configuration.virtual_button,
#                         profile.VirtualAxisButton
#                 ):
#                     self._action_configuration.virtual_button = \
#                         profile.VirtualAxisButton()
#                     self._virtual_button_model = VirtualButtonModel(
#                         self._action_configuration.virtual_button
#                     )
#             elif input_type == InputType.JoystickHat and \
#                     behaviour == InputType.JoystickButton:
#                 if not isinstance(
#                         self._action_configuration.virtual_button,
#                         profile.VirtualHatButton
#                 ):
#                     self._action_configuration.virtual_button = \
#                         profile.VirtualHatButton()
#                     self._virtual_button_model = VirtualButtonModel(
#                         self._action_configuration.virtual_button
#                     )
#
#             self.behaviourChanged.emit()
#
#     def _get_description(self) -> str:
#         return self._action_configuration.description
#
#     def _set_description(self, description: str) -> None:
#         if description != self._action_configuration.description:
#             self._action_configuration.description = description
#             self.descriptionChanged.emit()
#
#     def _find_node_with_id(self, uuid: uuid.UUID) -> tree.TreeNode:
#         """Returns the node with the desired id from the action tree.
#
#         Args:
#             uuid: uuid of the node to retrieve
#
#         Returns:
#             The TreeNode corresponding to the given uuid
#         """
#         predicate = lambda x: True if x.value and x.value.id == uuid else False
#         nodes = self._action_tree.root.nodes_matching(predicate)
#
#         if len(nodes) != 1:
#             raise error.GremlinError(f"Unable to retrieve node with id {uuid}")
#         return nodes[0]
#
#     @property
#     def behaviour_type(self):
#         return self._action_configuration.behaviour
#
#     def action_tree(self):
#         return self._action_tree
#
#     behaviour = Property(
#         str,
#         fget=_get_behaviour,
#         fset=_set_behaviour,
#         notify=behaviourChanged
#     )
#
#     description = Property(
#         str,
#         fget=_get_description,
#         fset=_set_description,
#         notify=descriptionChanged
#     )
