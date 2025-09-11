# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2025Lionel Ott
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
from enum import Enum
import logging
from typing import Generic, Tuple, TypeVar, Union

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
            return _InputType_to_enum_lookup[value.lower()]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid type in lookup")


_InputType_to_string_lookup = {
    InputType.JoystickAxis: "axis",
    InputType.JoystickButton: "button",
    InputType.JoystickHat: "hat",
    InputType.Keyboard: "key",
    InputType.Mouse: "mouse",
    InputType.VirtualButton: "virtual-button"
}

_InputType_to_enum_lookup = {
    "axis": InputType.JoystickAxis,
    "button": InputType.JoystickButton,
    "hat": InputType.JoystickHat,
    "key": InputType.Keyboard,
    "mouse": InputType.Mouse,
    "virtual-button": InputType.VirtualButton
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


class ScriptVariableType(enum.Enum):

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
    def to_string(value: ScriptVariableType) -> str:
        try:
            return _ScriptVariableType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid ScriptVariableType in lookup"
            )

    @staticmethod
    def to_enum(value: str) -> ScriptVariableType:
        try:
            return _ScriptVariableType_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid ScriptVariableType in lookup"
            )


_ScriptVariableType_to_string_lookup = {
    ScriptVariableType.Int: "Int",
    ScriptVariableType.Float: "Float",
    ScriptVariableType.String: "String",
    ScriptVariableType.Bool: "Bool",
    ScriptVariableType.PhysicalInput: "PhysicalInput",
    ScriptVariableType.VirtualInput: "VirtualInput",
    ScriptVariableType.Mode: "Mode",
    ScriptVariableType.Selection: "Selection"
}
_ScriptVariableType_to_enum_lookup = {
    "Int": ScriptVariableType.Int,
    "Float": ScriptVariableType.Float,
    "String": ScriptVariableType.String,
    "Bool": ScriptVariableType.Bool,
    "PhysicalInput": ScriptVariableType.PhysicalInput,
    "VirtualInput": ScriptVariableType.VirtualInput,
    "Mode": ScriptVariableType.Mode,
    "Selection": ScriptVariableType.Selection
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
    UUID = 12
    AxisMode = 13
    HatDirection = 14
    List = 15
    Selection = 16
    ActionActivationMode = 17,
    Point2D = 18,
    ScriptVariableType = 19,
    Path = 20,

    @staticmethod
    def to_string(value: PropertyType) -> str:
        try:
            return _PropertyType_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid PropertyType in lookup")

    @staticmethod
    def to_enum(value: str) -> PropertyType:
        try:
            return _PropertyType_to_enum_lookup[value.lower()]
        except KeyError:
            raise gremlin.error.GremlinError("Invalid PropertyType in lookup")

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
    PropertyType.UUID: "uuid",
    PropertyType.AxisMode: "axis_mode",
    PropertyType.HatDirection: "hat_direction",
    PropertyType.List: "list",
    PropertyType.Selection: "selection",
    PropertyType.ActionActivationMode: "activation-mode",
    PropertyType.Point2D: "point2d",
    PropertyType.ScriptVariableType: "plugin_variable_type",
    PropertyType.Path: "path",
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
    "uuid": PropertyType.UUID,
    "axis_mode": PropertyType.AxisMode,
    "hat_direction": PropertyType.HatDirection,
    "list": PropertyType.List,
    "selection": PropertyType.Selection,
    "activation-mode": PropertyType.ActionActivationMode,
    "point2d": PropertyType.Point2D,
    "plugin_variable_type": PropertyType.ScriptVariableType,
    "path": PropertyType.Path,
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

    Joystick = 1
    Keyboard = 2
    CurrentInput = 3

    @staticmethod
    def to_display(instance: ConditionType) -> str:
        lookup = {
            ConditionType.Joystick: "Joystick",
            ConditionType.Keyboard: "Keyboard",
            ConditionType.CurrentInput: "Current Input",
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
            ConditionType.Joystick: "joystick",
            ConditionType.Keyboard: "keyboard",
            ConditionType.CurrentInput: "current_input",
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
            "joystick": ConditionType.Joystick,
            "keyboard": ConditionType.Keyboard,
            "current_input": ConditionType.CurrentInput,
        }
        value = lookup.get(string, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid condition operator type: {str(string)}"
            )
        return value


class ActionProperty(enum.Enum):

    """Enumeration of the properties actions can be tagged with."""

    # Will reuse an existing action instead of creating a new one by default
    ReuseByDefault = 1
    # Will execute the action even if Gremlin is paused
    AlwaysExecute = 2
    # Default action activation modes
    ActivateOnPress = 3
    ActivateOnRelease = 4
    ActivateOnBoth = 5
    ActivateDisabled = 6
    # Disable auto release functionality for this action and child actions
    DisableAutoRelease = 7


class ActionActivationMode(enum.Enum):

    """Possible activation modes of button-like inputs."""

    Deactivated = 1
    Press = 2
    Release = 3
    Both = 4
    Disallowed = 5

    @staticmethod
    def to_string(instance: ActionActivationMode ) -> str:
        lookup = {
            ActionActivationMode.Deactivated: "deactivated",
            ActionActivationMode.Press: "press",
            ActionActivationMode.Release: "release",
            ActionActivationMode.Both: "both",
            ActionActivationMode.Disallowed: "disallowed",
        }
        value = lookup.get(instance, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid action activation mode: {str(instance)}"
            )
        return value

    @staticmethod
    def to_enum(string: str) -> ActionActivationMode:
        lookup = {
            "deactivated": ActionActivationMode.Deactivated,
            "press": ActionActivationMode.Press,
            "release": ActionActivationMode.Release,
            "both": ActionActivationMode.Both,
            "disallowed": ActionActivationMode.Disallowed
        }
        value = lookup.get(string, None)
        if value is None:
            raise gremlin.error.GremlinError(
                f"Invalid action activation mode: {str(string)}"
            )
        return value


class DataInsertionMode(Enum):

    """Specifies to insertion type to be performed."""

    Append = 0
    Prepend = 1


class DataCreationMode(Enum):

    """Specifies how a new AbstractActionData instance is created."""

    Create = 0
    Reuse = 1


class Point2D:

    """Represents a simple 2D point."""

    def __init__(self, x: float, y: float) -> None:
        """Creates a new point instance.

        Args:
            x: x coordinate of the point
            y: y coordinate of the point
        """
        self.x = x
        self.y = y

    @classmethod
    def from_string(self, val: str) -> Point2D:
        """Creates a new Point2D instance from the given string.

        Args:
            val: The string representation of the point

        Returns:
            New Point2D instance representing the given string
        """
        x, y = [float(v) for v in val.split(",")]
        return Point2D(x, y)

    def to_string(self) -> str:
        """Returns a string representation of the point.

        Returns:
            String representation of the point
        """
        return f"{self.x},{self.y}"

    def __add__(self, other: float) -> Point2D:
        """Adds another point to this one, returning the resulting sum.

        Args:
            other: point instance to add to this one

        Returns:
            New Point2D instance representing the sum
        """
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """Subtracts another point from this one, returning the result.

        Args:
            other: point instance to subtract from this one

        Returns:
            New Point2D instance representing the subtraction result
        """
        return Point2D(self.x - other.x, self.y - other.y)


NumericType = TypeVar("NumericType", int, float)

class ValueRange(Generic[NumericType]):

    """Represents a value range for a numerical type."""

    _low: NumericType
    _high: NumericType
    _value: NumericType

    def __init__(self, low: NumericType, high: NumericType) -> None:
        """Creates a new ValueRange.

        Will swap low and high if they are in the wrong order.

        Args:
            low: The lower bound of the range
            high: The upper bound of the range
        """
        if low > high:
            logging.getLogger("system").warning(
                f"ValueRange initialized with low > high ({low} > {high}),"
                "swapping values."
            )
            low, high = high, low
        self._low = low
        self._high = high
        self._value = low

    @property
    def value(self) -> NumericType:
        return self._value

    @value.setter
    def value(self, val: NumericType) -> None:
        """Sets the value represented by the ValueRange.

        If the given value exceeds the range's limits, it will be clamlped.

        Args:
            val: The new value to set
        """
        if self._low <= val <= self._high:
            self._value = val
        else:
            logging.getLogger("system").warning(
                f"Attempted to set ValueRange to {val}, which is outside the "
                f"range [{self._low}, {self._high}], clampping value."
            )
            self._value = max(self._low, min(val, self._high))
