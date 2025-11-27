# -*- coding: utf-8; -*-

# Copyright (C) 2017 Lionel Ott
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
import math
from typing import Any, List, Optional, TYPE_CHECKING, override
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, keyboard, macro, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, MouseButton, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class MapToKeyboardFunctor(AbstractFunctor):

    def __init__(self, action: MapToKeyboardData):
        super().__init__(action)

        self.press = macro.Macro()
        for key in self.data.keys:
            self.press.press(key)
        self.release = macro.Macro()
        for key in reversed(self.data.keys):
            self.release.release(key)

    @override
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        if self._should_execute(value):
            if value.current:
                macro.MacroManager().queue_macro(self.press)
            else:
                macro.MacroManager().queue_macro(self.release)


class MapToKeyboardModel(ActionModel):

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
            "core_plugins:map_to_keyboard/MapToKeyboardAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @Property(str, notify=changed)
    def keyCombination(self) -> str:
        return " + ".join([key.name for key in self._data.keys])

    @Slot(list)
    def updateInputs(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        # Sort keys such that modifiers are first
        all_keys = [keyboard.key_from_code(*evt.identifier) for evt in data]
        modifier_keys = []
        normal_keys = []
        for key in all_keys:
            if key in keyboard.modifier_keys():
                modifier_keys.append(key)
            else:
                normal_keys.append(key)
        self._data.keys = modifier_keys + normal_keys
        self.changed.emit()


class MapToKeyboardData(AbstractActionData):

    """Model of a map to keyboard action."""

    version = 1
    name = "Map to Keyboard"
    tag = "map-to-keyboard"
    icon = "\uF451"

    functor = MapToKeyboardFunctor
    model = MapToKeyboardModel

    properties = [
        ActionProperty.ActivateOnBoth
    ]
    input_types = [
        InputType.JoystickButton,
        InputType.Keyboard
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ):
        super().__init__(behavior_type)

        self.keys = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        for key_node in node.findall("input"):
            key = keyboard.key_from_code(
                util.read_property(key_node, "scan-code", PropertyType.Int),
                util.read_property(key_node, "is-extended", PropertyType.Bool)
            )
            self.keys.append(key)

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MapToKeyboardData.tag, self._id)
        for key in self.keys:
            node.append(util.create_node_from_data(
                "input",
                [
                    ("scan-code", key.scan_code, PropertyType.Int),
                    ("is-extended", key.is_extended, PropertyType.Bool)
                ]
            ))
        return node

    @override
    def is_valid(self) -> bool:
        return len(self.keys) > 0

    @override
    def _valid_selectors(self) -> List[str]:
        return []

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = MapToKeyboardData
