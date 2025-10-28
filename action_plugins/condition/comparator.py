# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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

from typing import List, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal

from gremlin import error, event_handler, input_cache, keyboard, util
from gremlin.base_classes import Value
from gremlin.input_cache import Keyboard
from gremlin.types import HatDirection, InputType, PropertyType
from gremlin.ui.profile import HatDirectionModel


if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1


class AbstractComparator(QtCore.QObject):

    """Base class of all condition comparators.

    Provides information needed for UI presentation as well as the logic to
    execute the condition comparison.
    """

    typeChanged = Signal(str)

    def __init__(self, parent: ta.OQO=None) -> None:
        """Creates a new instance.

        Args:
            parent: parent instance of this object
        """
        super().__init__(parent)

    def __call__(self, value: Value, events: List[event_handler.Event]) -> bool:
        """Evaluates the comparison returning a truth state.

        This method has to be implemented in all subclasses.

        Args:
            value: input value to use in the comparison
            events: events to check for validity

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

    @Property(str, notify=typeChanged)
    def typeName(self) -> str:
        """Returns the comparator's type name.

        Returns:
            Name of the comparator
        """
        return self._comparator_type()

    def _comparator_type(self) -> str:
        raise error.MissingImplementationError(
            "Comparator._comparator_type not implemented in subclass"
        )


@QtQml.QmlElement
class RangeComparator(AbstractComparator):

    """Compares the state of an axis to a specific range."""

    lowerLimitChanged = Signal()
    upperLimitChanged = Signal()

    def __init__(self, lower: float, upper: float) -> None:
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

    def __call__(self, value: Value, events: List[event_handler.Event]) -> bool:
        """Returns whether or not the provided values is within the range.

        Args:
            value: axis value to be compared
            events: events to check for validity

        Returns:
            True if the value is between the lower and upper value,
            False otherwise
        """
        # Check whether to use events or value
        if len(events) == 0:
            return self.lower <= value.current <= self.upper

        # Retrieve state of the events which should be just one
        if len(events) > 1:
            raise error.GremlinError(
                "More than a single device in a range comparator"
            )
        if events[0].event_type != InputType.JoystickAxis:
            raise error.GremlinError(
                f"Received type other than an axis in a range comparator."
            )

        axis = input_cache.Joystick()[events[0].device_guid].axis(
            events[0].identifier
        )
        return self.lower <= axis.value <= self.upper

    def from_xml(self, node: ElementTree.Element) -> None:
        self.lower = util.read_property(node, "lower-limit", PropertyType.Float)
        self.upper = util.read_property(node, "upper-limit", PropertyType.Float)

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ("comparator-type", self._comparator_type(), PropertyType.String),
            ("lower-limit", self.lower, PropertyType.Float),
            ("upper-limit", self.upper, PropertyType.Float)
        ]
        return util.create_node_from_data("comparator", entries)

    def _comparator_type(self) -> str:
        return "range"

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

    def __init__(self, is_pressed: bool) -> None:
        """Creates a new comparator instance.

        Args:
            is_pressed: state in which the button should be in
        """
        super().__init__()

        self.is_pressed = is_pressed

    def __call__(self, value: Value, events: List[event_handler.Event]) -> bool:
        """Returns True if the button states match, False otherwise.

        Args:
            value: button state to be compared with
            events: events to check for validity

        Returns:
            True if the button has matching state, False otherwise
        """
        # Check whether to use events or value
        if len(events) == 0:
            return self._process_value(value)

        # Ensure all events are of the same type
        if len(set([evt.event_type for evt in events])) > 1:
            raise error.GremlinError(
                "More than a single event type in condition"
            )

        if events[0].event_type == InputType.JoystickButton:
            return self._process_button(events)
        elif events[0].event_type == InputType.Keyboard:
            return self._process_keyboard(events)
        else:
            raise error.GremlinError(
                "Unsupported event type (" \
                f"{InputType.to_string(events[0].event_type)}" \
                ") in PressedComparator"
            )

    def from_xml(self, node: ElementTree.Element) -> None:
        self.is_pressed = \
            util.read_property(node, "is-pressed", PropertyType.Bool)

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ("comparator-type", self._comparator_type(), PropertyType.String),
            ("is-pressed", self.is_pressed, PropertyType.Bool)
        ]
        return util.create_node_from_data("comparator", entries)

    def _comparator_type(self) -> str:
        return "pressed"

    def _set_is_pressed(self, value: str) -> None:
        is_pressed = value == "Pressed"
        if is_pressed != self.is_pressed:
            self.is_pressed = is_pressed
            self.isPressedChanged.emit()

    @Property(str, fset=_set_is_pressed, notify=isPressedChanged)
    def isPressed(self) -> str:
        return "Pressed" if self.is_pressed else "Released"

    def _process_value(self, value: Value) -> bool:
        """Processes the comparator against the provided value.

        Args:
            Value instance of the activating input.

        Returns:
            True if the pressed state matches, False otherwise
        """
        return value.current == self.is_pressed

    def _process_button(self, events: List[event_handler.Event]) -> bool:
        """Processess the comparator for a set of buttons.

        Args:
            events: joystick buttons to check in the comparator

        Returns:
            True if the comparator holds for all buttons, False if at least one
            button fails the comparator
        """
        joystick = input_cache.Joystick()
        is_pressed = True
        for event in events:
            button = joystick[event.device_guid].button(event.identifier)
            is_pressed &= button.is_pressed == self.is_pressed
        return is_pressed

    def _process_keyboard(self, events: List[event_handler.Event]) -> bool:
        """Processes the comparator for a set of keys.

        Args:
            events: list of keys whose state is to be evaluated

        Returns:
            True if the comparator holds for all keys, False if at least one
            key fails the comparator
        """
        is_pressed = True
        for event in events:
            key = keyboard.key_from_code(
                event.identifier[0],
                event.identifier[1]
            )
            is_pressed &= Keyboard().is_pressed(key) == self.is_pressed
        return is_pressed


@QtQml.QmlElement
class DirectionComparator(AbstractComparator):

    """Compares the state of a hat to the specified states."""

    directionsChanged = Signal()

    def __init__(self, directions: List[HatDirection]) -> None:
        """Creates a new comparator instance.

        Args:
            directions: list of valid directions
        """
        super().__init__()

        self.directions = directions
        self._model = HatDirectionModel(self.directions)

    def __call__(self, value: Value, events: List[event_handler.Event]) -> bool:
        # Check whether to use events or value
        if len(events) == 0:
            return value.current in self.directions

        # Retrieve state of the events which should be just one
        if len(events) > 1:
            raise error.GremlinError(
                "More than a single device in a direction comparator"
            )
        if events[0].event_type != InputType.JoystickHat:
            raise error.GremlinError(
                f"Received type other than a hat in a direction comparator."
            )

        hat = input_cache.Joystick()[events[0].device_guid].hat(
            events[0].identifier
        )
        return hat.direction in self.directions

    def from_xml(self, node: ElementTree.Element) -> None:
        self.directions = util.read_properties(
            node,
            "direction",
            PropertyType.HatDirection
        )

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ("comparator-type", self._comparator_type(), PropertyType.String)
        ]
        for direction in self.directions:
            entries.append(("direction", direction, PropertyType.HatDirection))
        return util.create_node_from_data("comparator", entries)

    def _comparator_type(self) -> str:
        return "direction"

    @Property(HatDirectionModel, notify=directionsChanged)
    def model(self) -> HatDirectionModel:
        return self._model


def create_default_comparator(comparator_type: str) -> AbstractComparator:
    """Creates a comparator object of appropriate type with default values.

    Args:
        comparator_type: type of comparator to create

    Returns:
        Default initialized comparator
    """
    if comparator_type == "pressed":
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
    if comparator_type == "pressed":
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