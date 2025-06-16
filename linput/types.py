# -*- coding: utf-8; -*-

# Copyright (C) 2025 Linux Port Contributors
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
Linux Input Types

Native Linux data structures and enums for input handling.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Tuple
from dataclasses import dataclass


class InputType(Enum):
    """Types of input events that can be detected."""
    
    Keyboard = 1
    JoystickAxis = 2  
    JoystickButton = 3
    JoystickHat = 4
    Mouse = 5
    
    # Linux-specific input types for internal processing
    Axis = 10
    Button = 11  
    Hat = 12
    Key = 13


class DeviceActionType(Enum):
    """Device connection state changes."""
    
    Connected = 1
    Disconnected = 2


@dataclass
class AxisMap:
    """Mapping information for joystick axes."""
    
    axis_index: int
    axis_id: int


@dataclass 
class InputEvent:
    """Input event data from a device."""
    
    device_guid: uuid.UUID
    input_type: InputType
    code: int  # Input identifier (axis, button, key code, etc.)
    value: Any
    is_pressed: bool = False
    raw_value: Any = None


@dataclass
class DeviceSummary:
    """Information about a detected input device."""
    
    device_guid: uuid.UUID
    name: str
    vendor_id: int
    product_id: int
    axis_count: int
    button_count: int  
    hat_count: int
    axis_map: list[AxisMap]
    is_virtual: bool = False
    vjoy_id: int = 0  # For virtual output devices
    device_path: str = ""  # Linux device path
    
    def set_vjoy_id(self, vjoy_id: int) -> None:
        """Sets the virtual device id."""
        if self.is_virtual:
            self.vjoy_id = vjoy_id


# Pre-defined UUIDs for special devices
UUID_Keyboard = uuid.UUID('6f1d2b61-d5a0-11cf-bfc7-444553540000')
UUID_Mouse = uuid.UUID('378de44c-56ef-11d1-bc8c-00a0c91405dd') 
UUID_Virtual = uuid.UUID('89d5e905-1e26-4c52-ad46-7bcc06df4c20')
UUID_Intermediate_Output = uuid.UUID('f0af472f-8e17-493b-a1eb-7333ee8543f2')
UUID_Invalid = uuid.UUID('00000000-0000-0000-0000-000000000000')

# Aliases for compatibility
GUID_Keyboard = UUID_Keyboard
GUID_Mouse = UUID_Mouse
