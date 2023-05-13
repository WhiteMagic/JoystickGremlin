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

from gremlin import event_handler, plugin_manager, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    DataInsertionMode, Value
from gremlin.error import GremlinError
from gremlin.config import Configuration
from gremlin.profile import InputItemBinding, Library
from gremlin.types import InputType, PropertyType

from gremlin.ui.action_model import ActionModel


class RootFunctor(AbstractFunctor):

    def __init__(self, action: RootData) -> None:
        super().__init__(action)


class RootModel(ActionModel):

    #actionsChanged = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding: InputItemBinding,
            parent: QtCore.QObject
    ):
        super().__init__(data, binding, parent)

    def _add_action_impl(self, action: AbstractActionData, options: Any) -> None:
        self._data.insert_action(action, options)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:root/RootAction.qml"
        ).fileName()


class RootData(AbstractActionData):

    """Represents the root node of any action tree.

    This class mimicks the behavior of base_classes.AbstractActionModel but
    is not intended to be serialized. This is mainly needed to simplify the
    UI handling by providing a root-level container that holds all other
    actions.
    """

    version = 1
    name = "Root"
    tag = "root"

    functor = RootFunctor
    model = RootModel

    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ):
        super().__init__(behavior_type)

        self.children = []

    def from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        child_ids = util.read_action_ids(node.find("actions"))
        self.children = [library.get_action(aid) for aid in child_ids]

    def to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(RootData.tag, self._id)
        node.append(util.create_action_ids(
            "actions",
            [child.id for child in self.children]
        ))
        return node

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return ["children"]

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        if selector == "children":
            return self.children

    def _handle_behavior_change(
            self,
            old_behavior: InputType,
            new_behavior: InputType
    ) -> None:
        pass

create = RootData