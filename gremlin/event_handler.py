# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import functools
import inspect
import logging
import threading
import uuid
from collections.abc import Callable, Iterator
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


class EventGenerator(QtCore.QObject):
    """Generates events required to ensure consistent action executiong behavior.

    Turns a single event into possibly multiple events. In most cases the generator
    returns the original event. In rare cases related to global state changes additional
    events may be generated or events modified. This is to ensure that Gremlin behaves
    in a way that feels natural to users.

    A core purpose of the class is to generate additional events when a mode change
    has happened to ensure actions behave correctly. It also ensures events reach all
    relevant callbacks.
    """

    def __init__(self) -> None:
        """Creates a new instance."""
        super().__init__()
        # Stores the last mode an event has been dispatched in to ensure the
        # corresponding release event is dispatched. Used only for buttons and hats.
        self._last_dispatch_mode: dict[Event, str] = {}
        # Stores events tied to axis callbacks that need to be called no matter the
        # mode.
        self._axis_callbacks: dict[Event, list[tuple[str, InputBindingCallback]]] = {}
        mode_manager.ModeManager().modeChanged.connect(self._mode_changed_cb)

    def __call__(self, event: Event) -> Iterator[Event]:
        """Returns events to process.

        Args:
            event: Event from which to generate the events to process.

        Yields:
            Events to process.
        """
        match event.event_type:
            case (
                InputType.JoystickButton | InputType.Keyboard | InputType.VirtualButton
            ):
                yield self._generate_button_event(event)
            case InputType.JoystickHat:
                yield from self._generate_hat_events(event)
            case InputType.JoystickAxis:
                # First let the events be processed by callbacks before ensuring other
                # axis callbacks are called.
                axis_event = self._event_for_mode(
                    event, mode_manager.ModeManager().current.name
                )
                yield axis_event
                self._process_axis_callbacks(axis_event)
            case _:
                yield event

    def reset(self) -> None:
        """Resets the generator to default state."""
        self._last_dispatch_mode = {}
        self._axis_callbacks = {}

    def _generate_button_event(self, event: Event) -> Event:
        """Returns the button event to dispatch.

        Args:
            event: The button event to generate an event for.

        Returns:
            The press or release event corresponding to the given event.
        """
        mode_last_activated_in = self._last_dispatch_mode.get(event, event.mode)
        if event.is_pressed:
            self._last_dispatch_mode[event] = event.mode
            # Ensure actions can reset when a mode change ocurred since they were last
            # activated.
            if not EventHandler().is_same_binding(
                event, mode_last_activated_in, event.mode
            ):
                self._reset_binding(mode_last_activated_in, event)
            return event

        # Release events always have to be processed by the actions in the mode that
        # activated them.
        self._last_dispatch_mode[event] = mode_last_activated_in
        return self._event_for_mode(event, mode_last_activated_in)

    def _generate_hat_events(self, event: Event) -> list[Event]:
        """Returns the hat event(s) to dispatch.

        The logic implemented is similar to buttons in that an activated action should
        always receive a deactivation event. For a hat that's a center value event. If
        a center event would go to a different mode it is rerouted, and if none exists
        one is created.

        Args:
            event: The hat event to generate event(s) for.

        Returns:
            The event(s) to process.
        """
        mode_last_activated_in = self._last_dispatch_mode.pop(event, event.mode)

        if event.value == HatDirection.Center:
            return [self._event_for_mode(event, mode_last_activated_in)]

        self._last_dispatch_mode[event] = event.mode
        # Generate a center event for the last mode if a different binding would
        # receive this non-center event.
        if not EventHandler().is_same_binding(
            event, mode_last_activated_in, event.mode
        ):
            center_event = event.clone()
            center_event.mode = mode_last_activated_in
            center_event.value = HatDirection.Center
            return [center_event, event]

        return [event]

    def _process_axis_callbacks(self, event: Event) -> None:
        """Calls all matching callbacks for the given event.

        Args:
            event: The axis event to process.
        """
        if event not in self._axis_callbacks:
            return

        handler = EventHandler()
        event_callbacks = handler.binding_for(event.mode, event) or []
        remaining = []
        for mode, callback in self._axis_callbacks[event]:
            # Binding is active again and already received the event.
            if any(callback is entry for entry in event_callbacks):
                continue
            if handler.process_callbacks or callback.always_execute:
                callback(self._event_for_mode(event, mode))
            if callback.is_held():
                remaining.append((mode, callback))
        # A release fed above may have changed mode and added further callbacks.
        remaining += self._axis_callbacks.pop(event, [])
        if remaining:
            self._axis_callbacks[event] = remaining

    def _event_for_mode(self, event: Event, mode: str) -> Event:
        """Returns the event to dispatch in the given mode.

        If the event's mode and given mode match the original event is returned. If not
        a copy of the event with only the mode changed is returned.

        Args:
            event: the event to dispatch
            mode: name of the mode to dispatch the event in

        Returns:
            The event itself if it already is in the mode, a clone otherwise
        """
        if event.mode != mode:
            mode_event = event.clone()
            mode_event.mode = mode
            return mode_event
        return event

    @QtCore.Slot(str, str)
    def _mode_changed_cb(self, mode_name: str, previous_mode: str) -> None:
        """Performs maintenance required by a mode change.

        A Qt slot is used to ensure processing handles on the main thread together with
        other events, ensuring ordering.

        Args:
            mode_name: Name of the now active mode.
            previous_mode: Name of the previously active mode.
        """
        if previous_mode == mode_name:
            return

        # Process only axis events as buttons and hats have correct release events.
        # Every binding from the previous mode that would execute different actions in
        # the new mode triggers their actions' reset. Additionally, a callback is
        # registered for every axis to ensure that virtual buttons are properly managed.
        handler = EventHandler()
        for modes in handler.callbacks.values():
            for event in list(modes.get(previous_mode, {})):
                if (
                    event is not None
                    and event.event_type == InputType.JoystickAxis
                    and not handler.is_same_binding(event, previous_mode, mode_name)
                ):
                    self._reset_binding(previous_mode, event)
                    self._add_axis_callbacks(previous_mode, event)

    def _add_axis_callbacks(self, mode: str, event: Event) -> None:
        """Remembers the pressed virtual buttons of the axis binding.

        Args:
            mode: Name of the mode whose binding is no longer active.
            event: The axis event whose binding is no longer active.
        """
        callbacks = self._axis_callbacks.get(event, [])
        for callback in self._get_input_binding_callbacks(mode, event):
            if callback.is_held() and not any(
                callback is entry for _, entry in callbacks
            ):
                callbacks.append((mode, callback))
        if callbacks:
            self._axis_callbacks[event] = callbacks

    def _reset_binding(self, mode: str, event: Event) -> None:
        """Resets the functors bound to the event in the given mode.

        Args:
            mode: Name of the mode whose binding to reset.
            event: The event whose binding to reset.
        """
        for callback in self._get_input_binding_callbacks(mode, event):
            callback.reset()

    def _get_input_binding_callbacks(
        self, mode: str, event: Event
    ) -> list[InputBindingCallback]:
        """Returns the action callbacks bound to the event in the given mode.

        Args:
            mode: Name of the mode to look the event up in.
            event: The event to look up.

        Returns:
            The bound callbacks without those of user scripts.
        """
        return [
            callback
            for callback in EventHandler().binding_for(mode, event) or []
            if isinstance(callback, InputBindingCallback)
        ]


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
        self._event_generator = EventGenerator()

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
        self._event_generator.reset()

    @QtCore.Slot(Event)
    def process_event(self, input_event: Event) -> None:
        """Passes the event to all callbacks registered for it.

        The method ensures that additional events required by switching modes and other
        tricky edge cases are generated and emitted.

        Args:
            event: the event to process
        """
        for event in self._event_generator(input_event):
            for cb in self._matching_callbacks(event):
                try:
                    cb(event)
                except error.VJoyError as e:
                    signal.display_error("Error encountered with vJoy.", str(e))
                    logging.getLogger("system").exception(f"VJoy error: '{e}'")
                    self.pause()

    def _matching_callbacks(self, event: Event) -> list[Callable[[Event], None]]:
        """Returns the list of callbacks to execute in response to
        the provided event.

        Args:
            event: the event for which to search the matching callbacks

        Returns:
            A list of all callbacks registered and valid for the given event.
        """
        # Obtain callbacks matching the event
        callback_list = []
        if event.device_guid in self.callbacks:
            callback_list = (
                self.callbacks[event.device_guid].get(event.mode, {}).get(event, [])
            )

        # Filter events when the system is paused
        if not self.process_callbacks:
            return [c for c in callback_list if c.always_execute]
        else:
            return callback_list

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
