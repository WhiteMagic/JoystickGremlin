# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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

from enum import Enum
from typing import List, NamedTuple, Optional
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

import dill

from gremlin import util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.event_handler import Event
from gremlin.profile import InputItemBinding, Library
from gremlin.types import InputType, PropertyType

from gremlin.ui.action_model import ActionModel
from gremlin.ui.profile import LabelValueSelectionModel


class AxisIdentifier(NamedTuple):

    """Identifies a single axis that is used in an axis merge."""

    guid: uuid.UUID4 = dill.GUID_Invalid
    axis_id: int | uuid.UUID = -1


class MergeOperation(Enum):

    """Represents the available merge operations."""

    Average = 0
    Minimum = 1
    Maximum = 2

    __enum_to_string = {
        Average: "average",
        Minimum: "minimum",
        Maximum: "maximum"
    }

    __string_to_enum = {
        "average": Average,
        "minimum": Minimum,
        "maximum": Maximum
    }

    @staticmethod
    def to_string(value: MergeOperation) -> str:
        try:
            return MergeOperation.__enum_to_string[value]
        except KeyError:
            raise GremlinError(
                "MergeOperation: invalid value in lookup '{value}'"
            )

    @staticmethod
    def to_enum(value: str) -> MergeOperation:
        try:
            return MergeOperation.__string_to_enum[value]
        except KeyError:
            raise GremlinError(
                "MergeOperation: invalid value in lookup '{value}'"
            )


class MergeAxisFunctor(AbstractFunctor):

    def __init__(self, action: MergeAxisModel):
        super().__init__(action)

    def process_event(self, event: Event, value: Value) -> None:
        for functor in self.functors["children"]:
            functor(event, value)


class MergeAxisModel(ActionModel):

    modelChanged = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ):
        super().__init__(data, binding_model, action_index, parent_index, parent)

    @Property(list, notify=modelChanged)
    def operationList(self) -> List[str]:
        """Returns the list of all valid operation names.

        Returns:
            List of valid operation names
        """
        return sorted(
            [e.name for e in MergeOperation
             if not e.name.startswith("_MergeOperation")]
        )

    @Property(list, notify=modelChanged)
    def actionList(self) -> List[str]:
        """Returns the list of all existing MergeAction instances of a provile.

        Returns:
            List of all existing actions
        """
        all_actions = self._binding_model.input_item_binding.libary.actions_of_type(MergeAxisData)

    @Property(LabelValueSelectionModel, notify=modelChanged)
    def mergeActions(self) -> LabelValueSelectionModel:
        return LabelValueSelectionModel([1,2,3], ["One", "Two", "Three"])

    def _add_action_impl(self, action: AbstractActionData, options: Any) -> None:
        self._data.insert_action(action, options)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:merge_axis/MergeAxisAction.qml"
        ).fileName()


class MergeAxisData(AbstractActionData):

    version = 1
    name = "Merge Axis"
    tag = "merge-axis"

    functor = MergeAxisFunctor
    model = MergeAxisModel

    input_types = {
        InputType.JoystickAxis
    }

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ):
        super().__init__(behavior_type)

        # Merge action information
        self.label = ""
        self.axis_in1 = AxisIdentifier()
        self.axis_in2 = AxisIdentifier()
        self.operation = MergeOperation.Average

        self.children = []

    def from_xml(self, node: ElementTree.Element) -> None:
        self._id = util.read_action_id(node)
        self.label = util.read_property(node, "label", PropertyType.String)
        self.axis_in1.guid = util.read_property(
            node, "axis1-guid", PropertyType.GUID
        )
        self.axis_in1.axis_id = util.read_property(
            node, "axis1-axis", [PropertyType.Int, PropertyType.UUID]
        )
        self.axis_in2.guid = util.read_property(
            node, "axis2-guid", PropertyType.GUID
        )
        self.axis_in2.axis_id = util.read_property(
            node, "axis2-axis", [PropertyType.Int, PropertyType.UUID]
        )
        self.operation = MergeOperation.to_enum(util.read_property(
            node, "operation", PropertyType.String
        ))
        child_ids = util.read_action_ids(node.find("actions"))
        self.children = [library.get_action(aid) for aid in child_ids]

    def to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MergeAxisData.tag, self._id)
        entries = [
            ["label", self.label, PropertyType.String],
            ["axis1-guid", self.axis_in1.guid, PropertyType.GUID],
            ["axis1-axis", self.axis_in1.axis_id, [PropertyType.Int, PropertyType.UUID]],
            ["axis2-guid", self.axis_in2.guid, PropertyType.GUID],
            ["axis2-axis", self.axis_in2.axis_id, [PropertyType.Int, PropertyType.UUID]],
            [
                "operation",
                MergeOperation.to_string(self.operation),
                PropertyType.String
            ],
        ]
        util.append_property_nodes(node, entries)
        node.append(util.create_action_ids(
            "actions",
            [child.id for child in self.children]
        ))

        return node

    def is_valid(self) -> bool:
        return super().is_valid()

    def _valid_selectors(self) -> List[str]:
        return ["children"]

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        if selector == "children":
            return self.children

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = MergeAxisData