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

from PySide2 import QtCore
from PySide2.QtCore import Property, Signal, Slot

from gremlin import error


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
        QtCore.Qt.UserRole + 3: QtCore.QByteArray("profile_data".encode()),
        QtCore.Qt.UserRole + 4: QtCore.QByteArray("qml_path".encode()),
    }

    def __init__(self, action_tree, parent=None):
        super().__init__(parent)

        self._action_tree = action_tree

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
                return f"{node.value.name}: {node.value.description}"
            elif role_name == "qml_path":
                return node.value.qml_path()
            elif role_name == "profile_data":
                return node.value
        except error.GremlinError as e:
            print(f"Invalid index: {e}")

    def roleNames(self) -> typing.Dict:
        return ActionTree.roles