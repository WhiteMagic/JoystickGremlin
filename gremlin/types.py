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


import enum

import gremlin.error


class ActivationRule(enum.Enum):

    """Activation rules for collections of conditions.

    All requires all the conditions in a collection to evaluate to True while
    Any only requires a single condition to be True.
    """

    All = 1
    Any = 2


class InputType(enum.Enum):

    """Enumeration of possible input types."""

    Keyboard = 1
    JoystickAxis = 2
    JoystickButton = 3
    JoystickHat = 4
    Mouse = 5
    VirtualButton = 6

    @staticmethod
    def to_string(value) -> str:
        try:
            return _InputType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")

    @staticmethod
    def to_enum(value: str):
        try:
            return _InputType_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")


_InputType_to_string_lookup = {
    InputType.JoystickAxis: "axis",
    InputType.JoystickButton: "button",
    InputType.JoystickHat: "hat",
    InputType.Keyboard: "key",
}

_InputType_to_enum_lookup = {
    "axis": InputType.JoystickAxis,
    "button": InputType.JoystickButton,
    "hat": InputType.JoystickHat,
    "key": InputType.Keyboard
}


class AxisNames(enum.Enum):

    """Names associated with axis indices."""

    X = 1
    Y = 2
    Z = 3
    RX = 4
    RY = 5
    RZ = 6
    SLIDER = 7
    DIAL = 8

    @staticmethod
    def to_string(value):
        try:
            return _AxisNames_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid AxisName lookup, {}".format(value)
            )

    @staticmethod
    def to_enum(value):
        try:
            return _AxisNames_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid AxisName lookup, {}".format(value)
            )


_AxisNames_to_string_lookup = {
    AxisNames.X: "X Axis",
    AxisNames.Y: "Y Axis",
    AxisNames.Z: "Z Axis",
    AxisNames.RX: "X Rotation",
    AxisNames.RY: "Y Rotation",
    AxisNames.RZ: "Z Rotation",
    AxisNames.SLIDER: "Slider",
    AxisNames.DIAL: "Dial"
}
_AxisNames_to_enum_lookup = {
    "X Axis": AxisNames.X,
    "Y Axis": AxisNames.Y,
    "Z Axis": AxisNames.Z,
    "X Rotation": AxisNames.RX,
    "Y Rotation": AxisNames.RY,
    "Z Rotation": AxisNames.RZ,
    "Slider": AxisNames.SLIDER,
    "Dial": AxisNames.DIAL
}


class AxisButtonDirection(enum.Enum):

    """Possible activation directions for axis button instances."""

    Anywhere = 1
    Below = 2
    Above = 3

    @staticmethod
    def to_string(value):
        try:
            return _AxisButtonDirection_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid AxisButtonDirection lookup, {}".format(value)
            )

    @staticmethod
    def to_enum(value):
        try:
            return _AxisButtonDirection_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid AxisButtonDirection lookup, {}".format(value)
            )


_AxisButtonDirection_to_string_lookup = {
    AxisButtonDirection.Anywhere: "anywhere",
    AxisButtonDirection.Above: "above",
    AxisButtonDirection.Below: "below"
}
_AxisButtonDirection_to_enum_lookup = {
    "anywhere": AxisButtonDirection.Anywhere,
    "above": AxisButtonDirection.Above,
    "below": AxisButtonDirection.Below
}


class MouseButton(enum.Enum):

    """Enumeration of all possible mouse buttons."""

    Left = 1
    Right = 2
    Middle = 3
    Forward = 4
    Back = 5
    WheelUp = 10
    WheelDown = 11

    @staticmethod
    def to_string(value):
        try:
            return _MouseButton_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")

    @staticmethod
    def to_enum(value):
        try:
            return _MouseButton_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")


_MouseButton_to_string_lookup = {
    MouseButton.Left: "Left",
    MouseButton.Right: "Right",
    MouseButton.Middle: "Middle",
    MouseButton.Forward: "Forward",
    MouseButton.Back: "Back",
    MouseButton.WheelUp: "Wheel Up",
    MouseButton.WheelDown: "Wheel Down",
}
_MouseButton_to_enum_lookup = {
    "Left": MouseButton.Left,
    "Right": MouseButton.Right,
    "Middle": MouseButton.Middle,
    "Forward": MouseButton.Forward,
    "Back": MouseButton.Back,
    "Wheel Up": MouseButton.WheelUp,
    "Wheel Down": MouseButton.WheelDown,
}


class DeviceType(enum.Enum):

    """Enumeration of the different possible input types."""

    Keyboard = 1
    Joystick = 2
    VJoy = 3

    @staticmethod
    def to_string(value):
        try:
            return _DeviceType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")

    @staticmethod
    def to_enum(value):
        try:
            return _DeviceType_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")


_DeviceType_to_string_lookup = {
    DeviceType.Keyboard: "keyboard",
    DeviceType.Joystick: "joystick",
    DeviceType.VJoy: "vjoy"
}
_DeviceType_to_enum_lookup = {
    "keyboard": DeviceType.Keyboard,
    "joystick": DeviceType.Joystick,
    "vjoy": DeviceType.VJoy
}


class PluginVariableType(enum.Enum):

    """Enumeration of all supported variable types."""

    Int = 1
    Float = 2
    String = 3
    Bool = 4
    PhysicalInput = 5
    VirtualInput = 6
    Mode = 7
    Selection = 8

    @staticmethod
    def to_string(value):
        try:
            return _PluginVariableType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid PluginVariableType in lookup"
            )

    @staticmethod
    def to_enum(value):
        try:
            return _PluginVariableType_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid PluginVariableType in lookup"
            )


_PluginVariableType_to_string_lookup = {
    PluginVariableType.Int: "Int",
    PluginVariableType.Float: "Float",
    PluginVariableType.String: "String",
    PluginVariableType.Bool: "Bool",
    PluginVariableType.PhysicalInput: "PhysicalInput",
    PluginVariableType.VirtualInput: "VirtualInput",
    PluginVariableType.Mode: "Mode",
    PluginVariableType.Selection: "Selection"
}
_PluginVariableType_to_enum_lookup = {
    "Int": PluginVariableType.Int,
    "Float": PluginVariableType.Float,
    "String": PluginVariableType.String,
    "Bool": PluginVariableType.Bool,
    "PhysicalInput": PluginVariableType.PhysicalInput,
    "VirtualInput": PluginVariableType.VirtualInput,
    "Mode": PluginVariableType.Mode,
    "Selection": PluginVariableType.Selection
}


class MergeAxisOperation(enum.Enum):

    """Possible merge axis operation modes."""

    Average = 1
    Minimum = 2
    Maximum = 3
    Sum = 4

    @staticmethod
    def to_string(value):
        try:
            return _MergeAxisOperation_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid MergeAxisOperation in lookup"
            )

    @staticmethod
    def to_enum(value):
        try:
            return _MergeAxisOperation_to_enum_lookup[value.lower()]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid MergeAxisOperation in lookup"
            )


_MergeAxisOperation_to_string_lookup = {
    MergeAxisOperation.Average: "average",
    MergeAxisOperation.Minimum: "minimum",
    MergeAxisOperation.Maximum: "maximum",
    MergeAxisOperation.Sum: "sum"
}
_MergeAxisOperation_to_enum_lookup = {
    "average": MergeAxisOperation.Average,
    "minimum": MergeAxisOperation.Minimum,
    "maximum": MergeAxisOperation.Maximum,
    "sum": MergeAxisOperation.Sum
}
