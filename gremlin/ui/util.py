# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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

import threading
from typing import Callable, List, Optional, TYPE_CHECKING

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from gremlin import device_helpers, event_handler, keyboard, shared_state, \
    windows_event_hook
from gremlin.types import InputType, MouseButton

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.Util"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class InputListenerModel(QtCore.QObject):

    """Allows recording user inputs with an on-screen prompt."""

    # Signal emitted when the listening for inputs is done to let the UI
    # know the overlay can be removed and emits the recorded inputs
    listeningTerminated = Signal(list)
    # Signal emitted when the listener is activated or deactivated
    enabledChanged = Signal(bool)
    # Signal emitted when the accepted InputTypes change
    eventTypesChanged = Signal()
    # Signal emitted when multiple inputs are accepted or ignored
    multipleInputsChanged = Signal(bool)

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        # List of InputTypes that will be listened to
        self._event_types = []
        # If True more than the first input will be returned
        self._multiple_inputs = False
        # Timer terminating the listening process in various scenarios
        self._abort_timer = threading.Timer(1.0, self._stop_listening)
        # Received inputs
        self._inputs = []
        # Flag indicating whether the listener is active or not
        self._is_enabled = False

    def _get_event_types(self) -> List[str]:
        return [InputType.to_string(v) for v in self._event_types]

    def _set_event_types(self, event_types: List[str]) -> None:
        types = sorted(
            [InputType.to_enum(v) for v in event_types],
            key=lambda v: InputType.to_string(v)
        )
        if types != self._event_types:
            self._event_types = types
            self.eventTypesChanged.emit()

    def _get_current_inputs(self) -> List[event_handler.Event]:
        return self._inputs

    def _get_is_enabled(self) -> bool:
        return self._is_enabled

    def _set_is_enabled(self, is_enabled: bool) -> None:
        if is_enabled != self._is_enabled:
            self._is_enabled = is_enabled
            shared_state.set_suspend_input_highlighting(self._is_enabled)
            if self._is_enabled:
                self._inputs = []
                self._connect_listeners()
            else:
                self._disconnect_listeners()
            self.enabledChanged.emit(self._is_enabled)

    def _get_multiple_inputs(self) -> bool:
        return self._multiple_inputs

    def _set_multiple_inputs(self, value: bool) -> None:
        if value != self._multiple_inputs:
            self._multiple_inputs = value
            self.multipleInputsChanged.emit(self._multiple_inputs)

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
        try:
            event_listener.keyboard_event.disconnect(self._kb_event_cb)
        except RuntimeError as e:
            pass
        try:
            event_listener.joystick_event.disconnect(self._joy_event_cb)
        except RuntimeError as e:
            pass
        try:
            event_listener.mouse_event.disconnect(self._mouse_event_cb)
        except RuntimeError as e:
            pass

        # Stop mouse hook in case it is running
        # FIXME: can this break things?
        windows_event_hook.MouseHook().stop()

    def _stop_listening(self) -> None:
        """Stops all listening activities."""
        self._disconnect_listeners()
        shared_state.delayed_input_highlighting_suspension()
        self.listeningTerminated.emit(self._inputs)

    def _maybe_terminate_listening(self, event: event_handler.Event) -> None:
        """Terminates listening to user input if adequate."""
        # ESC key always triggers the abort timer
        if event.is_pressed and event.event_type == InputType.Keyboard:
            key = keyboard.key_from_code(
                event.identifier[0],
                event.identifier[1]
            )
            if key == keyboard.key_from_name("esc") and \
                    not self._abort_timer.is_alive():
                self._abort_timer = threading.Timer(1.0, self._stop_listening)
                self._abort_timer.start()

        # Only react to events being listened to
        if event.event_type not in self._event_types:
            return

        # Ignore multi event setting for axis and hat events
        if event.event_type in [InputType.JoystickAxis, InputType.JoystickHat]:
            self._inputs = [event]
            self._abort_timer.cancel()
            self.listeningTerminated.emit(self._inputs)

        # Terminate listening if a release event is observed or a mouse wheel
        # is actuated
        wheel_scrolled = event.event_type == InputType.Mouse and \
                event.identifier in [MouseButton.WheelUp, MouseButton.WheelDown]
        if not event.is_pressed or wheel_scrolled:
            self._abort_timer.cancel()
            self.listeningTerminated.emit(self._inputs)

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

        # Ensure the event corresponds to a significant enough change in input
        process_event = \
            device_helpers.JoystickInputSignificant().should_process(event)

        if process_event:
            device_helpers.JoystickInputSignificant().reset()
            if event.event_type == InputType.JoystickButton and event.is_pressed:
                self._inputs.append(event)
            else:
                self._inputs.append(event)
            self._inputs = list(set(self._inputs))
            self._maybe_terminate_listening(event)

    def _kb_event_cb(self, event: event_handler.Event) -> None:
        """Passes the pressed key to the provided callback.

        Args:
            event: the keypress event to be processed
        """
        # Record events as needed
        if event.event_type in self._event_types:
            if self._multiple_inputs:
                if event.is_pressed:
                    self._inputs.append(event)
            else:
                if not event.is_pressed:
                    self._inputs.append(event)
            self._inputs = list(set(self._inputs))
            self._maybe_terminate_listening(event)

        # Ensure the timer is cancelled and reset in case the ESC is released
        # and we're not looking to return keyboard events
        key = keyboard.key_from_code(event.identifier[0], event.identifier[1])
        if key == keyboard.key_from_name("esc") and not event.is_pressed:
            self._abort_timer.cancel()
            self._abort_timer = threading.Timer(1.0, self._stop_listening)
            self._abort_timer.start()

    def _mouse_event_cb(self, event: event_handler.Event) -> None:
        """Passes the pressed mouse input to the provided callback.

        Args:
            event: the mouse event to be processed
        """
        # FIXME: handle multiple input events
        if event not in self._inputs:
            self._inputs.append(event)
        self._maybe_terminate_listening(event)

    currentInput = Property(
        str,
        fget=_get_current_inputs,
        notify=listeningTerminated
    )

    enabled = Property(
        bool,
        fget=_get_is_enabled,
        fset=_set_is_enabled,
        notify=enabledChanged
    )

    multipleInputs = Property(
        bool,
        fget=_get_multiple_inputs,
        fset=_set_multiple_inputs,
        notify=multipleInputsChanged
    )

    eventTypes = Property(
        list,
        fget=_get_event_types,
        fset=_set_event_types,
        notify=eventTypesChanged
    )
