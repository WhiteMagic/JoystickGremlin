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

from abc import abstractmethod, ABCMeta
from typing import Any, List, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal

from gremlin import error, event_handler, input_cache, keyboard, util
from gremlin.base_classes import Value
from gremlin.common import SingletonMetaclass
from gremlin.input_cache import Keyboard
from gremlin.types import HatDirection, InputType, PropertyType
from gremlin.ui.profile import HatDirectionModel


if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1


class AbstractComparatorModel(QtCore.QObject):

    """Base class for comparator QML models.

    Provides information needed for UI presentation.
    """

    name : str = ""

    typeChanged = Signal(str)

    def __init__(self, parent: ta.OQO=None) -> None:
        """Creates a new instance.

        Args:
            parent: parent instance of this object
        """
        super().__init__(parent)

    @Property(str, notify=typeChanged)
    def typeName(self) -> str:
        """Returns the comparator's type name.

        Returns:
            Name of the comparator
        """
        return self.name


@QtQml.QmlElement
class RangeComparatorModel(AbstractComparatorModel):

    """Compares the state of an axis to a specific range."""

    name = "range"

    lowerLimitChanged = Signal()
    upperLimitChanged = Signal()

    def __init__(self, data: RangeComparator) -> None:
        """Creates a new axis range comparison object.

        Args:
            lower: lower value of the axis range
            high: upper value of the axis range
        """
        super().__init__()

        self.data = data

    def _set_lower_limit(self, value: float) -> None:
        if self.data.lower != value:
            self.data.lower = value
            self.lowerLimitChanged.emit()

    def _set_upper_limit(self, value: float) -> None:
        if self.data.upper != value:
            self.data.upper = value
            self.upperLimitChanged.emit()

    @Property(float, fset=_set_lower_limit, notify=lowerLimitChanged)
    def lowerLimit(self) -> float:
        return self.data.lower

    @Property(float, fset=_set_upper_limit, notify=upperLimitChanged)
    def upperLimit(self) -> float:
        return self.data.upper


@QtQml.QmlElement
class PressedComparatorModel(AbstractComparatorModel):

    """Compares the state of a button to a specific state."""

    name = "pressed"

    isPressedChanged = Signal()

    def __init__(self, data: PressedComparator) -> None:
        """Creates a new comparator instance.

        Args:
            is_pressed: state in which the button should be in
        """
        super().__init__()

        self.data = data

    def _set_is_pressed(self, value: str) -> None:
        is_pressed = (value == "Pressed")
        if self.data.is_pressed != is_pressed:
            self.data.is_pressed = is_pressed
            self.isPressedChanged.emit()

    @Property(str, fset=_set_is_pressed, notify=isPressedChanged)
    def isPressed(self) -> str:
        return "Pressed" if self.data.is_pressed else "Released"


@QtQml.QmlElement
class DirectionComparatorModel(AbstractComparatorModel):

    """Compares the state of a hat to the specified states."""

    name = "direction"

    directionsChanged = Signal()

    def __init__(self, data: DirectionComparator) -> None:
        """Creates a new comparator instance.

        Args:
            directions: list of valid directions
        """
        super().__init__()

        self.data = data
        self._model = HatDirectionModel(self.data.directions)

    @Property(HatDirectionModel, notify=directionsChanged)
    def model(self) -> HatDirectionModel:
        return self._model


class AbstractComparator(metaclass=ABCMeta):

    """Base class of all comparators, provides logic and data."""

    @abstractmethod
    def from_xml(self, node: ElementTree.Element) -> None:
        pass

    @abstractmethod
    def to_xml(self) -> ElementTree.Element:
        pass

    @abstractmethod
    def __call__(self, value: Value, states: List[Any]) -> bool:
        pass


class RangeComparator(AbstractComparator):

    """Compares the state of an axis to a specific range."""

    model = RangeComparatorModel

    def __init__(self, lower: float=-1.0, upper: float=1.0) -> None:
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

    def __call__(self, value: Value, states: List[Any]) -> bool:
        """Returns whether or not the provided values is within the range.

        Args:
            value: axis value to be compared
            events: events to check for validity

        Returns:
            True if the value is between the lower and upper value,
            False otherwise
        """
        return self.lower <= states[0] <= self.upper

    def from_xml(self, node: ElementTree.Element) -> None:
        self.lower = util.read_property(node, "lower-limit", PropertyType.Float)
        self.upper = util.read_property(node, "upper-limit", PropertyType.Float)

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ("comparator-type", "range", PropertyType.String),
            ("lower-limit", self.lower, PropertyType.Float),
            ("upper-limit", self.upper, PropertyType.Float)
        ]
        return util.create_node_from_data("comparator", entries)


class PressedComparator(AbstractComparator):

    """Compares the state of a button to a specific state."""

    model = PressedComparatorModel

    def __init__(self, is_pressed: bool=False) -> None:
        """Creates a new comparator instance.

        Args:
            is_pressed: state in which the button should be in
        """
        super().__init__()

        self.is_pressed = is_pressed

    def __call__(self, value: Value, states: List[Any]) -> bool:
        """Returns True if the button states match, False otherwise.

        Args:
            value: button state to be compared with
            events: events to check for validity

        Returns:
            True if the button has matching state, False otherwise
        """
        return states[0] == self.is_pressed

    def from_xml(self, node: ElementTree.Element) -> None:
        self.is_pressed = \
            util.read_property(node, "is-pressed", PropertyType.Bool)

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ("comparator-type", "pressed", PropertyType.String),
            ("is-pressed", self.is_pressed, PropertyType.Bool)
        ]
        return util.create_node_from_data("comparator", entries)


class DirectionComparator(AbstractComparator):

    """Compares the state of a hat to the specified states."""

    model = DirectionComparatorModel

    def __init__(self, directions: List[HatDirection]=[]) -> None:
        """Creates a new comparator instance.

        Args:
            directions: list of valid directions
        """
        super().__init__()

        self.directions = directions

    def __call__(self, value: Value, states: List[Any]) -> bool:
        return states[0] in self.directions

    def from_xml(self, node: ElementTree.Element) -> None:
        self.directions = util.read_properties(
            node,
            "direction",
            PropertyType.HatDirection
        )

    def to_xml(self) -> ElementTree.Element:
        entries = [
            ("comparator-type", "direction", PropertyType.String)
        ]
        for direction in self.directions:
            entries.append(("direction", direction, PropertyType.HatDirection))
        return util.create_node_from_data("comparator", entries)
