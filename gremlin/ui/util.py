# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from PySide6 import (
    QtCore,
    QtGui,
)

import gremlin.ui.type_aliases as ta
from gremlin import (
    device_helpers,
    event_handler,
    keyboard,
    process_monitor,
    shared_state,
    windows_event_hook,
)
from gremlin.common import SingletonMetaclass
from gremlin.config import Configuration
from gremlin.keyboard import key_from_code
from gremlin.macro import (
    AbstractAction,
    JoystickAction,
    KeyAction,
    MouseButtonAction,
    PauseAction,
)
from gremlin.types import (
    HatDirection,
    InputType,
    MouseButton,
)

QML_IMPORT_NAME = "Gremlin.Util"
QML_IMPORT_MAJOR_VERSION = 1


@ta.QmlElement
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

    def __init__(self, parent: ta.OQO = None) -> None:
        super().__init__(parent)

        # List of InputTypes that will be listened to.
        self._event_types: list[InputType] = []
        # If True more than the first input will be returned.
        self._multiple_inputs = False
        # Timer terminating the listening process in various scenarios.
        self._abort_timer = threading.Timer(1.0, self._abort_listening)
        # Received inputs while listening.
        self._inputs: list[event_handler.Event] = []
        # Flag indicating whether the listener is active or not.
        self._is_enabled = False

    def _connect_listeners(self) -> None:
        # Start listening to user inputs.
        event_listener = event_handler.EventListener()
        # Keyboard events are always listened to in order to catch the ESC
        # key to abort input listening.
        event_listener.keyboard_event.connect(self._kb_event_cb)
        if (
            InputType.JoystickAxis in self._event_types
            or InputType.JoystickButton in self._event_types
            or InputType.JoystickHat in self._event_types
        ):
            event_listener.joystick_event.connect(self._joy_event_cb)
        if InputType.Mouse in self._event_types:
            windows_event_hook.MouseHook().start()
            event_listener.mouse_event.connect(self._mouse_event_cb)

    def _disconnect_listeners(self) -> None:
        event_listener = event_handler.EventListener()
        event_listener.keyboard_event.disconnect(self._kb_event_cb)
        if (
            InputType.JoystickAxis in self._event_types
            or InputType.JoystickButton in self._event_types
            or InputType.JoystickHat in self._event_types
        ):
            try:
                event_listener.joystick_event.disconnect(self._joy_event_cb)
            except RuntimeError:
                pass
        if InputType.Mouse in self._event_types:
            try:
                event_listener.mouse_event.disconnect(self._mouse_event_cb)
            except RuntimeError:
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
                if device_helpers.JoystickInputSignificant().should_process(event):
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
        is_esc = keyboard.key_from_code(*event.identifier) == keyboard.key_from_name(
            "esc"
        )
        if is_esc:
            if event.is_pressed and not self._abort_timer.is_alive():
                self._abort_timer = threading.Timer(1.0, self._abort_listening)
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

    def _set_event_types(self, event_types: list[str]) -> None:
        types = sorted(
            [InputType.to_enum(v) for v in event_types],
            key=lambda v: InputType.to_string(v),
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
        list, fget=_get_current_inputs, notify=listeningTerminated
    )

    enabled = QtCore.Property(
        bool, fget=_get_is_enabled, fset=_set_is_enabled, notify=enabledChanged
    )

    multipleInputs = QtCore.Property(
        bool,
        fget=_get_multiple_inputs,
        fset=_set_multiple_inputs,
        notify=multipleInputsChanged,
    )

    eventTypes = QtCore.Property(
        list, fget=_get_event_types, fset=_set_event_types, notify=eventTypesChanged
    )


class MacroRecorder:
    """Records keyboard, mouse, and joystick inputs and creates appropriate
    macro actions.

    The class requires a callback that is called for every recorded action. It is the
    callback's responsability to handle the addition of the new action.
    """

    def __init__(
        self,
        append_action_callback: Callable[[AbstractAction], None],
    ) -> None:
        self._append_action_callback = append_action_callback
        self._valid_event_types: list[InputType] = []
        self._record_timings: bool = False
        self._last_event_time: int = 0
        self._last_recordings: dict[event_handler.Event, int] = {}
        self._axis_recordings: dict[
            event_handler.Event, device_helpers.AxisChangeSignificanceTracker
        ] = {}
        self._is_recording: bool = False
        self._config = Configuration()

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self, events_to_record: list[InputType], record_timings: bool) -> None:
        if self._is_recording:
            logging.getLogger("system").warning(
                "MacroRecorder.start() called while already recording"
            )
            return

        # Configure recording parameters.
        self._valid_event_types = events_to_record
        self._record_timings = record_timings

        # Reset internal state.
        self._last_recordings = {}
        self._axis_recordings = {}
        self._is_recording = True
        shared_state.set_suspend_input_highlighting(True)

        # Hookup required event listeners.
        el = event_handler.EventListener()
        if InputType.Keyboard in self._valid_event_types:
            el.keyboard_event.connect(self._queue_event_recording)
        if InputType.Mouse in self._valid_event_types:
            windows_event_hook.MouseHook().start()
            el.mouse_event.connect(self._queue_event_recording)
        if any(
            input_type in self._valid_event_types
            for input_type in (
                InputType.JoystickButton,
                InputType.JoystickAxis,
                InputType.JoystickHat,
            )
        ):
            el.joystick_event.connect(self._queue_event_recording)

    def stop(self) -> None:
        if not self._is_recording:
            logging.getLogger("system").warning(
                "MacroRecorder.stop() called while not recording"
            )
            return

        # Attempt to disconnect all event handlers, failure is silently ignored.
        el = event_handler.EventListener()
        for event_signal in (el.keyboard_event, el.mouse_event, el.joystick_event):
            try:
                event_signal.disconnect(self._queue_event_recording)
            except RuntimeError:
                pass
        if InputType.Mouse in self._valid_event_types:
            windows_event_hook.MouseHook().stop()
        shared_state.set_suspend_input_highlighting(False)
        self._is_recording = False

    def _queue_event_recording(self, event: event_handler.Event) -> None:
        QtCore.QTimer.singleShot(0, lambda: self._record_event(event))

    def _record_event(self, event: event_handler.Event) -> None:
        if not self._is_recording or event.event_type not in self._valid_event_types:
            return

        # Check if the event corressponds to an axis that has a significant
        # enough change to record it again.
        if event.event_type == InputType.JoystickAxis:
            if event in self._axis_recordings:
                if not self._axis_recordings[event].is_significant_change(event.value):
                    return
            else:
                self._axis_recordings[event] = (
                    device_helpers.AxisChangeSignificanceTracker(
                        event.value,
                        self._config.value(
                            "action", "macro", "axis-minimum-change-amount"
                        ),
                        self._config.value(
                            "action", "macro", "axis-minimum-time-interval"
                        ),
                        True,
                    )
                )

        match event.event_type:
            case InputType.Keyboard:
                action = KeyAction(key_from_code(*event.identifier), event.is_pressed)
            case InputType.Mouse:
                action = MouseButtonAction(event.identifier, event.is_pressed)
            case InputType.JoystickButton:
                action = JoystickAction(
                    event.device_guid,
                    event.event_type,
                    event.identifier,
                    event.is_pressed,
                )
            case InputType.JoystickAxis | InputType.JoystickHat:
                action = JoystickAction(
                    event.device_guid,
                    event.event_type,
                    event.identifier,
                    event.value,
                )
            case _:
                return

        time_now = time.monotonic_ns()
        if self._record_timings and self._last_event_time > 0:
            self._append_action_callback(
                PauseAction((time_now - self._last_event_time) / 1e9)
            )
        self._last_event_time = time_now
        self._append_action_callback(action)


@ta.QmlElement
class ProcessListModel(QtCore.QAbstractListModel):
    """Provides a list model of all currently running processes."""

    def __init__(self, parent: ta.OQO = None) -> None:
        super().__init__(parent)

        self._processes = sorted(process_monitor.list_current_processes())

    @QtCore.Slot()
    def refresh(self) -> None:
        """Refreshes the list of running processes."""
        self.beginResetModel()
        self._processes = sorted(process_monitor.list_current_processes())
        self.endResetModel()

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._processes)

    def data(
        self, index: ta.ModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole
    ) -> str:
        if not index.isValid():
            return ""

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._processes[index.row()]
        return ""


class ColorInformation(metaclass=SingletonMetaclass):
    """Contains the information about the primary colors of the UI theme.

    Information is provided via a QML object (ColorInformation.qml) that holds the
    color information of the Universal theme as properties.
    """

    def __init__(self) -> None:
        self._accent_color = QtGui.QColor("blue")
        self._background_color = QtGui.QColor("white")
        self._foreground_color = QtGui.QColor("black")
        self._is_dark_theme = False

    def update_colors(self, color_information: QtCore.QObject) -> None:
        self._accent_color = color_information.property("accent")
        self._background_color = color_information.property("background")
        self._foreground_color = color_information.property("foreground")
        self._is_dark_theme = color_information.property("isDarkTheme")

    @property
    def accent(self) -> QtGui.QColor:
        return self._accent_color

    @property
    def background(self) -> QtGui.QColor:
        return self._background_color

    @property
    def foreground(self) -> QtGui.QColor:
        return self._foreground_color

    @property
    def is_dark_theme(self) -> bool:
        return self._is_dark_theme


def to_local_path(path_or_url: str) -> Path:
    """Returns a Path irrespective of the input path formatting.

    Args:
        path_or_url: path to a local file as either a string or QUrl

    Returns:
        Path object representing the local file path
    """
    if path_or_url.startswith("file://"):
        return Path(QtCore.QUrl(path_or_url).toLocalFile())
    return Path(path_or_url)
