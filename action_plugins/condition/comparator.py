# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2021 Lionel Ott
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


from typing import List
from xml.etree import ElementTree

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal

from gremlin import error, util
from gremlin.base_classes import Value
from gremlin.types import HatDirection, InputType, PropertyType


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1


class AbstractComparator(QtCore.QObject):

    """Base class of all condition comparators.

    Provides information needed for UI presentation as well as the logic to
    execute the condition comparison.
    """

    def __init__(self, parent=None):
        """Creates a new instance.

        Args:
            parent: parent instance of this object
        """
        super().__init__(parent)

    def __call__(self, value: Value) -> bool:
        """Evaluates the comparison returning a truth state.

        This method has to be implemented in all subclasses.

        Args:
            value: input value to use in the comparison

        Returns:
            True if the condition evaluates to True, False otherwise
        """
        raise error.MissingImplementationError(
            "Comparator.__call__ not implemented in subclass"
        )

    def from_xml(self, node: ElementTree.Element) -> None:
        """Populates the comparator's information using the XML node's data.

        Args:
            node: XML node representing the comparator's content
        """
        raise error.MissingImplementationError(
            "Comparator.from_xml not implemented in subclass"
        )

    def to_xml(self) -> ElementTree.Element:
        """Returns the comparator's information as an XML node.

        Returns:
            XML node representing the comparator
        """
        raise error.MissingImplementationError(
            "Comparator.to_xml not implemented in subclass"
        )



@QtQml.QmlElement
class RangeComparator(AbstractComparator):

    """Compares the state of an axis to a specific range."""

    lowerLimitChanged = Signal()
    upperLimitChanged = Signal()

    def __init__(self, lower: float, upper: float):
        """Creates a new axis range comparison object.

        Args:
            lower: lower value of the axis range
            high: upper value of the axis range
        """
        super().__init__()

        if lower > upper:
            lower, upper = upper, lower
        self.lower = lower
        self.upper = upper

    def __call__(self, value: Value) -> bool:
        """Returns whether or not the provided values is within the range.

        Args:
            value: axis value to be compared

        Returns:
            True if the value is between the lower and upper value,
            False otherwise
        """
        return self.lower <= value.current <= self.upper

    def from_xml(self, node: ElementTree.Element) -> None:
        self.lower = util.read_property(node, "lower-limit", PropertyType.Float)
        self.upper = util.read_property(node, "upper-limit", PropertyType.Float)

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ["comparator-type", "axis", PropertyType.String],
            ["lower-limit", self.lower, PropertyType.Float],
            ["upper-limit", self.upper, PropertyType.Float]
        ]
        return util.create_node_from_data("comparator", entries)

    def _set_lower_limit(self, value: float) -> None:
        if self.lower != value:
            self.lower = value
            self.lowerLimitChanged.emit()

    def _set_upper_limit(self, value: float) -> None:
        if self.upper != value:
            self.upper = value
            self.upperLimitChanged.emit()

    @Property(float, fset=_set_lower_limit, notify=lowerLimitChanged)
    def lowerLimit(self) -> float:
        return self.lower

    @Property(float, fset=_set_upper_limit, notify=upperLimitChanged)
    def upperLimit(self) -> float:
        return self.upper


@QtQml.QmlElement
class PressedComparator(AbstractComparator):

    """Compares the state of a button to a specific state."""

    isPressedChanged = Signal()

    def __init__(self, is_pressed: bool):
        """Creates a new comparator instance.

        Args:
            is_pressed: state in which the button should be in
        """
        super().__init__()

        self.is_pressed = is_pressed

    def __call__(self, value: Value) -> bool:
        """Returns True if the button states match, False otherwise.

        Args:
            value: button state to be compared with

        Returns:
            True if the button has matching state, False otherwise
        """
        return value.current == self.is_pressed

    def from_xml(self, node: ElementTree.Element) -> None:
        self.is_pressed = \
            util.read_property(node, "is-pressed", PropertyType.Bool)

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ["comparator-type", "button", PropertyType.String],
            ["is-pressed", self.is_pressed, PropertyType.Bool]
        ]
        return util.create_node_from_data("comparator", entries)

    def _set_is_pressed(self, value: str) -> None:
        is_pressed = value == "Pressed"
        if is_pressed != self.is_pressed:
            self.is_pressed = is_pressed
            self.isPressedChanged.emit()

    @Property(str, fset=_set_is_pressed, notify=isPressedChanged)
    def isPressed(self) -> str:
        return "Pressed" if self.is_pressed else "Released"


@QtQml.QmlElement
class DirectionComparator(AbstractComparator):

    """Compares the state of a hat to the specified states."""

    directionsChanged = Signal()

    def __init__(self, directions: List[HatDirection]):
        """Creates a new comparator instance.

        Args:
            directions: list of valid directions
        """
        super().__init__()

        self.directions = directions

    def __call__(self, value: Value) -> bool:
        return value.current in self.directions

    def from_xml(self, node: ElementTree.Element) -> None:
        self.directions = util.read_properties(
            node,
            "direction",
            PropertyType.HatDirection
        )

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ["comparator-type", "hat", PropertyType.String]
        ]
        for direction in self.directions:
            entries.append(["direction", direction, PropertyType.HatDirection])
        return util.create_node_from_data("comparator", entries)


def create_default_comparator(comparator_type: str) -> AbstractComparator:
    """Creates a comparator object of appropriate type with default values.
    
    Args:
        comparator_type: type of comparator to create
    
    Returns:
        Default initialized comparator
    """
    if comparator_type == "button":
        return PressedComparator(True)
    elif comparator_type == "range":
        return RangeComparator(0.0, 1.0)
    elif comparator_type == "direction":
        return DirectionComparator([HatDirection.North])
    else:
        raise error.ProfileError(
            f"Unable to create comparator, type \"{comparator_type}\" is unknown."
        )


def create_comparator_from_xml(node: ElementTree.Element) -> AbstractComparator:
    """Returns a comparator object for the specified data.

    Args:
        node: XML node storing the condition information

    Returns:
        Comparator instance representing the stored information
    """
    comparator_type = util.read_property(
        node,
        "comparator-type",
        PropertyType.String
    )
    if comparator_type == "button":
        return PressedComparator(
            util.read_property(node, "is-pressed", PropertyType.Bool)
        )
    elif comparator_type == "range":
        return RangeComparator(
            util.read_property(node, "lower-limit", PropertyType.Float),
            util.read_property(node, "upper-limit", PropertyType.Float)
        )
    elif comparator_type == "direction":
        return DirectionComparator(
            util.read_properties(node, "direction", PropertyType.HatDirection)
        )
    else:
        raise error.ProfileError(
            f"Unable to create comparator, type \"{comparator_type}\" is unknown."
        )