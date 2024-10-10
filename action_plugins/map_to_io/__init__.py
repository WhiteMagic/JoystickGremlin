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

from typing import TYPE_CHECKING, List
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import mode_manager, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    DataCreationMode, Value
from gremlin.error import GremlinError
from gremlin.event_handler import Event, EventListener
from gremlin.intermediate_output import IntermediateOutput
from gremlin.profile import Library
from gremlin.types import ActionProperty, AxisMode, InputType, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel


if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class MapToIOFunctor(AbstractFunctor):

    def __init__(self, instance: MapToIOData):
        super().__init__(instance)
        self._io = IntermediateOutput()
        self._event_listener = EventListener()

    def __call__(self, event: Event, value: Value) -> None:
        if not self._should_execute(value):
            return

        # Emit an event with the IO guid and the rest of the system will
        # then take core of executing it
        io_input = self._io[self.data.io_input_guid]
        is_pressed = value.current \
            if io_input.type == InputType.JoystickButton else None
        if self.data.button_inverted:
            is_pressed = not is_pressed
        input_value = value.current \
            if io_input.type != InputType.JoystickButton else None
        self._event_listener.joystick_event.emit(
            Event(
                event_type=io_input.type,
                identifier=io_input.guid,
                device_guid=self._io.device_guid,
                mode=mode_manager.ModeManager().current.name,
                value=input_value,
                is_pressed=is_pressed,
                raw_value=value.raw
            )
        )


class MapToIOModel(ActionModel):

    ioInputGuidChanged = Signal()
    ioInputTypeChanged = Signal()
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
    ):
        super().__init__(data, binding_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:map_to_io/MapToIOAction.qml"
        ).fileName()

    def _get_io_input_guid(self) -> str:
        return str(self._data.io_input_guid)

    def _set_io_input_guid(self, guid_str: str) -> None:
        try:
            guid = uuid.UUID(guid_str)
            if guid != self._data.io_input_guid:
                self._data.io_input_guid = guid
                self.ioInputGuidChanged.emit()
        except ValueError:
            pass

    def _get_io_input_type(self) -> str:
        return InputType.to_string(self._data.io_input_type)

    def _set_io_input_type(self, input_type: str) -> None:
        input_type_tmp = InputType.to_enum(input_type)
        if input_type_tmp == self._data.io_input_type:
            return
        self._data.io_input_type = input_type_tmp
        self.ioInputTypeChanged.emit()

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

    ioInputGuid = Property(
        str,
        fget=_get_io_input_guid,
        fset=_set_io_input_guid,
        notify=ioInputGuidChanged
    )
    ioInputType = Property(
        str,
        fget=_get_io_input_type,
        fset=_set_io_input_type,
        notify=ioInputTypeChanged
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

class MapToIOData(AbstractActionData):

    """Action propagating data to the intermediate output inputs."""

    version = 1
    name  = "Map to IO"
    tag = "map-to-io"
    icon = "\uF6E7"

    functor = MapToIOFunctor
    model = MapToIOModel

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
    ):
        super().__init__(behavior_type)

        # Select an initially valid IO input
        io = IntermediateOutput()
        try:
            io_input = io.inputs_of_type([behavior_type])[0]
        except (GremlinError, IndexError):
            io.create(behavior_type)
            io_input = io.inputs_of_type([behavior_type])[0]

        # Model variables
        self.io_input_guid = io_input.guid
        self.io_input_type = behavior_type
        self.axis_mode = AxisMode.Absolute
        self.axis_scaling = 1.0
        self.button_inverted = False

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.io_input_guid = util.read_property(
            node, "io-input-guid", PropertyType.UUID
        )
        self.io_input_type = util.read_property(
            node, "io-input-type", PropertyType.InputType
        )
        if self.io_input_type == InputType.JoystickAxis:
            self.axis_mode = util.read_property(
                node, "axis-mode", PropertyType.AxisMode
            )
            self.axis_scaling = util.read_property(
                node, "axis-scaling", PropertyType.Float
            )
        if self.io_input_type == InputType.JoystickButton:
            self.button_inverted = util.read_property(
                node, "button-inverted", PropertyType.Bool
            )

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MapToIOData.tag, self._id)
        node.append(util.create_property_node(
            "io-input-guid", self.io_input_guid, PropertyType.UUID
        ))
        node.append(util.create_property_node(
            "io-input-type", self.io_input_type, PropertyType.InputType
        ))
        if self.io_input_type == InputType.JoystickAxis:
            node.append(util.create_property_node(
                "axis-mode", self.axis_mode, PropertyType.AxisMode
            ))
            node.append(util.create_property_node(
                "axis-scaling", self.axis_scaling, PropertyType.Float
            ))
        if self.io_input_type == InputType.JoystickButton:
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
        self._io_input_type = new_behavior


create = MapToIOData