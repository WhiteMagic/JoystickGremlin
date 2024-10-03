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

import enum
from typing import Any, List, Optional, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    DataCreationMode, Value
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import InputType, MouseButton, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class MapToMouseMode(enum.Enum):

    Button = 1
    Motion = 2

    @staticmethod
    def lookup(value: str) -> MapToMouseMode:
        match(value):
            case "Button":
                return MapToMouseMode.Button
            case "Motion":
                return MapToMouseMode.Motion


class MapToMouseFunctor(AbstractFunctor):

    """Implements the function implementing MapToMouse behavior at runtime."""

    def __init__(self, action: MapToMouseData):
        super().__init__(action)

    def __call__(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
        """Processes the provided event.

        Args:
            event: the input event to process
            value: the potentially modified input value
        """
        pass


class MapToMouseModel(ActionModel):

    # Signal emitted when the description variable's content changes
    changed = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ):
        super().__init__(data, binding_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:map_to_mouse/MapToMouseAction.qml"
        ).fileName()

    def _icon_string_impl(self) -> str:
        return MapToMouse.icon

    def _get_mode(self) -> str:
        return self._data.mode.name

    def _set_mode(self, value: str) -> None:
        mode = MapToMouseMode.lookup(value)
        if mode != self._data.mode:
            self._data.mode = mode
            self.changed.emit()

    @Property(str, notify=changed)
    def button(self) -> str:
        return MouseButton.to_string(self._data.button)

    @Slot(list)
    def updateInputs(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        self._data.button = data[0].identifier
        self.changed.emit()

    mode = Property(
        str,
        fget=_get_mode,
        fset=_set_mode,
        notify=changed
    )


class MapToMouseData(AbstractActionData):

    """Model of a description action."""

    version = 1
    name = "Map to Mouse"
    tag = "map-to-mouse"
    icon = "\uF49B"

    functor = MapToMouseFunctor
    model = MapToMouseModel

    properties = []
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ):
        super().__init__(behavior_type)

        # Model variables
        self.mode = MapToMouseMode.Button
        self.button = MouseButton.Left

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.mode = MapToMouseMode.lookup(util.read_property(
            node, "mode", PropertyType.String
        ))

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MapToMouseData.tag, self._id)
        node.append(util.create_property_node(
            "mode", self.mode.name, PropertyType.String
        ))
        return node

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return []

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = MapToMouseData
