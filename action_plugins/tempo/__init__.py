# -*- coding: utf-8; -*-

# Copyright (C) 2021 Lionel Ott
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

import copy
import logging
import threading
import time
from typing import Any, List, Optional, TYPE_CHECKING, override
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, fsm, util
from gremlin.error import GremlinError, ProfileError
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.config import Configuration
from gremlin.profile import Library
from gremlin.tree import TreeNode
from gremlin.types import ActionProperty, InputType, PropertyType, DataCreationMode

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class TempoFunctor(AbstractFunctor):

    def __init__(self, action: TempoData):
        super().__init__(action)

        # self.start_time = 0
        self.timer = None
        self.value_press = None
        self.event_press = None
        self.fsm = self._create_fsm()

    @override
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty] = []
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

        self.fsm.perform(
            "press" if value.current else "release",
            event,
            value,
            properties
        )

    def _create_fsm(self) -> fsm.FiniteStateMachine:
        T = fsm.Transition
        short_pulse = lambda e, v, p: self._pulse_event(
            self.functors["short"],
            self.event_press,
            self.value_press,
            p
        )
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
                ("short", "release"): T([short_pulse], "wait"),
                ("short", "timeout"): T([long_press], "long"),
                ("long", "release"): T([long_release], "wait")
            }
        elif self.data.activate_on == "press":
            transitions = {
                ("wait", "press"): T(
                    [self._start_timer, short_press], "short"
                ),
                ("wait", "timeout"): T([noop], "wait"),
                ("short", "release"): T([short_release], "wait"),
                ("short", "timeout"): T([long_press], "long"),
                ("long", "release"): T([long_release, short_release], "wait")
            }

        return fsm.FiniteStateMachine("wait", states, actions, transitions)

    def _start_timer(self, *args) -> None:
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.data.threshold, self._timeout)
        self.timer.start()

    def _timeout(self) -> None:
        self.fsm.perform("timeout", self.event_press, self.value_press, [])


class TempoModel(ActionModel):

    actionsChanged = Signal()
    activateOnChanged = Signal()
    thresholdChanged = Signal()

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

    @Property(float, fset=_set_threshold, notify=thresholdChanged)
    def threshold(self) -> float:
        return self._data.threshold

    def _set_activate_on(self, value: str) -> None:
        if value not in ["press", "release"]:
            raise GremlinError(f"Received invalid activateOn value {value}")

        if self._data.activate_on != value:
            self._data.activate_on = value
            self.activateOnChanged.emit()

    @Property(str, fset=_set_activate_on, notify=activateOnChanged)
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
    def is_valid(self) -> bool:
        return True

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