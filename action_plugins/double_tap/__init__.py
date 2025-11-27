# -*- coding: utf-8; -*-

# Copyright (C) 2025 Lionel Ott
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
from typing import List, Optional, TYPE_CHECKING, override
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import event_handler, fsm, util
from gremlin.error import GremlinError, ProfileError
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.config import Configuration
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class DoubleTapFunctor(AbstractFunctor):

    def __init__(self, action: DoubleTapData) -> None:
        super().__init__(action)

        self.timer = None
        self.value_press = None
        self.event_press = None
        self.fsm = self._create_fsm()

    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        if not isinstance(value.current, bool):
            logging.getLogger("system").warning(
                f"Invalid data type received in DoubleTap action: {event.value}"
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
        # Define lambda functions for the needed actions
        T = fsm.Transition
        noop = lambda *args: None
        single_pulse = lambda e, v, p: self._pulse_event(
            self.functors["single"],
            self.event_press,
            self.value_press,
            p
        )
        single_press = lambda e, v, p: self._process_event(
            self.functors["single"],
            self.event_press,
            self.value_press,
            p
        )
        single_release = lambda e, v, p: self._process_event(
            self.functors["single"], e, v, p
        )
        double_press = lambda e, v, p: self._process_event(
            self.functors["double"],
            self.event_press,
            self.value_press,
            p
        )
        double_release = lambda e, v, p: self._process_event(
            self.functors["double"], e, v, p
        )

        states = ["neutral", "p1", "p1+t", "p2+t", "t"]
        actions = ["press", "release", "timeout"]
        if self.data.activate_on == "exclusive":
            transitions = {
                ("neutral", "press"): T([self._start_timer], "p1+t"),
                ("neutral", "release"): T([noop], "neutral"),
                ("neutral", "timeout"): T([noop], "neutral"),
                ("p1+t", "release"): T([noop], "t"),
                ("p1+t", "timeout"): T([single_press], "p1"),
                ("p1", "release"): T([single_release], "neutral"),
                ("t", "press"): T([double_press], "p2+t"),
                ("t", "timeout"): T([single_pulse], "neutral"),
                ("p2+t", "release"): T([double_release], "neutral"),
                ("p2+t", "timeout"): T([noop], "p2+t")
            }
        elif self.data.activate_on == "combined":
            transitions = {
                ("neutral", "press"): T(
                    [single_press, self._start_timer], "p1+t"
                ),
                ("neutral", "timeout"): T([noop], "neutral"),
                ("p1+t", "release"): T([single_release], "t"),
                ("p1+t", "timeout"): T([noop], "p1"),
                ("p1", "release"): T([single_release], "neutral"),
                ("t", "press"): T(
                    [single_press, double_press], "p2+t"
                ),
                ("t", "timeout"): T([noop], "neutral"),
                ("p2+t", "release"): T(
                    [single_release, double_release], "neutral"
                ),
                ("p2+t", "timeout"): T([noop], "p2+t")
            }
        return fsm.FiniteStateMachine("neutral", states, actions, transitions)

    def _timeout(self) -> None:
        self.fsm.perform("timeout", self.event_press, self.value_press, [])

    def _start_timer(self, *args) -> None:
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.data.threshold, self._timeout)
        self.timer.start()


class DoubleTapModel(ActionModel):

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
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:double_Tap/DoubleTapAction.qml"
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
        if value not in ["exclusive", "combined"]:
            raise GremlinError(f"Received invalid activateOn value {value}")

        if self._data.activate_on != value:
            self._data.activate_on = value
            self.activateOnChanged.emit()

    @Property(str, fset=_set_activate_on, notify=activateOnChanged)
    def activateOn(self) -> str:
        return self._data.activate_on


class DoubleTapData(AbstractActionData):

    """A container with two actions which are triggered based on whether the
    input is pressed once or twice in quick succession.

    A short press will run the fist action while a double press will run the
    second action.
    """

    version = 1
    name = "Double Tap"
    tag = "double-tap"
    icon = "\uF26F"

    functor = DoubleTapFunctor
    model = DoubleTapModel

    properties = (
        ActionProperty.ActivateDisabled,
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

        self.single_actions = []
        self.double_actions = []
        self.threshold = Configuration().value("action", "double-tap", "duration")
        self.activate_on = "exclusive"

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        short_ids = util.read_action_ids(node.find("single-actions"))
        self.single_actions = [library.get_action(aid) for aid in short_ids]
        long_ids = util.read_action_ids(node.find("double-actions"))
        self.double_actions = [library.get_action(aid) for aid in long_ids]
        self.threshold = util.read_property(
            node, "threshold", PropertyType.Float
        )
        self.activate_on = util.read_property(
            node, "activate-on", PropertyType.String
        )
        if self.activate_on not in ["exclusive", "combined"]:
            raise ProfileError(
                f"Invalid activat-on value present: {self.activate_on}"
            )

    @override
    def _to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
        node = util.create_action_node(DoubleTapData.tag, self._id)
        node.append(util.create_action_ids(
            "single-actions", [action.id for action in self.single_actions]
        ))
        node.append(util.create_action_ids(
            "double-actions", [action.id for action in self.double_actions]
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
        return ["single", "double"]

    @override
    def _get_container(
            self,
            selector: Optional[str] = None
    ) -> List[AbstractActionData]:
        if selector == "single":
            return self.single_actions
        elif selector == "double":
            return self.double_actions

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = DoubleTapData

Configuration().register(
    "action",
    "double-tap",
    "duration",
    PropertyType.Float,
    0.5,
    "The time in seconds that can elapse between subsequent presses in order " \
        "to trigger the double tap action.",
    {
        "min": 0.0,
        "max": 10.0
    },
    True
)