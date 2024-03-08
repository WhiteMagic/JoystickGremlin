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

import uuid
from typing import Any, List, Optional, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value, DataCreationMode
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import InputType, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel
from gremlin.ui.profile import LabelValueSelectionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class ReferenceModel(ActionModel):

    modelChanged = Signal()

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
            "core_plugins:reference/ReferenceAction.qml"
        ).fileName()

    def _get_actions(self) -> LabelValueSelectionModel:
        parent_action_ids = []
        for pa in self.library.actions_by_predicate(
                lambda x: x.behavior_type == self.input_type
        ):
            for a in pa.get_actions()[0]:
                if a.id == self._data.id:
                    parent_action_ids.append(pa.id)

        def selector(action) -> bool:
            # Only consider actions that are of a valid type
            if action.tag in ["reference"]:
                return False
            if action.behavior_type != self.input_type:
                return False

            # Reject all actions that would result in a loop
            if action.id in parent_action_ids:
                return False

            return True

        # Grab library and get all actions that fit with the given input modality
        actions = self.library.actions_by_predicate(selector)
        # print(actions)
        return LabelValueSelectionModel(
            [a.action_label for a in actions],
            [str(a.id) for a in actions],
            bootstrap=[a.icon for a in actions],
            parent=self
        )

    @Slot(str)
    def referenceAction(self, value: str) -> None:
        action = self.library.get_action(uuid.UUID(value))
        print(value)
        self._binding_model.append_action(action, self.sequence_index)
        self._binding_model.remove_action(self.sequence_index)

    @Slot(str)
    def duplicateAction(self, value: str) -> None:
        action = self.library.get_action(uuid.UUID(value))
        print(value)

    actions = Property(
        LabelValueSelectionModel,
        fget=_get_actions,
        notify=modelChanged
    )


class ReferenceData(AbstractActionData):

    """Data for the library reference action."""

    version = 1
    name = "Reference"
    tag = "reference"
    icon = "\uF470"

    functor = None
    model = ReferenceModel
    default_creation = DataCreationMode.Create

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

    def _from_xml(
            self,
            node: ElementTree.Element,
            library: Library
    ) -> None:
        pass

    def _to_xml(self) -> ElementTree.Element:
        return ElementTree.Element()

    def is_valid(self) -> bool:
        return False

    def _valid_selectors(self) -> List[str]:
        return []

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = ReferenceData
