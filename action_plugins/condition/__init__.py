# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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


import logging
from typing import List, Optional
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import joystick_handling, profile_library
from gremlin import util
from gremlin.base_classes import AbstractActionModel, AbstractFunctor
from gremlin.types import InputType, PropertyType
from gremlin.ui.profile import ActionNodeModel


class ConditionFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)

    def process_event(self, event, value):
        return True


class ConditionModel(AbstractActionModel):

    version = 1
    name = "Condition"
    tag = "condition"

    functor = ConditionFunctor
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    def __init__(
            self,
            action_tree: profile_library.ActionTree,
            input_type: InputType = InputType.JoystickButton,
            parent: Optional[QtCore.QObject] = None
    ):
        super().__init__(action_tree, input_type, parent)

        self.true_action_ids = []
        self.false_action_ids = []

    @Property("QVariantList", notify=AbstractActionModel.modelChanged)
    def trueActionNodes(self) -> List[ActionNodeModel]:
        nodes = []
        for node in self._action_tree.root.nodes_matching(
                lambda x: x.value.id in self.true_action_ids
        ):
            nodes.append(ActionNodeModel(node, self._action_tree, parent=self))
        return nodes

    @Property("QVariantList", notify=AbstractActionModel.modelChanged)
    def falseActionNodes(self) -> List[ActionNodeModel]:
        nodes = []
        for node in self._action_tree.root.nodes_matching(
                lambda x: x.value.id in self.false_action_ids
        ):
            nodes.append(ActionNodeModel(node, self._action_tree, parent=self))
        return nodes

    def from_xml(self, node: ElementTree.Element ) -> None:
        self._id = util.read_action_id(node)
        # Parse IF action ids
        self.true_action_ids = util.read_action_ids(node.find("if-actions"))
        # Parse ELSE action ids
        self.false_action_ids = util.read_action_ids(node.find("else-actions"))

    def to_xml(self) -> ElementTree:
        node = util.create_action_node(ConditionModel.tag, self._id)
        return node

    def is_valid(self) -> bool:
        return True

    def qml_path(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:condition/ConditionAction.qml"
        ).fileName()


create = ConditionModel