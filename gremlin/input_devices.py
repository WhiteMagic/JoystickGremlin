# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
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
import logging
from queue import PriorityQueue
import time
import threading

from PyQt5 import QtCore
import sdl2

from gremlin import event_handler, macro, util
from gremlin.util import SingletonDecorator, convert_sdl_hat, extract_ids
from gremlin.error import GremlinError
from vjoy.vjoy import VJoy


class CallbackRegistry(object):

    """Registry of all callbacks known to the system."""

    def __init__(self):
        self._registry = {}

    def add(self, callback, event, mode, always_execute=False):
        device_id = util.device_id(event)
        function_name = callback.__name__

        if device_id not in self._registry:
            self._registry[device_id] = {}
        if mode not in self._registry[device_id]:
            self._registry[device_id][mode] = {}

        if event not in self._registry[device_id][mode]:
            self._registry[device_id][mode][event] = {}
        if function_name not in self._registry[device_id][mode][event]:
            self._registry[device_id][mode][event][function_name] = \
                (callback, always_execute)
        else:
            logging.warning("Function with name {} exists multiple"
                            " times".format(function_name))

    @property
    def registry(self):
        """Returns the registry dictionary.

        :return registry dictionary
        """
        return self._registry

    def clear(self):
        """Clears the registry entries."""
        self._registry = {}


class PeriodicRegistry(object):

    """Registry for periodically executed functions."""

    def __init__(self):
        """Creates a new instance."""
        self._registry = {}
        self._running = False
        self._thread = threading.Thread(target=self._thread_loop)
        self._queue = PriorityQueue()

    def start(self):
        """Starts the event loop."""
        # Only create a new thread and start it if the thread is not
        # currently running
        self._running = True
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._thread_loop)
            self._thread.start()

    def stop(self):
        """Stops the event loop."""
        self._running = False
        if self._thread.is_alive():
            self._thread.join()

    def add(self, callback, interval):
        """Adds a function to execute periodically.

        :param callback the function to execute
        :param interval the time between executions
        """
        self._registry[callback] = (interval, callback)

    def remove(self, callback):
        """Removes a callback from the registry."""
        if callback in self._registry:
            del self._registry[callback]

    def clear(self):
        """Clears the registry."""
        self._registry = {}

    def _create_queue_entry(self, key):
        """Creates a priority queue entry based on a callback.

        :param key the callback to create the priority queue entry for
        :return priority queue entry
        """
        return (time.time() + self._registry[key][0], key)

    def _thread_loop(self):
        """Main execution loop run in a separate thread."""
        # Populate the queue
        self._queue = PriorityQueue()
        print(self._registry.values())
        for item in self._registry.values():
            self._queue.put(self._create_queue_entry(item[1]))

        while self._running:
            # Process all events that require running
            item = self._queue.get()
            while item[0] < time.time():
                item[1]()

                self._queue.put(self._create_queue_entry(item[1]))
                item = self._queue.get()
            self._queue.put(item)

            time.sleep(0.01)


# Global registry of all registered callbacks
callback_registry = CallbackRegistry()

# Global registry of all periodic callbacks
periodic_registry = PeriodicRegistry()


class VJoyProxy(object):

    """Manages the usage of vJoy and allows shared access all
    callbacks."""

    vjoy_devices = {}

    def __getitem__(self, key):
        """Returns the requested vJoy instance.

        :param key id of the vjoy device
        :return the corresponding vjoy device
        """
        if key in VJoyProxy.vjoy_devices:
            return VJoyProxy.vjoy_devices[key]
        else:
            if not isinstance(key, int):
                raise TypeError("Integer ID expected")

            device = VJoy(key)
            VJoyProxy.vjoy_devices[key] = device
            return device

    @classmethod
    def reset(cls):
        """Relinquishes control over all held VJoy devices."""
        for device in VJoyProxy.vjoy_devices.values():
            device.invalidate()
        VJoyProxy.vjoy_devices = {}


class JoystickWrapper(object):

    """Wraps SDL2 joysticks and presents an API similar to vjoy."""

    def __init__(self, jid):
        """Creates a new wrapper object for the given object id.

        :param jid the id of the joystick instance to wrap
        """
        if jid > sdl2.joystick.SDL_NumJoysticks():
            raise GremlinError("No device with the provided ID exist")
        self._joystick = sdl2.SDL_JoystickOpen(jid)

    def windows_id(self):
        """Returns the system id of the wrapped joystick.

        :return system id of this device
        """
        return sdl2.joystick.SDL_JoystickInstanceID(self._joystick)

    def axis(self, index):
        """Returns the current value of the axis with the given index.

        The index is 1 based, i.e. the first axis starts with index 1.

        :param index the index of the axis to return to value of
        :return the current value of the axis
        """
        return sdl2.SDL_JoystickGetAxis(self._joystick, index-1) / float(32768)

    def button(self, index):
        """Returns the current state of the button with the given index.

        The index is 1 based, i.e. the first button starts with index 1.

        :param index the index of the axis to return to value of
        :return the current state of the button
        """
        return sdl2.SDL_JoystickGetButton(self._joystick, index-1)

    def hat(self, index):
        """Returns the current state of the hat with the given index.

        The index is 1 based, i.e. the first hat starts with index 1.

        :param index the index of the hat to return to value of
        :return the current state of the hat
        """
        return convert_sdl_hat(sdl2.SDL_JoystickGetHat(
            self._joystick, index-1)
        )

    def axis_count(self):
        """Returns the number of axis of the joystick.

        :return number of axes
        """
        return sdl2.SDL_JoystickNumAxes(self._joystick)


class JoystickProxy(object):

    """Allows read access to joystick state information."""

    # Dictionary of initialized joystick devices
    joystick_devices = {}

    def __getitem__(self, key):
        """Returns the requested joystick instance.

        If the joystick instance exists it is returned directly,
        otherwise it is first created and then returned.

        :param key id of the joystick device
        :return the corresponding joystick device
        """
        if key in JoystickProxy.joystick_devices:
            return JoystickProxy.joystick_devices[key]
        else:
            if type(key) != int:
                raise TypeError("Integer ID expected")
            if key > sdl2.joystick.SDL_NumJoysticks():
                raise GremlinError("No device with the provided ID exist")

            # The id used to open the device is not the same as the
            # system_id reported by SDL, hence we grab all devices and
            # store them using their system_id
            for i in range(sdl2.joystick.SDL_NumJoysticks()):
                joy = JoystickWrapper(i)
                JoystickProxy.joystick_devices[joy.windows_id()] = joy
            return JoystickProxy.joystick_devices[key]


class VJoyPlugin(object):

    """Plugin providing automatic access to the VJoyProxy object.

    For a function to use this plugin it requires one of its parameters
    to be named "vjoy".
    """

    vjoy = VJoyProxy()

    def __init__(self):
        self.keyword = "vjoy"

    def install(self, callback, signature):
        """Decorates the given callback function to provide access to
        the VJoyProxy object.

        Only if the signature contains the plugin's keyword is the
        decorator applied.

        :param callback the callback to decorate
        :param signature the signature of the original callback
        :return either the original callback or the newly decorated
            version
        """
        if self.keyword not in signature.parameters:
            return callback

        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            kwargs[self.keyword] = VJoyPlugin.vjoy
            callback(*args, **kwargs)

        return wrapper


class JoystickPlugin(object):

    """Plugin providing automatic access to the JoystickProxy object.

    For a function to use this plugin it requires one of its parameters
    to be named "joy".
    """

    joystick = JoystickProxy()

    def __init__(self):
        self.keyword = "joy"

    def install(self, callback, signature):
        """Decorates the given callback function to provide access
        to the JoystickProxy object.

        Only if the signature contains the plugin's keyword is the
        decorator applied.

        :param callback the callback to decorate
        :param signature the signature of the original callback
        :return either the original callback or the newly decorated
            version
        """
        if self.keyword not in signature.parameters:
            return callback

        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            kwargs[self.keyword] = JoystickPlugin.joystick
            callback(*args, **kwargs)

        return wrapper


@SingletonDecorator
class Keyboard(QtCore.QObject):

    """Provides access to the keyboard state."""

    def __init__(self):
        """Initialises a new object."""
        QtCore.QObject.__init__(self)
        self._keyboard_state = {}

    @QtCore.pyqtSlot(event_handler.Event)
    def keyboard_event(self, event):
        """Handles keyboard events and updates state.

        :param event the keyboard event to use to update state
        """
        key = macro.key_from_code(
            event.identifier[0],
            event.identifier[1]
        )
        self._keyboard_state[key] = event.is_pressed

    def is_pressed(self, key):
        """Returns whether or not the key is pressed.

        :param key the key to check
        :return True if the key is pressed, False otherwise
        """
        if isinstance(key, str):
            key = macro.key_from_name(key)
        elif isinstance(key, macro.Keys.Key):
            pass
        return self._keyboard_state.get(key, False)


class KeyboardPlugin(object):

    """Plugin providing automatic access to the Keyboard object.

    For a function to use this plugin it requires one of its parameters
    to be named "keyboard".
    """

    keyboard = Keyboard()

    def __init__(self):
        self.keyword = "keyboard"

    def install(self, callback, signature):
        """Decorates the given callback function to provide access to
        the Keyboard object.

        Only if the signature contains the plugin's keyword is the
        decorator applied.

        :param callback the callback to decorate
        :param signature the signature of the original callback
        :return either the original callback or the newly decorated
            version
        """
        if self.keyword not in signature.parameters:
            return callback

        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            kwargs[self.keyword] = KeyboardPlugin.keyboard
            callback(*args, **kwargs)

        return wrapper


class JoystickDecorator(object):

    """Creates customized decorators for physical joystick devices."""

    def __init__(self, name, device_id, mode):
        """Creates a new instance with customized decorators.

        :param name the name of the device
        :param device_id the device id in the system
        :param mode the mode in which the decorated functions
            should be active
        """
        self.name = name
        self.mode = mode
        self.axis = functools.partial(
            _axis, device_id=device_id, mode=mode
        )
        self.button = functools.partial(
            _button, device_id=device_id, mode=mode
        )
        self.hat = functools.partial(
            _hat, device_id=device_id, mode=mode
        )


@SingletonDecorator
class AutomaticButtonRelease(QtCore.QObject):

    """Ensures that vjoy buttons are reliably released.

    The class ensures that vjoy buttons are released even if they
    have been pressed in a different mode then the active one when
    the physical button that pressed them is released.
    """

    def __init__(self):
        """Initializes the instance."""
        QtCore.QObject.__init__(self)

        self._registry = {}
        el = event_handler.EventListener()
        el.joystick_event.connect(self._joystick_cb)

    def register(self, vjoy_input, physical_event):
        """Registers a physical and vjoy button pair for tracking.

        :param vjoy_input the vjoy button to release, represented as
            (vjoy_device_id, vjoy_button_id)
        :param physical_event the button event when release should
            trigger the release of the vjoy button
        """
        release_evt = physical_event.clone()
        release_evt.is_pressed = False

        if release_evt not in self._registry:
            self._registry[release_evt] = []
        self._registry[release_evt].append(vjoy_input)

    def _joystick_cb(self, evt):
        """Releases vjoy buttons if appropriate.

        If any vjoy buttons are associated with the event they are
        released

        :param evt the joystick event to process
        """
        if evt in self._registry and not evt.is_pressed:
            vjoy = VJoyProxy()
            for entry in self._registry[evt]:
                vjoy[entry[0]].button[entry[1]].is_pressed = False
            self._registry[evt] = []


def _button(button_id, device_id, mode, always_execute=False):
    """Decorator for button callbacks.

    :param button_id the id of the button on the physical joystick
    :param device_id the id of input device
    :param mode the mode in which this callback is active
    :param always_execute if True the decorated function is executed
        even when the program is not listening to inputs
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        hid, wid = extract_ids(device_id)
        event = event_handler.Event(
            event_type=event_handler.InputType.JoystickButton,
            hardware_id=hid,
            windows_id=wid,
            identifier=button_id
        )
        callback_registry.add(wrapper_fn, event, mode, always_execute)

        return wrapper_fn

    return wrap


def _hat(hat_id, device_id, mode, always_execute=False):
    """Decorator for hat callbacks.

    :param hat_id the id of the button on the physical joystick
    :param device_id the id of input device
    :param mode the mode in which this callback is active
    :param always_execute if True the decorated function is executed
        even when the program is not listening to inputs
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        hid, wid = extract_ids(device_id)
        event = event_handler.Event(
            event_type=event_handler.InputType.JoystickHat,
            hardware_id=hid,
            windows_id=wid,
            identifier=hat_id
        )
        callback_registry.add(wrapper_fn, event, mode, always_execute)

        return wrapper_fn

    return wrap


def _axis(axis_id, device_id, mode, always_execute=False):
    """Decorator for axis callbacks.

    :param axis_id the id of the axis on the physical joystick
    :param device_id the id of input device
    :param mode the mode in which this callback is active
    :param always_execute if True the decorated function is executed
        even when the program is not listening to inputs
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        hid, wid = extract_ids(device_id)
        event = event_handler.Event(
            event_type=event_handler.InputType.JoystickAxis,
            hardware_id=hid,
            windows_id=wid,
            identifier=axis_id
        )
        callback_registry.add(wrapper_fn, event, mode, always_execute)

        return wrapper_fn

    return wrap


def keyboard(key_name, mode, always_execute=False):
    """Decorator for keyboard key callbacks.

    :param key_name name of the key of this callback
    :param mode the mode in which this callback is active
    :param always_execute if True the decorated function is executed
        even when the program is not listening to inputs
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        key = macro.key_from_name(key_name)
        event = event_handler.Event.from_key(key)
        callback_registry.add(wrapper_fn, event, mode, always_execute)

        return wrapper_fn

    return wrap


def periodic(interval):
    """Decorator for periodic function callbacks.

    :param interval the duration between executions of the function
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        periodic_registry.add(wrapper_fn, interval)

        return wrapper_fn

    return wrap


def squash(value, function):
    """Returns the appropriate function value when the function is
    squashed to [-1, 1].

    :param value the function value to compute
    :param function the function to be squashed
    :return function value at value after squashing
    """
    return (2 * function(value)) / abs(function(-1) - function(1))


def deadzone(value, low, low_center, high_center, high):
    """Returns the mapped value taking the provided deadzone into
    account.

    The following relationship between the limits has to hold.
    -1 <= low < low_center <= 0 <= high_center < high <= 1

    :param value the raw input value
    :param low low deadzone limit
    :param low_center lower center deadzone limit
    :param high_center upper center deadzone limit
    :param high high deadzone limit
    :return corrected value
    """
    if value >= 0:
        return min(1, max(0, (value - high_center) / abs(high - high_center)))
    else:
        return max(-1, min(0, (value - low_center) / abs(low - low_center)))
