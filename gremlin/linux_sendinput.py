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
Linux SendInput Replacement

Provides Linux-native input sending functionality using the linput backend,
completely replacing the Windows SendInput API.
"""

import logging
import threading
import time
from typing import Optional

import linput
from gremlin.common import SingletonDecorator
from gremlin.event_handler import Event
from gremlin.types import MouseButton


@SingletonDecorator
class LinuxInputSender:
    """Linux-native input sender using linput backend."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._keyboard_mouse_manager = None
        self._send_lock = threading.Lock()

    def _get_manager(self):
        """Get the keyboard/mouse manager, initializing if needed."""
        if self._keyboard_mouse_manager is None:
            try:
                self._keyboard_mouse_manager = linput.get_keyboard_mouse_manager()
            except Exception as e:
                self._logger.error(f"Failed to get keyboard/mouse manager: {e}")
                raise
        return self._keyboard_mouse_manager

    def send_keyboard_event(self, key_code: int, is_pressed: bool, extended: bool = False):
        """Send a keyboard event.
        
        Args:
            key_code: The key code to send
            is_pressed: True for key press, False for key release
            extended: Extended key flag (ignored on Linux)
        """
        with self._send_lock:
            try:
                manager = self._get_manager()
                if is_pressed:
                    manager.send_key_press(key_code)
                else:
                    manager.send_key_release(key_code)
            except Exception as e:
                self._logger.error(f"Failed to send keyboard event: {e}")

    def send_mouse_event(self, button: MouseButton, is_pressed: bool, x: Optional[int] = None, y: Optional[int] = None):
        """Send a mouse event.
        
        Args:
            button: Mouse button to send
            is_pressed: True for button press, False for button release
            x: Optional X coordinate
            y: Optional Y coordinate
        """
        with self._send_lock:
            try:
                manager = self._get_manager()
                
                # Convert MouseButton enum to internal button ID
                button_map = {
                    MouseButton.Left: 1,
                    MouseButton.Right: 2,
                    MouseButton.Middle: 3,
                }
                button_id = button_map.get(button)
                
                if button_id and is_pressed:  # Only handle press events for clicks
                    manager.send_mouse_click(button_id, x, y)
                    
            except Exception as e:
                self._logger.error(f"Failed to send mouse event: {e}")

    def send_mouse_motion(self, x: int, y: int, relative: bool = False):
        """Send mouse motion.
        
        Args:
            x: X coordinate or relative movement
            y: Y coordinate or relative movement
            relative: Whether coordinates are relative (not supported on Linux with pynput)
        """
        with self._send_lock:
            try:
                manager = self._get_manager()
                if not relative:
                    manager.send_mouse_move(x, y)
                else:
                    # For relative movement, we'd need to get current position and add
                    self._logger.warning("Relative mouse movement not fully supported")
                    
            except Exception as e:
                self._logger.error(f"Failed to send mouse motion: {e}")

    def send_mouse_scroll(self, direction: int, clicks: int = 1):
        """Send mouse scroll.
        
        Args:
            direction: Scroll direction (positive = up, negative = down)
            clicks: Number of scroll clicks
        """
        with self._send_lock:
            try:
                manager = self._get_manager()
                # Convert direction to dx, dy for pynput
                dx = 0
                dy = clicks if direction > 0 else -clicks
                manager.send_mouse_scroll(dx, dy)
                
            except Exception as e:
                self._logger.error(f"Failed to send mouse scroll: {e}")

    def send_text(self, text: str):
        """Send text string.
        
        Args:
            text: Text to send
        """
        with self._send_lock:
            try:
                manager = self._get_manager()
                manager.send_text(text)
                
            except Exception as e:
                self._logger.error(f"Failed to send text: {e}")


# Legacy compatibility functions
def send_keyboard_event(key_code: int, is_pressed: bool, extended: bool = False):
    """Legacy function for sending keyboard events."""
    sender = LinuxInputSender()
    sender.send_keyboard_event(key_code, is_pressed, extended)

def send_mouse_event(button: MouseButton, is_pressed: bool, x: Optional[int] = None, y: Optional[int] = None):
    """Legacy function for sending mouse events."""
    sender = LinuxInputSender()
    sender.send_mouse_event(button, is_pressed, x, y)

def send_mouse_motion(x: int, y: int, relative: bool = False):
    """Legacy function for sending mouse motion."""
    sender = LinuxInputSender()
    sender.send_mouse_motion(x, y, relative)

def send_mouse_scroll(direction: int, clicks: int = 1):
    """Legacy function for sending mouse scroll."""
    sender = LinuxInputSender()
    sender.send_mouse_scroll(direction, clicks)

def send_text(text: str):
    """Legacy function for sending text."""
    sender = LinuxInputSender()
    sender.send_text(text)
