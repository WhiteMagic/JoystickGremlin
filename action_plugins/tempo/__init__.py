# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2021 Lionel Ott
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
from typing import List, Optional
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import error, event_handler, plugin_manager, \
    profile_library, util
from gremlin.base_classes import AbstractActionModel, AbstractFunctor, Value
from gremlin.tree import TreeNode
from gremlin.types import InputType, PropertyType
from gremlin.ui.profile import ActionNodeModel


class TempoFunctor(AbstractFunctor):

    def __init__(self, action: TempoModel):
        super().__init__(action)

        self.start_time = 0
        self.timer = None
        self.value_press = None
        self.event_press = None

        self.short_actions = \
            [a.node.value.functor(a.node.value) for a in action.shortActions]
        self.long_actions = \
            [a.node.value.functor(a.node.value) for a in action.longActions]

    def process_event(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
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


class TempoModel(AbstractActionModel):

    """A container with two actions which are triggered based on the duration
    of the activation.

    A short press will run the fist action while a longer press will run the
    second action.
    """

    version = 1
    name = "Tempo"
    tag = "tempo"

    functor = TempoFunctor

    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    actionsChanged = Signal()
    activateOnChanged = Signal()
    thresholdChanged = Signal()

    def __init__(
            self,
            action_tree: profile_library.ActionTree,
            input_type: InputType = InputType.JoystickButton,
            parent: Optional[QtCore.QObject] = None
    ):
        """Creates a new instance.

        :param parent the InputItem this container is linked to
        """
        super().__init__(action_tree, input_type, parent)
        self._short_action_ids = []
        self._long_action_ids = []
        self._threshold = 0.5
        self._activate_on = "release"

    def from_xml(self, node: ElementTree.Element) -> None:
        self._id = util.read_action_id(node)
        self._short_action_ids = util.read_action_ids(node.find("short-actions"))
        self._long_action_ids = util.read_action_ids(node.find("long-actions"))
        self._threshold = util.read_property(
            node, "threshold", PropertyType.Float
        )
        self._activate_on = util.read_property(
            node, "activate-on", PropertyType.String
        )
        if self._activate_on not in ["press", "release"]:
            raise error.ProfileError(f"Invalid activat-on value present: {self._activate_on}")

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
        node = util.create_action_node(TempoModel.tag, self._id)
        node.append(util.create_action_ids(
            "short-actions", self._short_action_ids
        ))
        node.append(util.create_action_ids(
            "long-actions", self._long_action_ids
        ))
        node.append(util.create_property_node(
            "threshold", self._threshold, PropertyType.Float
        ))
        node.append(util.create_property_node(
            "activate-on", self._activate_on, PropertyType.String
        ))

        return node

    def qml_path(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:tempo/TempoAction.qml"
        ).fileName()

    def is_valid(self) -> True:
        return True

    def remove_action(self, action: AbstractActionModel) -> None:
        """Removes the provided action from this action.

        Args:
            action: the action to remove
        """
        self._remove_from_list(self._short_action_ids, action.id)
        self._remove_from_list(self._long_action_ids, action.id)

    def add_action_after(
        self,
        anchor: AbstractActionModel,
        action: AbstractActionModel
    ) -> None:
        """Adds the provided action after the specified anchor.

        Args:
            anchor: action after which to insert the given action
            action: the action to remove
        """
        self._insert_into_list(self._short_action_ids, anchor.id, action.id, True)
        self._insert_into_list(self._long_action_ids, anchor.id, action.id, True)

    def insert_action(self, container: str, action: AbstractActionModel) -> None:
        if container == "short":
            self._short_action_ids.insert(0, action.id)
        elif container == "long":
            self._long_action_ids.insert(0, action.id)
        else:
            raise error.GremlinError(
                f"Invalid container for a Tempo action: '{container}`"
            )

    @Slot(str, str)
    def addAction(self, action_name: str, activation: str) -> None:
        """Adds a new action to one of the two condition branches.

        Args:
            action_name: name of the action to add
            activation: which of the two activation types to add the action two, valid
                options are [short, long]
        """
        action = plugin_manager.ActionPlugins().get_class(action_name)(
            self._action_tree,
            self.behavior_type
        )

        predicate = lambda x: True if x.value and x.value.id == self.id else False
        nodes = self._action_tree.root.nodes_matching(predicate)
        if len(nodes) != 1:
            raise error.GremlinError(f"Node with ID {self.id} has invalid state")
        nodes[0].add_child(TreeNode(action))
        if activation == "short":
            self._short_action_ids.append(action.id)
        elif activation == "long":
            self._long_action_ids.append(action.id)
        else:
            raise error.GremlinError(f"Invalid branch specification: {activation}")

        self.actionsChanged.emit()

    @Property(list, notify=actionsChanged)
    def shortActions(self) -> List[ActionNodeModel]:
        return self._create_node_list(self._short_action_ids)

    @Property(list, notify=actionsChanged)
    def longActions(self) -> List[ActionNodeModel]:
        return self._create_node_list(self._long_action_ids)

    def _set_threshold(self, value: float) -> None:
        if self._threshold != value:
            self._threshold = value
            self.thresholdChanged.emit()

    @Property(float, fset=_set_threshold, notify=thresholdChanged)
    def threshold(self) -> float:
        return self._threshold

    def _set_activate_on(self, value: str) -> None:
        if value not in ["press", "release"]:
            raise error.GremlinError(f"Received invalid activateOn value {value}")

        if self._activate_on != value:
            self._activate_on = value
            self.activateOnChanged.emit()

    @Property(str, fset=_set_activate_on, notify=activateOnChanged)
    def activateOn(self) -> str:
        return self._activate_on


create = TempoModel