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

import collections
import copy
import logging
import math
from typing import override, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore, QtGui, QtQml
from PySide6.QtCore import Property, Signal, Slot, QCborTag

from gremlin import event_handler, spline, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.error import GremlinError, ProfileError
from gremlin.input_cache import Joystick
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType
from gremlin.util import clamp

from gremlin.ui.action_model import SequenceIndex, ActionModel
from gremlin.ui.device import InputIdentifier
from gremlin.ui.profile import LabelValueSelectionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


Vector2 = collections.namedtuple("Vector2", ["x", "y"])


class DualAxisDeadzoneFunctor(AbstractFunctor):

    """Implements the function executed of the Description action at runtime."""

    def __init__(self, action: DualAxisDeadzoneData):
        super().__init__(action)

        self.joy = Joystick()

    @override
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        # Retrieve current joystick values
        x_value = self.joy[self.data.axis1.device_guid].axis(
            self.data.axis1.input_id
        ).value
        y_value = self.joy[self.data.axis2.device_guid].axis(
            self.data.axis2.input_id
        ).value

        # Apply the deadzones, a circular one around the center and a
        # rectangular around the outside.
        alpha = math.atan2(y_value, x_value)
        lower = Vector2(
            abs(math.cos(alpha) * self.data.inner_deadzone),
            abs(math.sin(alpha) * self.data.inner_deadzone)
        )
        upper = Vector2(self.data.outer_deadzone, self.data.outer_deadzone)

        try:
            px = max(0.0, min(1.0, (abs(x_value) - lower.x) / (upper.x - lower.x)))
            py = max(0.0, min(1.0, (abs(y_value) - lower.y) / (upper.y - lower.y)))

            # Create separate value instances and set their values before passing
            # everything on to the child functors. The event will not necessarily
            # corespond to the correct axis but that should be fine.
            value_x = copy.deepcopy(value)
            value_x.current = math.copysign(px, x_value)
            for functor in self.functors["first"]:
                functor(event, value_x, properties)

            value_y = copy.deepcopy(value)
            value_y.current = math.copysign(py, y_value)
            for functor in self.functors["second"]:
                functor(event, value_y, properties)
        except ZeroDivisionError:
            logging.getLogger("system").error(
                f"DualAxisDeadzone: ({self.data.label}) deadzone limits too " +
                f"close to each other"
            )


class DualAxisDeadzoneModel(ActionModel):

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
            "core_plugins:dual_axis_deadzone/DualAxisDeadzoneAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @Slot()
    def newDeadzone(self) -> None:
        action = DualAxisDeadzoneData.create(
            DataCreationMode.Create,
            self._binding_model.behavior_type
        )
        action.label = "Dual Axis Deadzone"

        self.library.add_action(action)
        self.modelChanged.emit()

    @Property(LabelValueSelectionModel, notify=modelChanged)
    def deadzoneActionList(self) -> LabelValueSelectionModel:
        deadzone_actions = sorted(
            self.library.actions_by_type(DualAxisDeadzoneData),
            key=lambda x: x.label,
        )

        return LabelValueSelectionModel(
            [da.label for da in deadzone_actions],
            [str(da.id) for da in deadzone_actions],
            parent=self
        )

    def _get_axis(self, idx: int) -> InputIdentifier:
        return self._data.axis1 if idx == 1 else self._data.axis2

    def _set_axis(self, idx: int, value: InputIdentifier) -> None:
        if idx == 1:
            if value != self._data.axis1:
                self._data.axis1 = value
                self.modelChanged.emit()
        else:
            if value != self._data.axis2:
                self._data.axis2 = value
                self.modelChanged.emit()

    def _get_deadzone(self) -> str:
        return str(self._data.id)

    def _set_deadzone(self, uuid_str: str) -> None:
        # Don't attempt to set the already set deadzone
        if util.parse_id_or_uuid(uuid_str) == self._data.id:
            return

        # Remove current input item assignments from the action being deselected
        item = self._binding_model.input_item_binding.input_item
        identifier = InputIdentifier(
            item.device_id,
            item.input_type,
            item.input_id
        )

        if self._data.axis1 == identifier:
            self._data.axis1 = InputIdentifier()
        if self._data.axis2 == identifier:
            self._data.axis2 = InputIdentifier()

        # Update the library and action entries
        self._binding_model.append_action(
            self.library.get_action(util.parse_id_or_uuid(uuid_str)),
            self.sequence_index
        )
        self._binding_model.remove_action(self.sequence_index)
        self._binding_model.rootActionChanged.emit()

    @Property(float, notify=modelChanged)
    def innerDeadzone(self) -> float:
        return self._data.inner_deadzone

    @innerDeadzone.setter
    def innerDeadzone(self, value: float) -> None:
        if value != self._data.inner_deadzone:
            if (self._data.outer_deadzone - value) > 0.01:
                self._data.inner_deadzone = value
            self.modelChanged.emit()

    @Property(str, notify=modelChanged)
    def label(self) -> str:
        return self._data.label

    @label.setter
    def label(self, label: str) -> None:
        if label != self._data.label:
            self._data.label = label
            self.modelChanged.emit()

    @Property(float, notify=modelChanged)
    def outerDeadzone(self) -> float:
        return self._data.outer_deadzone

    @outerDeadzone.setter
    def outerDeadzone(self, value: float) -> None:
        if value != self._data.outer_deadzone:
            if (value - self._data.inner_deadzone) > 0.01:
                self._data.outer_deadzone = value
            self.modelChanged.emit()

    axis1 = Property(
        InputIdentifier,
        fget=lambda c: DualAxisDeadzoneModel._get_axis(c, 1),
        fset=lambda c, x: DualAxisDeadzoneModel._set_axis(c, 1, x),
        notify=modelChanged
    )

    axis2 = Property(
        InputIdentifier,
        fget=lambda c: DualAxisDeadzoneModel._get_axis(c, 2),
        fset=lambda c, x: DualAxisDeadzoneModel._set_axis(c, 2, x),
        notify=modelChanged
    )

    deadzone = Property(
        str,
        fget=_get_deadzone,
        fset=_set_deadzone,
        notify=modelChanged
    )


class DualAxisDeadzoneData(AbstractActionData):

    """Model of a description action."""

    version = 1
    name = "Dual Axis Deadzone"
    tag = "dual-axis-deadzone"
    icon = "\uF18C"

    functor = DualAxisDeadzoneFunctor
    model = DualAxisDeadzoneModel

    properties = [
        ActionProperty.ActivateDisabled,
    ]
    input_types = [
        InputType.JoystickAxis,
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickAxis
    ):
        super().__init__(behavior_type)

        self.label = ""
        self.inner_deadzone = 0.0
        self.outer_deadzone = 1.0
        self.axis1 = InputIdentifier()
        self.axis2 = InputIdentifier()

        self.output1_actions = []
        self.output2_actions = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)

        # Parse deadzone information
        self.label = util.read_property(node, "label", PropertyType.String)
        self.inner_deadzone = util.read_property(
            node, "inner-deadzone", PropertyType.Float
        )
        self.outer_deadzone = util.read_property(
            node, "outer-deadzone", PropertyType.Float
        )

        # Parse axes data
        self.axis1.input_type = InputType.JoystickAxis
        self.axis1.device_guid = util.read_property(
            node, "axis1-guid", PropertyType.UUID
        )
        self.axis1.input_id = util.read_property(
            node, "axis1-axis", [PropertyType.Int, PropertyType.UUID]
        )
        self.axis2.input_type = InputType.JoystickAxis
        self.axis2.device_guid = util.read_property(
            node, "axis2-guid", PropertyType.UUID
        )
        self.axis2.input_id = util.read_property(
            node, "axis2-axis", [PropertyType.Int, PropertyType.UUID]
        )

        # Parse child actions
        output1_actions = util.read_action_ids(node.find("output1-actions"))
        self.output1_actions = \
            [library.get_action(aid) for aid in output1_actions]
        output2_actions = util.read_action_ids(node.find("output2-actions"))
        self.output2_actions = \
            [library.get_action(aid) for aid in output2_actions]

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(DualAxisDeadzoneData.tag, self._id)

        # Write axis and deadzone data
        entries = [
            ["label", self.label, PropertyType.String],
            ["inner-deadzone", self.inner_deadzone, PropertyType.Float],
            ["outer-deadzone", self.outer_deadzone, PropertyType.Float],
            ["axis1-guid", self.axis1.device_guid, PropertyType.UUID],
            ["axis1-axis", self.axis1.input_id, [PropertyType.Int, PropertyType.UUID]],
            ["axis2-guid", self.axis2.device_guid, PropertyType.UUID],
            ["axis2-axis", self.axis2.input_id, [PropertyType.Int, PropertyType.UUID]],
        ]
        util.append_property_nodes(node, entries)

        # Write action ids
        node.append(util.create_action_ids(
            "output1-actions", [action.id for action in self.output1_actions]
        ))
        node.append(util.create_action_ids(
            "output2-actions", [action.id for action in self.output2_actions]
        ))

        return node

    @override
    def is_valid(self) -> bool:
        axis_valid = self.axis1.isValid and self.axis2.isValid
        deadzone_valid = abs(self.outer_deadzone - self.inner_deadzone) >= 0.01
        return axis_valid and deadzone_valid

    @override
    def _valid_selectors(self) -> list[str]:
        return ["first", "second"]

    @override
    def _get_container(self, selector: str) -> list[AbstractActionData]:
        if selector == "first":
            return self.output1_actions
        elif selector == "second":
            return self.output2_actions

    @override
    def swap_uuid(self, old_uuid: uuid.UUID, new_uuid: uuid.UUID) -> bool:
        performed_swap = False
        if self.axis1.device_guid == old_uuid:
            self.axis1.device_guid = new_uuid
            performed_swap = True
        if self.axis2.device_guid == old_uuid:
            self.axis2.device_guid = new_uuid
            performed_swap = True
        return performed_swap

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = DualAxisDeadzoneData
