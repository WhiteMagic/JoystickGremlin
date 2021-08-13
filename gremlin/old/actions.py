# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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

import gremlin.keyboard
import gremlin.types

from . import input_devices, joystick_handling, util


def smart_all(conditions):
    """Returns True if all conditions are True, False otherwise.

    Employs short circuiting in order to prevent unnecessary evaluations.

    :param conditions the conditions to check
    :return True if all conditions are True, False otherwise
    """
    for condition in conditions:
        if not condition():
            return False
    return True


def smart_any(conditions):
    """Returns True if any conditions is True, False if none is True.

    Employs short circuiting in order to prevent unnecessary evaluations.

    :param conditions the conditions to check
    :return True if at least one condition is True, False otherwise
    """
    for condition in conditions:
        if condition():
            return True
    return False


# class ActivationCondition:

#     """Represents a set of conditions dictating the activation of actions.

#     This class contains a set of functions which evaluate to either True or
#     False which is used to indicate whether or not the entire condition is
#     True or False.
#     """

#     rule_function = {
#         base_classes.ActivationRule.All: smart_all,
#         base_classes.ActivationRule.Any: smart_any
#     }

#     def __init__(self, conditions, rule):
#         self._conditions = conditions
#         self._rule = rule

#     def process_event(self, event, value):
#         """Returns whether or not a condition is satisfied, i.e. true.

#         :param event the event this condition was triggered through
#         :param value process event value
#         :return True if all conditions are satisfied, False otherwise
#         """
#         return ActivationCondition.rule_function[self._rule](
#             [partial(c, event, value) for c in self._conditions]
#         )


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

    """Condition verifying the state of keyboard keys.

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
        self.key = gremlin.keyboard.key_from_code(scan_code, is_extended)

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
        self.device_guid = condition.device_guid
        self.input_type = condition.input_type
        self.input_id = condition.input_id
        self.condition = condition

    def __call__(self, event, value):
        """Evaluates the condition using the condition and provided data.

        :param event raw event that caused the condition to be evaluated
        :param value the possibly modified value
        :return True if the condition is satisfied, False otherwise
        """
        joy = input_devices.JoystickProxy()[self.device_guid]

        if self.input_type == gremlin.types.InputType.JoystickAxis:
            in_range = self.condition.range[0] <= \
                       joy.axis(self.input_id).value <= \
                       self.condition.range[1]

            if self.comparison in ["inside", "outside"]:
                return in_range if self.comparison == "inside" else not in_range
            else:
                return False
        elif self.input_type == gremlin.types.InputType.JoystickButton:
            if self.comparison == "pressed":
                return joy.button(self.input_id).is_pressed
            else:
                return not joy.button(self.input_id).is_pressed
        elif self.input_type == gremlin.types.InputType.JoystickHat:
            return joy.hat(self.input_id).direction == \
                   util.hat_direction_to_tuple(self.comparison)
        else:
            logging.getLogger("system").warning(
                "Invalid input_type {} received".format(self.input_type)
            )
            return False


class VJoyCondition(AbstractCondition):

    """Condition verifying the state of a vJoy input.

    vJoy devices have three possible input types: axis, button, or hat and each
    have their corresponding possibly sates. An axis can be inside or outside
    a specific range. Buttons can be pressed or released and hats can be in
    one of eight possible directions.
    """

    def __init__(self, condition):
        """Creates a new instance.

        :param condition the condition to check against
        """
        super().__init__(condition.comparison)
        self.vjoy_id = condition.vjoy_id
        self.device_guid = None
        for dev in joystick_handling.vjoy_devices():
            if dev.vjoy_id == self.vjoy_id:
                self.device_guid = dev.device_guid
                break
        self.input_type = condition.input_type
        self.input_id = condition.input_id
        self.condition = condition

    def __call__(self, event, value):
        """Evaluates the condition using the condition and provided data.

        :param event raw event that caused the condition to be evaluated
        :param value the possibly modified value
        :return True if the condition is satisfied, False otherwise
        """
        if self.device_guid is None:
            logging.getLogger("system").warning(
                "GUID for vJoy {} not found".format(self.vjoy_id)
            )
            return False
        joy = input_devices.JoystickProxy()[self.device_guid]

        if self.input_type == gremlin.types.InputType.JoystickAxis:
            in_range = self.condition.range[0] <= \
                       joy.axis(self.input_id).value <= \
                       self.condition.range[1]

            if self.comparison in ["inside", "outside"]:
                return in_range if self.comparison == "inside" else not in_range
            else:
                return False
        elif self.input_type == gremlin.types.InputType.JoystickButton:
            if self.comparison == "pressed":
                return joy.button(self.input_id).is_pressed
            else:
                return not joy.button(self.input_id).is_pressed
        elif self.input_type == gremlin.types.InputType.JoystickHat:
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
