# -*- coding: utf-8; -*-

# Copyright (C) 2023 Lionel Ott
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
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import input_cache, mode_manager, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value
from gremlin.error import GremlinError
from gremlin.event_handler import Event, EventListener
from gremlin.logical_device import LogicalDevice
from gremlin.profile import Library
from gremlin.types import ActionProperty, AxisMode, InputType, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel
from gremlin.ui.device import InputIdentifier


if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class MapToLogicalDeviceFunctor(AbstractFunctor):

    def __init__(self, instance: MapToLogicalDeviceData) -> None:
        super().__init__(instance)
        self._logical = LogicalDevice()
        self._event_listener = EventListener()

    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        if not self._should_execute(value):
            return
        input = self._logical[LogicalDevice.Input.Identifier(
            self.data.logical_input_type,
            self.data.logical_input_id
        )]

        # Determine correct event values and update the logical device's
        # internal state.
        is_pressed = None
        input_value = None
        match input.type:
            case InputType.JoystickAxis:
                input_value = value.current
                input.update(input_value)
            case InputType.JoystickButton:
                is_pressed = value.current
                if self.data.button_inverted:
                    is_pressed = not is_pressed
                input.update(is_pressed)
            case InputType.JoystickHat:
                input_value = value.current
                input.update(input_value)

        # Emit an event with the LogicalDevice guid and the rest of the
        # system will then take care of executing it.
        self._event_listener.joystick_event.emit(
            Event(
                event_type=input.type,
                identifier=input.id,
                device_guid=self._logical.device_guid,
                mode=mode_manager.ModeManager().current.name,
                value=input_value,
                is_pressed=is_pressed,
                raw_value=value.raw
            )
        )


class MapToLogicalDeviceModel(ActionModel):

    logicalInputIdentifierChanged = Signal()
    logicalInputTypeChanged = Signal()
    axisModeChanged = Signal()
    axisScalingChanged = Signal()
    buttonInvertedChanged = Signal()

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
            "core_plugins:map_to_logical_device/MapToLogicalDeviceAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_logical_input_identifier(self) -> InputIdentifier:
        return InputIdentifier(
            LogicalDevice().device_guid,
            self._data.logical_input_type,
            self._data.logical_input_id,
            parent=self
        )

    def _set_logical_input_identifier(self, identifier: InputIdentifier) -> None:
        new_identifier = InputIdentifier(
            LogicalDevice().device_guid,
            self._data.logical_input_type,
            self._data.logical_input_id,
            parent=self
        )
        if new_identifier != identifier:
            self._data.logical_input_id = identifier.input_id
            self._data.logical_input_type = identifier.input_type
            self.logicalInputIdentifierChanged.emit()

    def _get_axis_mode(self) -> str:
        return AxisMode.to_string(self._data.axis_mode)

    def _set_axis_mode(self, axis_mode: str) -> None:
        axis_mode_tmp = AxisMode.to_enum(axis_mode)
        if axis_mode_tmp == self._data.axis_mode:
            return
        self._data.axis_mode = axis_mode_tmp
        self.axisModeChanged.emit()

    def _get_axis_scaling(self) -> float:
        return self._data.axis_scaling

    def _set_axis_scaling(self, axis_scaling: float) -> None:
        if axis_scaling == self._data.axis_scaling:
            return
        self._data.axis_scaling = axis_scaling
        self.axisScalingChanged.emit()

    def _get_button_inverted(self) -> bool:
        return self._data.button_inverted

    def _set_button_inverted(self, button_inverted: bool) -> None:
        if button_inverted == self._data.button_inverted:
            return
        self._data.button_inverted = button_inverted
        self.buttonInvertedChanged.emit()

    logicalInputIdentifier = Property(
        InputIdentifier,
        fget=_get_logical_input_identifier,
        fset=_set_logical_input_identifier,
        notify=logicalInputIdentifierChanged
    )
    axisMode = Property(
        str,
        fget=_get_axis_mode,
        fset=_set_axis_mode,
        notify=axisModeChanged
    )
    axisScaling = Property(
        float,
        fget=_get_axis_scaling,
        fset=_set_axis_scaling,
        notify=axisScalingChanged
    )
    buttonInverted = Property(
        bool,
        fget=_get_button_inverted,
        fset=_set_button_inverted,
        notify=buttonInvertedChanged
    )

class MapToLogicalDeviceData(AbstractActionData):

    """Action propagating data to the logical device inputs."""

    version = 1
    name  = "Map to Logical Device"
    tag = "map-to-logical-device"
    icon = "\uF6E7"

    functor = MapToLogicalDeviceFunctor
    model = MapToLogicalDeviceModel

    properties = [
        ActionProperty.ActivateOnBoth
    ]
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ) -> None:
        super().__init__(behavior_type)

        # Select an initially valid logical input
        logical = LogicalDevice()
        try:
            logical_input = logical.inputs_of_type([behavior_type])[0]
        except (GremlinError, IndexError):
            logical.create(behavior_type)
            logical_input = logical.inputs_of_type([behavior_type])[0]

        # Model variables
        self.logical_input_id = logical_input.id
        self.logical_input_type = behavior_type
        self.axis_mode = AxisMode.Absolute
        self.axis_scaling = 1.0
        self.button_inverted = False

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.logical_input_id = util.read_property(
            node, "logical-input-id", PropertyType.Int
        )
        self.logical_input_type = util.read_property(
            node, "logical-input-type", PropertyType.InputType
        )
        if self.logical_input_type == InputType.JoystickAxis:
            self.axis_mode = util.read_property(
                node, "axis-mode", PropertyType.AxisMode
            )
            self.axis_scaling = util.read_property(
                node, "axis-scaling", PropertyType.Float
            )
        if self.logical_input_type == InputType.JoystickButton:
            self.button_inverted = util.read_property(
                node, "button-inverted", PropertyType.Bool
            )

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MapToLogicalDeviceData.tag, self._id)
        node.append(util.create_property_node(
            "logical-input-id", self.logical_input_id, PropertyType.Int
        ))
        node.append(util.create_property_node(
            "logical-input-type", self.logical_input_type, PropertyType.InputType
        ))
        if self.logical_input_type == InputType.JoystickAxis:
            node.append(util.create_property_node(
                "axis-mode", self.axis_mode, PropertyType.AxisMode
            ))
            node.append(util.create_property_node(
                "axis-scaling", self.axis_scaling, PropertyType.Float
            ))
        if self.logical_input_type == InputType.JoystickButton:
            node.append(util.create_property_node(
                "button-inverted", self.button_inverted, PropertyType.Bool
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
        self._logical_input_type = new_behavior


create = MapToLogicalDeviceData