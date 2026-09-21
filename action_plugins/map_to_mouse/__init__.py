# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import enum
import functools
import math
from typing import (
    TYPE_CHECKING,
    cast,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import (
    event_handler,
    event_helpers,
    mode_manager,
    sendinput,
    util,
)
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.signal import signal
from gremlin.types import (
    ActionProperty,
    HatDirection,
    InputType,
    MouseButton,
    PropertyType,
)
from gremlin.ui.action_model import (
    ActionModel,
    SequenceIndex,
)

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


# Axis values less than this valure are considered at rest, not triggering mouse motion
# contributions.
_AXIS_REST_THRESHOLD = 1e-3


class MapToMouseMode(enum.Enum):
    Button = 1
    Motion = 2

    @staticmethod
    def lookup(value: str) -> MapToMouseMode:
        match value:
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

        self._motion = sendinput.MouseMotionManager()
        self._mode_changes = event_helpers.ModeChangeActions()

    @override
    def __call__(
        self,
        event: event_handler.Event,
        value: Value,
        properties: list[ActionProperty] = [],
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

    def _perform_mouse_button(self, event: event_handler.Event, value: Value) -> None:
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

    def _motion_key(self, event: event_handler.Event) -> sendinput.MotionKey:
        """Returns the key identifying this action's contribution.

        Args:
            event: input event driving the motion

        Returns:
            Key under which to register the motion contribution
        """
        return (self.data.id, event)

    def _register_mode_change_cb(
        self, key: sendinput.MotionKey, event: event_handler.Event
    ) -> None:
        """Adds a mode change callback for the given action.

        Args:
            key: identifier of the contribution to track
            event: input event driving the motion
        """
        self._mode_changes.register(
            key, functools.partial(self._mode_change_cb, key, event)
        )

    def _remove_mode_change_cb(self, key: sendinput.MotionKey) -> None:
        """Removes the specified callback from the mode change handler.

        Args:
            key: identifier of the contribution no longer to track
        """
        self._mode_changes.unregister(key)

    def _mode_change_cb(
        self,
        key: sendinput.MotionKey,
        event: event_handler.Event,
        _old_mode: mode_manager.Mode,
        new_mode: mode_manager.Mode,
    ) -> bool:
        """Stops the action's mouse motino contributino if the new mode no longer
        routes the input here.

        Args:
            key: identifier of the contribution to stop
            event: input event that started the motion
            _old_mode: mode active before the change
            new_mode: mode active after the change

        Returns:
            True if the motion was stopped, False if the binding still applies
        """
        if event_handler.EventHandler().is_same_binding(
            event.device_guid, event, event.mode, new_mode.name
        ):
            return False

        self._motion.clear(key)
        return True

    def _axis_compass_direction(self) -> float:
        """Returns the heading a positive axis value moves the cursor towards.

        Returns:
            Heading in degree, 0 being north and 90 being east
        """
        direction_remap = {
            0.0: 180.0,
            90.0: 90.0,
        }
        return direction_remap.get(
            float(self.data.direction), float(self.data.direction)
        )

    def _perform_axis_motion(self, event: event_handler.Event, value: Value) -> None:
        """Processes axis-controlled motion.

        Args:
            event: input event to process
            value: potentially modified input value
        """
        speed = self.data.min_speed + abs(value.current) * (
            self.data.max_speed - self.data.min_speed
        )
        speed = math.copysign(speed, value.current)
        speed = 0.0 if abs(value.current) < _AXIS_REST_THRESHOLD else speed

        key = self._motion_key(event)
        self._motion.set_velocity(
            key,
            sendinput.Vector2.from_compass_direction(self._axis_compass_direction())
            * speed,
        )
        # A zero speed makes set_velocity drop the contribution.
        if speed == 0.0:
            self._remove_mode_change_cb(key)
        else:
            self._register_mode_change_cb(key, event)

    def _perform_button_motion(self, event: event_handler.Event, value: Value) -> None:
        """Processes button-controlled motion.

        Args:
            event: input event to process
            value: potentially modified input value
        """
        key = self._motion_key(event)
        if event.is_pressed:
            self._motion.set_accelerated_motion(
                key,
                sendinput.Vector2.from_compass_direction(self.data.direction),
                self.data.min_speed,
                self.data.max_speed,
                self.data.time_to_max_speed,
            )
            self._register_mode_change_cb(key, event)
        else:
            self._motion.clear(key)
            self._remove_mode_change_cb(key)

    def _perform_hat_motion(self, event: event_handler.Event, value: Value) -> None:
        """Processes hat-controlled motion.

        Args:
            event: input event to process
            value: potentially modified input value
        """
        key = self._motion_key(event)
        if value.current == HatDirection.Center:
            self._motion.clear(key)
            self._remove_mode_change_cb(key)
        else:
            # Hat directions are cartesian with y pointing up, screen
            # coordinates have y growing downwards.
            hat_x, hat_y = cast(HatDirection, value.current).value
            self._motion.set_accelerated_motion(
                key,
                sendinput.Vector2(hat_x, -hat_y).normalize(),
                self.data.min_speed,
                self.data.max_speed,
                self.data.time_to_max_speed,
            )
            self._register_mode_change_cb(key, event)


class MapToMouseModel(ActionModel):
    # Signal emitted when the description variable's content changes
    changed = QtCore.Signal()

    def __init__(
        self,
        data: AbstractActionData,
        binding_model: InputItemBindingModel,
        action_index: SequenceIndex,
        parent_index: SequenceIndex,
        parent: QtCore.QObject,
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return (
            "file:///"
            + QtCore.QFile("core_plugins:map_to_mouse/MapToMouseAction.qml").fileName()
        )

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_mode(self) -> str:
        return self._data.mode.name

    def _set_mode(self, value: str) -> None:
        mode = MapToMouseMode.lookup(value)
        if mode != self._data.mode:
            self._data.mode = mode
            self.changed.emit()
            signal.inputItemChanged.emit(self._binding_model.parent().enumeration_index)

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
    def updateInputs(self, data: list[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        self._data.button = data[0].identifier
        self.changed.emit()
        signal.inputItemChanged.emit(self._binding_model.parent().enumeration_index)

    mode = QtCore.Property(str, fget=_get_mode, fset=_set_mode, notify=changed)

    direction = QtCore.Property(
        int, fget=_get_direction, fset=_set_direction, notify=changed
    )

    minSpeed = QtCore.Property(
        int, fget=_get_min_speed, fset=_set_min_speed, notify=changed
    )

    maxSpeed = QtCore.Property(
        int, fget=_get_max_speed, fset=_set_max_speed, notify=changed
    )

    timeToMaxSpeed = QtCore.Property(
        float, fget=_get_time_to_max_speed, fset=_set_time_to_max_speed, notify=changed
    )


class MapToMouseData(AbstractActionData):
    """Model of a map to mouse action."""

    version = 1
    name = "Map to Mouse"
    tag = "map-to-mouse"
    icon = "\uf49b"

    functor = MapToMouseFunctor
    model = MapToMouseModel

    properties = (ActionProperty.ActivateOnBoth,)
    input_types = (
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard,
    )

    def __init__(self, behavior_type: InputType = InputType.JoystickButton) -> None:
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

    @property
    @override
    def chip_label(self) -> str:
        if self.mode == MapToMouseMode.Button:
            return f"Mouse {MouseButton.to_abbreviation(self.button)}"
        return "Mouse Motion"

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.mode = MapToMouseMode.lookup(
            util.read_property(node, "mode", PropertyType.String)
        )
        if self.mode == MapToMouseMode.Button:
            self.button = MouseButton.to_enum(
                util.read_property(node, "button", PropertyType.String)
            )
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
            entries.append(
                ["button", MouseButton.to_string(self.button), PropertyType.String]
            )
        else:
            entries.extend(
                [
                    ["direction", self.direction, PropertyType.Int],
                    ["min-speed", self.min_speed, PropertyType.Int],
                    ["max-speed", self.max_speed, PropertyType.Int],
                    ["time-to-max-speed", self.time_to_max_speed, PropertyType.Float],
                ]
            )

        util.append_property_nodes(node, entries)
        return node

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> list[str]:
        return []

    @override
    def _get_container(self, selector: str) -> list[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self, old_behavior: InputType, new_behavior: InputType
    ) -> None:
        if new_behavior in [InputType.JoystickAxis, InputType.JoystickHat]:
            self.mode = MapToMouseMode.Motion


create = MapToMouseData
