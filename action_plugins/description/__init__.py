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

from typing import Optional
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import event_handler, profile_library, util
from gremlin.base_classes import AbstractActionModel, AbstractFunctor, Value
from gremlin.types import InputType, PropertyType


class DescriptionFunctor(AbstractFunctor):

    """Implements the function executed of the Description action at runtime."""

    def __init__(self, action: DescriptionModel):
        super().__init__(action)

    def process_event(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
        """Processes the provided event.

        Args:
            event: the input event to process
            value: the potentially modified input value
        """
        pass


class DescriptionModel(AbstractActionModel):

    """Model of a description action."""

    version = 1
    name = "Description"
    tag = "description"

    functor = DescriptionFunctor

    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    # Signal emitted when the description variable's content changes
    descriptionChanged = Signal()

    def __init__(
            self,
            action_tree: profile_library.ActionTree,
            input_type: InputType=InputType.JoystickButton,
            parent: Optional[QtCore.QObject] = None
    ):
        super().__init__(action_tree, input_type, parent)

        # Model variables
        self._description = ""

    def _get_description(self) -> str:
        return self._description

    def _set_description(self, value: str) -> None:
        if str(value) == self._description:
            return
        self._description = str(value)
        self.descriptionChanged.emit()

    def from_xml(self, node: ElementTree.Element) -> None:
        self._id = util.read_action_id(node)
        self._description = util.read_property(
            node, "description", PropertyType.String
        )

    def to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(DescriptionModel.tag, self._id)
        node.append(util.create_property_node(
            "description", self._description, PropertyType.String
        ))
        return node

    def is_valid(self) -> True:
        return True

    def qml_path(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:description/DescriptionAction.qml"
        ).fileName()

    description = Property(
        str,
        fget=_get_description,
        fset=_set_description,
        notify=descriptionChanged
    )


create = DescriptionModel
