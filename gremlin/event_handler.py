# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import functools
import inspect
import logging
import threading
import uuid
from collections.abc import Callable
from typing import (
    Any,
)

from PySide6 import QtCore

import dill
from gremlin import (
    common,
    config,
    device_initialization,
    error,
    keyboard,
    mode_manager,
    signal,
    tree,
    util,
    windows_event_hook,
)
from gremlin.input_cache import (
    Joystick,
    Keyboard,
)
from gremlin.types import (
    Event,
    HatDirection,
    InputBindingCallback,
    InputType,
    ModeType,
)


@common.SingletonDecorator
class EventListener(QtCore.QObject):
    """Listens for keyboard and joystick events and publishes them
    via QT's signal/slot interface.
    """

    # Signal emitted when joystick events are received
    joystick_event = QtCore.Signal(Event)
    # Signal emitted when keyboard events are received
    keyboard_event = QtCore.Signal(Event)
    # Signal emitted when mouse events are received
    mouse_event = QtCore.Signal(Event)
    # Signal emitted when virtual button events are received
    virtual_event = QtCore.Signal(Event)
    # Signal emitted when a joystick is attached or removed
    device_change_event = QtCore.Signal()

    def __init__(self) -> None:
        """Creates a new instance."""
        QtCore.QObject.__init__(self)
        self.keyboard_hook = windows_event_hook.KeyboardHook()
        self.keyboard_hook.register(self._keyboard_handler)
        self.mouse_hook = windows_event_hook.MouseHook()
        self.mouse_hook.register(self._mouse_handler)

        # Calibration function for each axis of all devices
        self._calibrations = {}
        self._modes = mode_manager.ModeManager()

        # Joystick device change update timeout timer
        self._device_update_timer = None
        self._joystick = Joystick()
        self._keyboard = Keyboard()

        self._running = True
        self._stop_event = threading.Event()
        self.gremlin_active = False

        self._init_joysticks()
        self.keyboard_hook.start()

        threading.Thread(target=self._run).start()

    def terminate(self) -> None:
        """Stops the loop from running."""
        self._running = False
        self._stop_event.set()
        self.keyboard_hook.stop()
        dill.DILL.set_device_change_callback(lambda *_: None)
        dill.DILL.set_input_event_callback(lambda x: None)

    def restart(self) -> None:
        """Restarts the event listener."""
        if not self._running:
            self._running = True
            self.keyboard_hook.start()
            self._stop_event.clear()
            threading.Thread(target=self._run).start()

    def reload_calibration(self, device_guid: dill.GUID, axis_index: int) -> None:
        """Reloads the calibration data of the specified axis."""
        cfg = config.Configuration()
        key = (device_guid, axis_index)
        self._calibrations[key] = util.create_calibration_function(
            *cfg.get_calibration(*key)
        )

    def _run(self) -> None:
        """Starts the event loop."""
        dill.DILL.set_device_change_callback(self._joystick_device_handler)
        dill.DILL.set_input_event_callback(self._joystick_event_handler)
        while self._running:
            # Keep this thread alive until we are done
            self._stop_event.wait()

    def _joystick_event_handler(self, data: dill.InputEvent) -> None:
        """Callback for joystick events.

        The handler converts the event data into a signal which is then
        emitted.

        Args:
            data: the joystick event information
        """
        event = dill.InputEvent(data)
        if event.input_type == dill.InputType.Axis:
            calibrated_value = self._apply_calibration(event)
            self._joystick[event.device_guid.uuid].axis(event.input_index).update(
                calibrated_value
            )

            self.joystick_event.emit(
                Event(
                    event_type=InputType.JoystickAxis,
                    device_guid=event.device_guid.uuid,
                    identifier=event.input_index,
                    mode=self._modes.current.name,
                    value=calibrated_value,
                    raw_value=event.value,
                )
            )
        elif event.input_type == dill.InputType.Button:
            self._joystick[event.device_guid.uuid].button(event.input_index).update(
                event.value == 1
            )

            self.joystick_event.emit(
                Event(
                    event_type=InputType.JoystickButton,
                    device_guid=event.device_guid.uuid,
                    identifier=event.input_index,
                    mode=self._modes.current.name,
                    is_pressed=event.value == 1,
                )
            )
        elif event.input_type == dill.InputType.Hat:
            direction = util.dill_hat_lookup(event.value)
            self._joystick[event.device_guid.uuid].hat(event.input_index).update(
                direction
            )

            self.joystick_event.emit(
                Event(
                    event_type=InputType.JoystickHat,
                    device_guid=event.device_guid.uuid,
                    identifier=event.input_index,
                    mode=self._modes.current.name,
                    value=direction,
                )
            )

    def _joystick_device_handler(
        self, data: dill.DeviceSummary, action: dill.DeviceActionType
    ) -> None:
        """Callback for device change events.

        This is called when a device is added or removed from the system. This
        uses a timer to call the actual device update function to prevent
        the addition or removal of a multiple devices at the same time to
        cause repeat updates.

        Args:
            data: information about the device changing state
            action: whether the device was added or removed
        """
        if self._device_update_timer is not None:
            self._device_update_timer.cancel()
        self._device_update_timer = threading.Timer(0.2, self._run_device_list_update)
        self._device_update_timer.start()

    def _run_device_list_update(self) -> None:
        """Performs the update of the devices connected."""
        device_initialization.joystick_devices_initialization()
        self._init_joysticks()
        self.device_change_event.emit()

    def _keyboard_handler(self, event: Event) -> bool:
        """Callback for keyboard events.

        The handler converts the event data into a signal which is then
        emitted.

        Args:
            event: the keyboard event

        Returns:
            True to enable the event to propagate up further
        """
        # Ignore injected keyboard events while Gremlin is active
        # if self.gremlin_active and event.is_injected:
        #     return True

        key_id = keyboard.key_from_code(event.scan_code, event.is_extended)
        is_pressed = event.is_pressed
        is_repeat = self._keyboard.is_pressed(key_id) and is_pressed
        # Only emit an event if they key is pressed for the first
        # time or released but not when it's being held down
        if not is_repeat:
            self._keyboard.update(key_id, is_pressed)
            self.keyboard_event.emit(
                Event(
                    event_type=InputType.Keyboard,
                    device_guid=dill.UUID_Keyboard,
                    identifier=(key_id.scan_code, key_id.is_extended),
                    mode=self._modes.current.name,
                    is_pressed=is_pressed,
                )
            )

        # Allow the windows event to propagate further
        return True

    def _mouse_handler(self, event: Event) -> bool:
        """Callback for mouse events.

        The handler converts the event data into a signal which is then
        emitted.

        Args:
            event: the mouse event

        Returns:
            True to enable the event to propagate up further
        """
        # Ignore events we created via the macro system
        if not event.is_injected:
            self.mouse_event.emit(
                Event(
                    event_type=InputType.Mouse,
                    device_guid=dill.GUID_Keyboard,
                    identifier=event.button_id,
                    mode=self._modes.current.name,
                    is_pressed=event.is_pressed,
                )
            )

        # Allow the windows event to propagate further
        return True

    def _apply_calibration(self, event: Event) -> float:
        """Applies a calibration to raw input values.

        The resulting value will be in the range [-1, 1].

        Args:
            event: the event containing the data to be calibrated

        Returns:
            Value with applied calibration and scaling
        """
        key = (event.device_guid, event.input_index)
        if key in self._calibrations:
            return self._calibrations[key](event.value)
        else:
            logging.getLogger("system").warning(
                f"No calibration data for {key[0]} - Axis {key[1]}"
            )
            return util.with_default_center_calibration(event.value)

    def _init_joysticks(self) -> None:
        """Initializes joystick devices.

        Loads calibration data for the joystick.
        """
        for dev_info in device_initialization.joystick_devices():
            for entry in dev_info.axis_map:
                self.reload_calibration(dev_info.device_guid, entry.axis_index)


@common.SingletonDecorator
class EventHandler(QtCore.QObject):
    """Listens to the inputs from multiple different input devices."""

    # Signal emitted when the mode is changed
    mode_changed = QtCore.Signal(str)
    # Signal emitted when the application is pause / resumed
    is_active = QtCore.Signal(bool)

    def __init__(self) -> None:
        """Initializes the EventHandler instance."""
        QtCore.QObject.__init__(self)
        self.process_callbacks = True
        self.plugins = {}
        self.callbacks = {}
        self._event_lookup = {}
        # Callbacks that asked for the next event of an input, irrespective the mode.
        self._pending_callbacks: dict[Event, list[Callable[[Event], None]]] = {}
        mode_manager.ModeManager().modeChanged.connect(self._mode_changed_cb)

    def add_plugin(self, plugin: Any) -> None:  # noqa: ANN401
        """Adds a new plugin to be attached to event callbacks.

        Params:
            plugin: Instance of the plugin to add
        """
        # Do not add the same type of plugin multiple times
        if plugin.keyword not in self.plugins:
            self.plugins[plugin.keyword] = plugin

    def add_callback(
        self,
        device_guid: uuid.UUID,
        mode: str,
        event: Event,
        callback: InputBindingCallback | Callable[[Event], None],
    ) -> None:
        """Installs the provided callback for the given event.

        Args:
            device_guid: the GUID of the device the callback is associated with
            mode: the mode the callback belongs to
            event: the event for which to install the callback
            callback: the callback function to link to the provided event
        """
        if device_guid not in self.callbacks:
            self.callbacks[device_guid] = {}
        if mode not in self.callbacks[device_guid]:
            self.callbacks[device_guid][mode] = {}
        if event not in self.callbacks[device_guid][mode]:
            self.callbacks[device_guid][mode][event] = []
        self.callbacks[device_guid][mode][event].append(self._install_plugins(callback))

    def build_event_lookup(self, mode_list: list[tree.TreeNode]) -> None:
        """Builds the lookup table linking events to callbacks.

        This takes mode inheritance into account to create items in children
        if they do not override a parent's action.

        Args:
            modes: information about the mode hierarchy
        """
        for mode in mode_list:
            # Each device is treated separately
            for device_guid in self.callbacks:
                # Only attempt to copy handlers into child modes if the current
                # mode has any available
                if mode.value in self.callbacks[device_guid]:
                    device_cb = self.callbacks[device_guid]
                    mode_cb = device_cb[mode.value]
                    # Copy the handlers into each child mode, unless they
                    # have their own handlers already defined
                    for child in [e.value for e in mode.children]:
                        if child not in device_cb:
                            device_cb[child] = {}
                        for event, callbacks in mode_cb.items():
                            if event not in device_cb[child]:
                                device_cb[child][event] = callbacks

    def is_same_binding(self, event: Event, first_mode: str, second_mode: str) -> bool:
        """Returns whether both modes route the given event to the same binding.

        Args:
            event: the event whose binding to compare
            first_mode: name of the mode to compare against second_mode
            second_mode: name of the mode to compare against first_mode

        Returns:
            True if both modes dispatch the event to the same callbacks
        """
        return self.binding_for(first_mode, event) is self.binding_for(
            second_mode, event
        )

    def has_pending_callbacks(self, event: Event) -> bool:
        """Returns whether any callback asked for this next event.

        Args:
            event: the event identifying the input

        Returns:
            True if at least one callback waits for the input's next event
        """
        return bool(self._pending_callbacks.get(event))

    def binding_for(
        self, mode: str, event: Event
    ) -> list[Callable[[Event], None]] | None:
        """Returns the callbacks bound to the event in the given mode.

        Mode inheritance shares the very same list instance with every child mode,
        making identity of the returned list a test for an unchanged binding.

        Args:
            mode: name of the mode to look the event up in
            event: the event to look up

        Returns:
            The callbacks bound to the event, None if there are none
        """
        return self.callbacks.get(event.device_guid, {}).get(mode, {}).get(event)

    def resume(self) -> None:
        """Resumes the processing of callbacks."""
        self.process_callbacks = True
        self.is_active.emit(self.process_callbacks)

    def pause(self) -> None:
        """Stops the processing of callbacks."""
        self.process_callbacks = False
        self.is_active.emit(self.process_callbacks)

    def toggle_active(self) -> None:
        """Toggles the processing of callbacks on or off."""
        self.process_callbacks = not self.process_callbacks
        self.is_active.emit(self.process_callbacks)

    def clear(self) -> None:
        """Removes all attached callbacks."""
        self.callbacks = {}
        self._pending_callbacks = {}

    def teardown_bindings(self) -> None:
        """Tears down the functors of every attached input binding callback."""
        bindings = {}
        for modes in self.callbacks.values():
            for events in modes.values():
                for callback_list in events.values():
                    for callback in callback_list:
                        if isinstance(callback, InputBindingCallback):
                            bindings[id(callback)] = callback
        for binding in bindings.values():
            binding.teardown()

    @QtCore.Slot(Event)
    def process_event(self, input_event: Event) -> None:
        """Passes the event to all callbacks registered for or waiting on it.

        Callbacks waiting on the input that the event's mode doesn't bind are called
        first, as foreign, then the ones bound in the event's mode, as native.

        Args:
            input_event: the event to process
        """
        event = input_event
        current_mode = mode_manager.ModeManager().current.name
        # Axis events queued before a mode change belong to the new mode.
        if event.event_type == InputType.JoystickAxis and event.mode != current_mode:
            event = input_event.clone()
            event.mode = current_mode

        native_mode_bindings = list(self.binding_for(event.mode, event) or [])
        foreign_mode_bindings = set(self._pending_callbacks.get(event, [])) - set(
            native_mode_bindings
        )
        calls = [(callback, ModeType.Foreign) for callback in foreign_mode_bindings] + [
            (callback, ModeType.Native) for callback in native_mode_bindings
        ]

        # Get the reference to the callback list such that it can later be compared
        # to detect when a load profile action happened, as that makes the identity
        # test fail.
        callbacks = self.callbacks
        for callback, mode_type in calls:
            if self._may_run(callback):
                try:
                    wants_next_event = self._run_callback(callback, event, mode_type)
                except error.VJoyError as e:
                    signal.display_error("Error encountered with vJoy.", str(e))
                    logging.getLogger("system").exception(f"VJoy error: '{e}'")
                    self.pause()
                    return
                # A callback that triggered a profile reload ends further processing.
                if self.callbacks is not callbacks:
                    return
                self._set_pending(event, callback, wants_next_event)

    @QtCore.Slot(str, str)
    def _mode_changed_cb(self, mode_name: str, previous_mode: str) -> None:
        """Stops continuous actions performed by axis actions.

        Args:
            mode_name: name of the now active mode
            previous_mode: name of the previously active mode
        """
        if previous_mode == mode_name:
            return

        for modes in self.callbacks.values():
            for event in list(modes.get(previous_mode, {})):
                if (
                    event is not None
                    and event.event_type == InputType.JoystickAxis
                    and not self.is_same_binding(event, previous_mode, mode_name)
                ):
                    for callback in self.binding_for(previous_mode, event) or []:
                        if isinstance(callback, InputBindingCallback):
                            callback.reset()

    def _may_run(self, callback: Callable[[Event], None]) -> bool:
        """Returns whether the callback may run given Gremlin's execution state.

        When paused only certain actions that interact with the paused state are
        allowed to run.

        Args:
            callback: the callback to check

        Returns:
            True if processing is active or the callback always executes
        """
        return self.process_callbacks or (
            isinstance(callback, InputBindingCallback) and callback.always_execute
        )

    def _run_callback(
        self, callback: Callable[[Event], None], event: Event, mode_type: ModeType
    ) -> bool:
        """Runs the callback with the event.

        Script callbacks have no notion of paired activations, they always receive the
        release or centre for event "pairs".

        Args:
            callback: the callback to run
            event: the event to run it with
            mode_type: how the callback was reached

        Returns:
            True if the callback wants the next event of the input
        """
        if isinstance(callback, InputBindingCallback):
            return callback(event, mode_type)

        script_event = event
        if (
            mode_type == ModeType.Foreign
            and event.event_type == InputType.JoystickHat
            and event.value != HatDirection.Center
        ):
            script_event = event.clone()
            script_event.value = HatDirection.Center
        callback(script_event)

        match script_event.event_type:
            case InputType.JoystickHat:
                return script_event.value != HatDirection.Center
            case (
                InputType.JoystickButton | InputType.Keyboard | InputType.VirtualButton
            ):
                return bool(script_event.is_pressed)
            case _:
                return False

    def _set_pending(
        self, event: Event, callback: Callable[[Event], None], wants_next_event: bool
    ) -> None:
        """Adds the callback to or removes it from the input's pending callbacks.

        Args:
            event: the event identifying the input
            callback: the callback that answered
            wants_next_event: True if the callback wants the input's next event
        """
        pending = self._pending_callbacks.setdefault(event, [])
        is_pending = any(callback is entry for entry in pending)
        # Add to the list of pending callbacks.
        if wants_next_event and not is_pending:
            pending.append(callback)
        # Remove from the list of pending callbacks.
        elif is_pending and not wants_next_event:
            pending[:] = [entry for entry in pending if entry is not callback]

    def _install_plugins(
        self, callback: InputBindingCallback | Callable[[Event], None]
    ) -> Callable[[Event], None]:
        """Installs the current plugins into the given callback.

        Args:
            callback: the callback function to install the plugins into

        Returns:
            New callback with plugins installed
        """
        signature = inspect.signature(callback).parameters
        for keyword, plugin in self.plugins.items():
            if keyword in signature:
                callback = plugin.install(callback, functools.partial)
        return callback
