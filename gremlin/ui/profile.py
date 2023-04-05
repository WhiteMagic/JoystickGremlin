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

import uuid

from typing import Any, Dict, List, Optional

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from action_plugins.root import RootModel

import gremlin.profile
import gremlin.signal
from gremlin.types import AxisButtonDirection, HatDirection, InputType
from gremlin.util import clamp
from gremlin.plugin_manager import PluginManager

from gremlin.ui.action_model import ActionModel


QML_IMPORT_NAME = "Gremlin.Profile"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class VirtualButtonModel(QtCore.QObject):

    """Represents both axis and hat virtual buttons."""

    lowerLimitChanged = Signal()
    upperLimitChanged = Signal()
    directionChanged = Signal()
    hatDirectionChanged = Signal()

    def __init__(
        self,
        virtual_button: gremlin.profile.AbstractVirtualButton,
        parent: Optional[QtCore.QObject]=None
    ):
        """Creates a new instance.

        Args:
            virtual_button: the profile class representing the instance's data
            parent: parent object of the widget
        """
        super().__init__(parent)

        self.virtual_button = virtual_button

    def _get_lower_limit(self) -> float:
        return self.virtual_button.lower_limit

    def _set_lower_limit(self, value: float) -> None:
        if value != self.virtual_button.lower_limit:
            self.virtual_button.lower_limit = clamp(value, -1.0, 1.0)
            self.lowerLimitChanged.emit()

    def _get_upper_limit(self) -> float:
        return self.virtual_button.upper_limit

    def _set_upper_limit(self, value: float) -> None:
        if value != self.virtual_button.upper_limit:
            self.virtual_button.upper_limit = clamp(value, -1.0, 1.0)
            self.upperLimitChanged.emit()

    def _get_direction(self) -> str:
        return AxisButtonDirection.to_string(self.virtual_button.direction)

    def _set_direction(self, value: str) -> None:
        direction = AxisButtonDirection.to_enum(value.lower())
        if direction != self.virtual_button.direction:
            self.virtual_button.direction = direction
            self.directionChanged.emit()

    def _get_hat_state(self, hat_direction):
        return hat_direction in self.virtual_button.directions

    def _set_hat_state(self, hat_direction, is_active):
        if is_active:
            if hat_direction not in self.virtual_button.directions:
                self.virtual_button.directions.append(hat_direction)
                self.hatDirectionChanged.emit()
        else:
            if hat_direction in self.virtual_button.directions:
                index = self.virtual_button.directions.index(hat_direction)
                del self.virtual_button.directions[index]
                self.hatDirectionChanged.emit()

    lowerLimit = Property(
        float,
        fget=_get_lower_limit,
        fset=_set_lower_limit,
        notify=lowerLimitChanged
    )
    upperLimit = Property(
        float,
        fget=_get_upper_limit,
        fset=_set_upper_limit,
        notify=upperLimitChanged
    )
    direction = Property(
        str,
        fget=_get_direction,
        fset=_set_direction,
        notify=directionChanged
    )

    hatNorth = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.North),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.North, x),
        notify=hatDirectionChanged
    )
    hatNorthEast = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.NorthEast),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.NorthEast, x),
        notify=hatDirectionChanged
    )
    hatEast = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.East),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.East, x),
        notify=hatDirectionChanged
    )
    hatSouthEast = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.SouthEast),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.SouthEast, x),
        notify=hatDirectionChanged
    )
    hatSouth = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.South),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.South, x),
        notify=hatDirectionChanged
    )
    hatSouthWest = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.SouthWest),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.SouthWest, x),
        notify=hatDirectionChanged
    )
    hatWest = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.West),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.West, x),
        notify=hatDirectionChanged
    )
    hatNorthWest = Property(
        bool,
        fget=lambda cls: VirtualButtonModel._get_hat_state(cls, HatDirection.NorthWest),
        fset=lambda cls, x: VirtualButtonModel._set_hat_state(cls, HatDirection.NorthWest, x),
        notify=hatDirectionChanged
    )


@QtQml.QmlElement
class HatDirectionModel(QtCore.QObject):

    """QML model representing the directions of a hat."""

    directionsChanged = Signal()

    def __init__(
        self,
        directions: List[HatDirection],
        parent: Optional[QtCore.QObject]=None
    ):
        super().__init__(parent)

        self.directions = directions

    def _get_hat_state(self, direction: HatDirection) -> bool:
        return direction in self.directions

    def _set_hat_state(self, direction: HatDirection, is_active: bool) -> None:
        if is_active:
            if direction not in self.directions:
                self.directions.append(direction)
                self.directionsChanged.emit()
        else:
            if direction in self.directions:
                index = self.directions.index(direction)
                del self.directions[index]
                self.directionsChanged.emit()

    hatNorth = Property(
        bool,
        fget=lambda cls: HatDirectionModel._get_hat_state(cls, HatDirection.North),
        fset=lambda cls, x: HatDirectionModel._set_hat_state(cls, HatDirection.North, x),
        notify=directionsChanged
    )
    hatNorthEast = Property(
        bool,
        fget=lambda cls: HatDirectionModel._get_hat_state(cls, HatDirection.NorthEast),
        fset=lambda cls, x: HatDirectionModel._set_hat_state(cls, HatDirection.NorthEast, x),
        notify=directionsChanged
    )
    hatEast = Property(
        bool,
        fget=lambda cls: HatDirectionModel._get_hat_state(cls, HatDirection.East),
        fset=lambda cls, x: HatDirectionModel._set_hat_state(cls, HatDirection.East, x),
        notify=directionsChanged
    )
    hatSouthEast = Property(
        bool,
        fget=lambda cls: HatDirectionModel._get_hat_state(cls, HatDirection.SouthEast),
        fset=lambda cls, x: HatDirectionModel._set_hat_state(cls, HatDirection.SouthEast, x),
        notify=directionsChanged
    )
    hatSouth = Property(
        bool,
        fget=lambda cls: HatDirectionModel._get_hat_state(cls, HatDirection.South),
        fset=lambda cls, x: HatDirectionModel._set_hat_state(cls, HatDirection.South, x),
        notify=directionsChanged
    )
    hatSouthWest = Property(
        bool,
        fget=lambda cls: HatDirectionModel._get_hat_state(cls, HatDirection.SouthWest),
        fset=lambda cls, x: HatDirectionModel._set_hat_state(cls, HatDirection.SouthWest, x),
        notify=directionsChanged
    )
    hatWest = Property(
        bool,
        fget=lambda cls: HatDirectionModel._get_hat_state(cls, HatDirection.West),
        fset=lambda cls, x: HatDirectionModel._set_hat_state(cls, HatDirection.West, x),
        notify=directionsChanged
    )
    hatNorthWest = Property(
        bool,
        fget=lambda cls: HatDirectionModel._get_hat_state(cls, HatDirection.NorthWest),
        fset=lambda cls, x: HatDirectionModel._set_hat_state(cls, HatDirection.NorthWest, x),
        notify=directionsChanged
    )


@QtQml.QmlElement
class InputItemModel(QtCore.QObject):

    """QML model class representing an InputItem instance."""

    bindingsChanged = Signal()

    def __init__(self, input_item: gremlin.profile.InputItem, parent=None):
        super().__init__(parent)

        self._input_item = input_item

    @Property(QtCore.QObject, notify=bindingsChanged)
    def inputItemBindings(self) -> InputItemBindingListModel:
        return InputItemBindingListModel(
            self._input_item.action_sequences,
            self
        )

    @Slot()
    def createNewActionSequence(self) -> None:
        # Create root action
        action = PluginManager().create_instance(
            "Root",
            self._input_item.input_type
        )
        
        # Create binding instance and add it to the input item        
        binding = gremlin.profile.InputItemBinding(self._input_item)
        binding.root_action = action
        binding.behavior = self._input_item.input_type

        self._input_item.action_sequences.append(binding)
        self.bindingsChanged.emit()

    @Slot(str, str, str)
    def dropAction(self, source: str, target: str, method: str) -> None:
        """Handles dropping an action tree element

        Args:
            source: identifier of the tree being dropped
            target: identifier of the location on which the source is dropped
            method: type of drop action to perform
        """
        # Force a UI refresh without performing any model changes if both
        # source and target item are identical, i.e. an invalid drag&drop
        if source == target:
            self.bindingsChanged.emit()
            return

        source_id = uuid.UUID(source)
        target_id = uuid.UUID(target)
        source_entry = None
        for idx, entry in enumerate(self._input_item.action_sequences):
            entry_id = entry.library_reference.action_tree.root.value.id
            if entry_id == source_id:
                source_entry = self._input_item.action_sequences.pop(idx)
        if source_entry is not None:
            for idx, entry in enumerate(self._input_item.action_sequences):
                entry_id = entry.library_reference.action_tree.root.value.id
                if entry_id == target_id:
                    self._input_item.action_sequences.insert(idx+1, source_entry)

        self.bindingsChanged.emit()



@QtQml.QmlElement
class InputItemBindingModel(QtCore.QObject):

    """Model representing an ActionTree instance."""

    behaviorChanged = Signal()
    descriptionChanged = Signal()
    virtualButtonChanged = Signal()
    actionCountChanged = Signal()
    rootActionChanged = Signal()
    inputTypeChanged = Signal()

    def __init__(
            self,
            input_item_binding: gremlin.profile.InputItemBinding,
            parent=None
    ):
        super().__init__(parent)

        self._input_item_binding = input_item_binding
        self._virtual_button_model = VirtualButtonModel(
            self._input_item_binding.virtual_button
        )

    @Property(type=str, notify=inputTypeChanged)
    def inputType(self) -> str:
        return InputType.to_string(
            self._input_item_binding.input_item.input_type
        )

    @Property(type=VirtualButtonModel, notify=virtualButtonChanged)
    def virtualButton(self) -> VirtualButtonModel:
        return self._virtual_button_model

    @Property(type=int, notify=actionCountChanged)
    def actionCount(self) -> int:
        return self._action_tree.root.node_count

    @Property(str, constant=True)
    def actionTreeId(self) -> str:
        return str(self._input_item_binding.root_action.id)

    @Property(type=ActionModel, notify=rootActionChanged)
    def rootAction(self) -> RootModel:
        self.obj = RootModel(
            self._input_item_binding.root_action,
            self._input_item_binding,
            parent=self
        )
        return self.obj

    @property
    def input_item_binding(self) -> gremlin.profile.InputItemBinding:
        return self._input_item_binding

    def _get_behavior(self) -> str:
        return InputType.to_string(self._input_item_binding.behavior)

    def _set_behavior(self, text: str) -> None:
        behavior = InputType.to_enum(text)
        if behavior != self._input_item_binding.behavior:
            self._input_item_binding.behavior = behavior
            self._input_item_binding.virtual_button = None

            # Ensure a virtual button instance exists of the correct type
            # if one is needed
            input_type = self._input_item_binding.input_item.input_type
            if input_type == InputType.JoystickAxis and \
                    behavior == InputType.JoystickButton:
                if not isinstance(
                        self._input_item_binding.virtual_button,
                        gremlin.profile.VirtualAxisButton
                ):
                    self._input_item_binding.virtual_button = \
                        gremlin.profile.VirtualAxisButton()
                    self._virtual_button_model = VirtualButtonModel(
                        self._input_item_binding.virtual_button
                    )
            elif input_type == InputType.JoystickHat and \
                    behavior == InputType.JoystickButton:
                if not isinstance(
                        self._input_item_binding.virtual_button,
                        gremlin.profile.VirtualHatButton
                ):
                    self._input_item_binding.virtual_button = \
                        gremlin.profile.VirtualHatButton()
                    self._virtual_button_model = VirtualButtonModel(
                        self._input_item_binding.virtual_button
                    )

            # Update input type of all actions
            # node_list = self._action_tree.root.nodes_matching(lambda x: True)
            for node in self._action_tree.root.nodes_matching(lambda x: True):
                node.value.set_behavior_type(behavior)

            # Force full redraw of the action
            self.behaviorChanged.emit()
            self.rootActionChanged.emit()
            # This one might be overkill
            gremlin.signal.reloadUi.emit()

    def _get_description(self) -> str:
        return self._input_item_binding.description

    def _set_description(self, description: str) -> None:
        if description != self._input_item_binding.description:
            self._input_item_binding.description = description
            self.descriptionChanged.emit()

    @property
    def behavior_type(self):
        return self._input_item_binding.behavior

    behavior = Property(
        str,
        fget=_get_behavior,
        fset=_set_behavior,
        notify=behaviorChanged
    )

    description = Property(
        str,
        fget=_get_description,
        fset=_set_description,
        notify=descriptionChanged
    )


@QtQml.QmlElement
class InputItemBindingListModel(QtCore.QAbstractListModel):

    """List model of all InputItemBinding instances of a single input item."""

    # This fake single role and the roleName function are needed to have the
    # modelData property available in the QML delegate
    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray("fake".encode()),
    }

    def __init__(
        self,
        items: List[gremlin.profile.InputItemBinding],
        parent=None
    ):
        super().__init__(parent)

        self._action_configurations = items

    def rowCount(self, parent: QtCore.QModelIndex=...) -> int:
        return len(self._action_configurations)

    def data(self, index: QtCore.QModelIndex, role: int=...) -> Any:
        return InputItemBindingModel(
            self._action_configurations[index.row()],
            parent=self
        )

    def roleNames(self) -> Dict:
        return InputItemBindingListModel.roles
