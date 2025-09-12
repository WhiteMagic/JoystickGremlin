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

from __future__ import annotations

import functools
import inspect
import logging
import time
from threading import Thread, Timer
from typing import Any, Callable, List, TYPE_CHECKING
import uuid

from PySide6 import QtCore

import dill

from gremlin import common, config, device_initialization, error, keyboard, \
    mode_manager, util, shared_state, tree, windows_event_hook
from gremlin.input_cache import Joystick, Keyboard
from gremlin.types import InputType


if TYPE_CHECKING:
    from gremlin.base_classes import Value
    from gremlin.code_runner import CallbackObject


class Event:

    """Represents a single event captured by the system.

    An event can originate from the keyboard or joystick which is
    indicated by the EventType value. The value of the event has to
    be interpreted based on the type of the event.

    Keyboard and JoystickButton events have a simple True / False
    value stored in is_pressed indicating whether or not the key has
    been pressed. For JoystickAxis the value indicates the axis value
    in the range [-1, 1] stored in the value field. JoystickHat events
    represent the hat position as a unit tuple (x, y) representing
    deflection in cartesian coordinates in the value field.

    The extended field is used for Keyboard events only to indicate
    whether or not the key's scan code is extended one.
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
    ) -> None:
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
            if dev.device_guid.uuid == self.device_guid:
                device = dev
                break

        # Retrieve device name
        label = ""
        if device is None:
            logging.warning(
                f"Unable to find a device with GUID {str(self.device_guid)}"
            )
            label = "Unknown"
        else:
            label = device.name

        # Retrive input name
        label += " - "
        label += common.input_to_ui_string(
            self.event_type,
            self.identifier
        )

        return label

    def clone(self) -> Event:
        """Returns a clone of the event.

        Returns:
            Cloned copy of this event.
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

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, Event)
        return self.__hash__() == other.__hash__()

    def __ne__(self, other: object) -> bool:
        assert isinstance(other, Event)
        return not (self == other)

    def __str__(self) -> str:
        return f"{self.device_guid}: {self.event_type} {self.identifier}"

    def __hash__(self) -> int:
        """Computes the hash value of this event.

        The hash is comprised of the events type, identifier of the
        event source and the id of the event device. Events from the same
        input, e.g. axis, button, hat, key, with different values / states
        shall have the same hash.

        Returns:
            Integer hash value of this event
        """
        if self.event_type == InputType.Keyboard:
            return hash((
                self.device_guid,
                self.event_type.value,
                self.identifier,
                1 if self.identifier[1] else 0
            ))
        else:
            return hash((
                self.device_guid,
                self.event_type.value,
                self.identifier,
                0
            ))

    @staticmethod
    def from_key(key: keyboard.Key) -> Event:
        """Creates an event object corresponding to the provided key.

        Args:
            key: the Key object from which to create the Event

        Returns:
            Event object corresponding to the provided key
        """
        assert isinstance(key, keyboard.Key)
        return Event(
            event_type=InputType.Keyboard,
            identifier=(key.scan_code, key.is_extended),
            device_guid=dill.UUID_Keyboard,
            mode=mode_manager.ModeManager().current.name
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
        self.gremlin_active = False

        self._init_joysticks()
        self.keyboard_hook.start()

        Thread(target=self._run).start()

    def terminate(self) -> None:
        """Stops the loop from running."""
        self._running = False
        self.keyboard_hook.stop()

    def reload_calibration(self, uuid: uuid.UUID, axis_index: int) -> None:
        """Reloads the calibration data of the specified axis."""
        cfg = config.Configuration()
        key = (uuid, axis_index)
        self._calibrations[key] = util.create_calibration_function(
            *cfg.get_calibration(*key)
        )

    def _run(self) -> None:
        """Starts the event loop."""
        dill.DILL.set_device_change_callback(self._joystick_device_handler)
        dill.DILL.set_input_event_callback(self._joystick_event_handler)
        while self._running:
            # Keep this thread alive until we are done
            time.sleep(0.1)

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
            self._joystick[event.device_guid.uuid].axis(event.input_index) \
                .update(calibrated_value)

            self.joystick_event.emit(Event(
                event_type=InputType.JoystickAxis,
                device_guid=event.device_guid.uuid,
                identifier=event.input_index,
                mode=self._modes.current.name,
                value=calibrated_value,
                raw_value=event.value
            ))
        elif event.input_type == dill.InputType.Button:
            self._joystick[event.device_guid.uuid].button(event.input_index) \
                .update(event.value == 1)

            self.joystick_event.emit(Event(
                event_type=InputType.JoystickButton,
                device_guid=event.device_guid.uuid,
                identifier=event.input_index,
                mode=self._modes.current.name,
                is_pressed=event.value == 1
            ))
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
            self,
            data: dill.DeviceSummary,
            action: dill.DeviceActionType
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
        self._device_update_timer = Timer(0.2, self._run_device_list_update)
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

        key_id = (event.scan_code, event.is_extended)
        is_pressed = event.is_pressed
        is_repeat = self._keyboard.is_pressed(key_id) and is_pressed
        # Only emit an event if they key is pressed for the first
        # time or released but not when it's being held down
        if not is_repeat:
            self._keyboard.update(
                keyboard.key_from_code(key_id[0], key_id[1]),
                is_pressed
            )
            self.keyboard_event.emit(Event(
                event_type=InputType.Keyboard,
                device_guid=dill.UUID_Keyboard,
                identifier=key_id,
                mode=self._modes.current.name,
                is_pressed=is_pressed,
            ))

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
            self.mouse_event.emit(Event(
                event_type=InputType.Mouse,
                device_guid=dill.GUID_Keyboard,
                identifier=event.button_id,
                mode=self._modes.current.name,
                is_pressed=event.is_pressed,
            ))

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
        cfg = config.Configuration()
        for dev_info in device_initialization.joystick_devices():
            for entry in dev_info.axis_map:
                self.reload_calibration(
                    dev_info.device_guid,
                    entry.axis_index
                )


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

    def add_plugin(self, plugin: Any) -> None:
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
            callback: CallbackObject|Callable[[Event, Value], None]
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
        self.callbacks[device_guid][mode][event].append(
            self._install_plugins(callback)
        )

    def build_event_lookup(self, mode_list: List[tree.TreeNode]) -> None:
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

    @QtCore.Slot(Event)
    def process_event(self, event: Event) -> None:
        """Processes a single event by passing it to all callbacks
        registered for this event.

        Args:
            event: the event to process
        """
        for cb in self._matching_callbacks(event):
            try:
                cb(event)
            except error.VJoyError as e:
                util.display_error(str(e))
                logging.getLogger("system").exception(f"VJoy error: '{e}'")
                self.pause()

    def _matching_callbacks(
            self,
            event: Event
    ) -> List[Callable[[Event, Value], None]]:
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
                self.callbacks[event.device_guid]
                    .get(event.mode, {})
                    .get(event, [])
            )

        # Filter events when the system is paused
        if not self.process_callbacks:
            return [c for c in callback_list if c.always_execute]
        else:
            return callback_list

    def _install_plugins(
            self,
            callback: CallbackObject|Callable[[Event, Value], None]
    ) -> Callable[[Event, Value], None]:
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
