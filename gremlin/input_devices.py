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
import heapq
import inspect
import logging
import time
import threading

from PyQt5 import QtCore

import sdl2

from . import common, error, event_handler, joystick_handling, macro, util


class CallbackRegistry(object):

    """Registry of all callbacks known to the system."""

    def __init__(self):
        """Creates a new callback registry instance."""
        self._registry = {}

    def add(self, callback, event, mode, always_execute=False):
        """Adds a new callback to the registry.

        :param callback function to add as a callback
        :param event the event on which to trigger the callback
        :param mode the mode in which to trigger the callback
        :param always_execute if True the callback is run even if Gremlin
            is paused
        """
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
            logging.getLogger("system").warning(
                "Function with name {} exists multiple times".format(
                    function_name
                )
            )

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
        self._queue = []
        self._plugins = []

    def start(self):
        """Starts the event loop."""
        # Only proceed if we have functions to call
        if len(self._registry) == 0:
            return

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

    def clear(self):
        """Clears the registry."""
        self._registry = {}

    def _install_plugins(self, callback):
        """Installs the current plugins into the given callback.

        :param callback the callback function to install the plugins
            into
        :return new callback with plugins installed
        """
        signature = inspect.signature(callback)
        new_callback = self._plugins[0].install(callback, signature)
        for plugin in self._plugins[1:]:
            new_callback = plugin.install(new_callback, signature)
        return new_callback

    def _thread_loop(self):
        """Main execution loop run in a separate thread."""
        # Setup plugins to use
        self._plugins = [
            JoystickPlugin(),
            VJoyPlugin(),
            KeyboardPlugin()
        ]
        callback_map = {}

        # Populate the queue
        self._queue = []
        for item in self._registry.values():
            plugin_cb = self._install_plugins(item[1])
            callback_map[plugin_cb] = item[0]
            heapq.heappush(
                self._queue,
                (time.time() + callback_map[plugin_cb], plugin_cb)
            )

        # Main thread loop
        while self._running:
            # Process all events that require running
            while self._queue[0][0] < time.time():
                item = heapq.heappop(self._queue)
                item[1]()

                heapq.heappush(
                    self._queue,
                    (time.time() + callback_map[item[1]], item[1])
                )

            # Sleep until either the next function needs to be run or
            # our timeout expires
            time.sleep(min(self._queue[0][0] - time.time(), 1.0))


# Global registry of all registered callbacks
callback_registry = CallbackRegistry()

# Global registry of all periodic callbacks
periodic_registry = PeriodicRegistry()


class JoystickWrapper:

    """Wraps SDL2 joysticks and presents an API similar to vjoy."""

    class Input:

        """Represents a joystick input."""

        def __init__(self, joystick, index):
            """Creates a new instance.

            :param joystick the SDL joystick instance this input belongs to
            :param index the index of the input
            """
            self._joystick = joystick
            self._index = index

    class Axis(Input):

        """Represents a single axis of a joystick."""

        def __init__(self, joystick, index):
            super().__init__(joystick, index)

        @property
        def value(self):
            return sdl2.SDL_JoystickGetAxis(
                self._joystick, self._index
            ) / float(32768)

    class Button(Input):

        """Represents a single button of a joystick."""

        def __init__(self, joystick, index):
            super().__init__(joystick, index)

        @property
        def is_pressed(self):
            return sdl2.SDL_JoystickGetButton(self._joystick, self._index)

    class Hat(Input):

        """Represents a single hat of a joystick,"""

        def __init__(self, joystick, index):
            super().__init__(joystick, index)

        @property
        def direction(self):
            return util.convert_sdl_hat(sdl2.SDL_JoystickGetHat(
                self._joystick, self._index)
            )

    def __init__(self, jid):
        """Creates a new wrapper object for the given object id.

        :param jid the id of the joystick instance to wrap
        """
        if jid > sdl2.joystick.SDL_NumJoysticks():
            raise error.GremlinError("No device with the provided ID exist")
        self._joystick = sdl2.SDL_JoystickOpen(jid)
        self._axis = self._init_axes()
        self._buttons = self._init_buttons()
        self._hats = self._init_hats()
        self._name = sdl2.joystick.SDL_JoystickNameForIndex(jid).decode("utf-8")

    @property
    def name(self):
        """Returns the name of the joystick.

        :return name of the joystick
        """
        return self._name

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
        return self._axis[index-1]

    def button(self, index):
        """Returns the current state of the button with the given index.

        The index is 1 based, i.e. the first button starts with index 1.

        :param index the index of the axis to return to value of
        :return the current state of the button
        """
        return self._buttons[index-1]

    def hat(self, index):
        """Returns the current state of the hat with the given index.

        The index is 1 based, i.e. the first hat starts with index 1.

        :param index the index of the hat to return to value of
        :return the current state of the hat
        """
        return self._hats[index-1]

    def axis_count(self):
        """Returns the number of axis of the joystick.

        :return number of axes
        """
        return sdl2.SDL_JoystickNumAxes(self._joystick)

    def _init_axes(self):
        """Initializes the axes of the joystick.

        :return list of JoystickWrapper.Axis objects
        """
        axes = []
        for i in range(sdl2.SDL_JoystickNumAxes(self._joystick)):
            axes.append(JoystickWrapper.Axis(self._joystick, i))
        return axes

    def _init_buttons(self):
        """Initializes the buttons of the joystick.

        :return list of JoystickWrapper.Button objects
        """
        buttons = []
        for i in range(sdl2.SDL_JoystickNumButtons(self._joystick)):
            buttons.append(JoystickWrapper.Button(self._joystick, i))
        return buttons

    def _init_hats(self):
        """Initializes the hats of the joystick.

        :return list of JoystickWrapper.Hat objects
        """
        hats = []
        for i in range(sdl2.SDL_JoystickNumHats(self._joystick)):
            hats.append(JoystickWrapper.Hat(self._joystick, i))
        return hats


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
        if len(JoystickProxy.joystick_devices) == 0:
            # The id used to open the device is not the same as the
            # system_id reported by SDL, hence we grab all devices and
            # store them using their system_id
            for i in range(sdl2.joystick.SDL_NumJoysticks()):
                joy = JoystickWrapper(i)
                JoystickProxy.joystick_devices[joy.windows_id()] = joy
                JoystickProxy.joystick_devices[joy.name] = joy

        if key not in JoystickProxy.joystick_devices:
            raise error.GremlinError(
                "No device with the provided identifier: {} exists".format(key)
            )
        else:
            return JoystickProxy.joystick_devices[key]


class VJoyPlugin(object):

    """Plugin providing automatic access to the VJoyProxy object.

    For a function to use this plugin it requires one of its parameters
    to be named "vjoy".
    """

    vjoy = joystick_handling.VJoyProxy()

    def __init__(self):
        self.keyword = "vjoy"

    def install(self, callback, partial_fn):
        """Decorates the given callback function to provide access to
        the VJoyProxy object.

        Only if the signature contains the plugin's keyword is the
        decorator applied.

        :param callback the callback to decorate
        :param partial_fn function to create the partial function / method
        :return callback with the plugin parameter bound
        """
        return partial_fn(callback, vjoy=VJoyPlugin.vjoy)


class JoystickPlugin(object):

    """Plugin providing automatic access to the JoystickProxy object.

    For a function to use this plugin it requires one of its parameters
    to be named "joy".
    """

    joystick = JoystickProxy()

    def __init__(self):
        self.keyword = "joy"

    def install(self, callback, partial_fn):
        """Decorates the given callback function to provide access
        to the JoystickProxy object.

        Only if the signature contains the plugin's keyword is the
        decorator applied.

        :param callback the callback to decorate
        :param partial_fn function to create the partial function / method
        :return callback with the plugin parameter bound
        """
        return partial_fn(callback, joy=JoystickPlugin.joystick)


@common.SingletonDecorator
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
        elif isinstance(key, macro.Key):
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

    def install(self, callback, partial_fn):
        """Decorates the given callback function to provide access to
        the Keyboard object.

        :param callback the callback to decorate
        :param partial_fn function to create the partial function / method
        :return callback with the plugin parameter bound
        """
        return partial_fn(callback, keyboard=KeyboardPlugin.keyboard)


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


@common.SingletonDecorator
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
            vjoy = joystick_handling.VJoyProxy()
            for entry in self._registry[evt]:
                # Check if the button is valid otherwise we cause Gremlin
                # to crash
                if vjoy[entry[0]].is_button_valid(entry[1]):
                    vjoy[entry[0]].button(entry[1]).is_pressed = False
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

        hid, wid = util.extract_ids(device_id)
        event = event_handler.Event(
            event_type=common.InputType.JoystickButton,
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

        hid, wid = util.extract_ids(device_id)
        event = event_handler.Event(
            event_type=common.InputType.JoystickHat,
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

        hid, wid = util.extract_ids(device_id)
        event = event_handler.Event(
            event_type=common.InputType.JoystickAxis,
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


def squash(value, func):
    """Returns the appropriate function value when the function is
    squashed to [-1, 1].

    :param value the function value to compute
    :param func the function to be squashed
    :return function value at value after squashing
    """
    return (2 * func(value)) / abs(func(-1) - func(1))


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
