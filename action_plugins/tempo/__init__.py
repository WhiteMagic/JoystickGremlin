# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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
from typing import Any, List, Optional, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, util
from gremlin.error import GremlinError, ProfileError
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.config import Configuration
from gremlin.profile import Library
from gremlin.tree import TreeNode
from gremlin.types import InputType, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class TempoFunctor(AbstractFunctor):

    def __init__(self, action: TempoData):
        super().__init__(action)

        self.start_time = 0
        self.timer = None
        self.value_press = None
        self.event_press = None

        self.short_actions = \
            [a.node.value.functor(a.node.value) for a in action.shortActions]
        self.long_actions = \
            [a.node.value.functor(a.node.value) for a in action.longActions]

    def process_event(self, event: event_handler.Event, value: Value) -> None:
        # TODO: Currently this does not handle hat or axis events, however
        #       virtual buttons created on those inputs is supported
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

        # Execute tempo logic
        if value.current:
            self.start_time = time.time()
            self.timer = threading.Timer(self.data.threshold, self._long_press)
            self.timer.start()

            if self.data.activateOn == "press":
                self._process_event(
                    self.short_actions,
                    self.event_press,
                    self.value_press
                )
        else:
            # Short press
            if (self.start_time + self.data.threshold) > time.time():
                self.timer.cancel()

                if self.data.activateOn == "release":
                    threading.Thread(target=lambda: self._short_press(
                        self.event_press,
                        self.value_press,
                        event,
                        value
                    )).start()
                else:
                    self._process_event(self.short_actions, event, value)
            # Long press
            else:
                self._process_event(self.long_actions, event, value)
                if self.data.activateOn == "press":
                    self._process_event(self.short_actions, event, value)

            self.timer = None

    def _short_press(
        self,
        event_p: event_handler.Event,
        value_p: Value,
        event_r: event_handler.Event,
        value_r: Value
    ):
        """Callback executed for a short press action.

        :param event_p event to press the action
        :param value_p value to press the action
        :param event_r event to release the action
        :param value_r value to release the action
        """
        self._process_event(self.short_actions, event_p, value_p)
        time.sleep(0.05)
        self._process_event(self.short_actions, event_r, value_r)

    def _long_press(self):
        """Callback executed, when the delay expires."""
        self._process_event(
            self.long_actions,
            self.event_press,
            self.value_press
        )

    def _process_event(
        self,
        actions: List[AbstractFunctor],
        event: event_handler.Event,
        value: Value
    ):
        """Processes the provided event data with every provided action.

        Args:
            actions: List of actions to process the event with
            event: event to process
            value: value of the event
        """
        for action in actions:
            action.process_event(event, value)


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

    def _add_action_impl(self, action: AbstractActionData, options: Any) -> None:
        """Adds a new action to one of the two condition branches.

        Args:
            action: the action to add
            options: which of the two activation types to add the action two, valid
                options are [short, long]
        """
        predicate = lambda x: True if x.value and x.value.id == self.id else False
        nodes = self._action_tree.root.nodes_matching(predicate)
        if len(nodes) != 1:
            raise GremlinError(f"Node with ID {self.id} has invalid state")
        nodes[0].add_child(TreeNode(action))
        if options == "short":
            self._short_action_ids.append(action.id)
        elif options == "long":
            self._long_action_ids.append(action.id)
        else:
            raise GremlinError(f"Invalid branch specification: {options}")

        self.actionsChanged.emit()

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

    functor = TempoFunctor
    model = TempoModel

    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    def __init__(self, behavior_type: InputType=InputType.JoystickButton):
        super().__init__(behavior_type)

        self.short_actions = []
        self.long_actions = []
        self.threshold = Configuration().value("action", "tempo", "duration")
        self.activate_on = "release"

    def from_xml(self, node: ElementTree.Element, library: Library) -> None:
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

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
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

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return ["long", "short"]

    def _get_container(
            self,
            selector: Optional[str] = None
    ) -> List[AbstractActionData]:
        if selector == "short":
            return self.short_actions
        elif selector == "long":
            return self.long_actions

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
    {},
    True
)