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
UI-layer interfaces for breaking circular dependencies.

These interfaces allow UI components to depend on abstractions rather than
concrete implementations, breaking cycles between ui.profile and ui.action_model.

Clean Code Principle: Dependency Inversion Principle (SOLID)
"""

from __future__ import annotations

from typing import Any, List, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from gremlin.types import InputType
    from gremlin.domain.interfaces import IActionData


class IBindingModel(Protocol):
    """Abstract interface for input binding models.
    
    This breaks the circular dependency between ui.profile and ui.action_model
    by providing a common interface for accessing binding properties without
    importing the concrete implementation.
    
    REFACTORED: Created to break ui.profile <-> ui.action_model cycle using
    Dependency Inversion Principle (SOLID).
    """
    
    @property
    def behavior_type(self) -> 'InputType':
        """Returns the input behavior type of this binding."""
        ...
    
    @property
    def input_item_binding(self) -> Any:
        """Returns the underlying input item binding."""
        ...
    
    @property
    def root_action(self) -> 'IActionData':
        """Returns the root action of this binding."""
        ...
    
    def is_last_action_in_container(self, action: 'IActionData', container: Optional[str] = None) -> bool:
        """Check if action is the last in its container."""
        ...
    
    def get_child_actions(self, action: 'IActionData', container: Optional[str] = None) -> List[Any]:
        """Get child actions of the specified action."""
        ...
    
    def sync_data(self) -> None:
        """Synchronize data changes."""
        ...
    
    def remove_action(self, index: Any) -> None:
        """Remove action at index."""
        ...
    
    def parent(self) -> Any:
        """Get parent model."""
        ...
    
    def move_action(self, source: Any, target: Any, container: Optional[str] = None) -> None:
        """Move action from source to target."""
        ...
