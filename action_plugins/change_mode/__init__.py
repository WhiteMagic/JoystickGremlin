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
import logging
import threading
import time
from typing import List, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import error, event_handler, mode_manager, shared_state, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value
from gremlin.profile import Library
from gremlin.types import ActionProperty, AxisMode, InputType, PropertyType, DataCreationMode

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class ChangeType(enum.Enum):

    Switch = 1
    Cycle = 2
    Previous = 3
    Unwind = 4
    Temporary = 5

    @staticmethod
    def lookup(value: str) -> ChangeType:
        match value:
            case "Switch":
                return ChangeType.Switch
            case "Cycle":
                return ChangeType.Cycle
            case "Previous":
                return ChangeType.Previous
            case "Unwind":
                return ChangeType.Unwind
            case "Temporary":
                return ChangeType.Temporary
            case _:
                return ChangeType.Switch


class ChangeModeFunctor(AbstractFunctor):

    """Executes a mode change action callback."""

    def __init__(self, action: ChangeModeData):
        super().__init__(action)

        self._mode_sequence = None
        if self.data.change_type == ChangeType.Cycle:
            self._mode_sequence = \
                mode_manager.ModeSequence(self.data._target_modes)

    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        if not value.current and self.data.change_type != ChangeType.Temporary:
            return

        mm = mode_manager.ModeManager()
        if self.data.change_type == ChangeType.Switch:
            mm.switch_to(mode_manager.Mode(
                self.data.target_modes[0],
                mm.current.name
            ))
        elif self.data.change_type == ChangeType.Previous:
            mm.previous()
        elif self.data.change_type == ChangeType.Cycle:
            mm.cycle(self._mode_sequence)
        elif self.data.change_type == ChangeType.Unwind:
            mm.unwind()
        elif self.data.change_type == ChangeType.Temporary:
            # Enter the temporary mode when the input is pressed
            if value.current:
                mm.switch_to(mode_manager.Mode(
                    self.data.target_modes[0],
                    mm.current.name,
                    True
                ))
            # Leave the temporary mode when the input is released while in the
            # correct mode
            else:
                if mm.current.name == self.data._target_modes[0] and \
                        mm.current.is_temporary:
                    mm.unwind()

        logging.getLogger("system").debug(
            f"Mode Stack : [{', '.join(m.name for m in mm._mode_stack)}], " +
            f"Action : {self.data.change_type.name}"
        )


class ChangeModeModel(ActionModel):

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
            "core_plugins:change_mode/ChangeModeAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_change_type(self) -> str:
        return self._data.change_type.name

    def _set_change_type(self, value: str) -> None:
        if value != self._data.change_type.name:
            self._data.change_type = ChangeType.lookup(value)
            self.modelChanged.emit()

    def _get_target_modes(self) -> List[str]:
        return self._data.target_modes

    def _set_target_modes(self, values: List[str]) -> None:
        if values != self._data.target_modes:
            self._data.target_modes = values
            self.modelChanged.emit()

    @Slot()
    def addTargetMode(self) -> None:
        modes = self._data.target_modes
        modes.append(shared_state.current_profile.modes.first_mode)
        self._data.target_modes = modes
        self.modelChanged.emit()

    @Slot(int)
    def deleteTargetMode(self, index: int) -> None:
        modes = self._data.target_modes
        if index >= len(modes):
            raise error.GremlinError(
                f"Attempting to remove mode at index {index} when only "
                f"{len(modes)} entries exist."
            )
        del modes[index]
        self._data.target_modes = modes
        self.modelChanged.emit()

    @Slot(str, int)
    def setTargetMode(self, mode: str, index: int) -> None:
        modes = self._data.target_modes
        if index >= len(modes):
            raise error.GremlinError(
                f"Attempting to change the value of mode at index {index} "
                f"when only {len(modes)} entries exist."
            )
        if modes[index] != mode:
            modes[index] = mode
            self._data.target_modes = modes
            self.modelChanged.emit()

    changeType = Property(
        str,
        fget=_get_change_type,
        fset=_set_change_type,
        notify=modelChanged
    )

    targetModes = Property(
        list,
        fget=_get_target_modes,
        fset=_set_target_modes,
        notify=modelChanged
    )


class ChangeModeData(AbstractActionData):

    """Action permitting changing of modes."""

    version = 1
    name = "Change Mode"
    tag = "change-mode"
    icon = "\uF544"

    functor = ChangeModeFunctor
    model = ChangeModeModel

    properties = [
        ActionProperty.ActivateOnPress
    ]
    input_types = [
        InputType.JoystickButton,
        InputType.Keyboard
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ):
        super().__init__(behavior_type)

        self._change_type = ChangeType.Switch
        self._target_modes = [shared_state.current_profile.modes.first_mode]

    @property
    def change_type(self) -> ChangeType:
        return self._change_type

    @change_type.setter
    def change_type(self, value: ChangeType) -> None:
        if value == self._change_type:
            return

        self._change_type = value
        match value:
            case ChangeType.Switch | ChangeType.Temporary:
                self._target_modes = [
                    shared_state.current_profile.modes.first_mode
                ]
            case ChangeType.Previous | ChangeType.Unwind | ChangeType.Cycle:
                self._target_modes = []

    @property
    def target_modes(self) -> List[str]:
        return self._target_modes

    @target_modes.setter
    def target_modes(self, value: List[str]) -> None:
        if len(value) > 0 and \
                self._change_type in [ChangeType.Previous, ChangeType.Unwind]:
            raise error.GremlinError("Too many modes for change type")
        elif len(value) != 1 and \
                self._change_type in [ChangeType.Switch, ChangeType.Temporary]:
            raise error.GremlinError("Incorrect number of modes for change type")

        self._target_modes = value

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self._change_type = ChangeType.lookup(util.read_property(
            node, "change-type", PropertyType.String
        ))
        self._target_modes = []
        for entry in node.iter("target-mode"):
            self._target_modes.append(util.read_property(
                entry, "name", PropertyType.String
            ))

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(ChangeModeData.tag, self._id)
        node.append(util.create_property_node(
            "change-type", self._change_type.name, PropertyType.String
        ))
        for mode_name in self._target_modes:
            node.append(util.create_node_from_data(
                "target-mode", [("name", mode_name, PropertyType.String)]
            ))
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
