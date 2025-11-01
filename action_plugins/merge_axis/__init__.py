# -*- coding: utf-8; -*-

# Copyright (C) 2022 Lionel Ott
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
from typing import override, TYPE_CHECKING
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

import dill

from gremlin import shared_state, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.event_handler import Event
from gremlin.input_cache import Joystick
from gremlin.plugin_manager import PluginManager
from gremlin.profile import InputItemBinding, Library
from gremlin.types import ActionProperty, InputType, PropertyType, DataCreationMode

from gremlin.ui.action_model import ActionModel, SequenceIndex
from gremlin.ui.device import InputIdentifier
from gremlin.ui.profile import LabelValueSelectionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class MergeOperation(Enum):

    """Represents the available merge operations."""

    Average = 0
    Minimum = 1
    Maximum = 2
    Sum = 3
    Bidirectional = 4

    @classmethod
    def to_string(cls, value: MergeOperation) -> str:
        lookup = {
            MergeOperation.Average: "average",
            MergeOperation.Minimum: "minimum",
            MergeOperation.Maximum: "maximum",
            MergeOperation.Sum: "sum",
            MergeOperation.Bidirectional: "bidirectional",
        }

        res = lookup.get(value, None)
        if res is None:
            raise GremlinError(
                "MergeOperation: invalid value in lookup '{value}'"
            )
        return res

    @classmethod
    def to_enum(cls, value: str) -> MergeOperation:
        lookup = {
            "average": MergeOperation.Average,
            "minimum": MergeOperation.Minimum,
            "maximum": MergeOperation.Maximum,
            "sum": MergeOperation.Sum,
            "bidirectional": MergeOperation.Bidirectional,
        }
        res = lookup.get(value.lower(), None)
        if res is None:
            raise GremlinError(
                "MergeOperation: invalid value in lookup '{value.lower()}'"
            )
        return res


class MergeAxisFunctor(AbstractFunctor):

    def __init__(self, action: MergeAxisData):
        super().__init__(action)

    @override
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        joy = Joystick()
        axis1 = joy[self.data.axis_in1.device_guid].axis(
            self.data.axis_in1.input_id
        ).value
        axis2 = joy[self.data.axis_in2.device_guid].axis(
            self.data.axis_in2.input_id
        ).value

        value.current = MergeAxisFunctor.actions[self.data.operation](
            axis1, axis2
        )

        for functor in self.functors["children"]:
            functor(event, value, properties)

    @staticmethod
    def _average(value1: float, value2: float) -> float:
        return (value2 + value1) / 2.0

    @staticmethod
    def _minimum(value1: float, value2: float) -> float:
        return min(value1, value2)

    @staticmethod
    def _maximum(value1: float, value2: float) -> float:
        return max(value1, value2)

    @staticmethod
    def _sum(value1: float, value2: float) -> float:
        return util.clamp(value1 + value2, -1.0, 1.0)

    @staticmethod
    def _bidirectional(value1: float, value2: float) -> float:
        """Merges two axes into one:
            - the 1st axis controls the lower half of the value range
            - the 2nd axis controls the upper half

        Allows full deflection either way if only one axis is used.
        Performs differential mixing if both are used.

        Use case example: merging two pedal axes into a single left/right axis.
        """
        return (value2 - value1) / 2.0

    actions = {
        MergeOperation.Average: _average,
        MergeOperation.Minimum: _minimum,
        MergeOperation.Maximum: _maximum,
        MergeOperation.Sum: _sum,
        MergeOperation.Bidirectional: _bidirectional,
    }


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

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:merge_axis/MergeAxisAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @Property(LabelValueSelectionModel, notify=modelChanged)
    def operationList(self) -> LabelValueSelectionModel:
        """Returns the list of all valid operation names.

        Returns:
            List of valid operation names
        """
        operations = sorted(
            [e.name.capitalize() for e in MergeOperation
                if not e.name.startswith("_MergeOperation")]
        )
        return LabelValueSelectionModel(
            operations,
            operations,
            parent=self
        )

    @Property(LabelValueSelectionModel, notify=modelChanged)
    def mergeActionList(self) -> LabelValueSelectionModel:
        merge_actions = sorted(
            self.library.actions_by_type(MergeAxisData),
            key=lambda x: x.label,
        )

        return LabelValueSelectionModel(
            [ma.label for ma in merge_actions],
            [str(ma.id) for ma in merge_actions],
            parent=self
        )

    def _get_label(self) -> str:
        return self._data.label

    def _set_label(self, label: str) -> None:
        if label != self._data.label:
            self._data.label = label
            self.modelChanged.emit()

    def _get_merge_action(self) -> str:
        """Returns the UUID of the merge action being configured.

        Returns:
            string representation of an action UUID
        """
        return str(self._data.id)

    def _set_merge_action(self, uuid_str: str) -> None:
        """Sets the merge action to be configured..

        Args:
            uuid_str: string representation of an action UUID
        """
        # Do not process selecting the already active action
        if util.parse_id_or_uuid(uuid_str) == self._data.id:
            return

        # Remove current input item assignments from the action being deselected
        item = self._binding_model.input_item_binding.input_item
        identifier = InputIdentifier(
            item.device_id,
            item.input_type,
            item.input_id
        )

        if self._data.axis_in1 == identifier:
            self._data.axis_in1 = InputIdentifier()
        if self._data.axis_in2 == identifier:
            self._data.axis_in2 = InputIdentifier()

        # Update the library and action entries
        self._binding_model.append_action(
            self.library.get_action(util.parse_id_or_uuid(uuid_str)),
            self.sequence_index
        )
        self._binding_model.remove_action(self.sequence_index)
        self._binding_model.rootActionChanged.emit()

    def _get_axis(self, idx: int) -> InputIdentifier:
        return self._data.axis_in1 if idx == 1 else self._data.axis_in2

    def _set_axis(self, idx: int, value: InputIdentifier) -> None:
        if idx == 1:
            if value != self._data.axis_in1:
                self._data.axis_in1 = value
                self.modelChanged.emit()
        else:
            if value != self._data.axis_in2:
                self._data.axis_in2 = value
                self.modelChanged.emit()

    def _get_operation(self) -> str:
        return MergeOperation.to_string(self._data.operation).capitalize()

    def _set_operation(self, value: str) -> None:
        operation = MergeOperation.to_enum(value)
        if operation != self._data.operation:
            self._data.operation = operation
            self.modelChanged.emit()

    @Slot()
    def newMergeAxis(self) -> None:
        action = MergeAxisData.create(
            DataCreationMode.Create,
            self._binding_model.behavior_type
        )
        action.label = "New Merge Axis 123"

        self.library.add_action(action)
        self.modelChanged.emit()

    label = Property(
        str,
        fget=_get_label,
        fset=_set_label,
        notify=modelChanged
    )

    mergeAction = Property(
        str,
        fget=_get_merge_action,
        fset=_set_merge_action,
        notify=modelChanged
    )

    firstAxis = Property(
        InputIdentifier,
        fget=lambda c: MergeAxisModel._get_axis(c, 1),
        fset=lambda c, x: MergeAxisModel._set_axis(c, 1, x),
        notify=modelChanged
    )

    secondAxis = Property(
        InputIdentifier,
        fget=lambda c: MergeAxisModel._get_axis(c, 2),
        fset=lambda c, x: MergeAxisModel._set_axis(c, 2, x),
        notify=modelChanged
    )

    operation = Property(
        str,
        fget=_get_operation,
        fset=_set_operation,
        notify=modelChanged
    )


class MergeAxisData(AbstractActionData):

    version = 1
    name = "Merge Axis"
    tag = "merge-axis"
    icon = "\uF85C"

    functor = MergeAxisFunctor
    model = MergeAxisModel

    properties = [
        ActionProperty.ReuseByDefault,
        ActionProperty.ActivateDisabled,
    ]
    input_types = {
        InputType.JoystickAxis
    }

    def __init__(self, behavior_type: InputType=InputType.JoystickButton):
        super().__init__(behavior_type)

        self.label = ""
        self.axis_in1 = InputIdentifier()
        self.axis_in2 = InputIdentifier()
        self.operation = MergeOperation.Average

        self.children = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.label = util.read_property(node, "label", PropertyType.String)
        self.axis_in1.input_type = InputType.JoystickAxis
        self.axis_in1.device_guid = util.read_property(
            node, "axis1-guid", PropertyType.UUID
        )
        self.axis_in1.input_id = util.read_property(
            node, "axis1-axis", [PropertyType.Int, PropertyType.UUID]
        )
        self.axis_in2.input_type = InputType.JoystickAxis
        self.axis_in2.device_guid = util.read_property(
            node, "axis2-guid", PropertyType.UUID
        )
        self.axis_in2.input_id = util.read_property(
            node, "axis2-axis", [PropertyType.Int, PropertyType.UUID]
        )
        self.operation = MergeOperation.to_enum(util.read_property(
            node, "operation", PropertyType.String
        ))
        child_ids = util.read_action_ids(node.find("actions"))
        self.children = [library.get_action(aid) for aid in child_ids]

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MergeAxisData.tag, self._id)
        entries = [
            ["label", self.label, PropertyType.String],
            ["axis1-guid", self.axis_in1.device_guid, PropertyType.UUID],
            ["axis1-axis", self.axis_in1.input_id, [PropertyType.Int, PropertyType.UUID]],
            ["axis2-guid", self.axis_in2.device_guid, PropertyType.UUID],
            ["axis2-axis", self.axis_in2.input_id, [PropertyType.Int, PropertyType.UUID]],
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

    @override
    def is_valid(self) -> bool:
        return True

    @override
    def swap_uuid(self, old_uuid: uuid.UUID, new_uuid: uuid.UUID) -> bool:
        performed_swap = False
        if self.axis_in1.device_guid == old_uuid:
            self.axis_in1.device_guid = new_uuid
            performed_swap = True
        if self.axis_in2.device_guid == old_uuid:
            self.axis_in2.device_guid = new_uuid
            performed_swap = True
        return performed_swap

    @classmethod
    @override
    def _do_create(
            cls,
            mode: DataCreationMode,
            behavior_type: InputType
    ) -> AbstractActionData:
        if mode == DataCreationMode.Reuse:
            all_actions = shared_state.current_profile.library.actions_by_type(
            PluginManager().get_class(MergeAxisData.name)
            )
            if len(all_actions) == 0:
                return MergeAxisData(behavior_type)
            else:
                return all_actions[0]

    @override
    def _valid_selectors(self) -> list[str]:
        return ["children"]

    @override
    def _get_container(self, selector: str) -> list[AbstractActionData]:
        if selector == "children":
            return self.children

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = MergeAxisData