# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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

import enum
import threading
import time
from typing import List, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import error, event_handler, input_devices, joystick_handling, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value, DataCreationMode
from gremlin.config import Configuration
from gremlin.control_action import ModeManager, Mode
from gremlin.profile import Library
from gremlin.types import AxisMode, InputType, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class ChangeType(enum.Enum):

    Switch = 1
    Cycle = 2
    Previous = 3
    Unwind = 4
    Temporary = 5


class ChangeModeFunctor(AbstractFunctor):

    """Executes a mode change action callback."""

    def __init__(self, action: ChangeModeData):
        super().__init__(action)

    def __call__(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
        mode = Configuration().value(
            "action",
            ChangeModeData.tag,
            "identifier-mode",
        )
        # identifier = self.data.


class ChangeModeModel(ActionModel):

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
            "core_plugins:change_mode/ChangeModeAction.qml"
        ).fileName()


class ChangeModeData(AbstractActionData):

    """Action permitting changing of modes."""

    version = 1
    name = "Change Mode"
    tag = "change-mode"
    icon = "\uF544"

    functor = ChangeModeFunctor
    model = ChangeModeModel
    default_creation = DataCreationMode.Create

    input_types = [
        InputType.JoystickButton,
        InputType.Keyboard
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ):
        super().__init__(behavior_type)

        self.change_type = ChangeType.Switch
        self.target_mode = []

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        pass

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(ChangeModeData.tag, self._id)

        return node

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return []

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise error.GremlinError(f"{self.name}: has no containers")

    def _handle_behavior_change(
            self,
            old_behavior: InputType,
            new_behavior: InputType
    ) -> None:
        self._vjoy_input_type = new_behavior


create = ChangeModeData


Configuration().register(
    "action",
    ChangeModeData.tag,
    "identifier-mode",
    PropertyType.String,
    "name",
    "Defines how mode cycles are defined.",
    {},
    True
)
