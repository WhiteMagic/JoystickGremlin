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
from typing import Any, List, Optional, TYPE_CHECKING, override
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value
from gremlin.error import GremlinError
from gremlin.macro import AbstractAction
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType, DataCreationMode

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

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_actions(self) -> LabelValueSelectionModel:
        # Discover all actions that are an ancestor of the present action
        ancestor_action_ids = []
        queue = [self._data.id]
        while len(queue) > 0:
            aid = queue.pop(0)
            action_ids = [a.id for a in self.library.actions_by_predicate(
                lambda x: aid in [v.id for v in x.get_actions()[0]]
            )]
            ancestor_action_ids.extend(action_ids)
            queue.extend(action_ids)

        # Predicate to select only valid actions to show in the reference
        # list. Excludes all actions that:
        # - result in circular inclusions
        # - are of an incompatible input type
        # - are a reference action
        def selector(action) -> bool:
            # Only consider actions that are of a valid type
            if action.tag in ["reference"]:
                return False
            if action.behavior_type != self.input_type:
                return False

            # Reject all actions that would result in a loop
            if action.id in ancestor_action_ids:
                return False
            return True

        # Grab library and get all actions that fit with the given input modality
        actions = self.library.actions_by_predicate(selector)
        return LabelValueSelectionModel(
            [a.action_label for a in actions],
            [str(a.id) for a in actions],
            bootstrap=[a.icon for a in actions],
            parent=self
        )

    @Slot(str)
    def referenceAction(self, value: str) -> None:
        self._replace_reference(self.library.get_action(uuid.UUID(value)))

    @Slot(str)
    def duplicateAction(self, value: str) -> None:
        # Retrieve action and duplicate it before adding it to the tree
        action = self.library.get_action(uuid.UUID(value)).clone()
        self.library.add_action(action)
        self._replace_reference(action)

    def _replace_reference(self, action: AbstractActionData) -> None:
        # Replace reference action with the provided action
        self._binding_model.append_action(action, self.sequence_index)
        self._binding_model.remove_action(self.sequence_index)

        # Delete the reference action itself
        self.library.delete_action(self._data.id)

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

    properties = [
        ActionProperty.ActivateDisabled
    ]
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

    @override
    def _from_xml(
            self,
            node: ElementTree.Element,
            library: Library
    ) -> None:
        pass

    @override
    def _to_xml(self) -> ElementTree.Element:
        return ElementTree.Element()

    @override
    def is_valid(self) -> bool:
        return False

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


create = ReferenceData
