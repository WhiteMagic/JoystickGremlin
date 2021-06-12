# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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
from typing import Optional
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import actions, error, event_handler, joystick_handling, \
    profile_library, util
from gremlin.base_classes import AbstractActionModel, AbstractFunctor
from gremlin.types import AxisMode, InputType, PropertyType


# TODO:
# - check auto-release functionality once modes are back


class RemapFunctor(AbstractFunctor):

    """Executes a remap action when called."""

    def __init__(self, action: RemapModel):
        super().__init__(action)

        self.needs_auto_release = False #self._check_for_auto_release(action)
        self.thread_running = False
        self.should_stop_thread = False
        self.thread_last_update = time.time()
        self.thread = None
        self.axis_delta_value = 0.0
        self.axis_value = 0.0

    def process_event(
        self,
        event: event_handler.Event,
        value: actions.Value
    ) -> None:
        if self.data.vjoy_input_type == InputType.JoystickAxis:
            if self.data.axis_mode == AxisMode.Absolute:
                joystick_handling.VJoyProxy()[self.data.vjoy_device_id] \
                    .axis(self.data.vjoy_input_id).value = value.current
            else:
                self.should_stop_thread = abs(event.value) < 0.05
                self.axis_delta_value = \
                    value.current * (self.data.axis_scaling / 1000.0)
                self.thread_last_update = time.time()
                if self.thread_running is False:
                    if isinstance(self.thread, threading.Thread):
                        self.thread.join()
                    self.thread = threading.Thread(
                        target=self.relative_axis_thread
                    )
                    self.thread.start()

        elif self.data.vjoy_input_type == InputType.JoystickButton:
            # FIXME: reimplement
            # if event.event_type in [InputType.JoystickButton, InputType.Keyboard] \
            #         and event.is_pressed \
            #         and self.needs_auto_release:
            #     input_devices.ButtonReleaseActions().register_button_release(
            #         (self.data.vjoy_device_id, self.data.vjoy_input_id),
            #         event
            #     )

            joystick_handling.VJoyProxy()[self.data.vjoy_device_id] \
                .button(self.data.vjoy_input_id).is_pressed = value.current

        elif self.data.vjoy_input_type == InputType.JoystickHat:
            joystick_handling.VJoyProxy()[self.data.vjoy_device_id] \
                .hat(self.data.vjoy_input_id).direction = value.current

    def relative_axis_thread(self) -> None:
        self.thread_running = True
        vjoy_dev = joystick_handling.VJoyProxy()[self.data.vjoy_device_id]
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
                time.sleep(0.01)
            except error.VJoyError:
                self.thread_running = False

    # def _check_for_auto_release(self, action):
    #     activation_condition = None
    #     if action.parent.activation_condition:
    #         activation_condition = action.parent.activation_condition
    #     elif action.activation_condition:
    #         activation_condition = action.activation_condition
    #
    #     # If an input action activation condition is present the auto release
    #     # may have to be disabled
    #     needs_auto_release = True
    #     if activation_condition:
    #         for condition in activation_condition.conditions:
    #             if isinstance(condition, InputActionCondition):
    #                 # Remap like actions typically have an always activation
    #                 # condition associated with them
    #                 if condition.comparison != "always":
    #                     needs_auto_release = False
    #
    #     return needs_auto_release


class RemapModel(AbstractActionModel):

    """Action feeding a vJoy input."""

    version = 1
    name = "Remap"
    tag = "remap"

    functor = RemapFunctor
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    # Signals emitted when properties change
    vjoyDeviceIdChanged = Signal()
    vjoyInputIdChanged = Signal()
    inputTypeChanged = Signal()
    axisModeChanged = Signal()
    axisScalingChanged = Signal()

    def __init__(
            self,
            action_tree: profile_library.ActionTree,
            behavior_type: InputType=InputType.JoystickButton,
            parent: Optional[QtCore.QObject]=None
    ):
        super().__init__(action_tree, behavior_type, parent)

        # Determine a valid vjoy input
        device = joystick_handling.vjoy_devices()[0]
        vjoy_id = device.vjoy_id
        input_id = 1
        if behavior_type == InputType.JoystickAxis:
            input_id = device.axis_map[0].axis_index

        # Model variables
        self.vjoy_device_id = vjoy_id
        self.vjoy_input_id = input_id
        self.vjoy_input_type = behavior_type
        self.axis_mode = AxisMode.Absolute
        self.axis_scaling = 1.0

    def _get_vjoy_device_id(self) -> int:
        return self.vjoy_device_id

    def _set_vjoy_device_id(self, vjoy_device_id: int) -> None:
        if vjoy_device_id == self.vjoy_device_id:
            return
        self.vjoy_device_id = vjoy_device_id
        self.vjoyDeviceIdChanged.emit()

    def _get_vjoy_input_id(self) -> int:
        return self.vjoy_input_id

    def _set_vjoy_input_id(self, vjoy_input_id: int) -> None:
        if vjoy_input_id == self.vjoy_input_id:
            return
        self.vjoy_input_id = vjoy_input_id
        self.vjoyInputIdChanged.emit()

    def _get_vjoy_input_type(self) -> str:
        return InputType.to_string(self.vjoy_input_type)

    def _set_vjoy_input_type(self, input_type: str) -> None:
        input_type_tmp = InputType.to_enum(input_type)
        if input_type_tmp == self.vjoy_input_type:
            return
        self.vjoy_input_type = input_type_tmp
        self.inputTypeChanged.emit()

    def _get_axis_mode(self) -> str:
        return AxisMode.to_string(self.axis_mode)

    def _set_axis_mode(self, axis_mode: str) -> None:
        axis_mode_tmp = AxisMode.to_enum(axis_mode)
        if axis_mode_tmp == self.axis_mode:
            return
        self.axis_mode = axis_mode_tmp
        self.axisModeChanged.emit()

    def _get_axis_scaling(self) -> float:
        return self.axis_scaling

    def _set_axis_scaling(self, axis_scaling: float) -> None:
        if axis_scaling == self.axis_scaling:
            return
        self.axis_scaling = axis_scaling
        self.axisScalingChanged.emit()

    def from_xml(self, node: ElementTree.Element) -> None:
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

    def to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(RemapModel.tag, self._id)
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
        return node

    def is_valid(self) -> bool:
        return True

    def qml_path(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:remap/RemapAction.qml"
        ).fileName()

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        self._set_vjoy_input_type(InputType.to_string(new_behavior))


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


create = RemapModel
