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
from typing import Any, List, Optional, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from action_plugins import common

from gremlin import event_handler, keyboard, macro, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    DataCreationMode, Value
from gremlin.error import GremlinError, MissingImplementationError, ProfileError
from gremlin.macro import KeyAction
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType, \
    MouseButton, HatDirection

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class AbstractActionModel(QtCore.QObject):

    def __init__(self, action: macro.AbstractAction, parent=None):
        super().__init__(parent)

        self._action = action

    @Property(str, constant=True)
    def actionType(self) -> str:
        return self._action_type()

    def _action_type(self) -> str:
        raise MissingImplementationError(
            "_action_type not implemented in AbstractActionModel"
        )


class JoystickActionModel(AbstractActionModel):

    changed = Signal()

    def __init__(self, action: macro.JoystickAction, parent=None):
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "joystick"

    @Property(str, notify=changed)
    def inputType(self) -> str:
        return InputType.to_string(self._action.input_type)

    @Property(str, notify=changed)
    def label(self) -> str:
        return common.joystick_label(
            self._action.device_guid,
            self._action.input_type,
            self._action.input_id
        )

    @Slot(list)
    def updateJoystick(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of joystick events
        """
        # Sort keys such that modifiers are first
        self._action.device_guid = data[0].device_guid
        self._action.input_type = data[0].event_type
        self._action.input_id = data[0].identifier
        if data[0].event_type == InputType.JoystickAxis:
            self._action.value = 0.0
        elif data[0].event_type == InputType.JoystickButton:
            self._action.value = False
        elif data[0].event_type == InputType.JoystickHat:
            self._action.value = HatDirection.Center
        self.changed.emit()

    def _get_is_pressed(self) -> bool:
        if self._action.input_type == InputType.JoystickButton:
            return self._action.value

    def _set_is_pressed(self, value: bool) -> None:
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_axis_value(self) -> float:
        if self._action.input_type == InputType.JoystickAxis:
            return self._action.value

    def _set_axis_value(self, value: float) -> None:
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_hat_direction(self) -> str:
        if self._action.input_type == InputType.JoystickHat:
            print(HatDirection.to_string(self._action.value))
            return HatDirection.to_string(self._action.value)

    def _set_hat_direction(self, value: str) -> None:
        direction = HatDirection.to_enum(value)
        if direction != self._action.value:
            self._action.value = direction
            self.changed.emit()

    isPressed = Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    axisValue = Property(
        float,
        fget=_get_axis_value,
        fset=_set_axis_value,
        notify=changed
    )

    hatDirection = Property(
        str,
        fget=_get_hat_direction,
        fset=_set_hat_direction,
        notify=changed
    )


class KeyActionModel(AbstractActionModel):

    changed = Signal()

    def __init__(self, action: macro.KeyAction, parent=None):
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "key"

    def _get_is_pressed(self) -> bool:
        return self._action.is_pressed

    def _set_is_pressed(self, value: bool) -> None:
        if value != self._action.is_pressed:
            self._action.is_pressed = value
            self.changed.emit()

    def _get_key(self) -> str:
        return self._action.key.name

    @Slot(list)
    def updateKey(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        # Sort keys such that modifiers are first
        self._action.key = keyboard.key_from_code(*data[0].identifier)
        self.changed.emit()

    isPressed = Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    key = Property(
        str,
        fget=_get_key,
        notify=changed
    )


class MouseButtonActionModel(AbstractActionModel):

    changed = Signal()

    def __init__(self, action: macro.MouseButtonAction, parent=None):
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "mouse-button"

    def _get_is_pressed(self) -> bool:
        return self._action.is_pressed

    def _set_is_pressed(self, value: bool) -> None:
        if value != self._action.is_pressed:
            self._action.is_pressed = value
            self.changed.emit()

    def _get_button(self) -> str:
        return MouseButton.to_string(self._action.button)

    @Slot(list)
    def updateButton(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        # Sort keys such that modifiers are first
        self._action.button = data[0].identifier
        self.changed.emit()

    isPressed = Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    button = Property(
        str,
        fget=_get_button,
        notify=changed
    )


class MouseMotionActionModel(AbstractActionModel):

    changed = Signal()

    def __init__(self, action: macro.MouseMotionAction, parent=None):
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "mouse-motion"

    def _get_dx(self) -> int:
        return self._action.dx

    def _set_dx(self, value: int) -> None:
        if value != self._action.dx:
            self._action.dx = value
            self.changed.emit()

    def _get_dy(self) -> int:
        return self._action.dy

    def _set_dy(self, value: int) -> None:
        if value != self._action.dy:
            self._action.dy = value
            self.changed.emit()

    dx = Property(
        int,
        fget=_get_dx,
        fset=_set_dx,
        notify=changed
    )

    dy = Property(
        int,
        fget=_get_dy,
        fset=_set_dy,
        notify=changed
    )


class PauseActionModel(AbstractActionModel):

    changed = Signal()

    def __init__(self, action: macro.PauseAction, parent=None):
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "pause"

    def _get_duration(self) -> float:
        return self._action.duration

    def _set_duration(self, value: float) -> None:
        if value != self._action.duration:
            self._action.duration = value
            self.changed.emit()

    duration = Property(
        float,
        fget=_get_duration,
        fset=_set_duration,
        notify=changed
    )


class VJoyActionModel(AbstractActionModel):

    changed = Signal()

    def __init__(self, action: macro.VJoyAction, parent=None):
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "vjoy"

    def _get_input_type(self) -> str:
        return InputType.to_string(self._action.input_type)

    def _set_input_type(self, value: str) -> None:
        input_type = InputType.to_enum(value)
        if input_type != self._action.input_type:
            self._action.input_type = input_type
            if input_type == InputType.JoystickAxis:
                self._action.value = 0.0
            elif input_type == InputType.JoystickButton:
                self._action.value = False
            elif input_type == InputType.JoystickHat:
                self._action.value = HatDirection.Center
            self.changed.emit()

    def _get_input_id(self) -> int:
        return self._action.input_id

    def _set_input_id(self, value: int) -> None:
        if value != self._action.input_id:
            self._action.input_id = value
            self.changed.emit()

    def _get_vjoy_id(self) -> int:
        return self._action.vjoy_id

    def _set_vjoy_id(self, value: int) -> None:
        if value != self._action.vjoy_id:
            self._action.vjoy_id = value
            self.changed.emit()

    def _get_is_pressed(self) -> bool:
        if self._action.input_type == InputType.JoystickButton:
            return self._action.value

    def _set_is_pressed(self, value: bool) -> None:
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_axis_value(self) -> float:
        if self._action.input_type == InputType.JoystickAxis:
            return self._action.value

    def _set_axis_value(self, value: float) -> None:
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_hat_direction(self) -> str:
        if self._action.input_type == InputType.JoystickHat:
            print(HatDirection.to_string(self._action.value))
            return HatDirection.to_string(self._action.value)

    def _set_hat_direction(self, value: str) -> None:
        direction = HatDirection.to_enum(value)
        if direction != self._action.value:
            self._action.value = direction
            self.changed.emit()

    inputType = Property(
        str,
        fget=_get_input_type,
        fset=_set_input_type,
        notify=changed
    )

    inputId = Property(
        int,
        fget=_get_input_id,
        fset=_set_input_id,
        notify=changed
    )

    vjoyId = Property(
        int,
        fget=_get_vjoy_id,
        fset=_set_vjoy_id,
        notify=changed
    )

    isPressed = Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    axisValue = Property(
        float,
        fget=_get_axis_value,
        fset=_set_axis_value,
        notify=changed
    )

    hatDirection = Property(
        str,
        fget=_get_hat_direction,
        fset=_set_hat_direction,
        notify=changed
    )



class MacroRepeatModes(enum.Enum):

    Single = 1
    Count = 2
    Toggle = 3
    Hold = 4

    @staticmethod
    def lookup(value: str) -> MacroRepeatModes:
        match value:
            case "Single":
                return MacroRepeatModes.Single
            case "Count":
                return MacroRepeatModes.Count
            case "Toggle":
                return MacroRepeatModes.Toggle
            case "Hold":
                return MacroRepeatModes.Hold


class MacroFunctor(AbstractFunctor):

    """Implements the function executed of the Description action at runtime."""

    def __init__(self, action: DescriptionData):
        super().__init__(action)

        self.macro = macro.Macro()
        for action in self.data.actions:
            self.macro.add_action(action)
        self.macro.is_exclusive = self.data.is_exclusive
        self.macro.repeat = self.data.repeat_data

    def __call__(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
        """Processes the provided event.

        Args:
            event: the input event to process
            value: the potentially modified input value
        """
        if self._should_execute(value):
            macro.MacroManager().queue_macro(self.macro)


class MacroModel(ActionModel):

    # Signal emitted when the description variable's content changes
    changed = Signal()

    action_lookup = {
        "joystick": macro.JoystickAction.create,
        "key": macro.KeyAction.create,
        "mouse-button": macro.MouseButtonAction.create,
        "mouse-motion": macro.MouseMotionAction.create,
        "pause": macro.PauseAction.create,
        "vjoy": macro.VJoyAction.create,
    }

    model_lookup = {
        "joystick": JoystickActionModel,
        "pause": PauseActionModel,
        "mouse-button": MouseButtonActionModel,
        "mouse-motion": MouseMotionActionModel,
        "key": KeyActionModel,
        "vjoy": VJoyActionModel
    }

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
            "core_plugins:macro/MacroAction.qml"
        ).fileName()

    def _icon_string_impl(self) -> str:
        return MacroData.icon

    @Property(list, notify=changed)
    def actions(self) -> List[AbstractActionModel]:
        model_instances = [
            self.model_lookup[action.tag](action, self)
            for action in self._data.actions
        ]
        return model_instances

    @Slot(str)
    def addAction(self, name: str) -> None:
        self._data.actions.append(self.action_lookup[name]())
        self.changed.emit()

    @Slot(int)
    def removeAction(self, index: int) -> None:
        if index < len(self._data.actions):
            del self._data.actions[index]
            self.changed.emit()


class MacroData(AbstractActionData):

    """Model of a macro action."""

    version = 1
    name = "Macro"
    tag = "macro"
    icon = "\uF585"

    functor = MacroFunctor
    model = MacroModel

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

        # Model variables
        self.actions = []
        self.is_exclusive = False
        self.repeat_mode = MacroRepeatModes.Single
        self.repeat_data = None

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        type_lookup = {
            "joystick": macro.JoystickAction.create,
            "key": macro.KeyAction.create,
            "mouse-button": macro.MouseButtonAction.create,
            "mouse-motion": macro.MouseMotionAction.create,
            "pause": macro.PauseAction.create,
            "vjoy": macro.VJoyAction.create,
        }
        self._id = util.read_action_id(node)
        self.is_exclusive = util.read_property(
            node, "is-exclusive", PropertyType.Bool
        )
        self.repeat_mode = MacroRepeatModes.lookup(util.read_property(
            node, "repeat-mode", PropertyType.String)
        )
        for entry in node.iter("macro-action"):
            action_type = entry.get("type")
            action_obj = None
            if action_type in type_lookup:
                action_obj = type_lookup[action_type]()
                action_obj.from_xml(entry)
                self.actions.append(action_obj)
            else:
                raise ProfileError(
                    f"Unknown action type {action_type} in Macro action with " +
                    f"id {self._id}"
                )

    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MacroData.tag, self._id)
        util.append_property_nodes(
            node,
            [
                ["is-exclusive", self.is_exclusive, PropertyType.Bool],
                ["repeat-mode", self.repeat_mode.name, PropertyType.String],
            ]
        )
        for entry in self.actions:
            node.append(entry.to_xml())
        return node

    def is_valid(self) -> bool:
        return True

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


create = MacroData
