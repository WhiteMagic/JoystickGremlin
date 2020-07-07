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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional

import gremlin.error


class TreeNode:

    """Represents a single node in a tree.

    Supports basic functionaolity for tree construction and modification.
    """

    def __init__(
            self,
            value: Optional[Any] = None,
            parent: Optional[TreeNode] = None
    ):
        """Creates a new tree instance.

        Args:
            value: the value stored by this node
            parent: the node's parent
        """
        self.value = value
        self.parent = parent
        self.children = []
        if parent is not None:
            parent.add_child(self)

    def add_child(self, other: TreeNode) -> None:
        """Adds a new child node to the tree.

        Args:
            other: the node to add as child
        """
        other.parent = self
        self.children.append(other)

    def append_sibling(self, other: TreeNode) -> None:
        """Adds a sibling node to the tree at the end of the list of siblings.

        Args:
            other: the node to add as sibling
        """
        if self.parent is None:
            raise gremlin.error.GremlinError(
                "Cannot add sibling node to root node."
            )

        other.parent = self.parent
        self.parent.children.append(other)

    def insert_sibling_after(self, other: TreeNode) -> None:
        """Inserts a new sibling after this node.

        Args:
            other: the node to add as sibling
        """
        if self.parent is None:
            raise gremlin.error.GremlinError(
                "Cannot add sibling node to root node."
            )

        other.parent = self.parent
        index = self.parent.children.index(self)
        self.parent.children.insert(index+1, other)

    def insert_sibling_before(self, other: TreeNode) -> None:
        """Inserts a new sibling before this node.

        Args:
            other: the node to add as sibling
        """
        if self.parent is None:
            raise gremlin.error.GremlinError(
                "Cannot add sibling node to root node."
            )

        other.parent = self.parent
        index = self.parent.children.index(self)
        self.parent.children.insert(index, other)

    def set_parent(self, other: TreeNode) -> None:
        """Sets the parent of this node.

        Args:
            other: the node to set as parent
        """
        # Check for direct cycles. If any are present resolve them and log
        # a warning message as this could be a sign of unintended behavior
        if other.is_descendant(self) or self.is_descendant(other):
            raise gremlin.error.GremlinError(
                "Setting parent would cause a cycle, aborting"
            )

        if self.parent is not None:
            self.parent.remove_child(self)
        self.parent = other
        other.children.append(self)

    def remove_child(self, other: TreeNode) -> None:
        """Removes a child node from the tree.

        Args:
            other: the child node to remove
        """
        if other in self.children:
            other.parent = None
            self.children.remove(other)

    def detach(self) -> None:
        """Detaches this (sub)tree from the rest of the tree."""
        if self.parent is not None:
            self.parent.remove_child(self)
        self.parent = None

    def is_descendant(self, other: None) -> bool:
        """Returns whether or not other is a descendant of this node.

        Args:
            other: node to check for being a descendant

        Returns:
            True if the provided node is a descendant of this node and False
            otherwise.
        """
        node_list = self.children[:]
        while len(node_list) > 0:
            node = node_list.pop()
            if node == other:
                return True
            node_list.extend(node.children[:])
        return False

    def get_root(self) -> TreeNode:
        """Returns the root node of the tree.

        Returns:
            Root node of the tree
        """
        root_node = self
        while root_node.parent is not None:
            root_node = root_node.parent
        return root_node

    @property
    def node_count(self) -> int:
        """Returns the number of nodes in the tree.

        Returns:
            Number of nodes in the tree
        """
        stack = [self.get_root()]
        count = 0

        while len(stack) > 0:
            node = stack.pop()
            stack.extend(node.children)
            count += 1

        return count

    def node_at_index(self, index: int) -> TreeNode:
        """Returns the node with the specified index.

        Args:
            index: the index of the node to return

        Returns:
            Node corresponding to the provided index
        """
        stack = [self.get_root()]
        node_index = 0

        while len(stack) > 0:
            node = stack.pop()
            if node_index == index:
                return node

            node_index += 1
            stack.extend(node.children[::-1])

        raise gremlin.error.GremlinError(f"No node with index {index} exists.")

    def nodes_matching(self, predicate: Callable[[TreeNode], bool]) -> List[TreeNode]:
        """Returns the list of nodes for which the predicate is true.

        Args:
            predicate: function evaluating a TreeNode instance, returns True
                if the node should be returned, False otherwise

        Returns:
            List of TreeNode instance for which the predicate returns True
        """
        node_list = []
        stack = [self.get_root()]
        while len(stack) > 0:
            node = stack.pop()
            if predicate(node):
                node_list.append(node)
            stack.extend(node.children[::-1])
        return node_list

    @property
    def depth(self) -> int:
        """Returns the depth of this node within the tree.

        Returns:
            Depth of the node within the tree, 0 depth being the root
        """
        node_depth = 0
        current_parent = self.parent
        while current_parent is not None:
            current_parent = current_parent.parent
            node_depth += 1
        return node_depth

    @property
    def depth_first_index(self) -> int:
        """Returns the index of this node as found via depth first traversal.

        The depth first traversal enumerates nodes in pre-order manner.

        Return:
            Index of this node in depth first traversal, with 0 being the root.
        """
        stack = [self.get_root()]
        index = 0

        while len(stack) > 0:
            node = stack.pop()
            if node == self:
                return index

            index += 1
            stack.extend(node.children[::-1])

        raise gremlin.error.GremlinError("Unable to determine depth index.")
