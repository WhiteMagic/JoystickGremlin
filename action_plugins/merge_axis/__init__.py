# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2022 Lionel Ott
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
from gremlin.config import Configuration
from gremlin.tree import TreeNode
from gremlin.types import InputType, PropertyType
from gremlin.ui.profile import ActionNodeModel


class MergeAxisFunctor(AbstractFunctor):

    def __init__(self, action: MergeAxisModel):
        super().__init__(action)

    def process_event(self, event: event_handler.Event, value: Value) -> None:
        return super().process_event(event, value)


class MergeAxisModel(AbstractActionModel):

    version = 1
    name = "Merge Axis"
    tag = "merge-axis"

    functor = MergeAxisFunctor

    input_types = {
        InputType.JoystickAxis
    }

    def __init__(
            self,
            action_tree: profile_library.ActionTree,
            input_type: InputType = InputType.JoystickAxis,
            parent: Optional[QtCore.QObject] = None
    ):
        super().__init__(action_tree, input_type, parent)

    def from_xml(self, node: ElementTree.Element) -> None:
        return super().from_xml(node)

    def to_xml(self) -> ElementTree.Element:
        return super().to_xml()

    def qml_path(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:merge_axis/MergeAxisAction.qml"
        ).fileName()

    def is_valid(self) -> bool:
        return super().is_valid()


create = MergeAxisModel