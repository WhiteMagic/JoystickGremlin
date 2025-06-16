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
Linux Input/Output Backend for Joystick Gremlin

This module provides a pure Linux implementation for input device handling
and virtual output device creation, completely replacing the Windows-specific
DILL and vJoy systems.

This is a Linux-only implementation with no Windows compatibility.
"""

import logging

from . import device_manager
from . import keyboard_mouse  
from . import virtual_output
from . import types

# Re-export commonly used types and classes
from .types import (
    InputType, InputEvent, DeviceSummary, AxisInfo, ButtonInfo, HatInfo,
    UUID_Invalid, UUID_Keyboard, UUID_Mouse, GUID_Keyboard, GUID_Mouse
)
from .device_manager import DeviceManager
from .keyboard_mouse import KeyboardMouseManager
from .virtual_output import VirtualJoystick

# Global instances
_device_manager = None
_keyboard_mouse_manager = None

def initialize():
    """Initialize the Linux input/output backend."""
    global _device_manager, _keyboard_mouse_manager
    
    logger = logging.getLogger("system")
    logger.info("Initializing Linux input/output backend")
    
    # Initialize device manager for joystick/gamepad input
    _device_manager = DeviceManager()
    _device_manager.start_monitoring()
    
    # Initialize keyboard/mouse manager
    _keyboard_mouse_manager = KeyboardMouseManager()
    
    logger.info("Linux input/output backend initialized")

def shutdown():
    """Shutdown the Linux input/output backend and clean up resources."""
    global _device_manager, _keyboard_mouse_manager
    
    logger = logging.getLogger("system")
    logger.info("Shutting down Linux input/output backend")
    
    # Stop device monitoring
    if _device_manager:
        _device_manager.stop_monitoring()
        _device_manager = None
    
    # Clean up keyboard/mouse manager
    if _keyboard_mouse_manager:
        _keyboard_mouse_manager = None
    
    # Clean up any virtual devices
    virtual_output.cleanup_all_devices()
    
    logger.info("Linux input/output backend shutdown complete")

def get_device_manager():
    """Get the global device manager instance."""
    if _device_manager is None:
        raise RuntimeError("Linux input backend not initialized - call linput.initialize() first")
    return _device_manager

def get_keyboard_mouse_manager():
    """Get the global keyboard/mouse manager instance.""" 
    if _keyboard_mouse_manager is None:
        raise RuntimeError("Linux input backend not initialized - call linput.initialize() first")
    return _keyboard_mouse_manager

# Convenience functions for common operations
def get_joystick_devices():
    """Get list of all joystick/gamepad devices."""
    return get_device_manager().get_devices()

def get_device_count():
    """Get the number of joystick/gamepad devices."""
    return len(get_joystick_devices())

def get_device_information_by_index(index):
    """Get device information by index."""
    devices = get_joystick_devices()
    if 0 <= index < len(devices):
        return devices[index]
    return None

from .device_manager import EvdevInputManager
from .types import (
    InputEvent, 
    DeviceSummary, 
    InputType,
    DeviceActionType,
    AxisMap
)

__all__ = [
    "EvdevInputManager",
    "InputEvent",
    "DeviceSummary", 
    "InputType",
    "DeviceActionType",
    "AxisMap"
]
