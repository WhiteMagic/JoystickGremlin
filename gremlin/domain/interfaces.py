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
Core domain interfaces for action system.

These interfaces break circular dependencies between base_classes and profile
modules by providing abstract contracts that both can depend on.

Clean Code Principle: Dependency Inversion Principle (SOLID)
- High-level modules should not depend on low-level modules
- Both should depend on abstractions
"""

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol, TYPE_CHECKING, Sequence
import uuid
from xml.etree import ElementTree

if TYPE_CHECKING:
    from gremlin.types import InputType, ActionActivationMode


class ISerializable(Protocol):
    """Protocol for objects that can be serialized to/from XML.
    
    This replaces direct dependencies between modules by providing
    a common interface that both can implement.
    """
    
    def to_xml(self) -> ElementTree.Element:
        """Serialize object to XML.
        
        Returns:
            XML element representing this object
        """
        ...
    
    def from_xml(self, node: ElementTree.Element) -> None:
        """Deserialize object from XML.
        
        Args:
            node: XML element to deserialize from
        """
        ...


class IProfileElement(ABC):
    """Abstract base class for profile elements.
    
    This serves as the common base for actions, containers, and other
    profile components without creating circular dependencies.
    """
    
    def __init__(self):
        """Initialize profile element with unique ID."""
        self._id = uuid.uuid4()
    
    @property
    def id(self) -> uuid.UUID:
        """Returns the unique identifier.
        
        Returns:
            UUID of this element
        """
        return self._id
    
    @abstractmethod
    def to_xml(self) -> ElementTree.Element:
        """Serialize to XML.
        
        Returns:
            XML representation
        """
        pass
    
    @abstractmethod
    def from_xml(self, node: ElementTree.Element) -> None:
        """Deserialize from XML.
        
        Args:
            node: XML element to deserialize from
        """
        pass


class IActionData(ABC):
    """Abstract interface for action data.
    
    This breaks the circular dependency between base_classes and profile
    by providing a common interface that profile can depend on without
    importing the concrete implementation.
    """
    
    @property
    @abstractmethod
    def id(self) -> uuid.UUID:
        """Returns the action's unique identifier."""
        pass
    
    @property
    @abstractmethod
    def behavior_type(self) -> 'InputType':
        """Returns the behavior type of this action."""
        pass
    
    @property
    @abstractmethod
    def activation_mode(self) -> 'ActionActivationMode':
        """Returns the activation mode."""
        pass
    
    @property
    @abstractmethod
    def properties(self) -> list:
        """Returns the list of configurable properties for this action."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the display name of this action type."""
        pass
    
    @abstractmethod
    def functor(self, action: 'IActionData') -> typing.Callable:
        """Create a functor that executes this action.
        
        Args:
            action: The action data to create a functor for
            
        Returns:
            A callable that executes the action
        """
        pass
    
    @abstractmethod
    def is_valid(self) -> bool:
        """Check if this action is valid and can be executed.
        
        Returns:
            True if the action is properly configured, False otherwise
        """
        pass
    
    @abstractmethod
    def get_actions(self, selector: Optional[str] = None) -> tuple[Sequence['IActionData'], Sequence[str]]:
        """Get child actions and their labels.
        
        Args:
            selector: Optional selector to filter specific action types
            
        Returns:
            Tuple of (sequence of child actions, sequence of labels)
        """
        pass
    
    @abstractmethod
    def remove_action(self, index: int, selector: Optional[str] = None) -> None:
        """Remove a child action at the given index.
        
        Args:
            index: Index of the action to remove
            selector: Optional selector for specific action type
        """
        pass
    
    @abstractmethod
    def _valid_selectors(self) -> list[str]:
        """Get list of valid selectors for this action.
        
        Returns:
            List of valid selector strings
        """
        pass
    
    @abstractmethod
    def to_xml(self) -> ElementTree.Element:
        """Serialize to XML."""
        pass
    
    @abstractmethod
    def from_xml(self, node: ElementTree.Element, *args, **kwargs) -> None:
        """Deserialize from XML.
        
        Args:
            node: XML element to deserialize from
            *args: Additional positional arguments (implementation specific)
            **kwargs: Additional keyword arguments (implementation specific)
        """
        pass


class ILibrary(ABC):
    """Abstract interface for profile library.
    
    This allows base_classes to reference the library without
    importing profile.py directly.
    """
    
    @abstractmethod
    def get_action(self, action_id: uuid.UUID) -> Optional[IActionData]:
        """Get action by ID.
        
        Args:
            action_id: UUID of the action
            
        Returns:
            Action data or None if not found
        """
        pass
    
    @abstractmethod
    def add_action(self, action: IActionData) -> None:
        """Add action to library.
        
        Args:
            action: Action to add
        """
        pass
    
    @abstractmethod
    def remove_action(self, action_id: uuid.UUID) -> None:
        """Remove action from library.
        
        Args:
            action_id: UUID of action to remove
        """
        pass


class IContainer(ABC):
    """Abstract interface for action containers.
    
    Containers hold and manage collections of actions.
    """
    
    @abstractmethod
    def add_action(self, action: IActionData) -> None:
        """Add an action to this container."""
        pass
    
    @abstractmethod
    def remove_action(self, action: IActionData) -> None:
        """Remove an action from this container."""
        pass
    
    @abstractmethod
    def get_actions(self) -> List[IActionData]:
        """Get all actions in this container."""
        pass
