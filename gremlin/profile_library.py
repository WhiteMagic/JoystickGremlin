# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2022 Lionel Ott
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
from typing import TYPE_CHECKING
from xml.etree import ElementTree

from gremlin import error, plugin_manager
from gremlin.tree import TreeNode
from gremlin.util import safe_format, safe_read
from gremlin.types import InputType

if TYPE_CHECKING:
    from gremlin.base_classes import AbstractActionModel


class RootAction:

    """Represents the root node of any action tree.

    This class mimicks the behavior of base_classes.AbstractActionModel but
    is not intended to be serialized. This is mainly needed to simplify the
    UI handling by providing a root-level container that holds all other
    actions.
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

    def __init__(self, library: Library):
        """Creates a new instance.

        Args:
            library: reference to the Library instance this action tree is
                part of
        """
        self._library = library
        self._id = uuid.uuid4()
        self.root = TreeNode()
        self.root.value = RootAction()

    @property
    def id(self) -> uuid.UUID:
        """Returns the unique identifier of this instance.

        Returns:
            Unique id of this instance
        """
        return self._id

    def from_xml(self, action_tree_node: ElementTree) -> None:
        """Populates the instance with the XML instance data.

        Args:
            action_tree_node: XML subtree which contains the information
        """
        self._id = safe_read(action_tree_node, "id", uuid.UUID)
        self.root.value.id = self._id

        # Process each action reference entry
        for node in action_tree_node.findall("./action-reference"):
            # Ensure the required id attribute is present
            if "id" not in node.keys():
                raise error.ProfileError(
                    f"Missing id attribute for an action of tree with "
                    f"root: '{self.root.value.id}'"
                )

            # Grab the raw abstract action instance out of the library and
            # wrap it in a TreeNode before adding it to the tree.
            action_id = safe_read(node, "id", uuid.UUID)
            if not self._library.has_action(action_id):
                error.ProfileError(
                    f"Invalid action {action_id} referenced in {self.id}"
                )
            self.root.add_child(TreeNode(self._library.get_action(action_id)))

    def to_xml(self) -> ElementTree:
        """Returns an XML subtree representing the tree's information.

        Returns:
            XML element containing the object's information
        """
        node = ElementTree.Element("action-tree")
        node.set("id", safe_format(self._id, uuid.UUID))

        # Serialize the information about the root-level action references
        # used in this action tree instance
        for i in range(1, self.root.node_count()):
            child_node = ElementTree.Element("action-reference")
            child_node.set(
                "id",
                safe_format( self.root.node_at_index(i).value.id, uuid.UUID)
            )
            node.append(child_node)


class Library:

    """Stores library items which contain action configurations.

    Each item is a self contained entry with a UUID assigned to it which
    is used by the input items to reference the actual content.
    """

    def __init__(self):
        """Creates a new library instance.

        The library contains both the individual action configurations as well
        as the items composed of them.
        """
        self._actions = {}
        self._trees = {}

    def add_action(self, action: AbstractActionModel) -> None:
        self._actions[action.id] = action

    def delete_action(self, key: int) -> None:
        """Deletes the action with the given key from the library.

        Args:
            key: the key of the action to delete
        """
        if key in self._actions:
            del self._actions[key]

    def get_action(self, key: uuid.UUID) -> AbstractActionModel:
        """Returns the action specified by the key.

        If there is no action with the specified key an exception is throw.

        Args:
            key: the key to return an action for

        Returns:
            The  instance stored at the given key
        """
        if key not in self._actions:
            raise error.GremlinError(f"Invalid key for library action: {key}")
        return self._actions[key]

    def has_action(self, key: uuid.UUID) -> bool:
        """Checks if an action exists with the given key.

        Args:
            key: the key to check for

        Returns:
            True if an action exists for the specific key, False otherwise
        """
        return key in self._actions

    def add_tree(self, tree: ActionTree) -> None:
        """Adds the provided tree to the library.

        Args:
            tree: the tree to add
        """
        self._trees[tree.id] = tree

    def delete_tree(self, uuid: uuid.UUID) -> None:
        """Deletes the tree with the provided identifier from the library.

        Args:
            uuid: unique identifier of the tree to delete
        """
        if uuid in self._trees:
            del self._trees[uuid]

    def get_tree(self, key: uuid.UUID) -> ActionTree:
        """Returns the tree stored at the specified key.

        If there is no tree with the specified key an exception is throw.

        Args:
            key: the key of the tree to return

        Returns:
            The ActionTree instance stored at the given key
        """
        if key not in self._trees:
            raise error.GremlinError(f"Invalid uuid for action tree: {key}")
        return self._trees[key]

    def has_tree(self, key: uuid.UUID) -> bool:
        """Checks if a tree exists for the given key.

        Args:
            key: the key to check for

        Returns:
            True if a tree exists for the specific key, False otherwise
        """
        return key in self._trees

    def from_xml(self, node: ElementTree.Element) -> None:
        """Parses an library node to populate this instance.

        Args:
            node: XML node containing the library information
        """
        # Parse all actions
        for entry in node.findall("./library/action"):
            # Ensure all required attributes are present
            if not set(["id", "type"]).issubset(entry.keys()):
                raise error.ProfileError(
                    "Incomplete library action specification"
                )

            # Ensure the action type is known
            type_key = entry.get("type")
            if type_key not in plugin_manager.ActionPlugins().tag_map:
                action_id = safe_read(entry, "id", uuid.UUID)
                raise error.ProfileError(
                    f"Unknown type '{type_key}' in action with id '{action_id}'"
                )

            # Create action object, turn it into a tree node and store it
            action_obj = plugin_manager.ActionPlugins().tag_map[type_key](self)
            action_obj.from_xml(entry)
            # FIXME: does this need to be a TreeNode?
            if action_obj.id in self._actions:
                raise error.ProfileError(
                    f"Duplicate library action id: {action_obj.id}"
                )
            self._actions[action_obj.id] = action_obj

        # Parse all trees 
        for entry in node.findall("./library/action-tree"):
            action_tree = ActionTree(self)
            action_tree.from_xml(entry)

            if action_tree.id in self._trees:
                raise error.ProfileError(
                    f"Duplicate library item guid: {action_tree.id}"
                )
            self._trees[action_tree.id] = action_tree

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the content of this library.

        Returns:
            XML node holding the instance's content
        """
        node = ElementTree.Element("library")
        for item in self._actions.values():
            node.append(item.to_xml())
        for item in self._trees.values():
            node.append(item.to_xml())
        return node