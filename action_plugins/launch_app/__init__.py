# -*- coding: utf-8; -*-

# Copyright (C) 2024
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

import logging
import subprocess
from typing import List, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal

from gremlin import event_handler, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value

from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType

from gremlin.ui.action_model import SequenceIndex, ActionModel
from gremlin.ui import backend
from gremlin.error import GremlinError, ProfileError
from gremlin.util import file_exists_and_is_accessible

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class LaunchAppFunctor(AbstractFunctor):

    """Executes a file action callback."""

    def __init__(self, action: LaunchAppData):
        super().__init__(action)

    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        if not self._should_execute(value):
            return

        # log exceptions from subprocess
        try:
            subprocess.run([self.data.application_path])
        except subprocess.SubprocessError as e:
            logging.getLogger("system").exception(
                f"There was an error launching the application '{self.data.application_path}': {e}"
            )


class LaunchAppModel(ActionModel):

    fileChanged = Signal()

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
            "core_plugins:launch_app/LaunchAppAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_application_path(self) -> str:
        return self._data.application_path

    def _set_application_path(self, value: str) -> None:
        if value == self._data.application_path:
            return
        if not file_exists_and_is_accessible(value):
            raise GremlinError(f"{value} does not exists or is not accessible.")
        self._data.application_path = value
        self.fileChanged.emit()

    application_path = Property(
        str,
        fget=_get_application_path,
        fset=_set_application_path,
        notify=fileChanged
    )


class LaunchAppData(AbstractActionData):

    """Model of a execute file action."""

    version = 1
    name = "Launch Application"
    tag = "launch-app"
    icon = "\U0001F680"

    functor = LaunchAppFunctor
    model = LaunchAppModel

    properties = [
        ActionProperty.ActivateOnPress,
        ActionProperty.AlwaysExecute
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
        self.application_path = ""

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.application_path = util.read_property(
            node, "launch-app", PropertyType.String
        )

        if not self.is_valid():
            raise ProfileError(f"{self.application_path} does not exists or is not accessible.")

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(LaunchAppData.tag, self._id)
        node.append(util.create_property_node(
            "launch-app", self.application_path, PropertyType.String
        ))
        return node

    def is_valid(self) -> bool:
        return file_exists_and_is_accessible(self.application_path)

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


create = LaunchAppData
