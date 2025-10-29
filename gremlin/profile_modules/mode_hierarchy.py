# -*- coding: utf-8; -*-

"""Mode hierarchy management for profiles.

This module contains the ModeHierarchy class for managing mode
inheritance and relationships in profiles.

Extracted from gremlin.profile for better organization.
"""

from typing import List
from xml.etree import ElementTree

from gremlin import error
from gremlin.tree import TreeNode
from gremlin.util import safe_format


class ModeHierarchy:
    """Contains all the modes and their hierarchical information.
    
    Modes can inherit from parent modes, creating a tree structure
    of mode relationships. This class manages that hierarchy.
    """

    def __init__(self, parent_profile):
        """Creates a new mode hierarchy.

        Args:
            parent_profile: the profile this mode hierarchy is associated with
        """
        self._profile = parent_profile
        self._hierarchy = TreeNode("")
        self._hierarchy.add_child(TreeNode("Default"))

    @property
    def first_mode(self) -> str:
        """Returns the name of the first mode.

        Returns:
            Name of the first mode
        """
        return self._hierarchy.children[0].value

    def mode_names(self) -> List[str]:
        """Returns a list containing the names of all modes.

        Returns:
            List of all mode names
        """
        return sorted([node.value for node in self.mode_list()])

    def mode_list(self) -> List[TreeNode]:
        """Returns a list of all mode nodes.

        Returns:
            List containing TreeNodes of all modes
        """
        modes = self._hierarchy.nodes_matching(lambda x: True)
        modes.remove(self._hierarchy)
        return modes

    def valid_parents(self, mode_name: str) -> List[str]:
        """Returns the list of parents that are valid for the given mode.

        Args:
            mode_name: name of the mode for which to return valid parents

        Returns:
            List of valid parents for the specified mode
        """
        parent_candidates = []
        mode_node = self.find_mode(mode_name)
        for node in self.mode_list():
            if not mode_node.is_descendant(node) and node != mode_node:
                parent_candidates.append(node.value)
        return sorted(parent_candidates)

    def find_mode(self, mode_name: str) -> TreeNode:
        """Returns the node corresponding to the name with the given name.

        Args:
            mode_name: name of the mode to find and return

        Returns:
            Node corresponding to the node with the provided name
        """
        nodes = self._hierarchy.nodes_matching(lambda x: mode_name == x.value)
        if len(nodes) > 1:
            raise error.GremlinError(
                f"More than one mode named '{mode_name}' exists"
            )
        elif len(nodes) == 0:
            raise error.GremlinError(
                f"No node with the name '{mode_name}' exists"
            )
        return nodes[0]

    def add_mode(self, mode_name: str) -> None:
        """Adds a new mode to the hierarchy.

        Args:
            mode_name: name of the new mode to add
        """
        if self.mode_exists(mode_name):
            raise error.GremlinError(
                f"Attempting to add an already existing mode '{mode_name}'."
            )
        self._hierarchy.add_child(TreeNode(mode_name))

    def delete_mode(self, mode_name: str) -> None:
        """Deletes the mode with the given name from the hierarchy.

        Args:
            mode_name: name of the mode to delete
        """
        if not self.mode_exists(mode_name):
            raise error.GremlinError(
                f"Attempting to delete a non-existant mode '{mode_name}'."
            )

        # Find node and remove it from the hierarchy tree but reconnect its
        # children to their grandparent.
        node = self.find_mode(mode_name)
        parent_node = node.parent
        node.detach()
        for child in node.children:
            child.set_parent(parent_node)

        # Find all InputItem actions using the mode being deleted and remove
        # them as well.
        for device_id, input_items in self._profile.inputs.items():
            self._profile.inputs[device_id] = [
                x for x in input_items if x.mode != mode_name
            ]

    def rename_mode(self, old_name: str, new_name: str) -> None:
        """Changes the name of an existing mode.

        Args:
            old_name: name of the mode to rename
            new_name: new name for the mode
        """
        # Don't do anything if the names are the same
        if old_name == new_name:
            return

        # Handle missing mode to rename
        if not self.mode_exists(old_name):
            raise error.GremlinError(
                f"Attempting to rename non-existant mode '{old_name}'"
            )
        # Raise an error if renaming to an existing name
        elif self.mode_exists(new_name):
            raise error.GremlinError(
                f"Unable to rename '{old_name}' to '{new_name}' as a mode "
                f"with that name already exists"
            )

        # Perform renaming of the mode
        node = self.find_mode(old_name)
        node.value = new_name

        # Find all actions associated to the old mode name
        for action in self._actions_with_mode(old_name):
            action.mode = new_name

    def set_parent(self, mode_name: str, parent_name: str | None) -> None:
        """Sets the parent of the specified mode.

        Args:
            mode_name: name of the mode to set the parent of
            parent_name: name of the new parent mode
        """
        mode_node = self.find_mode(mode_name)
        parent_node = self.find_mode(parent_name)
        # Detach node before setting new parent to avoid cycle detection
        mode_node.detach()
        mode_node.set_parent(parent_node)

    def mode_exists(self, name: str) -> bool:
        """Checks if a mode with a given name already exists.

        Args:
            name: name of the mode to check for existence

        Returns:
            True if the mode exists, False otherwise
        """
        return len(self._hierarchy.nodes_matching(lambda x: name == x.value)) > 0

    def from_xml(self, root: ElementTree.Element) -> None:
        """Loads mode hierarchy from XML.

        Args:
            root: XML root element containing modes
        """
        # Parse individual nodes
        nodes = {}
        node_parents = {}
        for node in root.findall("./modes/mode"):
            if "parent" in node.attrib:
                node_parents[node.text] = node.get("parent")
            nodes[node.text] = TreeNode(node.text)

        # Reconstruct tree structure
        for child, parent in node_parents.items():
            nodes[child].set_parent(nodes[parent])

        self._hierarchy = TreeNode("")
        for node in nodes.values():
            if node.parent is None:
                node.set_parent(self._hierarchy)

    def to_xml(self) -> ElementTree.Element:
        """Converts mode hierarchy to XML.

        Returns:
            XML element containing mode hierarchy
        """
        node = ElementTree.Element("modes")
        for mode in self._hierarchy.nodes_matching(lambda x: True):
            if mode.parent is None:
                continue

            n_mode = ElementTree.Element("mode")
            n_mode.text = mode.value
            if mode.parent != self._hierarchy:
                n_mode.set(
                    "parent",
                    safe_format(mode.parent.value, str)
                )
            node.append(n_mode)
        return node

    def _actions_with_mode(self, mode: str) -> List:
        """Returns all actions belonging to the given mode.

        Args:
            mode: name of the mode for which to return all actions

        Returns:
            List of actions in the specified mode
        """
        actions = []
        for action_list in self._profile.inputs.values():
            actions.extend([x for x in action_list if x.mode == mode])
        return actions
