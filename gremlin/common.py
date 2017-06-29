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

input_type_to_name = {
    InputType.Keyboard: "Keyboard",
    InputType.JoystickAxis: "Axis",
    InputType.JoystickButton: "Button",
    InputType.JoystickHat: "Hat"
}

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