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
import uuid

from PySide2 import QtCore
from PySide2.QtCore import Property, Signal, Slot

from gremlin import error, tree


# Hierarchy of the item related classed:
# InputItemModel -> LibraryItemListModel -> ActionTree


class InputItemModel(QtCore.QObject):

    """QML model class representing a LibraryItem instance."""

    def __init__(self, input_item: profile.InputItem, parent=None):
        super().__init__(parent)

        self._input_item = input_item

    @Property(QtCore.QObject, constant=True)
    def libraryItems(self) -> LibraryItemListModel:
        return LibraryItemListModel(self._input_item.actions, self)


class LibraryItemListModel(QtCore.QAbstractListModel):

    """List model of all LibraryItem instances of a single input item."""

    # This fake single role and the roleName function are needed to have the
    # modelData property available in the QML delegate
    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("fake".encode()),
    }

    def __init__(self, items, parent=None):
        super().__init__(parent)

        self._items = items

    def rowCount(self, parent:QtCore.QModelIndex=...) -> int:
        return len(self._items)

    def data(self, index: QtCore.QModelIndex, role:int=...) -> typing.Any:
        return ActionTree(self._items[index.row()].action_tree)

    def roleNames(self) -> typing.Dict:
        return LibraryItemListModel.roles


class ActionTree(QtCore.QAbstractListModel):

    """Model representing the ActionTree structure for display via QML.

    The index uses the depth first enumeration of the tree structure. Index
    0 refers to the root node which by construction contains no data.
    """

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("name".encode()),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray("depth".encode()),
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("profileData".encode()),
        QtCore.Qt.UserRole + 4: QtCore.QByteArray("qmlPath".encode()),
        QtCore.Qt.UserRole + 5: QtCore.QByteArray("id".encode()),
        QtCore.Qt.UserRole + 6: QtCore.QByteArray("isExpanded".encode())
    }

    def __init__(self, action_tree, parent=None):
        super().__init__(parent)

        self._action_tree = action_tree
        self._is_expanded = {}

    def rowCount(self, parent: QtCore.QModelIndex=...) -> int:
        return self._action_tree.root.node_count - 1

    def data(self, index: QtCore.QModelIndex, role: int=...) -> typing.Any:
        if role not in ActionTree.roles:
            return "Unknown"

        role_name = ActionTree.roles[role].data().decode()
        try:
            node = self._action_tree.root.node_at_index(index.row() + 1)
            if role_name == "depth":
                return node.depth
            elif role_name == "name":
                return f"{node.value.name}"
            elif role_name == "qmlPath":
                return node.value.qml_path()
            elif role_name == "profileData":
                return node.value
            elif role_name == "id":
                return str(node.value.id)
            elif role_name == "isExpanded":
                return self._is_expanded.get(node.value.id, False)
        except error.GremlinError as e:
            print(f"Invalid index: {e}")

    def setData(
            self,
            index: QtCore.QModelIndex,
            value: typing.Any,
            role: int=...
    ) -> bool:
        if role not in ActionTree.roles:
            return False

        role_name = ActionTree.roles[role].data().decode()
        try:
            node = self._action_tree.root.node_at_index(index.row() + 1)
            if role_name == "isExpanded":
                self._is_expanded[node.value.id] = bool(value)
            else:
                return False

            self.dataChanged.emit(index, index)
            return True
        except error.GremlinError as e:
            print(f"Invalid index: {e}")
            return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        return QtCore.Qt.ItemFlag.ItemIsEditable | \
               QtCore.Qt.ItemFlag.ItemIsEnabled | \
               QtCore.Qt.ItemFlag.ItemIsSelectable

    def roleNames(self) -> typing.Dict:
        return ActionTree.roles

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
        source_node.detach()
        target_node.insert_sibling_after(source_node)

        self.layoutChanged.emit()

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
