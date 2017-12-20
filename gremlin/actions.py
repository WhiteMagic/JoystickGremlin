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

from abc import abstractmethod, ABCMeta
from functools import partial
import logging
import time

from . import base_classes, common, fsm, input_devices, macro, util


def smart_all(conditions):
    """Returns True if all conditions are True, False otherwise.

    Employs short circuiting in order to prevent unnecessary evalutions.

    :param conditions the conditions to check
    :return True if all conditions are True, False otherwise
    """
    for condition in conditions:
        if not condition():
            return False
    return True


def smart_any(conditions):
    """Returns True if any conditions is True, False if none is True.

    Employs short circuiting in order to prevent unnecessary evalutions.

    :param conditions the conditions to check
    :return True if at least one condition is True, False otherwise
    """
    for condition in conditions:
        if condition():
            return True
    return False


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


class ActivationCondition:

    """Represents a set of conditions dictating the activation of actions.

    This class contains a set of functions which evaluate to either True or
    False which is used to indicate whether or not the entire condition is
    True or False.
    """

    rule_function = {
        base_classes.ActivationRule.All: smart_all,
        base_classes.ActivationRule.Any: smart_any
    }

    def __init__(self, conditions, rule):
        self._conditions = conditions
        self._rule = rule

    def process_event(self, event, value):
        """Returns whether or not a condition is satisfied, i.e. true.

        :param event the event this condition was triggered through
        :param value process event value
        :return True if all conditions are satisfied, False otherwise
        """
        return ActivationCondition.rule_function[self._rule](
            [partial(c, event, value) for c in self._conditions]
        )


class AbstractCondition(metaclass=ABCMeta):

    """Represents an abstract condition.

    Conditions evaluate to either True or False and are given an event as well
    as possibly processed Value when being evaluated.
    """

    def __init__(self, comparison):
        """Creates a new condition with a specific comparision operation.

        :param comparison the comparison operation to perform when evaluated
        """
        self.comparison = comparison

    @abstractmethod
    def __call__(self, event, value):
        """Evaluates the condition using the condition and provided data.

        :param event raw event that caused the condition to be evaluated
        :param value the possibly modified value
        :return True if the condition is satisfied, False otherwise
        """
        pass


class KeyboardCondition(AbstractCondition):

    """Condition veryfing the state of keyboard keys.

    The conditions that can be checked on a keyboard is whether or not a
    particular key is pressed or released.
    """

    def __init__(self, scan_code, is_extended, comparison):
        """Creates a new instance.

        :param scan_code the scan code of the key to evaluate
        :param is_extended whether or not the key code is extended
        :param comparison the comparison operation to perform when evaluated
        """
        super().__init__(comparison)
        self.key = macro.key_from_code(scan_code, is_extended)

    def __call__(self, event, value):
        """Evaluates the condition using the condition and provided data.

        :param event raw event that caused the condition to be evaluated
        :param value the possibly modified value
        :return True if the condition is satisfied, False otherwise
        """
        key_pressed = input_devices.Keyboard().is_pressed(self.key)
        if self.comparison == "pressed":
            return key_pressed
        else:
            return not key_pressed


class JoystickCondition(AbstractCondition):

    """Condition verifying the state of a joystick input.

    Joysticks have three possible input types: axis, button, or hat and each
    have their corresponding possibly sates. An axis can be inside or outside
    a specific range. Buttons can be pressed or released and hats can be in
    one of eight possible directions.
    """

    def __init__(self, condition):
        """Creates a new instance.

        :param condition the condition to check against
        """
        super().__init__(condition.comparison)
        self.windows_id = condition.windows_id
        self.input_type = condition.input_type
        self.input_id = condition.input_id
        self.condition = condition

    def __call__(self, event, value):
        """Evaluates the condition using the condition and provided data.

        :param event raw event that caused the condition to be evaluated
        :param value the possibly modified value
        :return True if the condition is satisfied, False otherwise
        """
        joy = input_devices.JoystickProxy()[self.windows_id]

        if self.input_type == common.InputType.JoystickAxis:
            in_range = self.condition.range[0] <= \
                       joy.axis(self.input_id).value <= \
                       self.condition.range[1]

            if self.comparison in ["inside", "outside"]:
                return in_range if self.comparison == "inside" else not in_range
            else:
                return False
        elif self.input_type == common.InputType.JoystickButton:
            if self.comparison == "pressed":
                return joy.button(self.input_id).is_pressed
            else:
                return not joy.button(self.input_id).is_pressed
        elif self.input_type == common.InputType.JoystickHat:
            return joy.hat(self.input_id).direction == \
                   util.hat_direction_to_tuple(self.comparison)
        else:
            logging.getLogger("system").warning(
                "Invalid input_type {} received".format(self.input_type)
            )
            return False


class InputActionCondition(AbstractCondition):

    """Condition verifying the state of the triggering input itself.

    This checks the state of the input that triggered the event in the first
    place.
    """

    def __init__(self, comparison):
        """Creates a new instance.

        :param comparison the comparison operation to perform when evaluated
        """
        super().__init__(comparison)

    def __call__(self, event, value):
        """Evaluates the condition using the condition and provided data.

        :param event raw event that caused the condition to be evaluated
        :param value the possibly modified value
        :return True if the condition is satisfied, False otherwise
        """
        if self.comparison == "pressed":
            return value.current
        elif self.comparison == "released":
            return not value.current
        elif self.comparison == "always":
            return True
        else:
            return False


class VirtualButton(metaclass=ABCMeta):

    """Implements a button like interface."""

    def __init__(self):
        """Creates a new instance."""
        self._fsm = self._initialize_fsm()
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

    def process_event(self, event, value):
        """Process the input event and updates the value as needed.

        :param event the input event that triggered this virtual button
        :param value the value representation of the event's value
        :return True if a state transition occured, False otherwise
        """
        state_transition = self._do_process(event, value)
        value.current = self.is_pressed
        return state_transition

    @abstractmethod
    def _do_process(self, event, value):
        """Implementation of the virtual button logic.

        This method has to be implemented in subclasses to provide the logic
        deciding when a state transition, i.e. button press or release
        occurs.

        :param event the input event that is used to decide onthe state
        :param value the value representation of the event's value
        :return True if a state transition occured, False otherwise
        """
        pass

    def _press(self):
        """Executes the "press" action."""
        self._is_pressed = True
        return True

    def _release(self):
        """Executes the "release" action."""
        self._is_pressed = False
        return True

    def _noop(self):
        """Performs no action."""
        return False

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
        self._last_value = None
        self.forced_activation = False

    def _do_process(self, event, value):
        """Implementation of the virtual button logic.

        :param event the input event that is used to decide onthe state
        :param value the value representation of the event's value
        :return True if a state transition occured, False otherwise
        """
        self.forced_activation = False
        if self._last_value is None:
            self._last_value = event.value
        else:
            # Check if we moved over the activation region between two
            # consecutive measurements
            if self._last_value < self._lower_limit and \
                    event.value > self._upper_limit:
                self.forced_activation = True
            elif self._last_value > self._upper_limit and \
                    event.value < self._lower_limit:
                self.forced_activation = True

        self._last_value = event.value

        if not self.forced_activation:
            if self._lower_limit <= event.value <= self._upper_limit:
                return self._fsm.perform("press")
            else:
                return self._fsm.perform("release")
        else:
            return self._fsm.perform("press")


class HatButton(VirtualButton):

    """Virtual button based around a hat."""

    def __init__(self, directions):
        """Creates a new instance.

        :param directions hat directions used with this button
        """
        super().__init__()
        self._directions = directions

    def _do_process(self, event, value):
        """Implementation of the virtual button logic.

        :param event the input event that is used to decide onthe state
        :param value the value representation of the event's value
        :return True if a state transition occured, False otherwise
        """
        if util.hat_tuple_to_direction(event.value) in self._directions:
            return self._fsm.perform("press")
        else:
            return self._fsm.perform("release")
