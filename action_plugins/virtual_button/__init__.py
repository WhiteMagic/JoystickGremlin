# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from abc import (
    ABCMeta,
    abstractmethod,
)
from typing import (
    TYPE_CHECKING,
    cast,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore

import dill
from gremlin import (
    fsm,
    util,
)
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
    next_virtual_identifier,
)
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    AxisButtonDirection,
    Event,
    HatDirection,
    InputType,
    ModeType,
    PropertyType,
)
from gremlin.ui.action_model import (
    ActionModel,
    SequenceIndex,
)
from gremlin.ui.profile import HatDirectionModel
from gremlin.util import clamp

if TYPE_CHECKING:
    from gremlin.ui.profile import ActionSequenceModel


class VirtualButton(metaclass=ABCMeta):
    """Implements a button like interface."""

    def __init__(self) -> None:
        """Creates a new instance."""
        self._fsm = self._initialize_fsm()

    def _initialize_fsm(self) -> fsm.FiniteStateMachine:
        """Initializes the state of the button FSM."""
        states = ["up", "down"]
        actions = ["press", "release"]

        def noop() -> bool:
            return False

        def press() -> bool:
            return True

        def release() -> bool:
            return True

        transitions = {
            ("up", "press"): fsm.Transition([press], "down"),
            ("up", "release"): fsm.Transition([noop], "up"),
            ("down", "release"): fsm.Transition([release], "up"),
            ("down", "press"): fsm.Transition([noop], "down"),
        }
        return fsm.FiniteStateMachine("up", states, actions, transitions)

    @property
    def is_pressed(self) -> bool:
        """Returns whether the virtual button is currently pressed."""
        return self._fsm.current_state == "down"

    def clear_last_value(self) -> None:
        """Forgets the last input value seen by the button."""

    @abstractmethod
    def __call__(self, event: Event, value: Value) -> list[bool]:
        """Process the input event and updates the value as needed.

        Args:
            event: The input event to process
            value: the value of the event as modified by preceding actions

        Returns:
            List of states to process
        """


class VirtualAxisButton(VirtualButton):
    def __init__(
        self, lower_limit: float, upper_limit: float, direction: AxisButtonDirection
    ) -> None:
        super().__init__()
        self._lower_limit = lower_limit
        self._upper_limit = upper_limit
        self._direction = direction
        self._last_value = None

    def clear_last_value(self) -> None:
        """Forgets the last axis value, the next one carries no direction."""
        self._last_value = None

    def __call__(self, event: Event, value: Value) -> list[bool]:
        position = cast(float, value.current) if value.current is not None else 0.0
        forced_activation = False
        direction = AxisButtonDirection.Anywhere

        if self._last_value is not None:
            # Check if we moved over the activation region between two consecutive
            # measurements
            if (
                self._last_value < self._lower_limit
                and position > self._upper_limit
                or self._last_value > self._upper_limit
                and position < self._lower_limit
            ):
                forced_activation = True

            # Determine direction in which the axis is moving
            if self._last_value < position:
                direction = AxisButtonDirection.Below
            elif self._last_value > position:
                direction = AxisButtonDirection.Above

        self._last_value = position

        inside_range = self._lower_limit <= position <= self._upper_limit
        valid_direction = (
            direction == self._direction
            or self._direction == AxisButtonDirection.Anywhere
        )
        # Execute FSM transitions based on the activation directions.
        if forced_activation and valid_direction:
            actions = ["press", "release"]
        elif inside_range and (self.is_pressed or valid_direction):
            actions = ["press"]
        else:
            actions = ["release"]
        return [action == "press" for action in actions if self._fsm.perform(action)[0]]


class VirtualHatButton(VirtualButton):
    """Treats directional hat events as a button."""

    def __init__(self, directions: list[HatDirection]) -> None:
        super().__init__()
        self._directions = directions

    def __call__(self, event: Event, value: Value) -> list[bool]:
        is_pressed = event.value in self._directions
        action = "press" if is_pressed else "release"
        has_changed = self._fsm.perform(action)[0]
        return [is_pressed] if has_changed else []


class VirtualButtonFunctor(AbstractFunctor):
    """Turns an axis range or a set of hat directions into a button."""

    def __init__(self, action: VirtualButtonData) -> None:
        super().__init__(action)

        self._axis_button = VirtualAxisButton(
            action.lower_limit, action.upper_limit, action.direction
        )
        self._hat_button = VirtualHatButton(action.hat_directions)
        self._identifier = next_virtual_identifier()

    @override
    def __call__(
        self,
        event: Event,
        value: Value,
        properties: list[ActionProperty] = [],
    ) -> bool:
        button = self._button_for(event)
        answers = [
            self._process_event(
                self.functors["children"],
                self._button_event(event, is_pressed),
                Value(is_pressed, value.mode_type),
                properties,
            )
            for is_pressed in button(event, value)
        ]
        children_waiting = answers[-1] if answers else self.waiting_for_event()

        wants_next_event = button.is_pressed or children_waiting
        # No further events arrive until the button's mode is active again.
        if value.mode_type == ModeType.Foreign and not wants_next_event:
            button.clear_last_value()
        return wants_next_event

    @override
    def reset(self) -> None:
        """Forgets the last input value unless events keep arriving outside its
        mode."""
        if not (self._axis_button.is_pressed or self.waiting_for_event()):
            self._axis_button.clear_last_value()

    def _button_for(self, event: Event) -> VirtualButton:
        if event.event_type == InputType.JoystickHat:
            return self._hat_button
        return self._axis_button

    def _button_event(self, event: Event, is_pressed: bool) -> Event:
        """Returns the button event the children process.

        Args:
            event: the axis or hat event that changed the button's state
            is_pressed: the button's new state

        Returns:
            Button event carrying the mode of the input event
        """
        return Event(
            event_type=InputType.VirtualButton,
            identifier=self._identifier,
            device_guid=dill.UUID_Virtual,
            mode=event.mode,
            is_pressed=is_pressed,
            raw_value=is_pressed,
        )


class VirtualButtonModel(ActionModel):
    changed = QtCore.Signal()

    def __init__(
        self,
        data: AbstractActionData,
        sequence_model: ActionSequenceModel,
        action_index: SequenceIndex,
        parent_index: SequenceIndex,
        parent: QtCore.QObject,
    ) -> None:
        super().__init__(data, sequence_model, action_index, parent_index, parent)

        self._hat_directions = HatDirectionModel(self._data.hat_directions, self)

    def _qml_path_impl(self) -> str:
        return (
            "file:///"
            + QtCore.QFile(
                "core_plugins:virtual_button/VirtualButtonAction.qml"
            ).fileName()
        )

    @QtCore.Property(type=str, constant=True)
    def parentBehavior(self) -> str:
        return self._sequence_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @QtCore.Property(type=HatDirectionModel, constant=True)
    def hatDirections(self) -> HatDirectionModel:
        return self._hat_directions

    def _get_lower_limit(self) -> float:
        return self._data.lower_limit

    def _set_lower_limit(self, value: float) -> None:
        if value != self._data.lower_limit:
            self._data.lower_limit = clamp(value, -1.0, 1.0)
            self.changed.emit()

    def _get_upper_limit(self) -> float:
        return self._data.upper_limit

    def _set_upper_limit(self, value: float) -> None:
        if value != self._data.upper_limit:
            self._data.upper_limit = clamp(value, -1.0, 1.0)
            self.changed.emit()

    def _get_direction(self) -> str:
        return AxisButtonDirection.to_string(self._data.direction)

    def _set_direction(self, value: str) -> None:
        direction = AxisButtonDirection.to_enum(value.lower())
        if direction != self._data.direction:
            self._data.direction = direction
            self.changed.emit()

    lowerLimit = QtCore.Property(
        float, fget=_get_lower_limit, fset=_set_lower_limit, notify=changed
    )
    upperLimit = QtCore.Property(
        float, fget=_get_upper_limit, fset=_set_upper_limit, notify=changed
    )
    direction = QtCore.Property(
        str, fget=_get_direction, fset=_set_direction, notify=changed
    )


class VirtualButtonData(AbstractActionData):
    """Turns an axis range or a set of hat directions into a button."""

    version = 1
    name = "Virtual Button"
    tag = "virtual-button"
    icon = ""

    functor = VirtualButtonFunctor
    model = VirtualButtonModel

    properties = (ActionProperty.ActivateDisabled,)
    input_types = (InputType.JoystickAxis, InputType.JoystickHat)
    child_behavior_type = InputType.JoystickButton

    def __init__(self, behavior_type: InputType = InputType.JoystickAxis) -> None:
        super().__init__(behavior_type)

        self.lower_limit = -0.1
        self.upper_limit = 0.1
        self.direction = AxisButtonDirection.Anywhere
        self.hat_directions: list[HatDirection] = []
        self.children: list[AbstractActionData] = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.lower_limit = util.read_property(
            node, "lower-limit", PropertyType.Float, self.lower_limit
        )
        self.upper_limit = util.read_property(
            node, "upper-limit", PropertyType.Float, self.upper_limit
        )
        self.direction = AxisButtonDirection.to_enum(
            util.read_property(
                node,
                "axis-button-direction",
                PropertyType.String,
                AxisButtonDirection.to_string(self.direction),
            )
        )
        self.hat_directions = util.read_properties(
            node, "hat-direction", PropertyType.HatDirection
        )
        self.children = [
            library.get_action(aid)
            for aid in util.read_action_ids(node.find("actions"))
        ]

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(VirtualButtonData.tag, self._id)
        node.append(
            util.create_action_ids("actions", [child.id for child in self.children])
        )
        util.append_property_nodes(
            node,
            [
                ["lower-limit", self.lower_limit, PropertyType.Float],
                ["upper-limit", self.upper_limit, PropertyType.Float],
                [
                    "axis-button-direction",
                    AxisButtonDirection.to_string(self.direction),
                    PropertyType.String,
                ],
            ]
            + [
                ["hat-direction", direction, PropertyType.HatDirection]
                for direction in self.hat_directions
            ],
        )
        return node

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> list[str]:
        return ["children"]

    @override
    def _get_container(self, selector: str) -> list[AbstractActionData]:
        if selector == "children":
            return self.children
        raise GremlinError(f"{self.name}: has no container with name {selector}")


create = VirtualButtonData
