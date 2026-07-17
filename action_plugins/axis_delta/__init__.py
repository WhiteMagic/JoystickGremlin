# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    List,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import (
    event_handler,
    util,
)
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    InputType,
    PropertyType,
)
from gremlin.ui.action_model import (
    ActionModel,
    SequenceIndex,
)

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class AxisDeltaFunctor(AbstractFunctor):
    def __init__(self, action: AxisDeltaData) -> None:
        super().__init__(action)
        self._last_value: float | None = None
        self._accumulated: float = 0.0

    @override
    def __call__(
        self,
        event: event_handler.Event,
        value: Value,
        properties: list[ActionProperty] = [],
    ) -> None:
        if self._last_value is None:
            self._last_value = event.value
            return

        if not event.value:
            return

        delta = event.value - self._last_value
        self._last_value = event.value
        self._accumulated += delta

        press_event = event.clone()
        press_event.is_pressed = True

        if self._accumulated >= self.data.change_threshold:
            self._pulse_event(
                self.functors["positive"], press_event, Value(True), properties
            )
            self._accumulated = 0.0
        elif self._accumulated <= -self.data.change_threshold:
            self._pulse_event(
                self.functors["negative"], press_event, Value(True), properties
            )
            self._accumulated = 0.0


class AxisDeltaModel(ActionModel):
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
            + QtCore.QFile("core_plugins:axis_delta/AxisDeltaAction.qml").fileName()
        )

    def _action_behavior(self) -> str:
        return "button"

    def _get_change_threshold(self) -> float:
        return self._data.change_threshold

    def _set_change_threshold(self, value: float) -> None:
        if self._data.change_threshold != value:
            self._data.change_threshold = value
            self.changed.emit()

    changeThreshold = QtCore.Property(
        float, fget=_get_change_threshold, fset=_set_change_threshold, notify=changed
    )


class AxisDeltaData(AbstractActionData):
    version = 1
    name = "Axis Delta"
    tag = "axis-delta"
    icon = "\uf303"

    functor = AxisDeltaFunctor
    model = AxisDeltaModel

    properties = (ActionProperty.ActivateDisabled,)
    input_types = (InputType.JoystickAxis,)

    def __init__(self, behavior_type: InputType = InputType.JoystickAxis) -> None:
        super().__init__(behavior_type)
        self.change_threshold: float = Configuration().value(
            "action", "axis-delta", "threshold"
        )
        self.actions_positive: List[AbstractActionData] = []
        self.actions_negative: List[AbstractActionData] = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.change_threshold = util.read_property(
            node, "threshold", PropertyType.Float
        )
        self.actions_positive = [
            library.get_action(aid)
            for aid in util.read_action_ids(node.find("positive-actions"))
        ]
        self.actions_negative = [
            library.get_action(aid)
            for aid in util.read_action_ids(node.find("negative-actions"))
        ]

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(self.tag, self._id)
        node.append(
            util.create_property_node(
                "threshold", self.change_threshold, PropertyType.Float
            )
        )
        node.append(
            util.create_action_ids(
                "positive-actions", [a.id for a in self.actions_positive]
            )
        )
        node.append(
            util.create_action_ids(
                "negative-actions", [a.id for a in self.actions_negative]
            )
        )
        return node

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> List[str]:
        return ["positive", "negative"]

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        match selector:
            case "positive":
                return self.actions_positive
            case "negative":
                return self.actions_negative
            case _:
                raise GremlinError(
                    f"{self.name}: has no container with name {selector}"
                )

    @override
    def _handle_behavior_change(
        self, old_behavior: InputType, new_behavior: InputType
    ) -> None:
        pass


create = AxisDeltaData

Configuration().register(
    "action",
    "axis-delta",
    "threshold",
    PropertyType.Float,
    0.1,
    "Default axis delta threshold before triggering.",
    {"min": 0.0001, "max": 2.0},
    True,
)
