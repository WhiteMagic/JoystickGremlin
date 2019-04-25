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
import heapq
import inspect
import logging
import time
import threading

from PyQt5 import QtCore

from dill import DILL, GUID_Invalid

from . import common, error, event_handler, joystick_handling, \
    macro, profile, util


class CallbackRegistry:

    """Registry of all callbacks known to the system."""

    def __init__(self):
        """Creates a new callback registry instance."""
        self._registry = {}
        self._current_id = 0

    def add(self, callback, event, mode, always_execute=False):
        """Adds a new callback to the registry.

        :param callback function to add as a callback
        :param event the event on which to trigger the callback
        :param mode the mode in which to trigger the callback
        :param always_execute if True the callback is run even if Gremlin
            is paused
        """
        self._current_id += 1
        function_name = "{}_{:d}".format(callback.__name__, self._current_id)

        if event.device_guid not in self._registry:
            self._registry[event.device_guid] = {}
        if mode not in self._registry[event.device_guid]:
            self._registry[event.device_guid][mode] = {}

        if event not in self._registry[event.device_guid][mode]:
            self._registry[event.device_guid][mode][event] = {}
        self._registry[event.device_guid][mode][event][function_name] = \
            (callback, always_execute)

    @property
    def registry(self):
        """Returns the registry dictionary.

        :return registry dictionary
        """
        return self._registry

    def clear(self):
        """Clears the registry entries."""
        self._registry = {}


class PeriodicRegistry:

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
        signature = inspect.signature(callback).parameters
        partial_fn = functools.partial
        if "self" in signature:
            partial_fn = functools.partialmethod
        for plugin in self._plugins:
            if plugin.keyword in signature:
                callback = plugin.install(callback, partial_fn)
        return callback

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


def register_callback(callback, device, input_type, input_id):
    """Adds a callback to the registry.

    This function adds the provided callback to the global callback_registry
    for the specified event and mode combination.

    Parameters
    ==========
    callback : callable
        The callable object to execute when the event with the specified
        conditions occurs
    device : JoystickDecorator
        Joystick decorator specifying the device and mode in which to execute
        the callback
    input_type : common.InputType
        Type of input on which to execute the callback
    input_id : int
        Index of the input on which to execute the callback
    """
    event = event_handler.Event(
        event_type=input_type,
        device_guid=device.device_guid,
        identifier=input_id
    )
    callback_registry.add(callback, event, device.mode, False)


class JoystickWrapper:

    """Wraps joysticks and presents an API similar to vjoy."""

    class Input:

        """Represents a joystick input."""

        def __init__(self, joystick_guid, index):
            """Creates a new instance.

            :param joystick_guid the GUID of the device instance
            :param index the index of the input
            """
            self._joystick_guid = joystick_guid
            self._index = index

    class Axis(Input):

        """Represents a single axis of a joystick."""

        def __init__(self, joystick_guid, index):
            super().__init__(joystick_guid, index)

        @property
        def value(self):
            return DILL.get_axis(self._joystick_guid, self._index) / float(32768)

    class Button(Input):

        """Represents a single button of a joystick."""

        def __init__(self, joystick_guid, index):
            super().__init__(joystick_guid, index)

        @property
        def is_pressed(self):
            val = DILL.get_button(self._joystick_guid, self._index)
            return val #DILL.get_button(self._joystick_guid, self._index)

    class Hat(Input):

        """Represents a single hat of a joystick,"""

        def __init__(self, joystick_guid, index):
            super().__init__(joystick_guid, index)

        @property
        def direction(self):
            return util.dill_hat_lookup[
                DILL.get_hat(self._joystick_guid, self._index)
            ]

    def __init__(self, device_guid):
        """Creates a new wrapper object for the given object id.

        :param device_guid the GUID of the joystick instance to wrap
        """
        if DILL.device_exists(device_guid) is False:
            raise error.GremlinError(
                "No device with the provided GUID {} exist".format(device_guid)
            )
        self._device_guid = device_guid
        self._info = DILL.get_device_information_by_guid(self._device_guid)
        self._axis = self._init_axes()
        self._buttons = self._init_buttons()
        self._hats = self._init_hats()

    @property
    def device_guid(self):
        """Returns the GUID of the joystick.

        :return GUID for this joystick
        """
        return self._device_guid

    @property
    def name(self):
        """Returns the name of the joystick.

        :return name of the joystick
        """
        return self._info.name

    def is_axis_valid(self, axis_index):
        """Returns whether or not the specified axis exists for this device.

        :param axis_index the index of the axis in the AxisNames enum
        :return True the specified axis exists, False otherwise
        """
        for i in range(self._info.axis_count):
            if self._info.axis_map[i].axis_index == axis_index:
                return True
        return False

    def axis(self, index):
        """Returns the current value of the axis with the given index.

        The index is 1 based, i.e. the first axis starts with index 1.

        :param index the index of the axis to return to value of
        :return the current value of the axis
        """
        if index not in self._axis:
            raise error.GremlinError(
                "Invalid axis {} specified for device {}".format(
                    index,
                    self._device_guid
            ))
        return self._axis[index]

    def button(self, index):
        """Returns the current state of the button with the given index.

        The index is 1 based, i.e. the first button starts with index 1.

        :param index the index of the axis to return to value of
        :return the current state of the button
        """
        if not (0 < index < len(self._buttons)):
            raise error.GremlinError(
                "Invalid button {} specified for device {}".format(
                    index,
                    self._device_guid
                )
            )
        return self._buttons[index]

    def hat(self, index):
        """Returns the current state of the hat with the given index.

        The index is 1 based, i.e. the first hat starts with index 1.

        :param index the index of the hat to return to value of
        :return the current state of the hat
        """
        if not (0 < index < len(self._hats)):
            raise error.GremlinError(
                "Invalid hat {} specified for device {}".format(
                    index,
                    self._device_guid
                )
            )
        return self._hats[index]

    def axis_count(self):
        """Returns the number of axis of the joystick.

        :return number of axes
        """
        return self._info.axis_count

    def _init_axes(self):
        """Initializes the axes of the joystick.

        :return list of JoystickWrapper.Axis objects
        """
        axes = {}
        for i in range(self._info.axis_count):
            aid = self._info.axis_map[i].axis_index
            axes[aid] = JoystickWrapper.Axis(self._device_guid, aid)
        return axes

    def _init_buttons(self):
        """Initializes the buttons of the joystick.

        :return list of JoystickWrapper.Button objects
        """
        buttons = [None,]
        for i in range(self._info.button_count):
            buttons.append(JoystickWrapper.Button(self._device_guid, i+1))
        return buttons

    def _init_hats(self):
        """Initializes the hats of the joystick.

        :return list of JoystickWrapper.Hat objects
        """
        hats = [None,]
        for i in range(self._info.hat_count):
            hats.append(JoystickWrapper.Hat(self._device_guid, i+1))
        return hats


class JoystickProxy:

    """Allows read access to joystick state information."""

    # Dictionary of initialized joystick devices
    joystick_devices = {}

    def __getitem__(self, device_guid):
        """Returns the requested joystick instance.

        If the joystick instance exists it is returned directly, otherwise
        it is first created and then returned.

        :param device_guid GUID of the joystick device
        :return the corresponding joystick device
        """
        if device_guid not in JoystickProxy.joystick_devices:
            # If the device exists add process it and add it, otherwise throw
            # an exception
            if DILL.device_exists(device_guid):
                joy = JoystickWrapper(device_guid)
                JoystickProxy.joystick_devices[device_guid] = joy
            else:
                raise error.GremlinError(
                    "No device with guid {} exists".format(device_guid)
                )

        return JoystickProxy.joystick_devices[device_guid]


class VJoyPlugin:

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


class JoystickPlugin:

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


class KeyboardPlugin:

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


class JoystickDecorator:

    """Creates customized decorators for physical joystick devices."""

    def __init__(self, name, device_guid, mode):
        """Creates a new instance with customized decorators.

        :param name the name of the device
        :param device_guid the device id in the system
        :param mode the mode in which the decorated functions
            should be active
        """
        self.name = name
        self.mode = mode
        # Convert string based GUID to the actual GUID object
        try:
            self.device_guid = profile.parse_guid(device_guid)
        except error.ProfileError:
            logging.getLogger("system").error(
                "Invalid guid value '' received".format(device_guid)
            )
            self.device_guid = GUID_Invalid

        self.axis = functools.partial(
            _axis, device_guid=self.device_guid, mode=mode
        )
        self.button = functools.partial(
            _button, device_guid=self.device_guid, mode=mode
        )
        self.hat = functools.partial(
            _hat, device_guid=self.device_guid, mode=mode
        )


@common.SingletonDecorator
class ButtonReleaseActions(QtCore.QObject):

    """Ensures a desired action is run when a button is released."""

    def __init__(self):
        """Initializes the instance."""
        QtCore.QObject.__init__(self)

        self._registry = {}
        el = event_handler.EventListener()
        el.joystick_event.connect(self._input_event_cb)
        el.keyboard_event.connect(self._input_event_cb)
        el.virtual_event.connect(self._input_event_cb)
        eh = event_handler.EventHandler()
        self._current_mode = eh.active_mode
        eh.mode_changed.connect(self._mode_changed_cb)

    def register_callback(self, callback, physical_event):
        """Registers a callback with the system.

        :param callback the function to run when the corresponding button is
            released
        :param physical_event the physical event of the button being pressed
        """
        release_evt = physical_event.clone()
        release_evt.is_pressed = False

        if release_evt not in self._registry:
            self._registry[release_evt] = []
        # Do not record the mode since we may want to run the release action
        # independent of a mode
        self._registry[release_evt].append((callback, None))

    def register_button_release(self, vjoy_input, physical_event):
        """Registers a physical and vjoy button pair for tracking.

        This method ensures that vjoy buttons are released even if they
        have been pressed in a different mode then the active one when
        the physical button that pressed them is released.

        :param vjoy_input the vjoy button to release, represented as
            (vjoy_device_id, vjoy_button_id)
        :param physical_event the button event when release should
            trigger the release of the vjoy button
        """
        release_evt = physical_event.clone()
        release_evt.is_pressed = False

        if release_evt not in self._registry:
            self._registry[release_evt] = []
        # Record current mode so we only release if we've changed mode
        self._registry[release_evt].append((
            lambda: self._create_release_callback(vjoy_input),
            self._current_mode
        ))

    def _create_release_callback(self, vjoy_input):
        """Creates a button release callback.

        :param vjoy_input the vjoy input data to use in the release
        :return button release callback
        """
        vjoy = joystick_handling.VJoyProxy()
        # Check if the button is valid otherwise we cause Gremlin
        # to crash
        if vjoy[vjoy_input[0]].is_button_valid(vjoy_input[1]):
            vjoy[vjoy_input[0]].button(vjoy_input[1]).is_pressed = False
        else:
            logging.getLogger("system").warning(
                "Attempted to use non existent button: vJoy {:d} button {:d}".format(
                    vjoy_input[0], vjoy_input[1])
            )

    def _input_event_cb(self, evt):
        """Runs callbacks associated with the given event.

        :param evt the event to process
        """
        if evt in self._registry and not evt.is_pressed:
            for entry in self._registry[evt]:
                entry[0]()
            self._registry[evt] = []

    def _mode_changed_cb(self, mode):
        """Updates the current mode variable.

        :param mode the new mode
        """
        self._current_mode = mode


@common.SingletonDecorator
class JoystickInputSignificant:

    """Checks whether or not joystick inputs are significant."""

    def __init__(self):
        """Initializes the instance."""
        self._event_registry = {}
        self._mre_registry = {}
        self._time_registry = {}

    def should_process(self, event):
        """Returns whether or not a particular event is significant enough to
        process.

        :param event the event to check for significance
        :return True if it should be processed, False otherwise
        """
        self._mre_registry[event] = event

        if event.event_type == common.InputType.JoystickAxis:
            return self._process_axis(event)
        elif event.event_type == common.InputType.JoystickButton:
            return self._process_button(event)
        elif event.event_type == common.InputType.JoystickHat:
            return self._process_hat(event)
        else:
            logging.getLogger("system").warning(
                "Event with unknown type received"
            )
            return False

    def last_event(self, event):
        """Returns the most recent event of this type.

        :param event the type of event for which to return the most recent one
        """
        return self._mre_registry[event]

    def reset(self):
        """Resets the detector to a clean state for subsequent uses."""
        self._event_registry = {}
        self._mre_registry = {}
        self._time_registry = {}

    def _process_axis(self, event):
        """Process an axis event.

        :param event the axis event to process
        :return True if it should be processed, False otherwise
        """
        if event in self._event_registry:
            # Reset everything if we have no recent data
            if self._time_registry[event] + 5.0 < time.time():
                self._event_registry[event] = event
                self._time_registry[event] = time.time()
                return False
            # Update state
            else:
                self._time_registry[event] = time.time()
                if abs(self._event_registry[event].value - event.value) > 0.25:
                    self._event_registry[event] = event
                    self._time_registry[event] = time.time()
                    return True
                else:
                    return False
        else:
            self._event_registry[event] = event
            self._time_registry[event] = time.time()
            return False

    def _process_button(self, event):
        """Process a button event.

        :param event the button event to process
        :return True if it should be processed, False otherwise
        """
        return True

    def _process_hat(self, event):
        """Process a hat event.

        :param event the hat event to process
        :return True if it should be processed, False otherwise
        """
        return event.value != (0, 0)


def _button(button_id, device_guid, mode, always_execute=False):
    """Decorator for button callbacks.

    :param button_id the id of the button on the physical joystick
    :param device_guid the GUID of input device
    :param mode the mode in which this callback is active
    :param always_execute if True the decorated function is executed
        even when the program is not listening to inputs
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        event = event_handler.Event(
            event_type=common.InputType.JoystickButton,
            device_guid=device_guid,
            identifier=button_id
        )
        callback_registry.add(wrapper_fn, event, mode, always_execute)

        return wrapper_fn

    return wrap


def _hat(hat_id, device_guid, mode, always_execute=False):
    """Decorator for hat callbacks.

    :param hat_id the id of the button on the physical joystick
    :param device_guid the GUID of input device
    :param mode the mode in which this callback is active
    :param always_execute if True the decorated function is executed
        even when the program is not listening to inputs
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        event = event_handler.Event(
            event_type=common.InputType.JoystickHat,
            device_guid=device_guid,
            identifier=hat_id
        )
        callback_registry.add(wrapper_fn, event, mode, always_execute)

        return wrapper_fn

    return wrap


def _axis(axis_id, device_guid, mode, always_execute=False):
    """Decorator for axis callbacks.

    :param axis_id the id of the axis on the physical joystick
    :param device_guid the GUID of input device
    :param mode the mode in which this callback is active
    :param always_execute if True the decorated function is executed
        even when the program is not listening to inputs
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        event = event_handler.Event(
            event_type=common.InputType.JoystickAxis,
            device_guid=device_guid,
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
