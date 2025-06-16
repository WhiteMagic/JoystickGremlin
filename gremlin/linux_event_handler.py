# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
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
Linux-native event handling for Joystick Gremlin.

This module provides a complete Linux replacement for the Windows-specific
event handling system, using the linput backend for all input/output.
"""

from __future__ import annotations

import functools
import inspect
import logging
import time
from threading import Thread, Timer
from typing import Any, Callable, List, TYPE_CHECKING
import uuid

from PySide6 import QtCore

import linput

from gremlin import common, config, device_initialization, error, keyboard, \
    mode_manager, util, shared_state, tree
from gremlin.input_cache import Joystick, Keyboard
from gremlin.types import InputType


if TYPE_CHECKING:
    from gremlin.base_classes import Value
    from gremlin.code_runner import CallbackObject


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
    """

    def __init__(
            self,
            event_type: InputType,
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

    def display_name(self) -> str:
        """Returns the display representation of this event.

        Returns:
            Textual representation of the event's input
        """
        # Retrieve the device instance belonging to this event
        device = None
        for dev in device_initialization.joystick_devices():
            if dev.device_guid == self.device_guid:
                device = dev
                break

        if device is None:
            # Handle keyboard events
            if self.device_guid == linput.GUID_Keyboard:
                return keyboard.key_from_code(
                    self.identifier[0],
                    self.identifier[1]
                ).name
            else:
                return "Unknown"

        # Format device input based on type
        if self.event_type == InputType.JoystickAxis:
            return f"{device.name} Axis {self.identifier}"
        elif self.event_type == InputType.JoystickButton:
            return f"{device.name} Button {self.identifier}"
        elif self.event_type == InputType.JoystickHat:
            return f"{device.name} Hat {self.identifier}"
        else:
            return "Unknown"

    def clone(self):
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


@common.SingletonDecorator
class EventListener(QtCore.QObject):
    """Listens for input events and dispatches them to registered callbacks."""

    # Signals for device and profile changes
    device_change_event = QtCore.Signal()
    profile_change_event = QtCore.Signal()
    mode_change_event = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("system")
        self._callbacks = []
        self._keyboard_callbacks = []
        self._is_running = False
        self._thread = None

        # Linux input managers
        self._device_manager = None
        self._keyboard_mouse_manager = None

    def start(self):
        """Start listening for input events."""
        if self._is_running:
            return

        self._logger.info("Starting Linux event listener")
        
        try:
            # Get Linux input managers
            self._device_manager = linput.get_device_manager()
            self._keyboard_mouse_manager = linput.get_keyboard_mouse_manager()

            # Register device callbacks
            self._device_manager.register_input_callback(self._joystick_event_handler)
            self._device_manager.register_device_callback(self._joystick_device_handler)

            # Register keyboard/mouse callbacks
            self._keyboard_mouse_manager.register_input_callback(self._keyboard_event_handler)

            self._is_running = True
            self._logger.info("Linux event listener started successfully")

        except Exception as e:
            self._logger.error(f"Failed to start event listener: {e}")
            raise

    def terminate(self):
        """Stop listening for input events."""
        if not self._is_running:
            return

        self._logger.info("Terminating Linux event listener")
        
        try:
            # Unregister callbacks if managers exist
            if self._device_manager:
                self._device_manager.unregister_input_callback(self._joystick_event_handler)
                self._device_manager.unregister_device_callback(self._joystick_device_handler)

            if self._keyboard_mouse_manager:
                self._keyboard_mouse_manager.unregister_input_callback(self._keyboard_event_handler)

            self._is_running = False
            self._device_manager = None
            self._keyboard_mouse_manager = None
            
            self._logger.info("Linux event listener terminated")

        except Exception as e:
            self._logger.error(f"Error terminating event listener: {e}")

    def _joystick_event_handler(self, event: linput.InputEvent) -> None:
        """Handle joystick input events from Linux backend."""
        try:
            # Convert Linux input event to Gremlin Event
            if event.input_type == linput.InputType.Axis:
                gremlin_event = Event(
                    event_type=InputType.JoystickAxis,
                    identifier=event.code,
                    device_guid=event.device_guid,
                    mode=mode_manager.ModeManager().get_current_mode(),
                    value=event.value,
                    raw_value=event.raw_value
                )
            elif event.input_type == linput.InputType.Button:
                gremlin_event = Event(
                    event_type=InputType.JoystickButton,
                    identifier=event.code,
                    device_guid=event.device_guid,
                    mode=mode_manager.ModeManager().get_current_mode(),
                    is_pressed=event.value > 0
                )
            elif event.input_type == linput.InputType.Hat:
                gremlin_event = Event(
                    event_type=InputType.JoystickHat,
                    identifier=event.code,
                    device_guid=event.device_guid,
                    mode=mode_manager.ModeManager().get_current_mode(),
                    value=(event.value, event.raw_value)  # (x, y) tuple
                )
            else:
                return  # Unknown event type

            # Dispatch to registered callbacks
            self._process_event(gremlin_event)

        except Exception as e:
            self._logger.error(f"Error processing joystick event: {e}")

    def _joystick_device_handler(self, device: linput.DeviceSummary, action: str) -> None:
        """Handle joystick device changes from Linux backend."""
        try:
            if action in ["added", "removed"]:
                self._logger.info(f"Device {action}: {device.name}")
                # Refresh device list
                device_initialization.joystick_devices_initialization()
                # Emit device change signal
                self.device_change_event.emit()
        except Exception as e:
            self._logger.error(f"Error processing device change: {e}")

    def _keyboard_event_handler(self, event: linput.InputEvent) -> None:
        """Handle keyboard input events from Linux backend."""
        try:
            # Convert to Gremlin keyboard event
            if event.input_type == linput.InputType.Key:
                gremlin_event = Event(
                    event_type=InputType.Keyboard,
                    identifier=(event.code, event.raw_value),  # (scan_code, extended)
                    device_guid=linput.GUID_Keyboard,
                    mode=mode_manager.ModeManager().get_current_mode(),
                    is_pressed=event.value > 0
                )
                
                # Dispatch to keyboard callbacks
                self._process_keyboard_event(gremlin_event)

        except Exception as e:
            self._logger.error(f"Error processing keyboard event: {e}")

    def _process_event(self, event: Event) -> None:
        """Process a joystick event by dispatching it to callbacks."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Error in event callback: {e}")

    def _process_keyboard_event(self, event: Event) -> None:
        """Process a keyboard event by dispatching it to callbacks."""
        for callback in self._keyboard_callbacks:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Error in keyboard callback: {e}")

    def register_callback(self, callback: Callable[[Event], None]) -> None:
        """Register a callback for joystick events.
        
        Args:
            callback: Function to call when a joystick event occurs
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[Event], None]) -> None:
        """Unregister a joystick event callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def register_keyboard_callback(self, callback: Callable[[Event], None]) -> None:
        """Register a callback for keyboard events.
        
        Args:
            callback: Function to call when a keyboard event occurs
        """
        if callback not in self._keyboard_callbacks:
            self._keyboard_callbacks.append(callback)

    def unregister_keyboard_callback(self, callback: Callable[[Event], None]) -> None:
        """Unregister a keyboard event callback.
        
        Args:
            callback: Function to remove from keyboard callbacks
        """
        if callback in self._keyboard_callbacks:
            self._keyboard_callbacks.remove(callback)
