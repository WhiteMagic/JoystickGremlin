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

from typing import TYPE_CHECKING, List
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.error import GremlinError
from gremlin.event_handler import Event
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType
from gremlin.ui.action_model import ActionModel, SequenceIndex

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class SplitAxisFunctor(AbstractFunctor):

    def __init__(self, action: SplitAxisData) -> None:
        super().__init__(action)

    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        if value.current < self.data.split_value:
            for functor in self.functors["lower"]:
                functor(event, value, properties)
        else:
            for functor in self.functors["upper"]:
                functor(event, value, properties)


class SplitAxisModel(ActionModel):

    splitValueChanged = QtCore.Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:split_axis/SplitAxisAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_split_value(self) -> float:
        return self._data.split_value

    def _set_split_value(self, value: float) -> None:
        if self._data.split_value != value:
            self._data.split_value = value
            self.splitValueChanged.emit()

    splitValue = QtCore.Property(
        float,
        fget=_get_split_value,
        fset=_set_split_value,
        notify=splitValueChanged
    )


class SplitAxisData(AbstractActionData):

    version = 1
    name = "Split Axis"
    tag = "split-axis"
    icon = "\uF859"

    functor = SplitAxisFunctor
    model = SplitAxisModel

    properties = (
        ActionProperty.ActivateDisabled,
    )
    input_types = (
        InputType.JoystickAxis,
    )

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickAxis
    ) -> None:
        super().__init__(behavior_type)

        self.lower_actions: List[AbstractActionData] = []
        self.upper_actions: List[AbstractActionData] = []
        self.split_value: float = 0.0

    def _from_xml(
            self,
            node: ElementTree.Element,
            library: Library
    ) -> None:
        self._id = util.read_action_id(node)
        lower_ids = util.read_action_ids(node.find("lower-actions"))
        self.lower_actions = [library.get_action(id) for id in lower_ids]
        upper_ids = util.read_action_ids(node.find("upper-actions"))
        self.upper_actions = [library.get_action(id) for id in upper_ids]
        self.split_value = util.read_property(
            node, "split-value", PropertyType.Float
        )

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(self.tag, self._id)
        node.append(util.create_property_node(
            "split-value", self.split_value, PropertyType.Float
        ))
        node.append(util.create_action_ids(
            "lower-actions", [action.id for action in self.lower_actions]
        ))
        node.append(util.create_action_ids(
            "upper-actions", [action.id for action in self.upper_actions]
        ))
        return node

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return ["lower", "upper"]

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        match selector:
            case "lower":
                return self.lower_actions
            case "upper":
                return self.upper_actions
            case _:
                raise GremlinError(
                    f"{self.name}: has no container with name {selector}"
                )

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass



create = SplitAxisData