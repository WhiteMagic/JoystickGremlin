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
Linux Virtual Output Devices

Native Linux implementation for virtual joystick output using uinput
to replace vJoy functionality.
"""

from __future__ import annotations

import logging
import os
import stat
import time
import uuid
from typing import Dict, List, Optional, Tuple

try:
    import uinput
    UINPUT_AVAILABLE = True
except ImportError:
    UINPUT_AVAILABLE = False
    uinput = None

from .types import DeviceSummary, AxisMap, UUID_VIRTUAL


class UInputError(Exception):
    """Exception raised when an error occurs with uinput."""
    
    def __init__(self, message: str):
        super().__init__(message)


class LinuxVirtualDevice:
    """
    A virtual joystick device using Linux uinput.
    Replaces vJoy functionality on Linux.
    """
    
    def __init__(self, device_id: int, name: str = None, 
                 axis_count: int = 8, button_count: int = 16, hat_count: int = 1):
        """
        Initialize a virtual device.
        
        Args:
            device_id: Unique ID for this virtual device
            name: Device name
            axis_count: Number of axes
            button_count: Number of buttons
            hat_count: Number of hat switches
        """
        if not UINPUT_AVAILABLE:
            raise UInputError("uinput module not available. Install python-uinput.")
        
        self.device_id = device_id
        self.name = name or f"Virtual Joystick {device_id}"
        self.axis_count = axis_count
        self.button_count = button_count
        self.hat_count = hat_count
        
        self._device: Optional[uinput.Device] = None
        self._axis_values: Dict[int, float] = {}
        self._button_states: Dict[int, bool] = {}
        self._hat_states: Dict[int, Tuple[int, int]] = {}
        
        self._logger = logging.getLogger(__name__)
        
        # Generate a consistent UUID for this virtual device
        device_info = f"virtual:{device_id}:{self.name}"
        self.device_guid = uuid.uuid5(UUID_VIRTUAL, device_info)
    
    def _check_uinput_permissions(self) -> None:
        """Check if we have permission to use uinput.
        
        Raises:
            UInputError: If uinput is not accessible
        """
        if not os.path.exists('/dev/uinput'):
            raise UInputError("/dev/uinput not found. Make sure uinput module is loaded.")
        
        uinput_stat = os.stat('/dev/uinput')
        has_permission = (uinput_stat.st_mode & stat.S_IWGRP or 
                         uinput_stat.st_mode & stat.S_IWOTH)
        
        if not has_permission and os.getuid() != 0:  # Not root
            self._logger.warning(
                "May not have permission to access /dev/uinput. "
                "Add user to 'input' group or run as root."
            )

    def _create_axis_events(self) -> list:
        """Create axis event definitions.
        
        Returns:
            List of axis event tuples
        """
        axis_events = [
            uinput.ABS_X, uinput.ABS_Y,      # Left stick
            uinput.ABS_RX, uinput.ABS_RY,    # Right stick  
            uinput.ABS_Z, uinput.ABS_RZ,     # Triggers
            uinput.ABS_THROTTLE, uinput.ABS_RUDDER  # Additional axes
        ]
        
        events = []
        for i in range(min(self.axis_count, len(axis_events))):
            events.append((axis_events[i], (-32768, 32767, 0, 0)))
            self._axis_values[i + 1] = 0.0
        
        return events

    def _create_button_events(self) -> list:
        """Create button event definitions.
        
        Returns:
            List of button events
        """
        button_events = [
            uinput.BTN_JOYSTICK, uinput.BTN_THUMB, uinput.BTN_THUMB2, uinput.BTN_TOP,
            uinput.BTN_TOP2, uinput.BTN_PINKIE, uinput.BTN_BASE, uinput.BTN_BASE2,
            uinput.BTN_BASE3, uinput.BTN_BASE4, uinput.BTN_BASE5, uinput.BTN_BASE6,
            uinput.BTN_DEAD, uinput.BTN_A, uinput.BTN_B, uinput.BTN_C
        ]
        
        events = []
        for i in range(min(self.button_count, len(button_events))):
            events.append(button_events[i])
            self._button_states[i + 1] = False
        
        return events

    def _create_hat_events(self) -> list:
        """Create hat switch (D-pad) event definitions.
        
        Returns:
            List of hat event tuples
        """
        hat_events = [
            (uinput.ABS_HAT0X, (-1, 1, 0, 0)),
            (uinput.ABS_HAT0Y, (-1, 1, 0, 0)),
            (uinput.ABS_HAT1X, (-1, 1, 0, 0)), 
            (uinput.ABS_HAT1Y, (-1, 1, 0, 0)),
        ]
        
        events = []
        for i in range(min(self.hat_count * 2, len(hat_events))):
            events.append(hat_events[i])
        
        for i in range(self.hat_count):
            self._hat_states[i + 1] = (0, 0)
        
        return events

    def _create_uinput_device(self, events: list) -> None:
        """Create the uinput device with specified events.
        
        Args:
            events: List of event definitions
        """
        self._device = uinput.Device(events, name=self.name)
        _register_device(self)
        
        # Small delay to let the device initialize
        time.sleep(0.1)
        
        self._logger.info(f"Created virtual device: {self.name} (ID: {self.device_id})")

    def create(self) -> None:
        """Create the virtual device."""
        if self._device:
            return
        
        try:
            self._check_uinput_permissions()
            
            # Gather all event definitions
            events = []
            events.extend(self._create_axis_events())
            events.extend(self._create_button_events())
            events.extend(self._create_hat_events())
            
            # Create the virtual device
            self._create_uinput_device(events)
            
        except Exception as e:
            self._logger.error(f"Failed to create virtual device: {e}")
            raise UInputError(f"Failed to create virtual device: {e}")
    
    def destroy(self) -> None:
        """Destroy the virtual device."""
        if self._device:
            try:
                self._device.destroy()
                self._device = None
                self._logger.info(f"Destroyed virtual device: {self.name}")
            except Exception as e:
                self._logger.error(f"Error destroying virtual device: {e}")
    
    def set_axis(self, axis_id: int, value: float) -> None:
        """
        Set axis value.
        
        Args:
            axis_id: Axis ID (1-based)
            value: Axis value in range [-1.0, 1.0]
        """
        if not self._device:
            return
        
        if axis_id < 1 or axis_id > self.axis_count:
            return
        
        try:
            # Clamp value to valid range
            value = max(-1.0, min(1.0, value))
            self._axis_values[axis_id] = value
            
            # Convert to uinput range (-32768 to 32767)
            raw_value = int(value * 32767)
            
            # Map axis ID to uinput axis
            axis_mapping = {
                1: uinput.ABS_X,
                2: uinput.ABS_Y,
                3: uinput.ABS_Z,
                4: uinput.ABS_RX,
                5: uinput.ABS_RY,
                6: uinput.ABS_RZ,
                7: uinput.ABS_THROTTLE,
                8: uinput.ABS_RUDDER
            }
            
            if axis_id in axis_mapping:
                self._device.emit(axis_mapping[axis_id], raw_value)
                self._device.syn()
                
        except Exception as e:
            self._logger.error(f"Error setting axis {axis_id}: {e}")
    
    def set_button(self, button_id: int, pressed: bool) -> None:
        """
        Set button state.
        
        Args:
            button_id: Button ID (1-based)
            pressed: Button pressed state
        """
        if not self._device:
            return
        
        if button_id < 1 or button_id > self.button_count:
            return
        
        try:
            self._button_states[button_id] = pressed
            
            # Map button ID to uinput button
            button_mapping = {
                1: uinput.BTN_JOYSTICK,
                2: uinput.BTN_THUMB,
                3: uinput.BTN_THUMB2,
                4: uinput.BTN_TOP,
                5: uinput.BTN_TOP2,
                6: uinput.BTN_PINKIE,
                7: uinput.BTN_BASE,
                8: uinput.BTN_BASE2,
                9: uinput.BTN_BASE3,
                10: uinput.BTN_BASE4,
                11: uinput.BTN_BASE5,
                12: uinput.BTN_BASE6,
                13: uinput.BTN_DEAD,
                14: uinput.BTN_A,
                15: uinput.BTN_B,
                16: uinput.BTN_C
            }
            
            if button_id in button_mapping:
                self._device.emit(button_mapping[button_id], 1 if pressed else 0)
                self._device.syn()
                
        except Exception as e:
            self._logger.error(f"Error setting button {button_id}: {e}")
    
    def set_hat(self, hat_id: int, direction: Tuple[int, int]) -> None:
        """
        Set hat switch direction.
        
        Args:
            hat_id: Hat ID (1-based)
            direction: Hat direction as (x, y) tuple where values are -1, 0, or 1
        """
        if not self._device:
            return
        
        if hat_id < 1 or hat_id > self.hat_count:
            return
        
        try:
            x, y = direction
            x = max(-1, min(1, x))
            y = max(-1, min(1, y))
            
            self._hat_states[hat_id] = (x, y)
            
            # Map hat ID to uinput hat axes
            if hat_id == 1:
                self._device.emit(uinput.ABS_HAT0X, x)
                self._device.emit(uinput.ABS_HAT0Y, y)
            elif hat_id == 2:
                self._device.emit(uinput.ABS_HAT1X, x)
                self._device.emit(uinput.ABS_HAT1Y, y)
            
            self._device.syn()
            
        except Exception as e:
            self._logger.error(f"Error setting hat {hat_id}: {e}")
    
    def reset(self) -> None:
        """Reset all axes, buttons, and hats to default state."""
        if not self._device:
            return
        
        try:
            # Reset axes to center
            for axis_id in range(1, self.axis_count + 1):
                self.set_axis(axis_id, 0.0)
            
            # Reset buttons to unpressed
            for button_id in range(1, self.button_count + 1):
                self.set_button(button_id, False)
            
            # Reset hats to center
            for hat_id in range(1, self.hat_count + 1):
                self.set_hat(hat_id, (0, 0))
                
            self._logger.debug(f"Reset virtual device: {self.name}")
            
        except Exception as e:
            self._logger.error(f"Error resetting virtual device: {e}")
    
    def get_device_summary(self) -> DeviceSummary:
        """Get device summary for this virtual device."""
        # Create axis map
        axis_map = []
        for i in range(1, self.axis_count + 1):
            axis_map.append(AxisMap(axis_index=i, axis_id=i))
        
        return DeviceSummary(
            device_guid=self.device_guid,
            name=self.name,
            vendor_id=0x1234,  # Virtual vendor ID
            product_id=0xBEAD,  # Virtual product ID
            axis_count=self.axis_count,
            button_count=self.button_count,
            hat_count=self.hat_count,
            axis_map=axis_map,
            is_virtual=True,
            vjoy_id=self.device_id,
            device_path=f"/dev/input/virtual{self.device_id}"
        )


class LinuxVirtualDeviceManager:
    """
    Manages multiple virtual devices.
    Replaces vJoy functionality on Linux.
    """
    
    def __init__(self):
        """Initialize the virtual device manager."""
        self._devices: Dict[int, LinuxVirtualDevice] = {}
        self._logger = logging.getLogger(__name__)
        self._logger.info("LinuxVirtualDeviceManager initialized")
    
    def create_device(self, device_id: int, name: str = None,
                     axis_count: int = 8, button_count: int = 16, hat_count: int = 1) -> LinuxVirtualDevice:
        """
        Create a virtual device.
        
        Args:
            device_id: Unique device ID
            name: Device name
            axis_count: Number of axes
            button_count: Number of buttons
            hat_count: Number of hats
            
        Returns:
            Created virtual device
        """
        if device_id in self._devices:
            raise UInputError(f"Virtual device {device_id} already exists")
        
        device = LinuxVirtualDevice(device_id, name, axis_count, button_count, hat_count)
        device.create()
        
        self._devices[device_id] = device
        self._logger.info(f"Created virtual device {device_id}: {device.name}")
        
        return device
    
    def get_device(self, device_id: int) -> Optional[LinuxVirtualDevice]:
        """Get virtual device by ID."""
        return self._devices.get(device_id)
    
    def device_exists(self, device_id: int) -> bool:
        """Check if virtual device exists."""
        return device_id in self._devices
    
    def destroy_device(self, device_id: int) -> None:
        """Destroy a virtual device."""
        if device_id in self._devices:
            device = self._devices.pop(device_id)
            device.destroy()
            self._logger.info(f"Destroyed virtual device {device_id}")
    
    def destroy_all(self) -> None:
        """Destroy all virtual devices."""
        for device_id in list(self._devices.keys()):
            self.destroy_device(device_id)
    
    def get_device_summaries(self) -> List[DeviceSummary]:
        """Get device summaries for all virtual devices."""
        summaries = []
        for device in self._devices.values():
            summaries.append(device.get_device_summary())
        return summaries


# Global instance
_virtual_device_manager = None

# Global registry to track all created virtual devices
_virtual_devices = []


def get_virtual_device_manager() -> LinuxVirtualDeviceManager:
    """Get the global virtual device manager instance."""
    global _virtual_device_manager
    if _virtual_device_manager is None:
        _virtual_device_manager = LinuxVirtualDeviceManager()
    return _virtual_device_manager


def cleanup_all_devices():
    """Clean up all virtual devices."""
    global _virtual_devices
    for device in _virtual_devices:
        try:
            device.destroy()
        except Exception as e:
            logger = logging.getLogger("system")
            logger.warning(f"Error cleaning up virtual device: {e}")
    _virtual_devices.clear()


def _register_device(device):
    """Register a virtual device for cleanup."""
    global _virtual_devices
    _virtual_devices.append(device)
