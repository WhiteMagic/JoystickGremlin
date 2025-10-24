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
Domain events for Joystick Gremlin.

This module contains the core Event class that represents input events
from keyboards and joysticks. Moved here from event_handler to break
circular dependencies.

Clean Code Principle: Dependency Inversion Principle (SOLID)
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from gremlin.types import InputType


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
