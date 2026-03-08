# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import copy
import logging
import threading
import time
from typing import (
    override,
    List,
    Optional,
    TYPE_CHECKING,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import (
    event_handler,
    fsm,
    util,
)
from gremlin.error import (
    GremlinError,
    ProfileError,
)
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.config import Configuration
from gremlin.device_helpers import ButtonReleaseActions, ModeMatch
from gremlin.mode_manager import ModeManager
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    InputType,
    PropertyType,
    DataCreationMode,
)
from gremlin.ui.action_model import (
    ActionModel,
    SequenceIndex,
)

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class TempoFunctor(AbstractFunctor):

    def __init__(self, action: TempoData) -> None:
        super().__init__(action)

        # self.start_time = 0
        self.timer = None
        self.value_press : Value = Value(None)
        self.event_press : event_handler.Event | None = None
        self.fsm = self._create_fsm()

    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: List[ActionProperty] = []
    ) -> None:
        if not isinstance(value.current, bool):
            logging.getLogger("system").warning(
                f"Invalid data type received in Tempo container: "
                f"{type(event.value)}"
            )
            return

        # Copy state when input is pressed
        if value.current:
            self.value_press = copy.deepcopy(value)
            self.event_press = event.clone()

            # Register a button release event to reset the FSM should the
            # input be released in a different mode.
            ButtonReleaseActions().register_callback(
                lambda: self._reset_fsm_if_required(event.mode),
                event,
                ModeMatch.IgnoreMode
            )

        self.fsm.perform(
            "press" if value.current else "release",
            event,
            value,
            properties
        )

    def _reset_fsm_if_required(self, activating_mode: str) -> None:
        if ModeManager().current.name != activating_mode:
            self.fsm.reset()

    def _create_fsm(self) -> fsm.FiniteStateMachine:
        T = fsm.Transition
        short_pulse = lambda e, v, p: self._short_pulse(p)
        short_press = lambda e, v, p: self._process_event(
            self.functors["short"],
            self.event_press,
            self.value_press,
            p
        )
        short_release = lambda e, v, p: self._process_event(
            self.functors["short"], e, v, p
        )
        long_press = lambda e, v, p: self._process_event(
            self.functors["long"],
            self.event_press,
            self.value_press,
            p
        )
        long_release = lambda e, v, p: self._process_event(
            self.functors["long"], e, v, []
        )
        noop = lambda *args: None

        states = ["wait", "short", "long"]
        actions = ["press", "release", "timeout"]
        transitions = {}
        if self.data.activate_on == "release":
            transitions = {
                ("wait", "press"): T([self._start_timer], "short"),
                ("wait", "timeout"): T([short_pulse], "wait"),
                ("wait", "release"): T([noop], "wait"),
                ("short", "release"): T([short_pulse], "wait"),
                ("short", "timeout"): T([long_press], "long"),
                ("long", "release"): T([long_release], "wait"),
            }
        elif self.data.activate_on == "press":
            transitions = {
                ("wait", "press"): T(
                    [self._start_timer, short_press], "short"
                ),
                ("wait", "timeout"): T([noop], "wait"),
                ("wait", "release"): T([noop], "wait"),
                ("short", "release"): T([short_release], "wait"),
                ("short", "timeout"): T([long_press], "long"),
                ("long", "release"): T([long_release, short_release], "wait"),
            }

        return fsm.FiniteStateMachine("wait", states, actions, transitions)

    def _start_timer(self, *args) -> None:
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.data.threshold, self._timeout)
        self.timer.start()

    def _short_pulse(self, properties: List[ActionProperty]) -> None:
        if self.timer:
            self.timer.cancel()
        self._pulse_event(
            self.functors["short"],
            self.event_press,
            self.value_press,
            properties
        )

    def _timeout(self) -> None:
        self.fsm.perform("timeout", self.event_press, self.value_press, [])


class TempoModel(ActionModel):

    actionsChanged = QtCore.Signal()
    activateOnChanged = QtCore.Signal()
    thresholdChanged = QtCore.Signal()

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
            "core_plugins:tempo/TempoAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _set_threshold(self, value: float) -> None:
        if self._data.threshold != value:
            self._data.threshold = value
            self.thresholdChanged.emit()

    @QtCore.Property(float, fset=_set_threshold, notify=thresholdChanged)
    def threshold(self) -> float:
        return self._data.threshold

    def _set_activate_on(self, value: str) -> None:
        if value not in ["press", "release"]:
            raise GremlinError(f"Received invalid activateOn value {value}")

        if self._data.activate_on != value:
            self._data.activate_on = value
            self.activateOnChanged.emit()

    @QtCore.Property(str, fset=_set_activate_on, notify=activateOnChanged)
    def activateOn(self) -> str:
        return self._data.activate_on


class TempoData(AbstractActionData):

    """A container with two actions which are triggered based on the duration
    of the activation.

    A short press will run the fist action while a longer press will run the
    second action.
    """

    version = 1
    name = "Tempo"
    tag = "tempo"
    icon = "\uF580"

    functor = TempoFunctor
    model = TempoModel

    properties = [
        ActionProperty.ActivateDisabled
    ]
    input_types = [
        InputType.JoystickButton,
        InputType.Keyboard
    ]

    def __init__(self, behavior_type: InputType=InputType.JoystickButton):
        super().__init__(behavior_type)

        self.short_actions = []
        self.long_actions = []
        self.threshold = Configuration().value("action", "tempo", "duration")
        self.activate_on = "release"

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        short_ids = util.read_action_ids(node.find("short-actions"))
        self.short_actions = [library.get_action(aid) for aid in short_ids]
        long_ids = util.read_action_ids(node.find("long-actions"))
        self.long_actions = [library.get_action(aid) for aid in long_ids]
        self.threshold = util.read_property(
            node, "threshold", PropertyType.Float
        )
        self.activate_on = util.read_property(
            node, "activate-on", PropertyType.String
        )
        if self.activate_on not in ["press", "release"]:
            raise ProfileError(
                f"Invalid activat-on value present: {self.activate_on}"
            )

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(TempoData.tag, self._id)
        node.append(util.create_action_ids(
            "short-actions", [action.id for action in self.short_actions]
        ))
        node.append(util.create_action_ids(
            "long-actions", [action.id for action in self.long_actions]
        ))
        node.append(util.create_property_node(
            "threshold", self.threshold, PropertyType.Float
        ))
        node.append(util.create_property_node(
            "activate-on", self.activate_on, PropertyType.String
        ))

        return node

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> List[str]:
        return ["long", "short"]

    @override
    def _get_container(
            self,
            selector: Optional[str] = None
    ) -> List[AbstractActionData]:
        if selector == "short":
            return self.short_actions
        elif selector == "long":
            return self.long_actions

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = TempoData

Configuration().register(
    "action",
    "tempo",
    "duration",
    PropertyType.Float,
    0.5,
    "Default time before triggering the long press action.",
    {
        "min": 0.0,
        "max": 10.0
    },
    True
)