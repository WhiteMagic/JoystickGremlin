# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2021 Lionel Ott
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


from __future__ import annotations

from collections.abc import Callable
import threading
from typing import List, Optional

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, input_devices, keyboard, shared_state, \
    windows_event_hook

from gremlin.types import InputType


QML_IMPORT_NAME = "Gremlin.Util"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class RandomStuff(QtCore.QObject):

    def __init__(self, parent=None):
        super.__init__(parent)
        print("blabla")


@QtQml.QmlElement
class InputListenerModel(QtCore.QObject):

    """Allows recording user inputs with an on-screen prompt."""

    # Signal emitted when the listening for inputs is done to let the UI
    # know the overlay can be removed
    listeningTerminated = Signal()

    inputChanged = Signal(str)
    eventTypesChanged = Signal()

    # def __init__(
    #         self,
    #         callback: Callable[..., None],
    #         event_types: List[InputType],
    #         return_kb_event: bool=False,
    #         multi_keys: bool=False,
    #         filter_func: Optional[Callable[[event_handler.Event], bool]]=None,
    #         parent: Optional[QtCore.QObject]=None
    # ):
    #     """Creates a new instance.

    #     Args:
    #         callback: the function to pass the user input to for processing
    #         event_types: the type of events to react to
    #         return_kb_event: return the keyboard event if True, otherwise the
    #             key information itself is returned
    #         multi_keys: return multiple inputs if True, otherwise only
    #             the first input is returned
    #         filter_func: function applied to input events to perform more
    #             complex input event filtering
    #         parent: the parent widget of this widget
    #     """
    def __init__(self, parent: Optional[QtCore.QObject]=None):
        super().__init__(parent)
 
        self.callback = None
        self._event_types = []
        self._return_kb_event = None
        self._multi_keys = False
        self.filter_func = None

        #self._abort_timer = threading.Timer(1.0, self.close)
        self._multi_key_storage = []

        # Disable ui input selection on joystick input
        shared_state.set_suspend_input_highlighting(True)

    def _get_event_types(self) -> List[str]:
        return [InputType.to_string(v) for v in self._event_types]

    def _set_event_types(self, event_types: List[str]) -> None:
        types = sorted([InputType.to_enum(v) for v in event_types])
        if types != self._event_types:
            self._event_types = types
            self._disconnect_listeners()
            self._connect_listeners()

            self.eventTypesChanged.emit()

    def _get_current_input(self) -> str:
        return f"Nothing"

    def _connect_listeners(self) -> None:
        # Start listening to user inputs
        event_listener = event_handler.EventListener()
        event_listener.keyboard_event.connect(self._kb_event_cb)
        if InputType.JoystickAxis in self._event_types or \
                InputType.JoystickButton in self._event_types or \
                InputType.JoystickHat in self._event_types:
            event_listener.joystick_event.connect(self._joy_event_cb)
        elif InputType.Mouse in self._event_types:
            windows_event_hook.MouseHook().start()
            event_listener.mouse_event.connect(self._mouse_event_cb)
    
    def _disconnect_listeners(self) -> None:
        event_listener = event_handler.EventListener()
        event_listener.keyboard_event.disconnect(self._kb_event_cb)
        event_listener.joystick_event.disconnect(self._joy_event_cb)
        event_listener.mouse_event.disconnect(self._mouse_event_cb)

        # Stop mouse hook in case it is running
        windows_event_hook.MouseHook().stop()

    def _joy_event_cb(self, event: event_handler.Event) -> None:
        """Passes the pressed joystick event to the provided callback.

        This only passes on joystick button presses.

        Args:
            event: the input event to process
        """
        # Ensure input highlighting is turned off, even if input request
        # dialogs are spawned in quick succession
        shared_state.set_suspend_input_highlighting(True)

        # Only react to events we're interested in
        if event.event_type not in self._event_types:
            return
        if self.filter_func is not None and not self.filter_func(event):
            return

        # Ensure the event corresponds to a significant enough change in input
        process_event = input_devices.JoystickInputSignificant() \
            .should_process(event)
        if event.event_type == InputType.JoystickButton:
            process_event &= not event.is_pressed

        if process_event:
            input_devices.JoystickInputSignificant().reset()
            self.callback(event)
            self.listeningTerminated.emit()

    def _kb_event_cb(self, event: event_handler.Event) -> None:
        """Passes the pressed key to the provided callback.

        Args:
            event: the keypress event to be processed
        """
        print("X")
        key = keyboard.key_from_code(
                event.identifier[0],
                event.identifier[1]
        )

        # Return immediately once the first key press is detected
        if not self._multi_keys:
            if event.is_pressed and key == keyboard.key_from_name("esc"):
                if not self._abort_timer.is_alive():
                    self._abort_timer.start()
            elif not event.is_pressed and \
                    InputType.Keyboard in self._event_types:
                if not self._return_kb_event:
                    self.callback(key)
                else:
                    self.callback(event)
                self._abort_timer.cancel()
                self.listeningTerminated.emit()
        # Record all key presses and return on the first key release
        else:
            if event.is_pressed:
                if InputType.Keyboard in self._event_types:
                    if not self._return_kb_event:
                        self._multi_key_storage.append(key)
                    else:
                        self._multi_key_storage.append(event)
                if key == keyboard.key_from_name("esc"):
                    # Start a timer and close if it expires, aborting the
                    # user input request
                    if not self._abort_timer.is_alive():
                        self._abort_timer.start()
            else:
                self._abort_timer.cancel()
                self.callback(self._multi_key_storage)
                self.listeningTerminated.emit()

        # Ensure the timer is cancelled and reset in case the ESC is released
        # and we're not looking to return keyboard events
        if key == keyboard.key_from_name("esc") and not event.is_pressed:
            self._abort_timer.cancel()
            self._abort_timer = threading.Timer(1.0, self.close)

    def _mouse_event_cb(self, event: event_handler.Event) -> None:
        """Passes the pressed mouse input to the provided callback.

        Args:
            event: the mouse event to be processed
        """
        self.callback(event)
        self.listeningTerminated.emit()

    def closeEvent(self, evt):
        # FIXME: we have to call this ourselves as the close event won't
        #        be seen by this anymore
        """Closes the overlay window."""
        event_listener = event_handler.EventListener()
        event_listener.keyboard_event.disconnect(self._kb_event_cb)
        if InputType.JoystickAxis in self._event_types or \
                InputType.JoystickButton in self._event_types or \
                InputType.JoystickHat in self._event_types:
            event_listener.joystick_event.disconnect(self._joy_event_cb)
        elif InputType.Mouse in self._event_types:
            event_listener.mouse_event.disconnect(self._mouse_event_cb)

        # Stop mouse hook in case it is running
        windows_event_hook.MouseHook().stop()

        # Delay un-suspending input highlighting to allow an axis that's being
        # moved to return to its center without triggering an input highlight
        shared_state.delayed_input_highlighting_suspension()
        super().closeEvent(evt)

    def _valid_event_types_string(self):
        """Returns a formatted string containing the valid event types.

        :return string representing the valid event types
        """
        valid_str = []
        if InputType.JoystickAxis in self._event_types:
            valid_str.append("Axis")
        if InputType.JoystickButton in self._event_types:
            valid_str.append("Button")
        if InputType.JoystickHat in self._event_types:
            valid_str.append("Hat")
        if InputType.Keyboard in self._event_types:
            valid_str.append("Key")

        return ", ".join(valid_str)

    currentInput = Property(
        str,
        fget=_get_current_input,
        notify=inputChanged
    )

    eventTypes = Property(
        list,
        fget=_get_event_types,
        fset=_set_event_types,
        notify=eventTypesChanged
    )