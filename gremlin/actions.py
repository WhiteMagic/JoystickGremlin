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

import copy
import logging
import threading
import time

from PyQt5 import QtCore, QtMultimedia

from . import common, control_action, error, fsm, input_devices, \
    joystick_handling, macro, tts


# Text to speech instance used by the tts action
tts_instance = tts.TextToSpeech()

# Qt media player instance
media_player = QtMultimedia.QMediaPlayer()


def _axis_to_axis(event, value, condition, vjoy_device_id, vjoy_input_id):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].axis(vjoy_input_id).value = value.current


def _axis_to_button(event, value, condition, vjoy_device_id, vjoy_input_id):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].button(vjoy_input_id).is_pressed = value.current


def _button_to_button(event, value, condition, vjoy_device_id, vjoy_input_id):
    if event.is_pressed:
        input_devices.ButtonReleaseActions().register_button_release(
            (vjoy_device_id, vjoy_input_id), event
        )

    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].button(vjoy_input_id).is_pressed = value.current


def _hat_to_button(event, value, condition, vjoy_device_id, vjoy_input_id):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].button(vjoy_input_id).is_pressed = value.current


def _hat_to_hat(event, value, condition, vjoy_device_id, vjoy_input_id):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].hat(vjoy_input_id).direction = value.current


def _key_to_button(event, value, condition, vjoy_device_id, vjoy_input_id):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].button(vjoy_input_id).is_pressed = value.current


def _remap_to_keyboard(event, value, condition, macro_press, macro_release):
    if value.current:
        macro.MacroManager().add_macro(macro_press, condition, event)
    else:
        macro.MacroManager().add_macro(macro_release, condition, event)


def _pause(event, value, condition):
    if value.current:
        control_action.pause()


def _play_sound(event, value, condition, fname, volume):
    if value.current:
        media_player.setMedia(
            QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(fname)))
        media_player.setVolume(volume)
        media_player.play()


def _resume(event, value, condition):
    if value.current:
        control_action.resume()


def _toggle_pause_resume(event, value, condition):
    if value.current:
        control_action.toggle_pause_resume()


def _text_to_speech(event, value, condition, text):
    if value.current:
        tts_instance.speak(tts.text_substitution(text))


def _temporary_mode_switch(event, value, condition, mode):
    if value.current:
        input_devices.ButtonReleaseActions().register_callback(
            control_action.switch_to_previous_mode,
            event
        )
        control_action.switch_mode(mode)


def _switch_mode(event, value, condition, mode):
    if value.current:
        control_action.switch_mode(mode)


def _switch_to_previous_mode(event, value, condition):
    if value.current:
        control_action.switch_to_previous_mode()


def _cycle_modes(event, value, condition, mode_list):
    if value.current:
        control_action.cycle_modes(mode_list)


def _run_macro(event, value, condition, macro_fn):
    if value.current:
        macro.MacroManager().add_macro(macro_fn, condition, event)


def _response_curve(event, value, condition, curve_fn, deadzone_fn):
    value.current = curve_fn(deadzone_fn(value.current))


def _split_axis(event, value, condition, split_fn):
    split_fn(value.current)


def _map_hat(vjoy_device_id, vjoy_input_id, data):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].hat(vjoy_input_id).direction = data


def _map_key(vjoy_device_id, vjoy_input_id, data):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].button(vjoy_input_id).is_pressed = data


class Value:

    """Represents an input value, keeping track of raw and "seen" value."""

    def __init__(self, raw):
        """Creates a new value and initializes it.

        :param raw the initial raw data
        """
        self._raw = raw
        self._current = raw

    @property
    def raw(self):
        """Returns the raw unmodified value.

        :return raw unmodified value
        """
        return self._raw

    @property
    def current(self):
        """Returns the current, potentially, modified value.

        :return current and potentially modified value
        """
        return self._current

    @current.setter
    def current(self, current):
        """Sets the current value which may differ from the raw one.

        :param current the new current value
        """
        self._current = current


class Factory:

    """Contains methods to create a variety of actions."""

    @staticmethod
    def play_sound(fname, volume):
        return lambda event, value, condition: _play_sound(
            event,
            value,
            condition,
            fname,
            volume
        )

    @staticmethod
    def remap_input(from_type, to_type, vjoy_device_id, vjoy_input_id):
        remap_lookup = {
            (common.InputType.JoystickAxis,
             common.InputType.JoystickAxis): _axis_to_axis,
            (common.InputType.JoystickAxis,
             common.InputType.JoystickButton): _axis_to_button,
            (common.InputType.JoystickButton,
             common.InputType.JoystickButton): _button_to_button,
            (common.InputType.JoystickHat,
             common.InputType.JoystickHat): _hat_to_hat,
            (common.InputType.JoystickHat,
             common.InputType.JoystickButton): _hat_to_button,
            (common.InputType.Keyboard,
             common.InputType.JoystickButton): _key_to_button,
        }

        remap_fn = remap_lookup.get((from_type, to_type), None)
        if remap_fn is not None:
            return lambda event, value, condition: remap_fn(
                event,
                value,
                condition,
                vjoy_device_id,
                vjoy_input_id,
            )

    @staticmethod
    def remap_to_keyboard(macro_press, macro_release):
        return lambda event, value, condition: _remap_to_keyboard(
            event,
            value,
            condition,
            macro_press,
            macro_release
        )

    @staticmethod
    def split_axis(split_fn):
        return lambda event, value, condition: _split_axis(
            event,
            value,
            condition,
            split_fn
        )

    @staticmethod
    def response_curve(curve_fn, deadzone_fn):
        return lambda event, value, condition: _response_curve(
            event,
            value,
            condition,
            curve_fn,
            deadzone_fn
        )

    @staticmethod
    def run_macro(macro_fn):
        return lambda event, value, condition: _run_macro(
            event,
            value,
            condition,
            macro_fn
        )

    @staticmethod
    def temporary_mode_switch(mode):
        return lambda event, value, conditition: _temporary_mode_switch(
            event,
            value,
            conditition,
            mode
        )

    @staticmethod
    def switch_mode(mode):
        return lambda event, value, condition: _switch_mode(
            event,
            value,
            condition,
            mode
        )

    @staticmethod
    def previous_mode():
        return lambda event, value, condition: _switch_to_previous_mode(
            event,
            value,
            condition
        )

    @staticmethod
    def cycle_modes(mode_list):
        return lambda event, value, condition: _cycle_modes(
            event,
            value,
            condition,
            mode_list
        )

    @staticmethod
    def pause():
        return lambda event, value, condition: _pause(
            event,
            value,
            condition
        )

    @staticmethod
    def resume():
        return lambda event, value, condition: _resume(
            event,
            value,
            condition
        )

    @staticmethod
    def toggle_pause_resume():
        return lambda event, value, condition: _toggle_pause_resume(
            event,
            value,
            condition
        )

    @staticmethod
    def text_to_speech(text):
        return lambda event, value, condition: _text_to_speech(
            event,
            value,
            condition,
            text
        )


class VirtualButton:

    """Implements a button like interface."""

    def __init__(self):
        """Creates a new instance."""
        self._fsm = self._initialize_fsm()
        self._callback = None
        self._is_pressed = False

    def _initialize_fsm(self):
        """Initializes the state of the button FSM."""
        states = ["up", "down"]
        actions = ["press", "release"]
        transitions = {
            ("up", "press"): fsm.Transition(self._press, "down"),
            ("up", "release"): fsm.Transition(self._noop, "up"),
            ("down", "release"): fsm.Transition(self._release, "up"),
            ("down", "press"): fsm.Transition(self._noop, "down")
        }
        return fsm.FiniteStateMachine("up", states, actions, transitions)

    def _press(self):
        """Executes the "press" action."""
        self._is_pressed = True
        self._callback(Value(self.is_pressed))

    def _release(self):
        """Executes the "release" action."""
        self._is_pressed = False
        self._callback(Value(self.is_pressed))

    def _noop(self):
        """Performs no action."""
        pass

    @property
    def is_pressed(self):
        """Returns whether or not the virtual button is pressed.

        :return True if the button is pressed, False otherwise
        """
        return self._is_pressed


class AxisButton(VirtualButton):

    """Virtual button based around an axis."""

    def __init__(self, lower_limit, upper_limit):
        """Creates a new instance.

        :param lower_limit lower axis value where the button range starts
        :param upper_limit upper axis value where the button range stops
        """
        super().__init__()
        self._lower_limit = min(lower_limit, upper_limit)
        self._upper_limit = max(lower_limit, upper_limit)

    def process(self, value, callback):
        """Processes events for the virtual axis button.

        :param value axis position
        :param callback the function to call when the state changes
        """
        self._callback = callback
        if self._lower_limit <= value <= self._upper_limit:
            self._fsm.perform("press")
        else:
            self._fsm.perform("release")


class HatButton(VirtualButton):

    """Virtual button based around a hat."""

    def __init__(self, directions):
        """Creates a new instance.

        :param directions hat directions used with this button
        """
        super().__init__()
        self._directions = directions

    def process(self, value, callback):
        """Process events for the virtual hat button.

        :param value hat direction
        :param callback the function to call when the state changes
        """
        self._callback = callback
        if value in self._directions:
            self._fsm.perform("press")
        else:
            self._fsm.perform("release")


class AbstractActionContainer:

    """Code implementation used by containers."""

    def __init__(self, action_sets, virtual_button):
        """Creates a new instance.

        :param action_sets the actions that are part of the container
        :param virtual_button virtual button instance used with this container
        """
        self.action_sets = action_sets
        self.virtual_button = virtual_button

    def _process_value(self, value):
        """Processes a value through the container, handling activation etc.

        :param value the original input value
        :return value once processed by the activation condition, if present
        """
        use_value = value
        if self.virtual_button is not None:
            use_value = Value(self.virtual_button.is_pressed)
        return use_value

    def __call__(self, event, value):
        """Executes the container.

        This will run the appropriate action contained in the container if
        activation condition and other checks are passed successfully.

        :param event the event triggering the execution
        :param value the even'ts value with potential modifications from other
            prior executions
        """
        if self.virtual_button is not None:
            self.virtual_button.process(
                event.value,
                lambda x: self._execute_call(event, x)
            )
        else:
            self._execute_call(event, value)

    def _execute_call(self, event, value):
        """Performs the actual execution of the container.

        This method is called by __call__ and has to be implemented by
        derived classes to implement the actual execution functionality.

        :param event the event triggering the execution
        :param value the even'ts value with potential modifications from other
            prior executions
        """
        raise error.GremlinError("Missing _execute_call implementation")


class Basic(AbstractActionContainer):

    """Implements the execution logic of basic containers."""

    def __init__(self, action_sets, virtual_button=None):
        """Creates a new instance.

        :param action_sets the actions that are part of the container
        :param virtual_button virtual button instance used with this container
        """
        super().__init__(action_sets, virtual_button)
        assert len(self.action_sets) == 1

    def _execute_call(self, event, value):
        """Executes the action stored within the container.

        :param event the event triggering the execution
        :param value the even'ts value with potential modifications from other
            prior executions
        """
        for action in self.action_sets[0]:
            action(event, value, self.virtual_button)


class Tempo(AbstractActionContainer):

    """Implements the execution logic of tempo containers."""

    # This entire container only makes sense for button like inputs

    def __init__(self, action_sets, virtual_button, duration):
        """Creates a new instance.

        :param action_sets the actions that are part of the container
        :param virtual_button virtual button instance used with this container
        :param duration time after which the long press action is used
        """
        super().__init__(action_sets, virtual_button)
        self.duration = duration
        self.start_time = 0
        self.timer = None
        self.value_press = None
        self.event_press = None

    def _execute_call(self, event, value):
        """Executes the action stored within the container.

        :param event the event triggering the execution
        :param value the even'ts value with potential modifications from other
            prior executions
        """
        # Has to change and use timers internally probably
        # 1. both press and release have to be sent for some actions, such
        #   as macro or remap
        # 2. want to be able to do things where long is being held down and
        #   start doing it as soon as the delay has expired

        if isinstance(value.current, bool) and value.current:
            self.value_press = copy.deepcopy(value)
            self.event_press = event.clone()

        if value.current:
            self.start_time = time.time()
            self.timer = threading.Timer(self.duration, self._long_press)
            self.timer.start()
        else:
            if (self.start_time + self.duration) > time.time():
                self.timer.cancel()
                for action in self.action_sets[0]:
                    action(
                        self.event_press,
                        self.value_press,
                        self.virtual_button
                    )
                time.sleep(0.1)
                for action in self.action_sets[0]:
                    action(event, value, self.virtual_button)
            else:
                for action in self.action_sets[1]:
                    action(event, value, self.virtual_button)

            self.timer = None

    def _long_press(self):
        """Callback executed, when the delay expires."""
        for action in self.action_sets[1]:
            action(
                self.event_press,
                self.value_press,
                self.virtual_button
            )


class Chain(AbstractActionContainer):

    """Implements the execution logic of the chain container."""

    def __init__(self, action_sets, virtual_button, timeout=0.0):
        """Creates a new instance.

        :param action_sets the actions that are part of the container
        :param virtual_button virtual button instance used with this container
        :param timeout duration after which the chain resets to the first entry
        """
        super().__init__(action_sets, virtual_button)
        self.index = 0
        self.timeout = timeout
        self.last_execution = 0.0
        self.last_value = None

    def _execute_call(self, event, value):
        """Executes the action stored within the container.

        :param event the event triggering the execution
        :param value the even'ts value with potential modifications from other
            prior executions
        """
        if self.timeout > 0.0:
            if self.last_execution + self.timeout < time.time():
                self.index = 0
                self.last_execution = time.time()

        # TODO: This behaves somewhat odd with hats and axes. Axes do nothing
        #   as they make no sense while hats only switch to the next element
        #   if the hat is let go.

        # FIXME: Currently this allows the use of "hat as button" and
        #   "hat as hat" in the same chain which is entirely useless and
        #   shouldn't be done but can't truly be prevented.

        # FIXME: Currently this behaves oddly with axis macros due to them only
        #   entering this section when the "button" is pressed and not on
        #   release.

        # Execute action
        for action in self.action_sets[self.index]:
            action(event, value, self.virtual_button)

        # Decide how to switch to next action
        if event.event_type in [
            common.InputType.JoystickAxis,
            common.InputType.JoystickHat
        ]:
            if self.virtual_button is not None:
                if not value.current:
                    self.index = (self.index + 1) % len(self.action_sets)
            else:
                if event.event_type == common.InputType.JoystickHat:
                    if event.value == (0, 0):
                        self.index = (self.index + 1) % len(self.action_sets)
                    self.last_value = event.value
                else:
                    logging.getLogger("system").warning(
                        "Trying to use chain container with an axis, this is "
                        "not a sensible thing."
                    )
                    return
        else:
            if not value.current:
                self.index = (self.index + 1) % len(self.action_sets)


# class SmartToggle(AbstractActionContainer):
#
#     def __init__(self, actions, duration=0.25):
#         if not isinstance(actions, list):
#             actions = [actions]
#         super().__init__(actions)
#         self.duration = duration
#
#         self._init_time = 0
#         self._is_toggled = False
#
#     def _execute_call(self, value):
#         # FIXME: breaks when held while toggle is active
#         if value:
#             self._init_time = time.time()
#             if not self._is_toggled:
#                 self.actions[0](value)
#         else:
#             if time.time() < self._init_time + self.duration:
#                 # Toggle action
#                 if self._is_toggled:
#                     self.actions[0](value)
#                 self._is_toggled = not self._is_toggled
#             else:
#                 # Tap action
#                 self.actions[0](value)
#
#
# class DoubleTap(AbstractActionContainer):
#
#     def __init__(self, actions, timeout=0.5):
#         if not isinstance(actions, list):
#             actions = [actions]
#         super().__init__(actions)
#         self.timeout = timeout
#
#         self._init_time = 0
#         self._triggered = False
#
#     def _execute_call(self, value):
#         if value:
#             if time.time() > self._init_time + self.timeout:
#                 self._init_time = time.time()
#             else:
#                 self.actions[0](value)
#                 self._triggered = True
#         elif not value and self._triggered:
#             self.actions[0](value)
#             self._triggered = False
