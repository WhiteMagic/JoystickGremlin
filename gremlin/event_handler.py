# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2017 Lionel Ott
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
from threading import Thread

from PyQt5 import QtCore

import sdl2
import sdl2.ext

from . import common, config, error, joystick_handling, keyboard_hook, \
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

    ShiftEventId = 36
    ShiftDeviceId = 0
    ShiftSystemId = 32
    ShiftIdentifier = 40

    def __init__(
            self,
            event_type,
            identifier,
            hardware_id,
            windows_id,
            value=None,
            is_pressed=None,
            raw_value=None
    ):
        """Creates a new Event object.

        :param event_type the type of the event, one of the EventType
            values
        :param identifier the identifier of the event source
        :param hardware_id the hardware identifier of the device which
            created the event
        :param windows_id the index of the device as assigned by windows
        :param value the value of a joystick axis or hat
        :param is_pressed boolean flag indicating if a button or key
        :param raw_value the raw SDL value of the axis
            is pressed
        """
        self.event_type = event_type
        self.identifier = identifier
        self.hardware_id = hardware_id
        self.windows_id = windows_id
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
            self.hardware_id,
            self.windows_id,
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
        event source and the id of the event device.

        :return integer hash value of this event
        """
        hash_val = 0
        if self.event_type == common.InputType.Keyboard:
            extended_val = 1 << 8 if self.identifier[1] else 0
            hash_val += (extended_val + int(self.identifier[0])) \
                << Event.ShiftIdentifier
        else:
            hash_val += self.identifier << Event.ShiftIdentifier
        hash_val += self.event_type.value << Event.ShiftEventId
        if util.g_duplicate_devices:
            hash_val += self.windows_id << Event.ShiftSystemId
        hash_val += self.hardware_id << Event.ShiftDeviceId

        return hash_val

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
            hardware_id=0,
            windows_id=0
        )


@common.SingletonDecorator
class EventListener(QtCore.QObject):

    """Listens for keyboard and joystick events and publishes them
    via QT's signal/slot interface.
    """

    # Signal emitted when keyboard events are received
    keyboard_event = QtCore.pyqtSignal(Event)
    # Signal emitted when joystick events are received
    joystick_event = QtCore.pyqtSignal(Event)
    # Signal emitted when a joystick is attached or removed
    device_change_event = QtCore.pyqtSignal()

    def __init__(self):
        """Creates a new instance."""
        QtCore.QObject.__init__(self)
        self.keyboard_hook = keyboard_hook.KeyboardHook()
        self.keyboard_hook.register(self._keyboard_handler)
        self._joysticks = {}
        self._joystick_guid_map = {}
        self._calibrations = {}
        self._running = True
        self._keyboard_state = {}

        self._init_joysticks()
        self.keyboard_hook.start()
        Thread(target=self._run).start()

    def terminate(self):
        """Stops the loop from running."""
        self._running = False
        self.keyboard_hook.stop()

    def _run(self):
        """Starts the event loop."""
        while self._running:
            # Process joystick events
            for event in sdl2.ext.get_events():
                self._joystick_handler(event)
            time.sleep(0.001)

    def _keyboard_handler(self, event):
        """Callback for keyboard events.

        The handler converts the event data into a signal which is then
        emitted.

        :param event the keyboard event
        """
        # Ignore events we created via the macro system
        if not event.is_injected:
            key_id = (event.scan_code, event.is_extended)
            is_pressed = event.is_pressed
            is_repeat = self._keyboard_state.get(key_id, False) and is_pressed
            # Only emit an event if they key is pressed for the first
            # time or released but not when it's being held down
            if not is_repeat:
                self._keyboard_state[key_id] = is_pressed
                self.keyboard_event.emit(Event(
                    event_type=common.InputType.Keyboard,
                    hardware_id=0,
                    windows_id=0,
                    identifier=key_id,
                    is_pressed=is_pressed,
                ))
        # Allow the windows event to propagate further
        return True

    def _joystick_handler(self, event):
        """Callback for joystick events.

        The handler converts the event data into a signal which is then
        emitted.

        :param event the joystick event
        """
        if event.type == sdl2.SDL_JOYAXISMOTION:
            if self._joystick_guid_map[event.jaxis.which] != 873639358:
                calib_id = (
                    self._joystick_guid_map[event.jaxis.which],
                    event.jaxis.axis + 1
                )
                self.joystick_event.emit(Event(
                    event_type=common.InputType.JoystickAxis,
                    hardware_id=self._joystick_guid_map[event.jaxis.which],
                    windows_id=event.jaxis.which,
                    identifier=event.jaxis.axis + 1,
                    value=self._calibrations[calib_id](event.jaxis.value),
                    raw_value=event.jaxis.value
                ))
        elif event.type in [sdl2.SDL_JOYBUTTONDOWN, sdl2.SDL_JOYBUTTONUP]:
            if self._joystick_guid_map[event.jbutton.which] != 873639358:
                self.joystick_event.emit(Event(
                    event_type=common.InputType.JoystickButton,
                    hardware_id=self._joystick_guid_map[event.jbutton.which],
                    windows_id=event.jbutton.which,
                    identifier=event.jbutton.button + 1,
                    is_pressed=event.jbutton.state == 1
                ))
        elif event.type == sdl2.SDL_JOYHATMOTION:
            if self._joystick_guid_map[event.jhat.which] != 873639358:
                self.joystick_event.emit(Event(
                    event_type=common.InputType.JoystickHat,
                    hardware_id=self._joystick_guid_map[event.jhat.which],
                    windows_id=event.jhat.which,
                    identifier=event.jhat.hat + 1,
                    value=util.convert_sdl_hat(event.jhat.value)
                ))
        elif event.type in [sdl2.SDL_JOYDEVICEADDED, sdl2.SDL_JOYDEVICEREMOVED]:
            self._init_joysticks()
            self.device_change_event.emit()

    def _init_joysticks(self):
        """Initializes joystick devices."""
        for i in range(sdl2.joystick.SDL_NumJoysticks()):
            joy = sdl2.SDL_JoystickOpen(i)
            if joy is None:
                logging.getLogger("system").error(
                    "Invalid joystick device at id {}".format(i)
                )
            else:
                guid = self._get_device_guid(joy)
                self._joysticks[guid] = joy
                self._joystick_guid_map[sdl2.SDL_JoystickInstanceID(joy)] = guid
                self._load_calibrations(guid)

    def _get_device_guid(self, device):
        """Returns the GUID of the provided device.

        :param device SDL2 joystick device for which to get the GUID
        :return GUID for the provided device
        """
        vendor_id = sdl2.SDL_JoystickGetVendor(device)
        product_id = sdl2.SDL_JoystickGetProduct(device)
        return (vendor_id << 16) + product_id

    def _load_calibrations(self, guid):
        """Loads the calibration data for the given joystick.

        :param guid the id of the joystick to load the calibration
            data for
        """
        cfg = config.Configuration()
        for i in range(sdl2.SDL_JoystickNumAxes(self._joysticks[guid])):
            device = joystick_handling.JoystickDeviceData(self._joysticks[guid])
            limits = cfg.get_calibration(util.device_id(device), i + 1)
            self._calibrations[(guid, i+1)] = \
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
        """Creates a new instance."""
        QtCore.QObject.__init__(self)
        self.process_callbacks = True
        self.plugins = {}
        self.callbacks = {}
        self._event_lookup = {}
        self._active_mode = None
        self._previous_mode = None

    @property
    def active_mode(self):
        return self._active_mode

    @property
    def previous_mode(self):
        return self._previous_mode

    def add_plugin(self, plugin):
        """Adds a new plugin to be attached to event callbacks.

        :param plugin the plugin to add
        """
        # Do not add the same type of plugin multiple times
        if plugin.keyword not in self.plugins:
            self.plugins[plugin.keyword] = plugin

    def add_callback(self, device_id, mode, event, callback, permanent=False):
        """Installs the provided callback for the given event.

        :param device_id the id of the device the callback is
            associated with
        :param mode the mode the callback belongs to
        :param event the event for which to install the callback
        :param callback the callback function to link to the provided
            event
        :param permanent if True the callback is always active even
            if the system is paused
        """
        if device_id not in self.callbacks:
            self.callbacks[device_id] = {}
        if mode not in self.callbacks[device_id]:
            self.callbacks[device_id][mode] = {}
        if event not in self.callbacks[device_id][mode]:
            self.callbacks[device_id][mode][event] = []
        self.callbacks[device_id][mode][event].append((
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
            for device_id in self.callbacks:
                # Only attempt to copy handlers if we have any available in
                # the parent mode
                if parent in self.callbacks[device_id]:
                    device_cb = self.callbacks[device_id]
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
            self._active_mode = new_mode
            self.mode_changed.emit(self._active_mode)

            cfg = config.Configuration()
            cfg.set_last_mode(cfg.last_profile, self._active_mode)

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
        callback_list = []
        # Obtain callbacks matching the event
        device_id = util.device_id(event)
        if device_id in self.callbacks:
            callback_list = self.callbacks[device_id].get(
                self._active_mode, {}
            ).get(event, [])
        # Filter events when the system is paused
        if not self.process_callbacks:
            return [c[0] for c in callback_list if c[1]]
        else:
            return [c[0] for c in callback_list]

    def _install_plugins(self, callback):
        """Installs the current plugins into the given callback.

        :param callback the callback function to install the plugins
            into
        :return new callback with plugins installed
        """
        signature = inspect.signature(callback).parameters
        partial_fn = functools.partial
        if "self" in signature:
            partial_fn = functools.partialmethod
        for keyword, plugin in self.plugins.items():
            if keyword in signature:
                callback = plugin.install(callback, partial_fn)
        return callback
