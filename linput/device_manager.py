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
Linux Input Device Manager

Pure Linux implementation for managing input devices using evdev and pyudev.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

import evdev
import pyudev

from .types import (
    InputEvent,
    DeviceSummary, 
    InputType,
    DeviceActionType,
    AxisMap,
    UUID_KEYBOARD,
    UUID_VIRTUAL
)


class EvdevInputError(Exception):
    """Exception raised when an error occurs in the input system."""
    
    def __init__(self, message: str):
        super().__init__(message)


class EvdevInputManager:
    """
    Linux Input Manager using evdev
    
    Manages joystick/gamepad input devices on Linux using the evdev library.
    """
    
    def __init__(self):
        """Initialize the input manager."""
        self._devices: Dict[str, evdev.InputDevice] = {}
        self._device_summaries: List[DeviceSummary] = []
        self._device_paths: Dict[uuid.UUID, str] = {}
        
        # Event callbacks
        self._input_event_callback: Optional[Callable[[InputEvent], None]] = None
        self._device_change_callback: Optional[Callable[[DeviceSummary, DeviceActionType], None]] = None
        
        # Threading for device monitoring and event processing
        self._monitor_thread: Optional[threading.Thread] = None
        self._event_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Device monitoring with udev
        self._udev_context = pyudev.Context()
        self._udev_monitor = pyudev.Monitor.from_netlink(self._udev_context)
        self._udev_monitor.filter_by(subsystem='input')
        
        self._logger = logging.getLogger(__name__)
        self._logger.info("EvdevInputManager initialized")
    
    def start(self) -> None:
        """Start the input manager."""
        if self._running:
            return
        
        self._logger.info("Starting input manager...")
        self._scan_devices()
        self._start_monitoring()
        self._running = True
        self._logger.info("Input manager started")
    
    def stop(self) -> None:
        """Stop the input manager."""
        if not self._running:
            return
        
        self._logger.info("Stopping input manager...")
        self._running = False
        self._stop_monitoring()
        self._close_all_devices()
        self._logger.info("Input manager stopped")
    
    def get_device_count(self) -> int:
        """Get the number of detected joystick devices."""
        return len(self._device_summaries)
    
    def get_devices(self) -> List[DeviceSummary]:
        """Get all detected devices."""
        return self._device_summaries.copy()
    
    def get_device_by_index(self, index: int) -> DeviceSummary:
        """Get device by index."""
        if 0 <= index < len(self._device_summaries):
            return self._device_summaries[index]
        raise EvdevInputError(f"Invalid device index: {index}")
    
    def get_device_by_guid(self, device_guid: uuid.UUID) -> DeviceSummary:
        """Get device by GUID."""
        for device in self._device_summaries:
            if device.device_guid == device_guid:
                return device
        raise EvdevInputError(f"Device with GUID {device_guid} not found")
    
    def device_exists(self, device_guid: uuid.UUID) -> bool:
        """Check if device exists."""
        try:
            self.get_device_by_guid(device_guid)
            return True
        except EvdevInputError:
            return False
    
    def set_input_event_callback(self, callback: Callable[[InputEvent], None]) -> None:
        """Set callback for input events."""
        self._input_event_callback = callback
    
    def set_device_change_callback(self, callback: Callable[[DeviceSummary, DeviceActionType], None]) -> None:
        """Set callback for device changes."""
        self._device_change_callback = callback
    
    def _scan_devices(self) -> None:
        """Scan for available joystick devices."""
        self._device_summaries.clear()
        self._devices.clear()
        self._device_paths.clear()
        
        device_paths = evdev.list_devices()
        self._logger.debug(f"Found {len(device_paths)} input devices")
        
        for device_path in device_paths:
            try:
                device = evdev.InputDevice(device_path)
                if self._is_joystick_device(device):
                    summary = self._create_device_summary(device)
                    if summary:
                        self._device_summaries.append(summary)
                        self._devices[device_path] = device
                        self._device_paths[summary.device_guid] = device_path
                        
                        self._logger.info(f"Added joystick: {summary.name} ({summary.device_guid})")
                else:
                    device.close()
                        
            except (OSError, PermissionError) as e:
                self._logger.warning(f"Cannot access device {device_path}: {e}")
                continue
        
        self._logger.info(f"Found {len(self._device_summaries)} joystick devices")
    
    def _is_joystick_device(self, device: evdev.InputDevice) -> bool:
        """Check if device is a joystick/gamepad."""
        caps = device.capabilities()
        
        # Must have key or absolute axis capabilities
        has_abs = evdev.ecodes.EV_ABS in caps
        has_key = evdev.ecodes.EV_KEY in caps
        
        if not (has_abs or has_key):
            return False
        
        # Check for joystick-specific axes
        if has_abs:
            abs_axes = caps.get(evdev.ecodes.EV_ABS, [])
            joystick_axes = {
                evdev.ecodes.ABS_X, evdev.ecodes.ABS_Y,
                evdev.ecodes.ABS_RX, evdev.ecodes.ABS_RY,
                evdev.ecodes.ABS_Z, evdev.ecodes.ABS_RZ,
                evdev.ecodes.ABS_HAT0X, evdev.ecodes.ABS_HAT0Y,
                evdev.ecodes.ABS_THROTTLE, evdev.ecodes.ABS_RUDDER
            }
            if any(axis in abs_axes for axis in joystick_axes):
                return True
        
        # Check for joystick/gamepad buttons
        if has_key:
            key_codes = caps.get(evdev.ecodes.EV_KEY, [])
            # Check for joystick buttons
            joystick_btns = set(range(evdev.ecodes.BTN_JOYSTICK, evdev.ecodes.BTN_JOYSTICK + 16))
            gamepad_btns = set(range(evdev.ecodes.BTN_GAMEPAD, evdev.ecodes.BTN_GAMEPAD + 16))
            if any(btn in key_codes for btn in (joystick_btns | gamepad_btns)):
                return True
        
        return False
    
    def _create_device_summary(self, device: evdev.InputDevice) -> Optional[DeviceSummary]:
        """Create device summary from evdev device."""
        try:
            caps = device.capabilities()
            
            # Generate deterministic UUID from device info
            device_info = f"{device.info.vendor:04x}:{device.info.product:04x}:{device.name}:{device.path}"
            device_uuid = uuid.uuid5(uuid.NAMESPACE_OID, device_info)
            
            # Map and count axes
            axis_count = 0
            axis_map = []
            if evdev.ecodes.EV_ABS in caps:
                abs_axes = caps[evdev.ecodes.EV_ABS]
                
                # Standard joystick axis mapping
                standard_axes = {
                    evdev.ecodes.ABS_X: 1,      # Left stick X
                    evdev.ecodes.ABS_Y: 2,      # Left stick Y  
                    evdev.ecodes.ABS_Z: 3,      # Left trigger
                    evdev.ecodes.ABS_RX: 4,     # Right stick X
                    evdev.ecodes.ABS_RY: 5,     # Right stick Y
                    evdev.ecodes.ABS_RZ: 6,     # Right trigger
                    evdev.ecodes.ABS_THROTTLE: 7,
                    evdev.ecodes.ABS_RUDDER: 8,
                    evdev.ecodes.ABS_WHEEL: 9,
                    evdev.ecodes.ABS_GAS: 10,
                    evdev.ecodes.ABS_BRAKE: 11,
                }
                
                for evdev_axis in abs_axes:
                    if evdev_axis in standard_axes:
                        axis_id = standard_axes[evdev_axis]
                        axis_map.append(AxisMap(axis_index=axis_id, axis_id=evdev_axis))
                        axis_count += 1
            
            # Count buttons
            button_count = 0
            if evdev.ecodes.EV_KEY in caps:
                key_codes = caps[evdev.ecodes.EV_KEY]
                # Count joystick and gamepad buttons
                joystick_btns = set(range(evdev.ecodes.BTN_JOYSTICK, evdev.ecodes.BTN_JOYSTICK + 16))
                gamepad_btns = set(range(evdev.ecodes.BTN_GAMEPAD, evdev.ecodes.BTN_GAMEPAD + 16))
                all_game_btns = joystick_btns | gamepad_btns
                button_count = len([btn for btn in key_codes if btn in all_game_btns])
            
            # Count hat switches (D-pads)  
            hat_count = 0
            if evdev.ecodes.EV_ABS in caps:
                abs_axes = caps[evdev.ecodes.EV_ABS]
                hat_axes = [
                    evdev.ecodes.ABS_HAT0X, evdev.ecodes.ABS_HAT0Y,
                    evdev.ecodes.ABS_HAT1X, evdev.ecodes.ABS_HAT1Y,
                    evdev.ecodes.ABS_HAT2X, evdev.ecodes.ABS_HAT2Y,
                    evdev.ecodes.ABS_HAT3X, evdev.ecodes.ABS_HAT3Y
                ]
                # Each hat needs both X and Y, so count pairs
                hat_count = len([axis for axis in abs_axes if axis in hat_axes]) // 2
            
            return DeviceSummary(
                device_guid=device_uuid,
                name=device.name,
                vendor_id=device.info.vendor,
                product_id=device.info.product,
                axis_count=axis_count,
                button_count=button_count,
                hat_count=hat_count,
                axis_map=axis_map,
                is_virtual=False,  # TODO: Detect virtual devices
                device_path=device.path
            )
            
        except Exception as e:
            self._logger.error(f"Failed to create device summary for {device.path}: {e}")
            return None
    
    def _start_monitoring(self) -> None:
        """Start device and event monitoring threads."""
        # Start device change monitoring
        self._monitor_thread = threading.Thread(target=self._monitor_device_changes, daemon=True)
        self._monitor_thread.start()
        
        # Start input event processing  
        self._event_thread = threading.Thread(target=self._process_input_events, daemon=True)
        self._event_thread.start()
        
        self._logger.debug("Started monitoring threads")
    
    def _stop_monitoring(self) -> None:
        """Stop monitoring threads."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        
        if self._event_thread and self._event_thread.is_alive():
            self._event_thread.join(timeout=1.0)
        
        self._logger.debug("Stopped monitoring threads")
    
    def _monitor_device_changes(self) -> None:
        """Monitor for device connection/disconnection."""
        self._logger.debug("Device change monitoring thread started")
        
        try:
            for device in iter(self._udev_monitor.poll, None):
                if not self._running:
                    break
                
                if device.action in ['add', 'remove'] and device.device_node and 'event' in device.device_node:
                    self._handle_device_change(device)
                    
        except Exception as e:
            self._logger.error(f"Device monitoring error: {e}")
    
    def _handle_device_change(self, udev_device) -> None:
        """Handle device connection/disconnection."""
        try:
            device_path = udev_device.device_node
            
            if udev_device.action == 'add':
                # Give device time to initialize
                time.sleep(0.2)
                
                try:
                    device = evdev.InputDevice(device_path)
                    if self._is_joystick_device(device):
                        summary = self._create_device_summary(device)
                        if summary:
                            self._device_summaries.append(summary)
                            self._devices[device_path] = device
                            self._device_paths[summary.device_guid] = device_path
                            
                            self._logger.info(f"Device connected: {summary.name}")
                            
                            if self._device_change_callback:
                                self._device_change_callback(summary, DeviceActionType.Connected)
                    else:
                        device.close()
                        
                except (OSError, PermissionError) as e:
                    self._logger.warning(f"Cannot access new device {device_path}: {e}")
            
            elif udev_device.action == 'remove':
                if device_path in self._devices:
                    device = self._devices.pop(device_path)
                    device.close()
                    
                    # Find and remove from summaries
                    for i, summary in enumerate(self._device_summaries):
                        if self._device_paths.get(summary.device_guid) == device_path:
                            del self._device_summaries[i]
                            del self._device_paths[summary.device_guid]
                            
                            self._logger.info(f"Device disconnected: {summary.name}")
                            
                            if self._device_change_callback:
                                self._device_change_callback(summary, DeviceActionType.Disconnected)
                            break
                            
        except Exception as e:
            self._logger.warning(f"Error handling device change: {e}")
    
    def _process_input_events(self) -> None:
        """Process input events from all devices."""
        self._logger.debug("Input event processing thread started")
        
        while self._running:
            try:
                if not self._devices:
                    time.sleep(0.1)
                    continue
                
                # Check each device for events
                for device_path, device in list(self._devices.items()):
                    try:
                        event = device.read_one()
                        if event and self._input_event_callback:
                            self._handle_input_event(device, event)
                            
                    except (OSError, IOError):
                        # Device was disconnected
                        self._logger.debug(f"Device {device_path} disconnected during read")
                        if device_path in self._devices:
                            del self._devices[device_path]
                        continue
                
                time.sleep(0.001)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                self._logger.error(f"Input event processing error: {e}")
                time.sleep(0.1)
    
    def _handle_input_event(self, device: evdev.InputDevice, event: evdev.InputEvent) -> None:
        """Handle a single input event."""
        try:
            # Find device summary
            device_summary = None
            for summary in self._device_summaries:
                if self._device_paths.get(summary.device_guid) == device.path:
                    device_summary = summary
                    break
            
            if not device_summary:
                return
            
            # Convert to our InputEvent format
            input_event = self._convert_evdev_event(device_summary, event)
            if input_event and self._input_event_callback:
                self._input_event_callback(input_event)
        
        except Exception as e:
            self._logger.error(f"Error handling input event: {e}")
    
    def _convert_evdev_event(self, device_summary: DeviceSummary, event: evdev.InputEvent) -> Optional[InputEvent]:
        """Convert evdev event to InputEvent."""
        
        if event.type == evdev.ecodes.EV_ABS:
            # Absolute axis event (analog sticks, triggers, etc.)
            axis_mapping = {
                evdev.ecodes.ABS_X: 1,
                evdev.ecodes.ABS_Y: 2,
                evdev.ecodes.ABS_Z: 3,
                evdev.ecodes.ABS_RX: 4,
                evdev.ecodes.ABS_RY: 5,
                evdev.ecodes.ABS_RZ: 6,
                evdev.ecodes.ABS_THROTTLE: 7,
                evdev.ecodes.ABS_RUDDER: 8,
                evdev.ecodes.ABS_WHEEL: 9,
                evdev.ecodes.ABS_GAS: 10,
                evdev.ecodes.ABS_BRAKE: 11,
            }
            
            if event.code in axis_mapping:
                # Regular axis - normalize to [-1.0, 1.0]
                # TODO: Get actual min/max values from device capabilities for proper normalization
                normalized_value = (event.value - 32768) / 32768.0
                normalized_value = max(-1.0, min(1.0, normalized_value))
                
                return InputEvent(
                    device_guid=device_summary.device_guid,
                    input_type=InputType.JoystickAxis,
                    input_id=axis_mapping[event.code],
                    value=normalized_value,
                    raw_value=event.value
                )
            
            elif event.code in {evdev.ecodes.ABS_HAT0X, evdev.ecodes.ABS_HAT0Y,
                               evdev.ecodes.ABS_HAT1X, evdev.ecodes.ABS_HAT1Y,
                               evdev.ecodes.ABS_HAT2X, evdev.ecodes.ABS_HAT2Y,
                               evdev.ecodes.ABS_HAT3X, evdev.ecodes.ABS_HAT3Y}:
                # Hat/D-pad event
                hat_id = (event.code - evdev.ecodes.ABS_HAT0X) // 2 + 1
                
                # For simplicity, return individual X/Y events
                # TODO: Combine X/Y events into single hat direction
                if event.code % 2 == 0:  # X axis
                    return InputEvent(
                        device_guid=device_summary.device_guid,
                        input_type=InputType.JoystickHat,
                        input_id=hat_id,
                        value=(event.value, 0),
                        raw_value=event.value
                    )
                else:  # Y axis
                    return InputEvent(
                        device_guid=device_summary.device_guid,
                        input_type=InputType.JoystickHat,
                        input_id=hat_id,
                        value=(0, event.value),
                        raw_value=event.value
                    )
        
        elif event.type == evdev.ecodes.EV_KEY:
            # Button event
            if (evdev.ecodes.BTN_JOYSTICK <= event.code <= evdev.ecodes.BTN_JOYSTICK + 15 or
                evdev.ecodes.BTN_GAMEPAD <= event.code <= evdev.ecodes.BTN_GAMEPAD + 15):
                
                # Map button codes to button IDs
                if evdev.ecodes.BTN_JOYSTICK <= event.code <= evdev.ecodes.BTN_JOYSTICK + 15:
                    button_id = event.code - evdev.ecodes.BTN_JOYSTICK + 1
                else:
                    button_id = event.code - evdev.ecodes.BTN_GAMEPAD + 1
                
                return InputEvent(
                    device_guid=device_summary.device_guid,
                    input_type=InputType.JoystickButton,
                    input_id=button_id,
                    value=bool(event.value),
                    is_pressed=bool(event.value),
                    raw_value=event.value
                )
        
        return None
    
    def _close_all_devices(self) -> None:
        """Close all open devices."""
        for device in self._devices.values():
            try:
                device.close()
            except Exception as e:
                self._logger.warning(f"Error closing device: {e}")
        
        self._devices.clear()
        self._device_summaries.clear()
        self._device_paths.clear()


# Global instance
_input_manager = None


def get_input_manager() -> EvdevInputManager:
    """Get the global input manager instance."""
    global _input_manager
    if _input_manager is None:
        _input_manager = EvdevInputManager()
    return _input_manager
