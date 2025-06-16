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
Linux Keyboard and Mouse Manager

Handles keyboard and mouse input/output using pynput for Linux systems.
"""

import logging
import time
from typing import Callable, Optional

import pynput
import pynput.keyboard
import pynput.mouse

from .types import (
    InputType,
    InputEvent,
    UUID_Keyboard,
    UUID_Mouse
)


class KeyboardMouseManager:
    """
    Manages keyboard and mouse input/output on Linux.
    """
    
    def __init__(self):
        """Initialize the keyboard/mouse manager."""
        self._running = False
        
        # Input listeners
        self._keyboard_listener: Optional[pynput.keyboard.Listener] = None
        self._mouse_listener: Optional[pynput.mouse.Listener] = None
        
        # Output controllers
        self._keyboard_controller = pynput.keyboard.Controller()
        self._mouse_controller = pynput.mouse.Controller()
        
        # Event callback
        self._input_event_callback: Optional[Callable[[InputEvent], None]] = None
        
        self._logger = logging.getLogger(__name__)
        self._logger.info("LinuxKeyboardMouseManager initialized")
    
    def start(self) -> None:
        """Start keyboard and mouse monitoring."""
        if self._running:
            return
        
        self._running = True
        
        # Start keyboard listener
        self._keyboard_listener = pynput.keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._keyboard_listener.start()
        
        # Start mouse listener  
        self._mouse_listener = pynput.mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self._mouse_listener.start()
        
        self._logger.info("Keyboard and mouse monitoring started")
    
    def stop(self) -> None:
        """Stop keyboard and mouse monitoring."""
        if not self._running:
            return
        
        self._running = False
        
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        
        self._logger.info("Keyboard and mouse monitoring stopped")
    
    def register_input_callback(self, callback: Callable[[InputEvent], None]) -> None:
        """Register a callback to be called when input events occur.
        
        Args:
            callback: Function to call with InputEvent when events occur
        """
        self._input_event_callback = callback
        self._logger.debug("Input event callback registered")
    
    def unregister_input_callback(self, callback: Callable[[InputEvent], None]) -> None:
        """Unregister a previously registered input callback.
        
        Args:
            callback: Function to remove from callback list
        """
        if self._input_event_callback == callback:
            self._input_event_callback = None
            self._logger.debug("Input event callback unregistered")
    
    def _on_key_press(self, key) -> None:
        """Handle key press events."""
        if self._input_event_callback:
            try:
                # Convert pynput key to our format
                key_id = self._convert_key_to_id(key)
                if key_id is not None:
                    event = InputEvent(
                        device_guid=UUID_Keyboard,
                        input_type=InputType.Key,
                        code=key_id,
                        value=True,
                        is_pressed=True
                    )
                    self._input_event_callback(event)
            except Exception as e:
                self._logger.error(f"Error handling key press: {e}")
    
    def _on_key_release(self, key) -> None:
        """Handle key release events."""
        if self._input_event_callback:
            try:
                # Convert pynput key to our format
                key_id = self._convert_key_to_id(key)
                if key_id is not None:
                    event = InputEvent(
                        device_guid=UUID_Keyboard,
                        input_type=InputType.Key,
                        code=key_id,
                        value=False,
                        is_pressed=False
                    )
                    self._input_event_callback(event)
            except Exception as e:
                self._logger.error(f"Error handling key release: {e}")
    
    def _on_mouse_click(self, x, y, button, pressed) -> None:
        """Handle mouse click events."""
        if self._input_event_callback:
            try:
                button_id = self._convert_mouse_button_to_id(button)
                if button_id is not None:
                    event = InputEvent(
                        device_guid=UUID_Mouse,
                        input_type=InputType.Mouse,
                        code=button_id,
                        value=pressed,
                        is_pressed=pressed
                    )
                    self._input_event_callback(event)
            except Exception as e:
                self._logger.error(f"Error handling mouse click: {e}")
    
    def _on_mouse_scroll(self, x, y, dx, dy) -> None:
        """Handle mouse scroll events."""
        if self._input_event_callback:
            try:
                # Handle scroll up
                if dy > 0:
                    event = InputEvent(
                        device_guid=UUID_Mouse,
                        input_type=InputType.Mouse,
                        code=4,  # Scroll up
                        value=dy,
                        is_pressed=True
                    )
                    self._input_event_callback(event)
                # Handle scroll down
                elif dy < 0:
                    event = InputEvent(
                        device_guid=UUID_Mouse,
                        input_type=InputType.Mouse,
                        code=5,  # Scroll down
                        value=abs(dy),
                        is_pressed=True
                    )
                    self._input_event_callback(event)
            except Exception as e:
                self._logger.error(f"Error handling mouse scroll: {e}")
    
    def _convert_key_to_id(self, key) -> Optional[int]:
        """Convert pynput key to internal key ID."""
        try:
            # Handle special keys
            if hasattr(key, 'vk'):
                return key.vk
            elif hasattr(key, 'char') and key.char:
                # Convert character to ASCII/scan code
                return ord(key.char.upper())
            else:
                # Handle named keys
                key_name = str(key).replace("Key.", "")
                return self._get_named_key_id(key_name)
        except Exception:
            return None
    
    def _get_named_key_id(self, key_name: str) -> Optional[int]:
        """Get ID for named keys."""
        named_keys = {
            'space': 32,
            'enter': 13,
            'tab': 9,
            'backspace': 8,
            'delete': 127,
            'esc': 27,
            'shift': 16,
            'ctrl': 17,
            'alt': 18,
            'up': 38,
            'down': 40,
            'left': 37,
            'right': 39,
            'home': 36,
            'end': 35,
            'page_up': 33,
            'page_down': 34,
            'f1': 112, 'f2': 113, 'f3': 114, 'f4': 115,
            'f5': 116, 'f6': 117, 'f7': 118, 'f8': 119,
            'f9': 120, 'f10': 121, 'f11': 122, 'f12': 123,
        }
        return named_keys.get(key_name.lower())
    
    def _convert_mouse_button_to_id(self, button) -> Optional[int]:
        """Convert pynput mouse button to internal button ID."""
        button_map = {
            pynput.mouse.Button.left: 1,
            pynput.mouse.Button.right: 2,
            pynput.mouse.Button.middle: 3,
        }
        return button_map.get(button)
    
    # Output methods
    def send_key_press(self, key_code: int) -> None:
        """Send a key press event."""
        try:
            key = self._convert_id_to_key(key_code)
            if key:
                self._keyboard_controller.press(key)
        except Exception as e:
            self._logger.error(f"Error sending key press: {e}")
    
    def send_key_release(self, key_code: int) -> None:
        """Send a key release event."""
        try:
            key = self._convert_id_to_key(key_code)
            if key:
                self._keyboard_controller.release(key)
        except Exception as e:
            self._logger.error(f"Error sending key release: {e}")
    
    def send_key_combination(self, *key_codes: int) -> None:
        """Send a key combination (like Ctrl+C)."""
        keys = []
        for code in key_codes:
            key = self._convert_id_to_key(code)
            if key:
                keys.append(key)
        
        if keys:
            with self._keyboard_controller.pressed(*keys[:-1]):
                self._keyboard_controller.press(keys[-1])
                self._keyboard_controller.release(keys[-1])
    
    def send_text(self, text: str) -> None:
        """Type text string."""
        try:
            self._keyboard_controller.type(text)
        except Exception as e:
            self._logger.error(f"Error sending text: {e}")
    
    def send_mouse_click(self, button: int, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Send a mouse click."""
        try:
            if x is not None and y is not None:
                self._mouse_controller.position = (x, y)
                time.sleep(0.01)  # Small delay to ensure position is set
            
            mouse_button = self._convert_id_to_mouse_button(button)
            if mouse_button:
                self._mouse_controller.click(mouse_button)
        except Exception as e:
            self._logger.error(f"Error sending mouse click: {e}")
    
    def send_mouse_move(self, x: int, y: int) -> None:
        """Move mouse to absolute position."""
        try:
            self._mouse_controller.position = (x, y)
        except Exception as e:
            self._logger.error(f"Error moving mouse: {e}")
    
    def send_mouse_scroll(self, dx: int, dy: int) -> None:
        """Send mouse scroll."""
        try:
            self._mouse_controller.scroll(dx, dy)
        except Exception as e:
            self._logger.error(f"Error sending mouse scroll: {e}")
    
    def _convert_id_to_key(self, key_id: int):
        """Convert internal key ID to pynput key."""
        # Handle ASCII characters
        if 32 <= key_id <= 126:
            return chr(key_id).lower()
        
        # Handle special keys
        special_keys = {
            13: pynput.keyboard.Key.enter,
            9: pynput.keyboard.Key.tab,
            8: pynput.keyboard.Key.backspace,
            127: pynput.keyboard.Key.delete,
            27: pynput.keyboard.Key.esc,
            16: pynput.keyboard.Key.shift,
            17: pynput.keyboard.Key.ctrl,
            18: pynput.keyboard.Key.alt,
            38: pynput.keyboard.Key.up,
            40: pynput.keyboard.Key.down,
            37: pynput.keyboard.Key.left,
            39: pynput.keyboard.Key.right,
            36: pynput.keyboard.Key.home,
            35: pynput.keyboard.Key.end,
            33: pynput.keyboard.Key.page_up,
            34: pynput.keyboard.Key.page_down,
            112: pynput.keyboard.Key.f1, 113: pynput.keyboard.Key.f2,
            114: pynput.keyboard.Key.f3, 115: pynput.keyboard.Key.f4,
            116: pynput.keyboard.Key.f5, 117: pynput.keyboard.Key.f6,
            118: pynput.keyboard.Key.f7, 119: pynput.keyboard.Key.f8,
            120: pynput.keyboard.Key.f9, 121: pynput.keyboard.Key.f10,
            122: pynput.keyboard.Key.f11, 123: pynput.keyboard.Key.f12,
        }
        return special_keys.get(key_id)
    
    def _convert_id_to_mouse_button(self, button_id: int) -> Optional[pynput.mouse.Button]:
        """Convert internal button ID to pynput mouse button."""
        button_map = {
            1: pynput.mouse.Button.left,
            2: pynput.mouse.Button.right,
            3: pynput.mouse.Button.middle,
        }
        return button_map.get(button_id)
