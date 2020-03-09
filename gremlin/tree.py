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
from typing import Any, Optional

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

    def add_sibling(self, other: TreeNode) -> None:
        """Adds a new sibling node to the tree.

        Args:
            other: the node to add as sibling
        """
        if self.parent is None:
            raise gremlin.error.GremlinError(
                "Cannot add sibling node to root node."
            )

        other.parent = self.parent
        self.parent.children.append(other)

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
