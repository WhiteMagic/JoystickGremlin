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
Linux-native replacement for the DILL (DirectInput LL) module.

This module provides UUID-based device identification compatible with linput,
replacing the Windows-specific GUID structures from the original DILL module.

DEPRECATED: This is a compatibility layer. New code should use linput directly.
"""

from __future__ import annotations

import uuid
import warnings
from typing import Optional

# Import from linput for device management
from typing import List, Optional, TYPE_CHECKING
import linput
from linput.types import UUID_Keyboard, UUID_Virtual, UUID_Intermediate_Output

if TYPE_CHECKING:
    from linput.types import DeviceSummary
else:
    DeviceSummary = None


class DILLError(Exception):
    """Exception raised when an error occurs within device operations."""

    def __init__(self, value: str):
        """Creates a new error instance with the given message.

        Args:
            value: the error message to use
        """
        super().__init__(value)


# Linux-native UUID constants (from linput)
# These replace the Windows _GUID structures

# Keyboard UUID (same across all keyboards on the system)
GUID_Keyboard = UUID_Keyboard

# Virtual device UUID marker
GUID_Virtual = UUID_Virtual

# Intermediate output UUID
GUID_IntermediateOutput = UUID_Intermediate_Output
UUID_IntermediateOutput = UUID_Intermediate_Output

# Invalid/uninitialized UUID
GUID_Invalid = uuid.UUID('00000000-0000-0000-0000-000000000000')
UUID_Invalid = GUID_Invalid


class GUID:
    """
    Compatibility wrapper for UUID to mimic Windows GUID behavior.
    
    DEPRECATED: Use uuid.UUID directly in new code.
    """
    
    def __init__(self, guid_uuid: Optional[uuid.UUID] = None):
        """Creates a GUID wrapper.
        
        Args:
            guid_uuid: UUID to wrap, or None for invalid GUID
        """
        warnings.warn(
            "GUID class is deprecated. Use uuid.UUID directly.",
            DeprecationWarning,
            stacklevel=2
        )
        self._uuid = guid_uuid if guid_uuid is not None else GUID_Invalid
    
    @staticmethod
    def from_uuid(guid_uuid: uuid.UUID) -> GUID:
        """Creates a GUID from a UUID.
        
        Args:
            guid_uuid: UUID to convert
            
        Returns:
            GUID wrapper
        """
        return GUID(guid_uuid)
    
    @staticmethod
    def from_str(guid_str: str) -> uuid.UUID:
        """Parses a GUID from a string.
        
        Args:
            guid_str: String representation of GUID
            
        Returns:
            UUID object
        """
        try:
            return uuid.UUID(guid_str)
        except ValueError as e:
            raise DILLError(f"Invalid GUID string: {guid_str}") from e
    
    def to_uuid(self) -> uuid.UUID:
        """Converts to UUID.
        
        Returns:
            The wrapped UUID
        """
        return self._uuid
    
    def __str__(self) -> str:
        """String representation."""
        return str(self._uuid)
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, GUID):
            return self._uuid == other._uuid
        if isinstance(other, uuid.UUID):
            return self._uuid == other
        return False
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self._uuid)


class DILL:
    """
    Device input compatibility layer for Linux.
    
    This replaces the Windows DirectInput functionality with Linux evdev/linput.
    
    DEPRECATED: Use linput.DeviceManager directly in new code.
    """
    
    @staticmethod
    def init():
        """Initialize device system (no-op, linput auto-initializes)."""
        warnings.warn(
            "DILL.init() is deprecated. linput auto-initializes.",
            DeprecationWarning,
            stacklevel=2
        )
        pass
    
    @staticmethod
    def get_device_information_by_guid(device_guid: uuid.UUID):  # type: ignore
        """Get device information by GUID.
        
        Args:
            device_guid: Device UUID
            
        Returns:
            Device summary or None if not found
        """
        try:
            device_mgr = linput.DeviceManager()
            return device_mgr.get_device_by_guid(device_guid)
        except (KeyError, AttributeError, RuntimeError):
            return None
    
    @staticmethod
    def get_devices():  # type: ignore
        """Get all connected devices.
        
        Returns:
            List of device summaries
        """
        try:
            device_mgr = linput.DeviceManager()
            return list(device_mgr.devices().values())
        except (AttributeError, RuntimeError):
            return []
    
    @staticmethod
    def get_guid(index: int) -> uuid.UUID:
        """Get device GUID by index.
        
        Args:
            index: Device index (deprecated concept)
            
        Returns:
            Device UUID
        """
        devices = DILL.get_devices()
        if 0 <= index < len(devices):
            return devices[index].device_guid
        return GUID_Invalid


# Deprecated aliases for backwards compatibility
_GUID = GUID  # Windows C structure equivalent
if not TYPE_CHECKING:
    DeviceSummary = linput.types.DeviceSummary  # Re-export from linput


def init():
    """Initialize DILL (deprecated, use linput.initialize())."""
    warnings.warn(
        "dill.init() is deprecated. Use linput.initialize().",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        linput.initialize()
    except RuntimeError:
        # Already initialized
        pass


__all__ = [
    'GUID',
    'DILL',
    'DILLError',
    'GUID_Keyboard',
    'GUID_Virtual',
    'GUID_IntermediateOutput',
    'GUID_Invalid',
    'UUID_Keyboard',
    'UUID_Virtual',
    'UUID_IntermediateOutput',
    'UUID_Invalid',
    'DeviceSummary',
    'init',
]


# Print deprecation warning when module is imported
warnings.warn(
    "\n"
    "=" * 80 + "\n"
    "WARNING: The 'dill' module is DEPRECATED and will be removed.\n"
    "Please use 'linput' directly for device management:\n"
    "  - import linput\n"
    "  - Use linput.DeviceManager for device enumeration\n"
    "  - Use uuid.UUID instead of dill.GUID\n"
    "  - GUID_Keyboard -> linput.GUID_Keyboard\n"
    "  - GUID_Virtual -> linput.UUID_VIRTUAL\n"
    "=" * 80,
    DeprecationWarning,
    stacklevel=2
)
