# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import copy
import logging
import threading
import time
from typing import List, TYPE_CHECKING, override
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import event_handler, fsm, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, UserFeedback, Value
from gremlin.config import Configuration
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType

from gremlin.ui.action_model import ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel
    from gremlin.ui.action_model import SequenceIndex


class SmartToggleFunctor(AbstractFunctor):

    def __init__(self, action: SmartToggleData) -> None:
        super().__init__(action)

        self.timer = None
        self.fsm = self._create_fsm()

    def _create_fsm(self) -> fsm.FiniteStateMachine:
        T = fsm.Transition
        noop = lambda *args: None
        process_event = lambda e, v, p: self._process_event(
            self.functors["children"], e, v, p
        )

        states = ["wait", "down", "held", "toggle"]
        actions = ["press", "release", "timeout"]
        transitions = {
            ("wait", "press"): T([process_event, self._start_timer], "down"),
            ("wait", "timeout"): T([noop], "wait"),
            ("down", "release"): T([noop], "toggle"),
            ("down", "timeout"): T([noop], "held"),
            ("held", "release"): T([process_event], "wait"),
            ("toggle", "press"): T([noop], "toggle"),
            ("toggle", "release"): T([process_event], "wait"),
            ("toggle", "timeout"): T([noop], "toggle"),
        }

        return fsm.FiniteStateMachine("wait", states, actions, transitions)

    def _timeout(self) -> None:
        self.fsm.perform("timeout", None, None, None)

    def _start_timer(self, *args) -> None:
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.data.delay, self._timeout)
        self.timer.start()

    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        self.fsm.perform(
            "press" if value.current else "release",
            event,
            value,
            properties + [ActionProperty.DisableAutoRelease]
        )


class SmartToggleModel(ActionModel):

    changed = Signal()

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
            "core_plugins:smart_toggle/SmartToggleAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_delay(self) -> float:
        return self._data.delay

    def _set_delay(self, value: float) -> None:
        if self._data.delay != value:
            self._data.delay = value
            self.changed.emit()

    delay = Property(
        float,
        fget=_get_delay,
        fset=_set_delay,
        notify=changed
    )


class SmartToggleData(AbstractActionData):

    """Represents the root node of any action tree.

    This class mimicks the behavior of base_classes.AbstractActionModel but
    is not intended to be serialized. This is mainly needed to simplify the
    UI handling by providing a root-level container that holds all other
    actions.
    """

    version = 1
    name = "Smart Toggle"
    tag = "smart-toggle"
    icon = "\uF41E"

    functor = SmartToggleFunctor
    model = SmartToggleModel

    properties = (
        ActionProperty.ActivateDisabled,
        ActionProperty.DisableAutoRelease,
    )
    input_types = (
        InputType.JoystickButton,
        InputType.Keyboard
    )

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ) -> None:
        super().__init__(behavior_type)

        self.delay = Configuration().value("action", "smart-toggle", "duration")
        self.children = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        child_ids = util.read_action_ids(node.find("actions"))
        self.children = [library.get_action(aid) for aid in child_ids]
        self.delay = util.read_property(node, "delay", PropertyType.Float)

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(SmartToggleData.tag, self._id)
        node.append(util.create_action_ids(
            "actions",
            [child.id for child in self.children]
        ))
        node.append(util.create_property_node(
            "delay", self.delay, PropertyType.Float
        ))
        return node

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> List[str]:
        return ["children"]

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        if selector == "children":
            return self.children

    @override
    def _handle_behavior_change(
            self,
            old_behavior: InputType,
            new_behavior: InputType
    ) -> None:
        pass


create = SmartToggleData


Configuration().register(
    "action",
    "smart-toggle",
    "duration",
    PropertyType.Float,
    0.5,
    "Default time before triggering the toggle mode.",
    {
        "min": 0.0,
        "max": 10.0
    },
    True
)