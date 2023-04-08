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

from typing import Any, List, Optional
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import event_handler, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.error import GremlinError
from gremlin.profile import InputItemBinding, Library
from gremlin.types import InputType, PropertyType

from gremlin.ui.action_model import ActionModel


class DescriptionFunctor(AbstractFunctor):

    """Implements the function executed of the Description action at runtime."""

    def __init__(self, action: DescriptionData):
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


class DescriptionModel(ActionModel):

    # Signal emitted when the description variable's content changes
    descriptionChanged = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding: InputItemBinding,
            parent: QtCore.QObject
    ):
        super().__init__(data, binding, parent)
    
    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:description/DescriptionAction.qml"
        ).fileName()
    
    def _get_description(self) -> str:
        return self._data.description

    def _set_description(self, value: str) -> None:
        if str(value) == self._data.description:
            return
        self._data.description = str(value)
        self.descriptionChanged.emit()

    description = Property(
        str,
        fget=_get_description,
        fset=_set_description,
        notify=descriptionChanged
    )


class DescriptionData(AbstractActionData):

    """Model of a description action."""

    version = 1
    name = "Description"
    tag = "description"

    functor = DescriptionFunctor
    model = DescriptionModel

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

        # Model variables
        self.description = ""

    def from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.description = util.read_property(
            node, "description", PropertyType.String
        )

    def to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(DescriptionData.tag, self._id)
        node.append(util.create_property_node(
            "description", self.description, PropertyType.String
        ))
        return node

    def is_valid(self) -> True:
        return True

    def _valid_selectors(self) -> List[str]:
        raise GremlinError(f"{self.name}: has no containers")

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = DescriptionData
