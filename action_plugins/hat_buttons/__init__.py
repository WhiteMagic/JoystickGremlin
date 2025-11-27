# -*- coding: utf-8; -*-

# Copyright (C) 2025 Lionel Ott
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

import copy
import time
from collections.abc import Callable
from typing import Any, List, Optional, TYPE_CHECKING, override
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, fsm, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value
from gremlin.error import GremlinError
from gremlin.plugin_manager import PluginManager
from gremlin.profile import Library
from gremlin.types import ActionProperty, HatDirection, InputType, \
    PropertyType, DataCreationMode

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class DirectionalButton:

    resolve_direction = {
        HatDirection.North: "North",
        HatDirection.NorthEast: "North East",
        HatDirection.East: "East",
        HatDirection.SouthEast: "South East",
        HatDirection.South: "South",
        HatDirection.SouthWest: "South West",
        HatDirection.West: "West",
        HatDirection.NorthWest: "North West",
        HatDirection.Center: "Center",
        "Center": HatDirection.Center,
        "North": HatDirection.North,
        "North East": HatDirection.NorthEast,
        "East": HatDirection.East,
        "South East": HatDirection.SouthEast,
        "South": HatDirection.South,
        "South West": HatDirection.SouthWest,
        "West": HatDirection.West,
        "North West": HatDirection.NorthWest,
    }

    def __init__(self, functors: Dict[str, List[Callable]], direction: str):
        self.functors = functors
        self.functor_direction = direction
        self.type_direction = DirectionalButton.resolve_direction[direction]

        self.fsm = self._create_fsm()

    def _create_fsm(self) -> fsm.FiniteStateMachine:
        T = fsm.Transition
        noop = lambda *args: None

        states = ["up", "down"]
        actions = ["press", "release"]
        transitions = {
            ("up", "press"): T([self._execute], "down"),
            ("up", "release"): T([noop], "up"),
            ("down", "release"): T([self._execute], "up"),
            ("down", "press"): T([noop], "down")
        }
        return fsm.FiniteStateMachine("up", states, actions, transitions)

    @override
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        is_pressed = event.value == self.type_direction
        action = "press" if is_pressed else "release"

        # Event creation
        btn_event = event.clone()
        btn_event.event_type = InputType.JoystickButton
        btn_event.is_pressed = is_pressed
        btn_event.value = None
        btn_value = Value(is_pressed)

        self.fsm.perform(action, btn_event, btn_value, properties)

    def _execute(
            self,
            event: event_handler.Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        for functor in self.functors[self.functor_direction]:
            functor(event, value, properties)


class HatButtonsFunctor(AbstractFunctor):

    """Implements the function executed of the Description action at runtime."""

    def __init__(self, action: HatButtonsData):
        super().__init__(action)

        self.buttons = []
        for direction in HatButtonsData.name_list[self.data.button_count]:
            self.buttons.append(DirectionalButton(self.functors, direction))

    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        for button in self.buttons:
            button(event, value, properties)


class HatButtonsModel(ActionModel):

    # Signal emitted when the description variable's content changes
    changed = Signal()

    name_lookup = {
        (4, 0): "North",
        (4, 1): "East",
        (4, 2): "South",
        (4, 3): "West",
        (8, 0): "North",
        (8, 1): "North East",
        (8, 2): "East",
        (8, 3): "South East",
        (8, 4): "South",
        (8, 5): "South West",
        (8, 6): "West",
        (8, 7): "North West"
    }

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
            "core_plugins:hat_buttons/HatButtonsAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  "button"

    @Slot(int, result=str)
    def buttonName(self, index: int) -> str:
        key = (self._data.button_count, index)
        if key not in HatButtonsModel.name_lookup:
            logging.getLogger("system").warning(
                f"Invalid button name lookup in HatButtons: {key}"
            )
        return HatButtonsModel.name_lookup[key]

    def _get_button_count(self) -> int:
        return self._data.button_count

    def _set_button_count(self, count: int) -> None:
        if self._data.button_count != count:
            self._data.button_count = count
            self.changed.emit()

    def _compatible_actions(self) -> List[str]:
        action_list = PluginManager().type_action_map[InputType.JoystickButton]
        action_list = [entry for entry in action_list if entry.tag != "root"]
        return [a.name for a in sorted(action_list, key=lambda x: x.name)]

    buttonCount = Property(
        type=int,
        fget=_get_button_count,
        fset=_set_button_count,
        notify=changed
    )



class HatButtonsData(AbstractActionData):

    """Model of a description action."""

    version = 1
    name = "Hat as Buttons"
    tag = "hat-buttons"
    icon = "\uF687"

    functor = HatButtonsFunctor
    model = HatButtonsModel

    properties = [
        ActionProperty.ActivateDisabled
    ]
    input_types = [
        InputType.JoystickHat
    ]

    name_list = {
        4: ["North", "East", "South", "West"],
        8: ["North", "North East", "East", "South East",
            "South", "South West", "West", "North West"]
    }

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ):
        super().__init__(InputType.JoystickButton)

        self.button_count = 4
        self.direction = {}
        for name in HatButtonsData. name_list[self.button_count]:
            self.direction[name] = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.button_count = util.read_property(
            node, "button-count", PropertyType.Int
        )
        self.direction = {}
        for name in HatButtonsData. name_list[self.button_count]:
            self.direction[name] = []
        # Extract action ids for each direction
        for elem in node.findall(".//action-id/.."):
            key = elem.tag
            action_ids = util.read_action_ids(elem)
            self.direction[key] = [library.get_action(aid) for aid in action_ids]

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(HatButtonsData.tag, self._id)
        node.append(util.create_property_node(
            "button-count", self.button_count, PropertyType.Int
        ))
        for direction, sequence in self.direction.items():
            node.append(util.create_action_ids(
                f"{direction}", [action.id for action in sequence]
            ))
        return node

    @override
    def is_valid(self) -> bool:
        return True

    @override
    def _valid_selectors(self) -> List[str]:
        return list(self.direction.keys())

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        if selector not in self.direction:
            raise GremlinError(f"Key {selector} invalid as hat direction")
        return self.direction[selector]

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = HatButtonsData
