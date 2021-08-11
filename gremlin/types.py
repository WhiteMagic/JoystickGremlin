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


from __future__ import annotations

import enum
from typing import Tuple, Union

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
    def to_string(value: InputType) -> str:
        try:
            return _InputType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")

    @staticmethod
    def to_enum(value: str) -> InputType:
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
    def to_string(value: AxisNames) -> str:
        try:
            return _AxisNames_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid AxisName lookup, {}".format(value)
            )

    @staticmethod
    def to_enum(value: str) -> AxisNames:
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
    def to_string(value: AxisButtonDirection) -> str:
        try:
            return _AxisButtonDirection_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid AxisButtonDirection lookup, {}".format(value)
            )

    @staticmethod
    def to_enum(value: str) -> AxisButtonDirection:
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
    def to_string(value: MouseButton) -> str:
        try:
            return _MouseButton_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")

    @staticmethod
    def to_enum(value: str) -> MouseButton:
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
    def to_string(value: DeviceType) -> str:
        try:
            return _DeviceType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")

    @staticmethod
    def to_enum(value: str) -> DeviceType:
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
    def to_string(value: PluginVariableType) -> str:
        try:
            return _PluginVariableType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid PluginVariableType in lookup"
            )

    @staticmethod
    def to_enum(value: str) -> PluginVariableType:
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
    def to_string(value: MergeAxisOperation) -> str:
        try:
            return _MergeAxisOperation_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid MergeAxisOperation in lookup"
            )

    @staticmethod
    def to_enum(value: str) -> MergeAxisOperation:
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


class PropertyType(enum.Enum):

    """Enumeration of all known property types."""

    String = 1
    Int = 2
    Float = 3
    Bool = 4
    AxisValue = 5
    IntRange = 6
    FloatRange = 7
    AxisRange = 8
    InputType = 9
    KeyboardKey = 10
    MouseInput = 11
    GUID = 12
    UUID = 13
    AxisMode = 14
    HatDirection = 15

    @staticmethod
    def to_string(value: PropertyType) -> str:
        try:
            return _PropertyType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid PropertyType in lookup"
            )

    @staticmethod
    def to_enum(value: str) -> PropertyType:
        try:
            return _PropertyType_to_enum_lookup[value.lower()]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid PropertyType in lookup"
            )

_PropertyType_to_string_lookup = {
    PropertyType.String: "string",
    PropertyType.Int: "int",
    PropertyType.Float: "float",
    PropertyType.Bool: "bool",
    PropertyType.AxisValue: "axis_value",
    PropertyType.IntRange: "int_range",
    PropertyType.FloatRange: "float_range",
    PropertyType.AxisRange: "axis_range",
    PropertyType.InputType: "input_type",
    PropertyType.KeyboardKey: "keyboard_key",
    PropertyType.MouseInput: "mouse_input",
    PropertyType.GUID: "guid",
    PropertyType.UUID: "uuid",
    PropertyType.AxisMode: "axis_mode",
    PropertyType.HatDirection: "hat_direction"
}
_PropertyType_to_enum_lookup = {
    "string": PropertyType.String,
    "int": PropertyType.Int,
    "float": PropertyType.Float,
    "bool": PropertyType.Bool,
    "axis_value": PropertyType.AxisValue,
    "int_range": PropertyType.IntRange,
    "float_range": PropertyType.FloatRange,
    "axis_range": PropertyType.AxisRange,
    "input_type": PropertyType.InputType,
    "keyboard_key": PropertyType.KeyboardKey,
    "mouse_input": PropertyType.MouseInput,
    "guid": PropertyType.GUID,
    "uuid": PropertyType.UUID,
    "axis_mode": PropertyType.AxisMode,
    "hat_direction": PropertyType.HatDirection
}


class AxisMode(enum.Enum):

    Absolute = 1
    Relative = 2

    @staticmethod
    def to_string(value: AxisMode) -> str:
        try:
            return _AxisMode_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid AxisMode in lookup"
            )

    @staticmethod
    def to_enum(value: str) -> AxisMode:
        try:
            return _AxisMode_to_enum_lookup[value.lower()]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid AxisMode in lookup"
            )

_AxisMode_to_string_lookup = {
    AxisMode.Absolute: "absolute",
    AxisMode.Relative: "relative"
}
_AxisMode_to_enum_lookup = {
    "absolute": AxisMode.Absolute,
    "relative": AxisMode.Relative
}


class HatDirection(enum.Enum):

    """Represents the possible directions a hat can take on."""

    Center = (0, 0)
    North = (0, 1)
    NorthEast = (1, 1)
    East = (1, 0)
    SouthEast = (1, -1)
    South = (0, -1)
    SouthWest = (-1, -1)
    West = (-1, 0)
    NorthWest = (-1, 1)

    @staticmethod
    def to_string(value: HatDirection) -> str:
        try:
            return _HatDirection_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid HatDirection in lookup"
            )

    @staticmethod
    def to_enum(value: Union[str, Tuple[int, int]]) -> HatDirection:
        try:
            if isinstance(value, str):
                return _HatDirection_to_enum_lookup[value.lower()]
            else:
                return _HatDirection_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid HatDirection in lookup"
            )

_HatDirection_to_string_lookup = {
    HatDirection.Center: "center",
    HatDirection.North: "north",
    HatDirection.NorthEast: "north-east",
    HatDirection.East: "east",
    HatDirection.SouthEast: "south-east",
    HatDirection.South: "south",
    HatDirection.SouthWest: "south-west",
    HatDirection.West: "west",
    HatDirection.NorthWest: "north-west",
}

_HatDirection_to_enum_lookup = {
    # String based
    "center": HatDirection.Center,
    "north": HatDirection.North,
    "north-east": HatDirection.NorthEast,
    "east": HatDirection.East,
    "south-east": HatDirection.SouthEast,
    "south": HatDirection.South,
    "south-west": HatDirection.SouthWest,
    "west": HatDirection.West,
    "north-west": HatDirection.NorthWest,
    # Direction tuple based
    (0, 0): HatDirection.Center,
    (0, 1): HatDirection.North,
    (1, 1): HatDirection.NorthEast,
    (1, 0): HatDirection.East,
    (1, -1): HatDirection.SouthEast,
    (0, -1): HatDirection.South,
    (-1, -1): HatDirection.SouthWest,
    (-1, 0): HatDirection.West,
    (-1, 1): HatDirection.NorthWest,
}


class LogicalOperator(enum.Enum):

    """Enumeration of possible condition combinations."""

    Any = 1
    All = 2

    @staticmethod
    def to_display(instance: LogicalOperator) -> str:
        lookup = {
            LogicalOperator.Any: "Any",
            LogicalOperator.All: "All"
        }
        value = lookup.get(instance, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid logical operator type: {str(instance)}"
            )
        return value

    @staticmethod
    def to_string(instance: LogicalOperator) -> str:
        lookup = {
            LogicalOperator.Any: "any",
            LogicalOperator.All: "all"
        }
        value = lookup.get(instance, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid logical operator type: {str(instance)}"
            )
        return value

    @staticmethod
    def to_enum(string: str) -> LogicalOperator:
        lookup = {
            "any": LogicalOperator.Any,
            "all": LogicalOperator.All
        }
        value = lookup.get(string, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid logical operator type: {str(string)}"
            )
        return value


class ConditionType(enum.Enum):

    """Enumeration of possible condition types."""

    InputState = 1
    Joystick = 2
    Keyboard = 3
    VJoy = 4

    @staticmethod
    def to_display(instance: ConditionType) -> str:
        lookup = {
            ConditionType.InputState: "Input State",
            ConditionType.Joystick: "Joystick",
            ConditionType.Keyboard: "Keyboard",
            ConditionType.VJoy: "vJoy"
        }
        value = lookup.get(instance, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid condition operator type: {str(instance)}"
            )
        return value

    @staticmethod
    def to_string(instance: ConditionType) -> str:
        lookup = {
            ConditionType.InputState: "input-state",
            ConditionType.Joystick: "joystick",
            ConditionType.Keyboard: "keyboard",
            ConditionType.VJoy: "vjoy"
        }
        value = lookup.get(instance, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid condition operator type: {str(instance)}"
            )
        return value

    @staticmethod
    def to_enum(string: str) -> ConditionType:
        lookup = {
            "input-state": ConditionType.InputState,
            "joystick": ConditionType.Joystick,
            "keyboard": ConditionType.Keyboard,
            "vjoy": ConditionType.VJoy
        }
        value = lookup.get(string, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid condition operator type: {str(string)}"
            )
        return value
