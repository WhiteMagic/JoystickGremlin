# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2025 Lionel Ott
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

"""
Shared UI models and data structures.

This module contains UI model classes that are shared between different
UI components. By extracting these into a separate module, we break
circular dependencies between ui.profile and ui.action_model.

Clean Code Principle: Separation of Concerns, Single Responsibility (SOLID)

REFACTORED: Extracted from action_model.py to break circular dependency.
"""

from __future__ import annotations


class SequenceIndex:
    """Represents an index into a sequence of actions.
    
    This models the QModelIndex class and provides a way to reference
    actions within a hierarchical structure.
    
    REFACTORED: Moved from action_model.py to break ui.profile <-> ui.action_model cycle.
    """

    def __init__(
            self,
            parent_index: int | None,
            container_name: str | None,
            index: int,
    ):
        """Creates a new action index instance.
        
        This models the QModelIndex class.
        
        Args:
            parent_index: index assigned to the parent action
            container_name: name of the parent's container
            index: index assigned to this action
        """
        self._parent_index = parent_index
        self._container_name = container_name
        self._index = index

    @property
    def index(self) -> int:
        """Returns the index of this action."""
        return self._index

    @property
    def parent_index(self) -> int | None:
        """Returns the parent action's index."""
        return self._parent_index

    @property
    def container_name(self) -> str | None:
        """Returns the container name."""
        return self._container_name

    def __str__(self) -> str:
        """Returns a string representation for debugging."""
        return f"SID: c={self.container_name}: p={self.parent_index} i={self.index}"


__all__ = ['SequenceIndex']
