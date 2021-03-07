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

from gremlin import error, plugin_manager, profile, tree, util
from gremlin.profile_library import ActionTree, RootAction
from gremlin.tree import TreeNode
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

    def __init__(self, items: List[profile.InputItemBinding], parent=None):
        super().__init__(parent)

        self._action_configurations = items

    def rowCount(self, parent: QtCore.QModelIndex=...) -> int:
        return len(self._action_configurations)

    def data(self, index: QtCore.QModelIndex, role: int=...) -> typing.Any:
        return InputItemBindingModel(
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

    """QML model representing a single action instance."""

    actionChanged = Signal()

    def __init__(
            self,
            node: tree.TreeNode,
            input_type: InputType,
            action_tree: ActionTree,
            parent=None
    ):
        super().__init__(parent)

        self._node = node
        self._input_type = input_type
        self._action_tree = action_tree

    @property
    def node(self) -> tree.TreeNode:
        return self._node

    @property
    def input_type(self) -> InputType:
        return self._input_type

    @property
    def action_tree(self) -> ActionTree:
        return self._action_tree

    Property(type=InputType, notify=actionChanged)
    def inputType(self) -> InputType:
        return self._input_type

    @Property(type="QVariant", notify=actionChanged)
    def actionModel(self) -> "AbstractActionModel":
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
        self._signal_change()

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
        self._signal_change()

    @Slot(str)
    def appendNewAction(self, action_name: str) -> None:
        """Creates a new action and appends it in the action tree after this node.

        Args:
            action_name: name of the action to add
        """
        action = plugin_manager.ActionPlugins().get_class(action_name)(
            self._action_tree,
            self._input_type
        )
        if self._node.parent is None:
            TreeNode(action, self._node)
        else:
            TreeNode(action, self._node.parent)

        self._signal_change()

    @Slot()
    def remove(self) -> None:
        self._node.detach()
        self._signal_change()

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
    def hasChildren(self) -> bool:
        return len(self._node.children) > 0

    @Property(type=bool, notify=actionChanged)
    def isRootNode(self) -> bool:
        return isinstance(self._node.value, RootAction)

    def _signal_change(self) -> None:
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, InputItemBindingModel):
                break
            else:
                parent = parent.parent()

        if isinstance(parent, InputItemBindingModel):
            parent.rootActionChanged.emit()
        else:
            raise error.GremlinError(
                "Unable to signal action node change due to corrupted "
                "action tree structure"
            )

    def _find_node_with_id(self, uuid: uuid.UUID) -> tree.TreeNode:
        """Returns the node with the desired id from the action tree.

        Args:
            uuid: uuid of the node to retrieve

        Returns:
            The TreeNode corresponding to the given uuid
        """
        predicate = lambda x: True if x.value and x.value.id == uuid else False
        nodes = self._action_tree.root.nodes_matching(predicate)

        if len(nodes) != 1:
            raise error.GremlinError(f"Unable to retrieve node with id {uuid}")
        return nodes[0]


class InputItemBindingModel(QtCore.QObject):

    """Model representing an ActionTree instance."""

    behaviorChanged = Signal()
    descriptionChanged = Signal()
    virtualButtonChanged = Signal()
    actionCountChanged = Signal()
    rootActionChanged = Signal()
    inputTypeChanged = Signal()

    def __init__(
            self,
            input_item_binding: profile.InputItemBinding,
            parent=None
    ):
        super().__init__(parent)

        self._input_item_binding = input_item_binding
        self._action_tree = input_item_binding.library_reference.action_tree
        self._virtual_button_model = VirtualButtonModel(
            self._input_item_binding.virtual_button
        )

    @Property(type=ActionNodeModel, notify=rootActionChanged)
    def rootNode(self) -> ActionNodeModel:
        return ActionNodeModel(
            self._action_tree.root,
            self._input_item_binding.behavior,
            self._action_tree,
            parent=self
        )

    @Property(type=list, notify=rootActionChanged)
    def topLevelNodes(self) -> List[ActionNodeModel]:
        nodes = []
        for node in self._action_tree.root.children:
            node.value.setParent(self)
            nodes.append(ActionNodeModel(
                node,
                self._input_item_binding.behavior,
                self._action_tree,
                parent=self
            ))
        return nodes

    @Property(type=str, notify=inputTypeChanged)
    def inputType(self) -> str:
        return InputType.to_string(
            self._input_item_binding.input_item.input_type
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
            input_type = self._input_item_binding.input_item.input_type
            if input_type == InputType.JoystickAxis and \
                    behavior == InputType.JoystickButton:
                if not isinstance(
                        self._input_item_binding.virtual_button,
                        profile.VirtualAxisButton
                ):
                    self._input_item_binding.virtual_button = \
                        profile.VirtualAxisButton()
                    self._virtual_button_model = VirtualButtonModel(
                        self._input_item_binding.virtual_button
                    )
            elif input_type == InputType.JoystickHat and \
                    behavior == InputType.JoystickButton:
                if not isinstance(
                        self._input_item_binding.virtual_button,
                        profile.VirtualHatButton
                ):
                    self._input_item_binding.virtual_button = \
                        profile.VirtualHatButton()
                    self._virtual_button_model = VirtualButtonModel(
                        self._input_item_binding.virtual_button
                    )

            self.behaviorChanged.emit()

    def _get_description(self) -> str:
        return self._input_item_binding.description

    def _set_description(self, description: str) -> None:
        if description != self._input_item_binding.description:
            self._input_item_binding.description = description
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
