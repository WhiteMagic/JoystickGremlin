# -*- coding: utf-8; -*-

# Copyright (C) 2024 Lionel Ott
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
from typing import Any, List, Optional, TYPE_CHECKING, override
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import event_handler, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType, DataCreationMode

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel



class PauseResumeType(enum.Enum):

    Pause = 1
    Resume = 2
    Toggle = 3

    @staticmethod
    def lookup(value: str) -> PauseResumeType:
        match value:
            case "Pause":
                return PauseResumeType.Pause
            case "Resume":
                return PauseResumeType.Resume
            case "Toggle":
                return PauseResumeType.Toggle


class PauseResumeFunctor(AbstractFunctor):

    def __init__(self, action: PauseResumeData):
        super().__init__(action)

    @override
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        if self._should_execute(value):
            if self.data.operation == PauseResumeType.Pause:
                event_handler.EventHandler().pause()
            elif self.data.operation == PauseResumeType.Resume:
                event_handler.EventHandler().resume()
            elif self.data.operation == PauseResumeType.Toggle:
                event_handler.EventHandler().toggle_active()


class PauseResumeModel(ActionModel):

    changed = Signal()

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
            "core_plugins:pause_resume/PauseResumeAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_operation(self) -> str:
        return self._data.operation.name

    def _set_operation(self, value: str) -> None:
        operation_type = PauseResumeType.lookup(value)
        if operation_type != self._data.operation:
            self._data.operation = operation_type
            self.changed.emit()

    operation = Property(
        str,
        fget=_get_operation,
        fset=_set_operation,
        notify=changed
    )


class PauseResumeData(AbstractActionData):

    """Model of a pause and resume action."""

    version = 1
    name = "Pause and Resume"
    tag = "pause-resume"
    icon = "\uF4C4"

    functor = PauseResumeFunctor
    model = PauseResumeModel

    properties = [
        ActionProperty.AlwaysExecute,
        ActionProperty.ActivateOnPress
    ]
    input_types = [
        InputType.JoystickButton,
        InputType.Keyboard
    ]

    def __init__(
            self,
            behavior_type: InputType = InputType.JoystickButton
    ):
        super().__init__(behavior_type)

        # Model variables
        self.operation = PauseResumeType.Pause

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.operation = PauseResumeType.lookup(util.read_property(
            node, "operation", PropertyType.String
        ))

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(PauseResumeData.tag, self._id)
        node.append(util.create_property_node(
            "operation", self.operation.name, PropertyType.String
        ))
        return node

    @override
    def is_valid(self) -> bool:
        return True

    @override
    def _valid_selectors(self) -> List[str]:
        return []

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass



create = PauseResumeData