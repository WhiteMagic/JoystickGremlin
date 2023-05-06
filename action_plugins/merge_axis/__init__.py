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


class AxisIdentifier(NamedTuple):

    """Identifies a single axis that is used in an axis merge."""

    guid: uuid.UUID4 = dill.GUID_Invalid
    axis_id: int = -1


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
        return super().process_event(event, value)


class MergeAxisModel(ActionModel):

    def __init__(
            self,
            data: AbstractActionData,
            binding: InputItemBinding,
            parent: QtCore.QObject
    ):
        super().__init__(data, binding, parent)

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
        self.axis_1 = AxisIdentifier()
        self.axis_2 = AxisIdentifier()
        self.operation = MergeOperation.Average

    def from_xml(self, node: ElementTree.Element) -> None:
        self._id = util.read_action_id(node)
        self.label = util.read_property(node, "label", PropertyType.String)
        self.axis_1.guid = util.read_property(
            node, "axis1-guid", PropertyType.GUID
        )
        self.axis_1.axis_id = util.read_property(
            node, "axis1-axis", PropertyType.Int
        )
        self.axis_2.guid = util.read_property(
            node, "axis2-guid", PropertyType.GUID
        )
        self.axis_2.axis_id = util.read_property(
            node, "axis2-axis", PropertyType.Int
        )
        self.operation = MergeOperation.to_enum(util.read_property(
            node, "operation", PropertyType.String
        ))

    def to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MergeAxisData.tag, self._id)
        entries = [
            ["label", self.label, PropertyType.String],
            ["axis1-guid", self.axis_1.guid, PropertyType.GUID],
            ["axis1-axis", self.axis_1.axis_id, PropertyType.Int],
            ["axis2-guid", self.axis_2.guid, PropertyType.GUID],
            ["axis2-axis", self.axis_2.axis_id, PropertyType.Int],
            [
                "operation",
                MergeOperation.to_string(self.operation),
                PropertyType.String
            ],
        ]
        util.append_property_nodes(node, entries)

        return node

    def is_valid(self) -> bool:
        return super().is_valid()
    
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


create = MergeAxisData