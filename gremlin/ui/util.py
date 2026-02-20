# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import threading
from typing import (
    Any,
    List,
    TYPE_CHECKING,
)

from PySide6 import (
    QtCore,
    QtQml,
)

from gremlin import (
    device_helpers,
    event_handler,
    keyboard,
    process_monitor,
    shared_state,
    windows_event_hook,
)
from gremlin.types import (
    InputType,
    HatDirection,
    MouseButton,
)

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.Util"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class InputListenerModel(QtCore.QObject):

    """Allows recording user inputs with an on-screen prompt."""

    # Signal emitted when the listening for inputs is done to let the UI
    # know the overlay can be removed and emits the recorded inputs.
    listeningTerminated = QtCore.Signal(list)
    # Signal emitted when the listener is activated or deactivated.
    enabledChanged = QtCore.Signal(bool)
    # Signal emitted when the accepted InputTypes change.
    eventTypesChanged = QtCore.Signal()
    # Signal emitted when the setting to accept multiple inputs changes.
    multipleInputsChanged = QtCore.Signal(bool)

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        # List of InputTypes that will be listened to.
        self._event_types : list[InputType] = []
        # If True more than the first input will be returned.
        self._multiple_inputs = False
        # Timer terminating the listening process in various scenarios.
        self._abort_timer = threading.Timer(1.0, self._abort_listening)
        # Received inputs while listening.
        self._inputs : list[event_handler.Event] = []
        # Flag indicating whether the listener is active or not.
        self._is_enabled = False

    def _connect_listeners(self) -> None:
        # Start listening to user inputs.
        event_listener = event_handler.EventListener()
        # Keyboard events are always listened to in order to catch the ESC
        # key to abort input listening.
        event_listener.keyboard_event.connect(self._kb_event_cb)
        if InputType.JoystickAxis in self._event_types or \
                InputType.JoystickButton in self._event_types or \
                InputType.JoystickHat in self._event_types:
            event_listener.joystick_event.connect(self._joy_event_cb)
        if InputType.Mouse in self._event_types:
            windows_event_hook.MouseHook().start()
            event_listener.mouse_event.connect(self._mouse_event_cb)

    def _disconnect_listeners(self) -> None:
        event_listener = event_handler.EventListener()
        event_listener.keyboard_event.disconnect(self._kb_event_cb)
        if InputType.JoystickAxis in self._event_types or \
                InputType.JoystickButton in self._event_types or \
                InputType.JoystickHat in self._event_types:
            try:
                event_listener.joystick_event.disconnect(self._joy_event_cb)
            except RuntimeError as e:
                pass
        if InputType.Mouse in self._event_types:
            try:
                event_listener.mouse_event.disconnect(self._mouse_event_cb)
            except RuntimeError as e:
                pass

        # Stop mouse hook in case it is running
        # FIXME: can this break things?
        windows_event_hook.MouseHook().stop()

    def _listening_done(self) -> None:
        """Stops listening and emits the recorded inputs."""
        if self._abort_timer.is_alive():
            self._abort_timer.cancel()
        self._disconnect_listeners()
        self.listeningTerminated.emit(list(set(self._inputs)))

    def _abort_listening(self) -> None:
        """Stops all listening activities."""
        self._disconnect_listeners()
        self.listeningTerminated.emit([])

    def _process_button(self, event: event_handler.Event) -> None:
        # Only react to events we're interested in.
        if event.event_type not in self._event_types:
            return

        # When recording multiple inputs we record them on press, as the first
        # release signals the end of input recording.
        if self._multiple_inputs and event.is_pressed:
            self._inputs.append(event)
        elif self._multiple_inputs and not event.is_pressed:
            self._listening_done()
        # When recording a single input we can terminate listening directly
        # with the first button press.
        elif not self._multiple_inputs and event.is_pressed:
            self._inputs = [event]
            self._listening_done()

    def _process_single_input_only(self, event: event_handler.Event) -> None:
        """Certain inputs do not make sense to be recorded as multiple inputs,
        these cause immediate termination of listening.

        The inputs that fall into this category are:
        - Mouse scroll wheel
        - Joystick axis and hat

        Args:
            event: the input event to process
        """
        self._inputs = [event]
        self._listening_done()

    def _joy_event_cb(self, event: event_handler.Event) -> None:
        """Processes a joystick event.

        Args:
            event: the input event to process
        """
        # Only react to events we're interested in.
        if event.event_type not in self._event_types:
            return

        # Ensure input highlighting is turned off, even if input request
        # dialogs are spawned in quick succession.
        shared_state.set_suspend_input_highlighting(True)

        match event.event_type:
            case InputType.JoystickButton:
                self._process_button(event)
            case InputType.JoystickAxis:
                if device_helpers.JoystickInputSignificant() \
                        .should_process(event):
                    self._process_single_input_only(event)
            case InputType.JoystickHat:
                if event.value != HatDirection.Center:
                    self._process_single_input_only(event)

    def _kb_event_cb(self, event: event_handler.Event) -> None:
        """Processes a keyboard event.

        Args:
            event: the key event to be processed
        """
        # Special handling for the ESC key, to abort listening if it is held.
        is_esc = keyboard.key_from_code(*event.identifier) == \
            keyboard.key_from_name("esc")
        if is_esc:
            if event.is_pressed and not self._abort_timer.is_alive():
                self._abort_timer = \
                    threading.Timer(1.0, self._abort_listening)
                self._abort_timer.start()

            # Avoid processing the ESC key as a regular input if keyboard
            # events are not being listened to.
            if event.event_type not in self._event_types:
                return

            # Standard behavior for multiple inputs case.
            if self._multiple_inputs and event.is_pressed:
                self._inputs.append(event)
            elif self._multiple_inputs and not event.is_pressed:
                self._listening_done()
            # Non-standard behavior, on release rather than press, for single
            # input case.
            elif not self._multiple_inputs and not event.is_pressed:
                self._inputs = [event]
                self._listening_done()
        else:
            self._process_button(event)

    def _mouse_event_cb(self, event: event_handler.Event) -> None:
        """Processes a mouse event.

        Args:
            event: the mouse event to be processed
        """
        # Only react to events we're interested in.
        if event.event_type not in self._event_types:
            return

        if event.identifier in [MouseButton.WheelUp, MouseButton.WheelDown]:
            self._process_single_input_only(event)
        else:
            self._process_button(event)

    def _get_event_types(self) -> list[str]:
        return [InputType.to_string(v) for v in self._event_types]

    def _set_event_types(self, event_types: List[str]) -> None:
        types = sorted(
            [InputType.to_enum(v) for v in event_types],
            key=lambda v: InputType.to_string(v)
        )
        if types != self._event_types:
            self._event_types = types
            self.eventTypesChanged.emit()

    def _get_current_inputs(self) -> list[event_handler.Event]:
        return self._inputs

    def _get_is_enabled(self) -> bool:
        return self._is_enabled

    def _set_is_enabled(self, is_enabled: bool) -> None:
        if is_enabled != self._is_enabled:
            self._is_enabled = is_enabled
            if self._is_enabled:
                shared_state.set_suspend_input_highlighting(self._is_enabled)
                self._inputs = []
                self._connect_listeners()
            else:
                shared_state.set_suspend_input_highlighting_delayed()
            self.enabledChanged.emit(self._is_enabled)

    def _get_multiple_inputs(self) -> bool:
        return self._multiple_inputs

    def _set_multiple_inputs(self, value: bool) -> None:
        if value != self._multiple_inputs:
            self._multiple_inputs = value
            self.multipleInputsChanged.emit(self._multiple_inputs)

    currentInput = QtCore.Property(
        list,
        fget=_get_current_inputs,
        notify=listeningTerminated
    )

    enabled = QtCore.Property(
        bool,
        fget=_get_is_enabled,
        fset=_set_is_enabled,
        notify=enabledChanged
    )

    multipleInputs = QtCore.Property(
        bool,
        fget=_get_multiple_inputs,
        fset=_set_multiple_inputs,
        notify=multipleInputsChanged
    )

    eventTypes = QtCore.Property(
        list,
        fget=_get_event_types,
        fset=_set_event_types,
        notify=eventTypesChanged
    )


@QtQml.QmlElement
class ProcessListModel(QtCore.QAbstractListModel):

    """Provides a list model of all currently running processes."""

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        self._processes = sorted(process_monitor.list_current_processes())

    @QtCore.Slot()
    def refresh(self) -> None:
        """Refreshes the list of running processes."""
        self.beginResetModel()
        self._processes = sorted(process_monitor.list_current_processes())
        self.endResetModel()

    def rowCount(self, parent: QtCore.QModelIndex=QtCore.QModelIndex()) -> int:
        return len(self._processes)

    def data(
        self,
        index: QtCore.QModelIndex,
        role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid():
            return ""

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._processes[index.row()]
        return ""
