# -*- coding: utf-8; -*-

# Copyright (C) 2016 Lionel Ott
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

import threading
import time
from typing import List, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from vjoy.vjoy import VJoyProxy

from gremlin import device_helpers, device_initialization, error, \
    event_handler, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.profile import Library
from gremlin.types import ActionProperty, AxisMode, InputType, PropertyType, DataCreationMode

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class MapToVjoyFunctor(AbstractFunctor):

    """Executes a map to vjoy action when called."""

    SCALING_MULTIPLIER = 1 / 1000.0
    THREAD_SLEEP_DURATION_S = 0.01

    def __init__(self, action: MapToVjoyData):
        super().__init__(action)

        self.needs_auto_release = False #self._check_for_auto_release(action)
        self.thread_running = False
        self.should_stop_thread = False
        self.thread_last_update = time.time()
        self.thread = None
        self.axis_delta_value = 0.0
        self.axis_value = 0.0

    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        if not self._should_execute(value):
            return

        if self.data.vjoy_input_type == InputType.JoystickAxis:
            if self.data.axis_mode == AxisMode.Absolute:
                VJoyProxy()[self.data.vjoy_device_id] \
                    .axis(self.data.vjoy_input_id).value = value.current
            else:
                self.should_stop_thread = abs(event.value) < 0.05
                self.axis_delta_value = value.current * (
                    self.data.axis_scaling * self.SCALING_MULTIPLIER
                )
                self.thread_last_update = time.time()
                if self.thread_running is False:
                    if isinstance(self.thread, threading.Thread):
                        self.thread.join()
                    self.thread = threading.Thread(
                        target=self.relative_axis_thread
                    )
                    self.thread.start()

        elif self.data.vjoy_input_type == InputType.JoystickButton:
            is_pressed = value.current
            if self.data.button_inverted:
                is_pressed = not is_pressed
            VJoyProxy()[self.data.vjoy_device_id] \
                .button(self.data.vjoy_input_id).is_pressed = is_pressed

            if is_pressed and ActionProperty.DisableAutoRelease not in properties:
                device_helpers.ButtonReleaseActions().register_button_release(
                    (self.data.vjoy_device_id, self.data.vjoy_input_id),
                    event,
                    self.data.button_inverted
                )

        elif self.data.vjoy_input_type == InputType.JoystickHat:
            VJoyProxy()[self.data.vjoy_device_id] \
                .hat(self.data.vjoy_input_id).direction = value.current

    def relative_axis_thread(self) -> None:
        self.thread_running = True
        vjoy_dev = VJoyProxy()[self.data.vjoy_device_id]
        self.axis_value = vjoy_dev.axis(self.data.vjoy_input_id).value
        while self.thread_running:
            # Abort if the vJoy device is no longer valid
            if not vjoy_dev.is_owned():
                self.thread_running = False
                return

            try:
                # If the vjoy value has was changed from what we set it to
                # in the last iteration, terminate the thread
                change = vjoy_dev.axis(self.data.vjoy_input_id).value - \
                        self.axis_value
                if abs(change) > 0.0001:
                    self.thread_running = False
                    self.should_stop_thread = True
                    return

                self.axis_value = util.clamp(
                    self.axis_value + self.axis_delta_value,
                    -1.0,
                    1.0
                )
                vjoy_dev.axis(self.data.vjoy_input_id).value = self.axis_value

                if self.should_stop_thread and \
                        self.thread_last_update + 1.0 < time.time():
                    self.thread_running = False
                time.sleep(self.THREAD_SLEEP_DURATION_S)
            except error.VJoyError:
                self.thread_running = False


class MapToVjoyModel(ActionModel):

    # Signals emitted when properties change
    vjoyDeviceIdChanged = Signal()
    vjoyInputIdChanged = Signal()
    inputTypeChanged = Signal()
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
            "core_plugins:map_to_vjoy/MapToVjoyAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_vjoy_device_id(self) -> int:
        return self._data.vjoy_device_id

    def _set_vjoy_device_id(self, vjoy_device_id: int) -> None:
        if vjoy_device_id == self._data.vjoy_device_id:
            return
        self._data.vjoy_device_id = vjoy_device_id
        self.vjoyDeviceIdChanged.emit()

    def _get_vjoy_input_id(self) -> int:
        return self._data.vjoy_input_id

    def _set_vjoy_input_id(self, vjoy_input_id: int) -> None:
        if vjoy_input_id == self._data.vjoy_input_id:
            return
        self._data.vjoy_input_id = vjoy_input_id
        self.vjoyInputIdChanged.emit()

    def _get_vjoy_input_type(self) -> str:
        return InputType.to_string(self._data.vjoy_input_type)

    def _set_vjoy_input_type(self, input_type: str) -> None:
        input_type_tmp = InputType.to_enum(input_type)
        if input_type_tmp == self._data.vjoy_input_type:
            return
        self._data.vjoy_input_type = input_type_tmp
        self.inputTypeChanged.emit()

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

    # Define properties
    vjoyDeviceId = Property(
        int,
        fget=_get_vjoy_device_id,
        fset=_set_vjoy_device_id,
        notify=vjoyDeviceIdChanged
    )
    vjoyInputId = Property(
        int,
        fget=_get_vjoy_input_id,
        fset=_set_vjoy_input_id,
        notify=vjoyInputIdChanged
    )
    vjoyInputType = Property(
        str,
        fget=_get_vjoy_input_type,
        fset=_set_vjoy_input_type,
        notify=inputTypeChanged
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


class MapToVjoyData(AbstractActionData):

    """Action feeding a vJoy device."""

    DEFAULT_SCALING = 1.0

    version = 1
    name = "Map to vJoy"
    tag = "map-to-vjoy"
    icon = "\uF448"

    functor = MapToVjoyFunctor
    model = MapToVjoyModel

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

        # Select an initially valid vJoy input
        device = device_initialization.vjoy_devices()[0]
        vjoy_id = device.vjoy_id
        input_id = 1
        if behavior_type == InputType.JoystickAxis:
            input_id = device.axis_map[0].axis_index

        # Model variables
        self.vjoy_device_id = vjoy_id
        self.vjoy_input_id = input_id
        self.vjoy_input_type = behavior_type
        self.axis_mode = AxisMode.Absolute
        self.axis_scaling = self.DEFAULT_SCALING
        self.button_inverted = False

    @classmethod
    def can_create(cls) -> bool:
        return len(device_initialization.vjoy_devices()) > 0

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.vjoy_device_id = util.read_property(
            node, "vjoy-device-id", PropertyType.Int
        )
        self.vjoy_input_id = util.read_property(
            node, "vjoy-input-id", PropertyType.Int
        )
        self.vjoy_input_type = util.read_property(
            node, "vjoy-input-type", PropertyType.InputType
        )
        if self.vjoy_input_type == InputType.JoystickAxis:
            self.axis_mode = util.read_property(
                node, "axis-mode", PropertyType.AxisMode
            )
            self.axis_scaling = util.read_property(
                node, "axis-scaling", PropertyType.Float
            )
        if self.vjoy_input_type == InputType.JoystickButton:
            self.button_inverted = util.read_property(
                node, "button-inverted", PropertyType.Bool
            )

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MapToVjoyData.tag, self._id)
        node.append(util.create_property_node(
            "vjoy-device-id", self.vjoy_device_id, PropertyType.Int
        ))
        node.append(util.create_property_node(
            "vjoy-input-id", self.vjoy_input_id, PropertyType.Int
        ))
        node.append(util.create_property_node(
            "vjoy-input-type", self.vjoy_input_type, PropertyType.InputType
        ))
        if self.vjoy_input_type == InputType.JoystickAxis:
            node.append(util.create_property_node(
                "axis-mode", self.axis_mode, PropertyType.AxisMode
            ))
            node.append(util.create_property_node(
                "axis-scaling", self.axis_scaling, PropertyType.Float
            ))
        if self.vjoy_input_type == InputType.JoystickButton:
            node.append(util.create_property_node(
                "button-inverted", self.button_inverted, PropertyType.Bool
            ))
        return node

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return []

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise error.GremlinError(f"{self.name}: has no containers")

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        self._vjoy_input_type = new_behavior


create = MapToVjoyData
