# -*- coding: utf-8; -*-

# Copyright (C) 2024 Lionel Ott
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

import time
from typing import Any, List, Optional, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from typing import override
from gremlin import event_handler, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType, DataCreationMode

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class ChainFunctor(AbstractFunctor):

    """Implements the function executed of the Description action at runtime."""

    def __init__(self, action: ChainData):
        super().__init__(action)

        self.current_index = 0
        self.last_execution = 0.0

    @override
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        if self.data.timeout > 0.0:
            if self.last_execution + self.data.timeout < time.time():
                self.current_index = 0
            self.last_execution = time.time()

        for functor in self.functors[str(self.current_index)]:
            functor(event, value, properties)

        if value.current:
            self.current_index = \
                (self.current_index + 1) % len(self.data.chain_sequences)


class ChainModel(ActionModel):

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
            "core_plugins:chain/ChainAction.qml"
        ).fileName()

    @Property(int, notify=changed)
    def chainCount(self) -> int:
        return len(self._data.chain_sequences)

    @Slot()
    def addSequence(self) -> None:
        self._data.chain_sequences.append([])
        self.changed.emit()

    @Slot(int)
    def removeSequence(self, index: int) -> None:
        if index < 0 or index >= len(self._data.chain_sequences):
            raise GremlinError(f"Index {index} invalid as chain container")

        del self._data.chain_sequences[index]
        self.changed.emit()
        self._binding_model.sync_data()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_timeout(self) -> float:
        return self._data.timeout

    def _set_timeout(self, value: float) -> None:
        if value != self._data.timeout:
            self._data.timeout = value
            self.changed.emit()

    timeout = Property(
        type=float,
        fget=_get_timeout,
        fset=_set_timeout,
        notify=changed
    )

class ChainData(AbstractActionData):

    """Model of a description action."""

    version = 1
    name = "Chain"
    tag = "chain"
    icon = "\uF813"

    functor = ChainFunctor
    model = ChainModel

    properties = [
        ActionProperty.ActivateDisabled
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

        self.chain_sequences = [[],]
        self.timeout = 0.0

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.timeout = util.read_property(node, "timeout", PropertyType.Float)
        chain_dict = {}
        # Extract action ids for each chain
        for elem in node.findall(".//action-id/.."):
            key = int(elem.tag.split("-")[1])
            action_ids = util.read_action_ids(elem)
            chain_dict[key] = [library.get_action(aid) for aid in action_ids]
        self.chain_sequences = []
        for idx in sorted(chain_dict.keys()):
            self.chain_sequences.append(chain_dict[idx])

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(ChainData.tag, self._id)
        for i, chain in enumerate(self.chain_sequences):
            node.append(util.create_action_ids(
                f"chain-{i}", [action.id for action in chain]
            ))
        node.append(util.create_property_node(
            "timeout", self.timeout, PropertyType.Float
        ))
        return node

    @override
    def is_valid(self) -> bool:
        return True

    @override
    def _valid_selectors(self) -> List[str]:
        return [str(i) for i in range(len(self.chain_sequences))]

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        index = int(selector)
        if index < 0 or index >= len(self.chain_sequences):
            raise GremlinError(f"Index {index} invalid as chain container")
        return self.chain_sequences[index]

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = ChainData
