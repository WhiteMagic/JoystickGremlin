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
Domain abstractions to break circular dependencies.

This module contains abstract base classes and protocols that are shared
between gremlin.base_classes and gremlin.profile, breaking the circular
dependency between them.

Clean Code Principle: Dependency Inversion Principle (SOLID)
- High-level modules should not depend on low-level modules
- Both should depend on abstractions

Also contains core domain types like Event to prevent circular dependencies
between base_classes, event_handler, and code_runner.
"""

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol, TYPE_CHECKING, Sequence
import uuid
from xml.etree import ElementTree

if TYPE_CHECKING:
    from gremlin.types import InputType, ActionActivationMode


class Event:
    """Represents a single event captured by the system.

    An event can originate from the keyboard or joystick which is
    indicated by the InputType value. The value of the event has to
    be interpreted based on the type of the event.

    Keyboard and JoystickButton events have a simple True / False
    value stored in is_pressed indicating whether or not the key has
    been pressed. For JoystickAxis the value indicates the axis value
    in the range [-1, 1] stored in the value field. JoystickHat events
    represent the hat position as a unit tuple (x, y) representing
    deflection in cartesian coordinates in the value field.
    
    REFACTORED: Moved from event_handler to domain to break circular dependency
    between base_classes → event_handler → code_runner → base_classes
    """

    def __init__(
            self,
            event_type: 'InputType',
            identifier: Any,
            device_guid: uuid.UUID,
            mode: str,
            value: Any | None=None,
            is_pressed: bool | None=None,
            raw_value: Any | None=None
    ):
        """Creates a new Event object.

        Args:
            event_type: the type of input causing the event
            identifier: the identifier of the event source
            device_guid: uuid identifying the device causing this event
            mode: name of the mode the system was in when the even was received
            value: the value of the input
            is_pressed: boolean flag indicating if a button or key is pressed
            raw_value: the raw value of the axis being moved
        """
        self.event_type = event_type
        self.identifier = identifier
        self.device_guid = device_guid
        self.mode = mode
        self.is_pressed = is_pressed
        self.value = value
        self.raw_value = raw_value

    def clone(self) -> 'Event':
        """Returns a copy of this event.

        Returns:
            Copy of this event
        """
        return Event(
            self.event_type,
            self.identifier,
            self.device_guid,
            self.mode,
            self.value,
            self.is_pressed,
            self.raw_value
        )

    def __eq__(self, other):
        return isinstance(other, Event) \
            and other.event_type == self.event_type \
            and other.identifier == self.identifier \
            and other.device_guid == self.device_guid

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.event_type, self.identifier, self.device_guid))


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
    def behavior_type(self) -> InputType:
        """Returns the behavior type of this action."""
        pass
    
    @property
    @abstractmethod
    def activation_mode(self) -> ActionActivationMode:
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


# Re-export for convenience
__all__ = [
    'ISerializable',
    'IProfileElement',
    'IActionData',
    'ILibrary',
    'IContainer',
]
