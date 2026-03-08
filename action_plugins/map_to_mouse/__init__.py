# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import enum
import math
from typing import (
    override,
    Any,
    List,
    Optional,
    TYPE_CHECKING,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import event_handler, sendinput, util
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    HatDirection,
    InputType,
    MouseButton,
    PropertyType,
)

from gremlin.ui.action_model import (
    SequenceIndex,
    ActionModel
)

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class MapToMouseMode(enum.Enum):

    Button = 1
    Motion = 2

    @staticmethod
    def lookup(value: str) -> MapToMouseMode:
        match(value):
            case "Button":
                return MapToMouseMode.Button
            case "Motion":
                return MapToMouseMode.Motion
            case _:
                raise GremlinError(f"Unknown MapToMouseMode: {value}")


class MapToMouseFunctor(AbstractFunctor):

    """Implements the function implementing MapToMouse behavior at runtime."""

    def __init__(self, action: MapToMouseData) -> None:
        super().__init__(action)

        self.mouse_controller = sendinput.MouseController()

    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        if not self._should_execute(value):
            return

        if self.data.mode == MapToMouseMode.Motion:
            if event.event_type == InputType.JoystickAxis:
                self._perform_axis_motion(event, value)
            elif event.event_type == InputType.JoystickHat:
                self._perform_hat_motion(event, value)
            else:
                self._perform_button_motion(event, value)
        else:
            self._perform_mouse_button(event, value)

    def _perform_mouse_button(
            self,
            event: event_handler.Event,
            value: Value
    ) -> None:
        """Processes mouse button presses.

        Args:
            event: input event to process
            value: potentially modified input value
        """
        if self.data.button in [MouseButton.WheelDown, MouseButton.WheelUp]:
            if value.current:
                sendinput.mouse_wheel(
                    1 if self.data.button == MouseButton.WheelDown else -1
                )
        else:
            if value.current:
                sendinput.mouse_press(self.data.button)
            else:
                sendinput.mouse_release(self.data.button)

    def _perform_axis_motion(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
        """Processes axis-controlled motion.

        Args:
            event: input event to process
            value: potentially modified input value
        """
        delta_motion = self.data.min_speed + abs(value.current) * \
                (self.data.max_speed - self.data.min_speed)
        delta_motion = math.copysign(delta_motion, value.current)
        delta_motion = 0.0 if abs(value.current) < 1e-6 else delta_motion

        dx = delta_motion if self.data.direction == 90 else None
        dy = delta_motion if self.data.direction == 0  else None
        self.mouse_controller.set_absolute_motion(dx, dy)

    def _perform_button_motion(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
        """Processes button-controlled motion.

        Args:
            event: input event to process
            value: potentially modified input value
        """
        if event.is_pressed:
            self.mouse_controller.add_accelerated_motion(
                self.data.direction,
                self.data.min_speed,
                self.data.max_speed,
                self.data.time_to_max_speed,
                event
            )
        else:
            self.mouse_controller.remove_accelerated_motion(event)

    def _perform_hat_motion(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
        """Processes hat-controlled motion.

        Args:
            event: input event to process
            value: potentially modified input value
        """
        direction_lut = {
            HatDirection.North: 0.0,
            HatDirection.NorthEast: 45.0,
            HatDirection.East: 90.0,
            HatDirection.SouthEast: 135.0,
            HatDirection.South: 180.0,
            HatDirection.SouthWest: 225.0,
            HatDirection.West: 270.0,
            HatDirection.NorthWest: 315.0,
        }

        if value.current == HatDirection.Center:
            self.mouse_controller.set_absolute_motion(0, 0)
        else:
            self.mouse_controller.add_accelerated_motion(
                direction_lut[value.current],
                self.data.min_speed,
                self.data.max_speed,
                self.data.time_to_max_speed,
                event
            )


class MapToMouseModel(ActionModel):

    # Signal emitted when the description variable's content changes
    changed = QtCore.Signal()

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
            "core_plugins:map_to_mouse/MapToMouseAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_mode(self) -> str:
        return self._data.mode.name

    def _set_mode(self, value: str) -> None:
        mode = MapToMouseMode.lookup(value)
        if mode != self._data.mode:
            self._data.mode = mode
            self.changed.emit()

    def _get_direction(self) -> int:
        return self._data.direction

    def _set_direction(self, value: int) -> None:
        if value != self._data.direction:
            self._data.direction = value
            self.changed.emit()

    def _get_min_speed(self) -> int:
        return self._data.min_speed

    def _set_min_speed(self, value: int) -> None:
        if value != self._data.min_speed:
            self._data.min_speed = value
            self.changed.emit()

    def _get_max_speed(self) -> int:
        return self._data.max_speed

    def _set_max_speed(self, value: int) -> None:
        if value != self._data.max_speed:
            self._data.max_speed = value
            self.changed.emit()

    def _get_time_to_max_speed(self) -> float:
        return self._data.time_to_max_speed

    def _set_time_to_max_speed(self, value: float) -> None:
        if value != self._data.time_to_max_speed:
            self._data.time_to_max_speed = value
            self.changed.emit()

    @QtCore.Property(str, notify=changed)
    def button(self) -> str:
        return MouseButton.to_string(self._data.button)

    @QtCore.Slot(list)
    def updateInputs(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        self._data.button = data[0].identifier
        self.changed.emit()

    mode = QtCore.Property(
        str,
        fget=_get_mode,
        fset=_set_mode,
        notify=changed
    )

    direction = QtCore.Property(
        int,
        fget=_get_direction,
        fset=_set_direction,
        notify=changed
    )

    minSpeed = QtCore.Property(
        int,
        fget=_get_min_speed,
        fset=_set_min_speed,
        notify=changed
    )

    maxSpeed = QtCore.Property(
        int,
        fget=_get_max_speed,
        fset=_set_max_speed,
        notify=changed
    )

    timeToMaxSpeed = QtCore.Property(
        float,
        fget=_get_time_to_max_speed,
        fset=_set_time_to_max_speed,
        notify=changed
    )


class MapToMouseData(AbstractActionData):

    """Model of a map to mouse action."""

    version = 1
    name = "Map to Mouse"
    tag = "map-to-mouse"
    icon = "\uF49B"

    functor = MapToMouseFunctor
    model = MapToMouseModel

    properties = (
        ActionProperty.ActivateOnBoth,
    )
    input_types = (
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    )

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ) -> None:
        super().__init__(behavior_type)

        # Model variables
        self.mode = MapToMouseMode.Button
        if behavior_type in [InputType.JoystickAxis, InputType.JoystickHat]:
            self.mode = MapToMouseMode.Motion
        self.button = MouseButton.Left
        self.direction = 0
        self.min_speed = 50
        self.max_speed = 250
        self.time_to_max_speed = 1.0

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.mode = MapToMouseMode.lookup(util.read_property(
            node, "mode", PropertyType.String
        ))
        if self.mode == MapToMouseMode.Button:
            self.button = MouseButton.to_enum(util.read_property(
                node, "button", PropertyType.String
            ))
        else:
            self.direction = util.read_property(node, "direction", PropertyType.Int)
            self.min_speed = util.read_property(node, "min-speed", PropertyType.Int)
            self.max_speed = util.read_property(node, "max-speed", PropertyType.Int)
            self.time_to_max_speed = util.read_property(
                node, "time-to-max-speed", PropertyType.Float
            )

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MapToMouseData.tag, self._id)
        entries = [
            ["mode", self.mode.name, PropertyType.String],
        ]
        if self.mode == MapToMouseMode.Button:
            entries.append([
                "button", MouseButton.to_string(self.button), PropertyType.String
            ])
        else:
            entries.extend([
                ["direction", self.direction, PropertyType.Int],
                ["min-speed", self.min_speed, PropertyType.Int],
                ["max-speed", self.max_speed, PropertyType.Int],
                ["time-to-max-speed", self.time_to_max_speed, PropertyType.Float],
            ])

        util.append_property_nodes(node, entries)
        return node

    @override
    def user_feedback(self) -> List[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> List[str]:
        return []

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        if new_behavior in [InputType.JoystickAxis, InputType.JoystickHat]:
            self.mode = MapToMouseMode.Motion


create = MapToMouseData
