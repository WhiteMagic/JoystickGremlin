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

import uuid
from xml.etree import ElementTree

from PySide6.QtCore import Property, Signal

from . import error, plugin_manager
from .tree import TreeNode
from .util import safe_format, safe_read
from .types import InputType


class RootAction:

    """Represents the root node of any action tree.

    This class mimicks the behavior of base_classes.AbstractActionModel but
    is not intended to be serialized.
    """

    def __init__(self):
        self._id = uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @id.setter
    def id(self, value: uuid.UUID):
        self._id = value

    @property
    def name(self) -> str:
        return "Root"

    def qml_path(self) -> str:
        return "RootAction.qml"

    def remove_action(self, action) -> None:
        """Removes the provided action from this action.

        Args:
            action: the action to remove
        """
        pass

    def add_action_after(self,  anchor, action) -> None:
        """Adds the provided action after the specified anchor.

        Args:
            anchor: action after which to insert the given action
            action: the action to remove
        """
        pass

    def set_behavior_type(self, new_behavior: InputType) -> None:
        """Sets the behavior of the root node.

        NoOp implementation to fit in with the rest of the rest of the node
        system.

        Args:
            new_behavior: new behavior of the node
        """
        pass


class ActionTree:

    """Represents a tree of actions.

    The tree contains both actions to execute as well as conditions controlling
    when and which actions will be executed.
    """

    def __init__(self):
        """Creates a new instance."""
        self.root = TreeNode()
        self.root.value = RootAction()

    def from_xml(self, action_tree_node: ElementTree) -> None:
        """Populates the instance with the XML instance data.

        Args:
            action_tree_node: XML subtree which contains the information
        """
        self.root.value.id = safe_read(action_tree_node, "root", uuid.UUID)

        # Create the action tree nodes corresponding to each <action> XML
        # element
        action_nodes = []
        action_ids = {}
        parent_ids = {}
        for node in action_tree_node.findall("./action"):
            # Ensure all required attributes are present
            if not set(["id", "type", "parent"]).issubset(node.keys()):
                raise error.ProfileError(
                    f"Missing attribute in an action of tree with "
                    f"root: '{self.root.value.id}'"
                )

            # Ensure the action type is known
            type_key = node.get("type")
            if type_key not in plugin_manager.ActionPlugins().tag_map:
                action_id = safe_read(node, "id", uuid.UUID)
                raise error.ProfileError(
                    f"Unknown type '{type_key}' in action '{action_id}"
                )

            # Create action data object
            action_data = plugin_manager.ActionPlugins().tag_map[type_key](self)
            action_data.from_xml(node)

            # Store node information
            action_node = TreeNode(action_data)
            action_nodes.append(action_node)
            action_ids[action_data.id] = len(action_nodes) - 1
            parent_ids[action_data.id] = safe_read(node, "parent", uuid.UUID)

        # Reconstruct the action tree structure
        for node in action_nodes:
            parent_id = parent_ids[node.value.id]

            parent_node = None
            if parent_id in action_ids:
                parent_node = action_nodes[action_ids[parent_id]]
            elif parent_id == self.root.value.id:
                parent_node = self.root
            else:
                raise error.ProfileError(
                    f"Parent id '{parent_id}' of action "
                    f"'{node.value.id}' is invalid"
                )
            node.set_parent(parent_node)

    def to_xml(self) -> ElementTree:
        """Returns an XML subtree representing the tree's information.

        Returns:
            XML element containing the object's information
        """
        node = ElementTree.Element("action-tree")
        node.set("root", safe_format(self.root.value.id, uuid.UUID))
        # Serialize very node in the tree and capture the tree structure
        for i in range(1, self.root.node_count):
            child = self.root.node_at_index(i)
            child_node = child.value.to_xml()
            parent_id = self.root.value.id
            if child.parent.depth > 0:
                parent_id = child.parent.value.id
            child_node.set("parent", safe_format(parent_id, uuid.UUID))

            node.append(child_node)
        return node


class LibraryItem:

    """Stores information about an individual library item.

    Contains the actual action configuration and the unique id associated
    with the particular item.
    """

    def __init__(self):
        self.action_tree = None
        self._id = uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        """Returns the unique identifier of this instance.

        Returns:
            Unique id of this instance
        """
        return self._id

    def from_xml(self, node: ElementTree.Element) -> None:
        """Parses an library item to populate this instance.

        Args:
            node: XML node containing the library item information
        """
        self._id = safe_read(node, "id", uuid.UUID)
        at_node = node.find("action-tree")
        self.action_tree = ActionTree()
        self.action_tree.from_xml(at_node)

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the content of this library.

        Returns:
            XML node holding the instance's content
        """
        node = ElementTree.Element("library-item")
        node.set("id", safe_format(self._id, uuid.UUID))
        node.append(self.action_tree.to_xml())
        return node


class Library:

    """Stores library items which contain action configurations.

    Each item is a self contained entry with a UUID assigned to it which
    is used by the input items to reference the actual content.
    """

    def __init__(self):
        """Creates a new library instance."""

        # Each entry is a container with it's action sets but without
        # conditions or virtual button configuration
        self._items = {}

    def __contains__(self, key: uuid.UUID) -> bool:
        """Checks if an item exists for the given key.

        Args:
            key: the key to check for

        Returns:
            True if an item exists for the specific key, False otherwise
        """
        return key in self._items

    def __getitem__(self, key: uuid.UUID) -> LibraryItem:
        """Returns the item stored at the specified key.

        If there is no item with the specified key an exception is throw.

        Args:
            key: the key to return an item for

        Returns:
            The LibraryItem instance stored at the given key
        """
        if key not in self._items:
            raise error.GremlinError(f"Invalid uuid for library entry: {key}")
        return self._items[key]

    def add_item(self, item: LibraryItem) -> None:
        """Adds the provided item to the library.

        Args:
            item: the item to add
        """
        self._items[item.id] = item

    def delete_item(self, uuid: uuid.UUID) -> None:
        """Deletes the item with the provided identifier from the library.

        Args:
            uuid: unique identifier of the item to delete
        """
        if uuid in self._items:
            del self._items[uuid]

    def from_xml(self, node: ElementTree.Element) -> None:
        """Parses an library node to populate this instance.

        Args:
            node: XML node containing the library information
        """
        for item in node.findall("./library/library-item"):
            library_item = LibraryItem()
            library_item.from_xml(item)

            if library_item.id in self._items:
                raise error.ProfileError(
                    f"Duplicate library item guid: {library_item.id}"
                )

            self._items[library_item.id] = library_item

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the content of this library.

        Returns:
            XML node holding the instance's content
        """
        node = ElementTree.Element("library")
        for item in self._items.values():
            node.append(item.to_xml())
        return node