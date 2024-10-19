# -*- coding: utf-8; -*-

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

import os
import logging
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
from gremlin.error import GremlinError

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class LoadProfileFunctor(AbstractFunctor):

    """Executes a load profile action callback."""

    def __init__(self, action: LoadProfileData):
        super().__init__(action)

    def __call__(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:

        if not self._should_execute(value):
            return

        logging.getLogger("system").debug(
            f"Loading profile ...{self.data._profileFilename}"
        )

        be = backend.Backend()
        be.loadProfile(self.data._profileFilename)
        be.activate_gremlin(False)
        be.activate_gremlin(True)


class LoadProfileModel(ActionModel):

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
            "core_plugins:load_profile/LoadProfileAction.qml"
        ).fileName()

    def _icon_string_impl(self) -> str:
        return LoadProfileData.icon

    def _get_profile_filename(self) -> str:
        return self._data._profileFilename

    def _set_profile_filename(self, value: str) -> None:
        if str(value) == self._data._profileFilename:
            return
        self._data._profileFilename = str(value)
        self.fileChanged.emit()

    profile_filename = Property(
        str,
        fget=_get_profile_filename,
        fset=_set_profile_filename,
        notify=fileChanged
    )


class LoadProfileData(AbstractActionData):

    """Model of a load profile action."""

    version = 1
    name = "Load Profile"
    tag = "load-profile"
    icon = "\U0001F504"

    functor = LoadProfileFunctor
    model = LoadProfileModel

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
        self._profileFilename = ""

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self._profileFilename = util.read_property(
            node, "load-profile", PropertyType.String
        )

        if not self.is_valid():
            raise GremlinError(f"{self._profileFilename} does not exists or is not accessible.")

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(LoadProfileData.tag, self._id)
        node.append(util.create_property_node(
            "load-profile", self._profileFilename, PropertyType.String
        ))
        return node

    def is_valid(self) -> bool:
        if len(self._profileFilename) > 0 and os.path.isfile(self._profileFilename) and \
           os.access(self._profileFilename, os.R_OK):
            return True
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


create = LoadProfileData
