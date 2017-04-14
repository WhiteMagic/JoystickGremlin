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

import time

from . import control_action, error, fsm, input_devices, joystick_handling, macro, tts


tts_instance = tts.TextToSpeech()


class ButtonCondition:

    def __init__(self, on_press, on_release):
        self.on_press = on_press
        self.on_release = on_release

    def __call__(self, value):
        if self.on_press and self.on_release:
            return True
        elif self.on_press:
            return value.current is True
        elif self.on_release:
            return value.current is False


class AxisCondition:

    def __init__(self):
        pass

    def __call__(self, value):
        return True


def axis_to_axis(event, value, condition, vjoy_device_id, vjoy_input_id):
    if condition(value):
        vjoy = joystick_handling.VJoyProxy()
        vjoy[vjoy_device_id].axis(vjoy_input_id).value = value.current


def button_to_button(event, value, condition, vjoy_device_id, vjoy_input_id):
    if condition.on_press and condition.on_release:
        if event.is_pressed:
            input_devices.AutomaticButtonRelease().register(
                (vjoy_device_id, vjoy_input_id), event
            )

    if condition(value):
        vjoy = joystick_handling.VJoyProxy()
        vjoy[vjoy_device_id].button(vjoy_input_id).is_pressed = value.current


def pause(event, value, condition):
    if condition(value):
        control_action.pause()


def resume(event, value, condition):
    if condition(value):
        control_action.resume()


def toggle_pause_resume(event, value, condition):
    if condition(value):
        control_action.toggle_pause_resume()


def text_to_speech(event, value, condition, text):
    if condition(value):
        tts_instance.speak(tts.text_substitution(text))


def switch_mode(event, value, condition, mode):
    if condition(value):
        control_action.switch_mode(mode)


def switch_to_previous_mode(event, value, condition):
    if condition(value):
        control_action.switch_to_previous_mode()


def cycle_modes(event, value, condition, mode_list):
    if condition(value):
        control_action.cycle_modes(mode_list)


def run_macro(event, value, condition, macro_fn):
    if condition(value):
        macro_fn.run()


def response_curve(event, value, condition, curve_fn, deadzone_fn):
    if condition(value):
        value.current = curve_fn(deadzone_fn(value.current))


def split_axis(event, value, condition, split_fn):
    if condition(value):
        split_fn(value.current)


def map_hat(vjoy_device_id, vjoy_input_id, data):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].hat(vjoy_input_id).direction = data


def map_key(vjoy_device_id, vjoy_input_id, data):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device_id].button(vjoy_input_id).is_pressed = data


def press_button(vjoy_device, vjoy_input):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device].button(vjoy_input).is_pressed = True


def release_button(vjoy_device, vjoy_input):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device].button(vjoy_input).is_pressed = False


# FIXME: make this somehow use the actual macro default
def tap_button(vjoy_device, vjoy_input, delay=0.1):
    vjoy = joystick_handling.VJoyProxy()
    vjoy[vjoy_device].button(vjoy_input).is_pressed = True
    time.sleep(delay)
    vjoy[vjoy_device].button(vjoy_input).is_pressed = False


def tap_key(key):
    assert isinstance(key, macro.Keys.Key)
    macro._send_key_down(key)
    time.sleep(macro.default_delay)
    macro._send_key_up(key)


def run_on_press(function, is_pressed):
    if is_pressed:
        return function(is_pressed)


def run_on_release(function, is_pressed):
    if not is_pressed:
        return function(is_pressed)


# def map_button(vjoy_device_id, vjoy_input_id, event, on_press=True, on_release=True):
#     vjoy = joystick_handling.VJoyProxy()
#
#     vjoy[vjoy_device_id].button(vjoy_input_id).is_pressed = event.is_pressed


# def run_function(function, on_press, on_release, condition_value):
#     if on_press and on_release:
#         return function
#     elif on_press and not on_release:
#         return lambda data: run_on_press(function, data)
#     elif not on_press and on_release:
#         return lambda data: run_on_release(function, data)


class Value:

    def __init__(self, raw):
        self._raw = raw
        self._current = raw

    @property
    def raw(self):
        return self._raw

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, current):
        self._current = current


class Factory:

    @staticmethod
    def axis_to_axis(vjoy_device_id, vjoy_button_id):
        return lambda event: axis_to_axis(
            vjoy_device_id,
            vjoy_button_id,
            event
        )

    @staticmethod
    def button_to_button(condition, vjoy_device_id, vjoy_button_id):
        return lambda event, value: button_to_button(
            event,
            value,
            condition,
            vjoy_device_id,
            vjoy_button_id,
        )

    @staticmethod
    def axis_to_axis(condition, vjoy_device_id, vjoy_button_id):
        return lambda event, value: axis_to_axis(
            event,
            value,
            condition,
            vjoy_device_id,
            vjoy_button_id,
        )

    @staticmethod
    def remap_input(condition, vjoy_device_id, vjoy_button_id):
        if isinstance(condition, ButtonCondition):
            return Factory.button_to_button(condition, vjoy_device_id, vjoy_button_id)
        elif isinstance(condition, AxisCondition):
            return Factory.axis_to_axis(condition, vjoy_device_id, vjoy_button_id)

    # @staticmethod
    # def map_hat(vjoy_device_id, vjoy_button_id):
    #     return lambda direction: map_hat(
    #         vjoy_device_id,
    #         vjoy_button_id,
    #         direction
    #     )
    #
    # @staticmethod
    # def tap_button(vjoy_device_id, vjoy_button_id):
    #     return lambda is_pressed: run_on_press(
    #         lambda: tap_button(vjoy_device_id, vjoy_button_id),
    #         is_pressed
    #     )
    #
    # @staticmethod
    # def tap_key(key):
    #     return lambda is_pressed: run_on_press(
    #         lambda: tap_key(key),
    #         is_pressed
    #     )

    @staticmethod
    def split_axis(condition, split_fn):
        return lambda event, value: split_axis(
            event,
            value,
            condition,
            split_fn
        )

    @staticmethod
    def response_curve(condition, curve_fn, deadzone_fn):
        return lambda event, value: response_curve(
            event,
            value,
            condition,
            curve_fn,
            deadzone_fn
        )

    @staticmethod
    def run_macro(condition, macro_fn):
        return lambda event, value: run_macro(
            event,
            value,
            condition,
            macro_fn
        )

    @staticmethod
    def switch_mode(condition, mode):
        return lambda event, value: switch_mode(
            event,
            value,
            condition,
            mode
        )

    @staticmethod
    def previous_mode(condition):
        return lambda event, value: switch_to_previous_mode(
            event,
            value,
            condition
        )

    @staticmethod
    def cycle_modes(condition, mode_list):
        return lambda event, value: cycle_modes(
            event,
            value,
            condition,
            mode_list
        )

    @staticmethod
    def pause(condition):
        return lambda event, value: pause(
            event,
            value,
            condition
        )

    @staticmethod
    def resume(condition):
        return lambda event, value: resume(
            event,
            value,
            condition
        )

    @staticmethod
    def toggle_pause_resume(condition):
        return lambda event, value: toggle_pause_resume(
            event,
            value,
            condition
        )

    @staticmethod
    def text_to_speech(condition, text):
        return lambda event, value: text_to_speech(
            event,
            value,
            condition,
            text
        )


class AxisButton:

    def __init__(self, lower_limit, upper_limit):
        self._lower_limit = min(lower_limit, upper_limit)
        self._upper_limit = max(lower_limit, upper_limit)
        self.callback = None
        self._fsm = self._initialize_fsm()

    def _initialize_fsm(self):
        states = ["up", "down"]
        actions = ["press", "release"]
        transitions = {
            ("up", "press"): fsm.Transition(self._press, "down"),
            ("up", "release"): fsm.Transition(self._noop, "up"),
            ("down", "release"): fsm.Transition(self._release, "up"),
            ("down", "press"): fsm.Transition(self._noop, "down")
        }
        return fsm.FiniteStateMachine("up", states, actions, transitions)

    def process(self, value, callback):
        self.callback = callback
        if self._lower_limit <= value <= self._upper_limit:
            self._fsm.perform("press")
        else:
            self._fsm.perform("release")

    def _press(self):
        self.callback(True)

    def _release(self):
        self.callback(False)

    def _noop(self):
        pass

    @property
    def is_pressed(self):
        return self._fsm.current_state == "down"


class AbstractActionContainer:

    def __init__(self, actions):
        self.actions = actions

    def __call__(self, value):
        raise error.GremlinError("Missing execute implementation")


class Basic(AbstractActionContainer):

    def __init__(self, actions):
        if not isinstance(actions, list):
            actions = [actions]
        super().__init__(actions)
        assert len(self.actions) == 1

    def __call__(self, event, value):
        self.actions[0](event, value)


class Tempo(AbstractActionContainer):

    def __init__(self, actions, duration):
        super().__init__(actions)
        self.duration = duration
        self.start_time = 0

    def __call__(self, value):
        if value:
            self.start_time = time.time()
        else:
            if (self.start_time + self.duration) > time.time():
                self.actions[0](value)
            else:
                self.actions[1](value)


class Chain(AbstractActionContainer):

    def __init__(self, actions, timeout=0.0):
        super().__init__(actions)
        self.index = 0
        self.timeout = timeout
        self.last_execution = 0.0

    def __call__(self, value):
        # FIXME: reset via timeout not yet implemented
        if self.timeout > 0.0:
            if self.last_execution + self.timeout < time.time():
                self.index = 0
                self.last_execution = time.time()

        self.actions[self.index](value)
        if not value:
            self.index = (self.index + 1) % len(self.actions)


class SmartToggle(AbstractActionContainer):

    def __init__(self, actions, duration=0.25):
        if not isinstance(actions, list):
            actions = [actions]
        super().__init__(actions)
        self.duration = duration

        self._init_time = 0
        self._is_toggled = False

    def __call__(self, value):
        # FIXME: breaks when held while toggle is active
        if value:
            self._init_time = time.time()
            if not self._is_toggled:
                self.actions[0](value)
        else:
            if time.time() < self._init_time + self.duration:
                # Toggle action
                if self._is_toggled:
                    self.actions[0](value)
                self._is_toggled = not self._is_toggled
            else:
                # Tap action
                self.actions[0](value)


class DoubleTap(AbstractActionContainer):

    def __init__(self, actions, timeout=0.5):
        if not isinstance(actions, list):
            actions = [actions]
        super().__init__(actions)
        self.timeout = timeout

        self._init_time = 0
        self._triggered = False

    def __call__(self, value):
        if value:
            if time.time() > self._init_time + self.timeout:
                self._init_time = time.time()
            else:
                self.actions[0](value)
                self._triggered = True
        elif not value and self._triggered:
            self.actions[0](value)
            self._triggered = False
