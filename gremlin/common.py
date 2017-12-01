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

import enum


class InputType(enum.Enum):

    """Enumeration of possible UI input types."""

    Keyboard = 1
    JoystickAxis = 2
    JoystickButton = 3
    JoystickHat = 4
    Count = 5


def index_to_direction(direction):
    """Returns a direction index to a direction name.

    :param direction index of the direction to convert
    :return text representation of the direction index
    """
    lookup = {
        1: "Up",
        2: "Up & Right",
        3: "Right",
        4: "Down & Right",
        5: "Down",
        6: "Down & Left",
        7: "Left",
        8: "Up & Left"
    }
    return lookup[int(direction)]


def input_type_to_tag(input_type):
    """Returns the XML tag corresponding to the given InputType enum.

    :param input_type InputType enum to translate into a XML tag
    :return XML tag corresponding to the provided InputType enum
    """
    lookup = {
        InputType.JoystickAxis: "axis",
        InputType.JoystickButton: "button",
        InputType.JoystickHat: "hat",
        InputType.Keyboard: "key",
    }
    if input_type in lookup:
        return lookup[input_type]
    else:
        raise gremlin.error.ProfileError(
            "Invalid input type specified {}".format(input_type)
        )

def tag_to_input_type(tag):
    """Returns the InputType corresponding to the provided tag.

    :param tag textual representation of the input type
    :return InputType corresponding to the given tag
    """
    lookup = {
        "axis": InputType.JoystickAxis,
        "button": InputType.JoystickButton,
        "hat": InputType.JoystickHat,
        "key": InputType.Keyboard
    }
    if tag in lookup:
        return lookup[tag]
    else:
        raise gremlin.error.ProfileError(
            "Invalid input type specified {}".format(tag)
        )


# Mapping from InputType values to their textual representation
input_type_to_name = {
    InputType.Keyboard: "Keyboard",
    InputType.JoystickAxis: "Axis",
    InputType.JoystickButton: "Button",
    InputType.JoystickHat: "Hat"
}


# Mapping from hat direction tuples to their textual representation
direction_tuple_lookup = {
    (0, 0): "Center",
    (0, 1): "North",
    (1, 1): "North East",
    (1, 0): "East",
    (1, -1): "South East",
    (0, -1): "South",
    (-1, -1): "South West",
    (-1, 0): "West",
    (-1, 1): "North West",
    "Center": (0, 0),
    "North": (0, 1),
    "North East": (1, 1),
    "East": (1, 0),
    "South East": (1, -1),
    "South": (0, -1),
    "South West": (-1, -1),
    "West": (-1, 0),
    "North West": (-1, 1)
}


# Names of vJoy axis according to their index
vjoy_axis_names = [
    "X",
    "Y",
    "Z",
    "X Rotation",
    "Y Rotation",
    "Z Rotation",
    "Slider",
    "Dial"
]


class SingletonDecorator:

    """Decorator turning a class into a singleton."""

    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance


class DeviceType(enum.Enum):

    """Enumeration of the different possible input types."""

    Keyboard = 1
    Joystick = 2
    VJoy = 3
