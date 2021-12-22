# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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

import functools
import inspect
import logging
import time
from threading import Thread, Timer

from PyQt5 import QtCore

import dill
from . import common, config, error, joystick_handling, windows_event_hook, \
    macro, util


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
            event_type,
            identifier,
            device_guid,
            value=None,
            is_pressed=None,
            raw_value=None
    ):
        """Creates a new Event object.

        :param event_type the type of the event, one of the EventType
            values
        :param identifier the identifier of the event source
        :param device_guid Device GUID identifying the device causing this event
        :param value the value of a joystick axis or hat
        :param is_pressed boolean flag indicating if a button or key
        :param raw_value the raw SDL value of the axis
            is pressed
        """
        self.event_type = event_type
        self.identifier = identifier
        self.device_guid = device_guid
        self.is_pressed = is_pressed
        self.value = value
        self.raw_value = raw_value

    def clone(self):
        """Returns a clone of the event.

        :return cloned copy of this event
        """
        return Event(
            self.event_type,
            self.identifier,
            self.device_guid,
            self.value,
            self.is_pressed,
            self.raw_value
        )

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        """Computes the hash value of this event.

        The hash is comprised of the events type, identifier of the
        event source and the id of the event device. Events from the same
        input, e.g. axis, button, hat, key, with different values / states
        shall have the same hash.

        :return integer hash value of this event
        """
        if self.event_type == common.InputType.Keyboard:
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
    def from_key(key):
        """Creates an event object corresponding to the provided key.

        :param key the Key object from which to create the Event
        :return Event object corresponding to the provided key
        """
        assert isinstance(key, macro.Key)
        return Event(
            event_type=common.InputType.Keyboard,
            identifier=(key.scan_code, key.is_extended),
            device_guid=dill.GUID_Keyboard
        )


@common.SingletonDecorator
class EventListener(QtCore.QObject):

    """Listens for keyboard and joystick events and publishes them
    via QT's signal/slot interface.
    """

    # Signal emitted when joystick events are received
    joystick_event = QtCore.pyqtSignal(Event)
    # Signal emitted when keyboard events are received
    keyboard_event = QtCore.pyqtSignal(Event)
    # Signal emitted when mouse events are received
    mouse_event = QtCore.pyqtSignal(Event)
    # Signal emitted when virtual button events are received
    virtual_event = QtCore.pyqtSignal(Event)
    # Signal emitted when a joystick is attached or removed
    device_change_event = QtCore.pyqtSignal()

    def __init__(self):
        """Creates a new instance."""
        QtCore.QObject.__init__(self)
        self.keyboard_hook = windows_event_hook.KeyboardHook()
        self.keyboard_hook.register(self._keyboard_handler)
        self.mouse_hook = windows_event_hook.MouseHook()
        self.mouse_hook.register(self._mouse_handler)

        # Calibration function for each axis of all devices
        self._calibrations = {}

        # Joystick device change update timeout timer
        self._device_update_timer = None

        self._running = True
        self._keyboard_state = {}
        self.gremlin_active = False

        #self._init_joysticks()
        self.keyboard_hook.start()

        Thread(target=self._run).start()

    def terminate(self):
        """Stops the loop from running."""
        self._running = False
        self.keyboard_hook.stop()

    def reload_calibrations(self):
        """Reloads the calibration data from the configuration file."""
        cfg = config.Configuration()
        for key in self._calibrations:
            limits = cfg.get_calibration(key[0], key[1])
            self._calibrations[key] = \
                util.create_calibration_function(
                    limits[0],
                    limits[1],
                    limits[2]
                )

    def _run(self):
        """Starts the event loop."""
        dill.DILL.set_device_change_callback(self._joystick_device_handler)
        dill.DILL.set_input_event_callback(self._joystick_event_handler)
        while self._running:
            # Keep this thread alive until we are done
            time.sleep(0.1)

    def _joystick_event_handler(self, data):
        """Callback for joystick events.

        The handler converts the event data into a signal which is then
        emitted.

        :param data the joystick event
        """
        event = dill.InputEvent(data)
        if event.input_type == dill.InputType.Axis:
            self.joystick_event.emit(Event(
                event_type=common.InputType.JoystickAxis,
                device_guid=event.device_guid,
                identifier=event.input_index,
                value=self._apply_calibration(event),
                raw_value=event.value
            ))
        elif event.input_type == dill.InputType.Button:
            self.joystick_event.emit(Event(
                event_type=common.InputType.JoystickButton,
                device_guid=event.device_guid,
                identifier=event.input_index,
                is_pressed=event.value == 1
            ))
        elif event.input_type == dill.InputType.Hat:
            self.joystick_event.emit(Event(
                event_type=common.InputType.JoystickHat,
                device_guid=event.device_guid,
                identifier=event.input_index,
                value=util.dill_hat_lookup[event.value]
            ))

    def _joystick_device_handler(self, data, action):
        """Callback for device change events.

        This is called when a device is added or removed from the system. This
        uses a timer to call the actual device update function to prevent
        the addition or removal of a multiple devices at the same time to
        cause repeat updates.

        :param data information about the device changing state
        :param action whether the device was added or removed
        """
        if self._device_update_timer is not None:
            self._device_update_timer.cancel()
        self._device_update_timer = Timer(0.2, self._run_device_list_update)
        self._device_update_timer.start()

    def _run_device_list_update(self):
        """Performs the update of the devices connected."""
        joystick_handling.joystick_devices_initialization()
        self._init_joysticks()
        self.device_change_event.emit()

    def _keyboard_handler(self, event):
        """Callback for keyboard events.

        The handler converts the event data into a signal which is then
        emitted.

        :param event the keyboard event
        """
        # Ignore injected keyboard events while Gremlin is active
        # if self.gremlin_active and event.is_injected:
        #     return True

        key_id = (event.scan_code, event.is_extended)
        is_pressed = event.is_pressed
        is_repeat = self._keyboard_state.get(key_id, False) and is_pressed
        # Only emit an event if they key is pressed for the first
        # time or released but not when it's being held down
        if not is_repeat:
            self._keyboard_state[key_id] = is_pressed
            self.keyboard_event.emit(Event(
                event_type=common.InputType.Keyboard,
                device_guid=dill.GUID_Keyboard,
                identifier=key_id,
                is_pressed=is_pressed,
            ))

        # Allow the windows event to propagate further
        return True

    def _mouse_handler(self, event):
        """Callback for mouse events.

        The handler converts the event data into a signal which is then
        emitted.

        :param event the mouse event
        """
        # Ignore events we created via the macro system
        if not event.is_injected:
            self.mouse_event.emit(Event(
                event_type=common.InputType.Mouse,
                device_guid=dill.GUID_Keyboard,
                identifier=event.button_id,
                is_pressed=event.is_pressed,
            ))
        # Allow the windows event to propagate further
        return True

    def _apply_calibration(self, event):
        key = (event.device_guid, event.input_index)
        if key in self._calibrations:
            return self._calibrations[key](event.value)
        else:
            return util.axis_calibration(event.value, -32768, 0, 32767)

    def _init_joysticks(self):
        """Initializes joystick devices."""
        for dev_info in joystick_handling.joystick_devices():
            self._load_calibrations(dev_info)

    def _load_calibrations(self, device_info):
        """Loads the calibration data for the given joystick.

        :param device_info information about the device
        """
        cfg = config.Configuration()
        for entry in device_info.axis_map:
            limits = cfg.get_calibration(
                device_info.device_guid,
                entry.axis_index
            )
            self._calibrations[(device_info.device_guid, entry.axis_index)] = \
                util.create_calibration_function(
                    limits[0],
                    limits[1],
                    limits[2]
                )


@common.SingletonDecorator
class EventHandler(QtCore.QObject):

    """Listens to the inputs from multiple different input devices."""

    # Signal emitted when the mode is changed
    mode_changed = QtCore.pyqtSignal(str)
    # Signal emitted when the application is pause / resumed
    is_active = QtCore.pyqtSignal(bool)

    def __init__(self):
        """Initializes the EventHandler instance."""
        QtCore.QObject.__init__(self)
        self.process_callbacks = True
        self.plugins = {}
        self.callbacks = {}
        self._event_lookup = {}
        self._active_mode = None
        self._previous_mode = None

    @property
    def active_mode(self):
        """Returns the currently active mode.

        :return name of the currently active mode
        """
        return self._active_mode

    @property
    def previous_mode(self):
        """Returns the previously active mode.

        :return name of the previously active mode
        """
        return self._previous_mode

    def add_plugin(self, plugin):
        """Adds a new plugin to be attached to event callbacks.

        :param plugin the plugin to add
        """
        # Do not add the same type of plugin multiple times
        if plugin.keyword not in self.plugins:
            self.plugins[plugin.keyword] = plugin

    def add_callback(self, device_guid, mode, event, callback, permanent=False):
        """Installs the provided callback for the given event.

        :param device_guid the GUID of the device the callback is
            associated with
        :param mode the mode the callback belongs to
        :param event the event for which to install the callback
        :param callback the callback function to link to the provided
            event
        :param permanent if True the callback is always active even
            if the system is paused
        """
        if device_guid not in self.callbacks:
            self.callbacks[device_guid] = {}
        if mode not in self.callbacks[device_guid]:
            self.callbacks[device_guid][mode] = {}
        if event not in self.callbacks[device_guid][mode]:
            self.callbacks[device_guid][mode][event] = []
        self.callbacks[device_guid][mode][event].append((
            self._install_plugins(callback),
            permanent
        ))

    def build_event_lookup(self, inheritance_tree):
        """Builds the lookup table linking event to callback.

        This takes mode inheritance into account.

        :param inheritance_tree the tree of parent and children in the
            inheritance structure
        """
        # Propagate events from parent to children if the children lack
        # handlers for the available events
        for parent, children in inheritance_tree.items():
            # Each device is treated separately
            for device_guid in self.callbacks:
                # Only attempt to copy handlers if we have any available in
                # the parent mode
                if parent in self.callbacks[device_guid]:
                    device_cb = self.callbacks[device_guid]
                    parent_cb = device_cb[parent]
                    # Copy the handlers into each child mode, unless they
                    # have their own handlers already defined
                    for child in children:
                        if child not in device_cb:
                            device_cb[child] = {}
                        for event, callbacks in parent_cb.items():
                            if event not in device_cb[child]:
                                device_cb[child][event] = callbacks

            # Recurse until we've dealt with all modes
            self.build_event_lookup(children)

    def change_mode(self, new_mode):
        """Changes the currently active mode.

        :param new_mode the new mode to use
        """
        mode_exists = False
        for device in self.callbacks.values():
            if new_mode in device:
                mode_exists = True
        if not mode_exists:
            logging.getLogger("system").error(
                "The mode \"{}\" does not exist or has no"
                " associated callbacks".format(new_mode)
            )

        if mode_exists:
            if self._active_mode != new_mode:
                self._previous_mode = self._active_mode

            cfg = config.Configuration()
            cfg.set_last_mode(cfg.last_profile, new_mode)

            self._active_mode = new_mode
            self.mode_changed.emit(self._active_mode)

    def resume(self):
        """Resumes the processing of callbacks."""
        self.process_callbacks = True
        self.is_active.emit(self.process_callbacks)

    def pause(self):
        """Stops the processing of callbacks."""
        self.process_callbacks = False
        self.is_active.emit(self.process_callbacks)

    def toggle_active(self):
        """Toggles the processing of callbacks on or off."""
        self.process_callbacks = not self.process_callbacks
        self.is_active.emit(self.process_callbacks)

    def clear(self):
        """Removes all attached callbacks."""
        self.callbacks = {}

    @QtCore.pyqtSlot(Event)
    def process_event(self, event):
        """Processes a single event by passing it to all callbacks
        registered for this event.

        :param event the event to process
        """
        for cb in self._matching_callbacks(event):
            try:
                cb(event)
            except error.VJoyError as e:
                util.display_error(str(e))
                logging.getLogger("system").exception(
                    "VJoy related error: {}".format(e)
                )
                self.pause()

    def _matching_callbacks(self, event):
        """Returns the list of callbacks to execute in response to
        the provided event.

        :param event the event for which to search the matching
            callbacks
        :return a list of all callbacks registered and valid for the
            given event
        """
        # Obtain callbacks matching the event
        callback_list = []
        if event.device_guid in self.callbacks:
            callback_list = self.callbacks[event.device_guid].get(
                self._active_mode, {}
            ).get(event, [])

        # Filter events when the system is paused
        if not self.process_callbacks:
            return [c[0] for c in callback_list if c[1]]
        else:
            return [c[0] for c in callback_list]

    def _install_plugins(self, callback):
        """Installs the current plugins into the given callback.

        :param callback the callback function to install the plugins into
        :return new callback with plugins installed
        """
        signature = inspect.signature(callback).parameters
        for keyword, plugin in self.plugins.items():
            if keyword in signature:
                callback = plugin.install(callback, functools.partial)
        return callback
