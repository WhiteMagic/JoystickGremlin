# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import enum
from typing import (
    override,
    List,
    TYPE_CHECKING,
)
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore

from action_plugins import common
import dill

from gremlin import (
    device_helpers,
    event_handler,
    keyboard,
    macro,
    util,
)
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.error import (
    GremlinError,
    MissingImplementationError,
    ProfileError,
)
from gremlin.logical_device import LogicalDevice
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    AxisMode,
    HatDirection,
    InputType,
    MouseButton,
    PropertyType,
)

from gremlin.ui.action_model import (
    ActionModel,
    SequenceIndex,
)
from gremlin.ui.device import InputIdentifier

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel
    import gremlin.ui.type_aliases as ta


class AbstractActionModel(QtCore.QObject):

    def __init__(
        self,
        action: macro.AbstractAction,
        parent: ta.OQO=None
    ) -> None:
        super().__init__(parent)
        self._action = action

    @QtCore.Property(str, constant=True)
    def actionType(self) -> str:
        return self._action_type()

    def _action_type(self) -> str:
        raise MissingImplementationError(
            "_action_type not implemented in AbstractActionModel"
        )


class JoystickActionModel(AbstractActionModel):

    changed = QtCore.Signal()

    def __init__(
        self,
        action: macro.JoystickAction,
        parent: ta.OQO=None
    ) -> None:
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "joystick"

    @QtCore.Property(str, notify=changed)
    def inputType(self) -> str:
        return InputType.to_string(self._action.input_type)

    @QtCore.Property(str, notify=changed)
    def label(self) -> str:
        if self._action.device_guid == dill.UUID_Invalid:
            return ""
        else:
            return common.joystick_label(
                self._action.device_guid,
                self._action.input_type,
                self._action.input_id
            )

    @QtCore.Slot(list)
    def updateJoystick(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to joystick events.

        We only expect to receive a single event and thus only store the
        information from the first event.

        Args:
            data: list of joystick events
        """
        if not data:
            self._action.device_guid = dill.UUID_Invalid
            self._action.input_type = InputType.JoystickButton
            self._action.input_id = 1
            self._action.value = False
        else:
            # Extract information about first input
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
        return False

    def _set_is_pressed(self, value: bool) -> None:
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_axis_value(self) -> float:
        if self._action.input_type == InputType.JoystickAxis:
            return self._action.value
        return 0.0

    def _set_axis_value(self, value: float) -> None:
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_hat_direction(self) -> str:
        if self._action.input_type == InputType.JoystickHat:
            return HatDirection.to_string(self._action.value)
        return HatDirection.to_string(HatDirection.Center)

    def _set_hat_direction(self, value: str) -> None:
        direction = HatDirection.to_enum(value)
        if direction != self._action.value:
            self._action.value = direction
            self.changed.emit()

    isPressed = QtCore.Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    axisValue = QtCore.Property(
        float,
        fget=_get_axis_value,
        fset=_set_axis_value,
        notify=changed
    )

    hatDirection = QtCore.Property(
        str,
        fget=_get_hat_direction,
        fset=_set_hat_direction,
        notify=changed
    )


class KeyActionModel(AbstractActionModel):

    changed = QtCore.Signal()

    def __init__(self, action: macro.KeyAction, parent: ta.OQO=None) -> None:
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
        return "" if self._action.key is None else self._action.key.name

    @QtCore.Slot(list)
    def updateKey(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        # Sort keys such that modifiers are first
        self._action.key = None if not data else \
            keyboard.key_from_code(*data[0].identifier)
        self.changed.emit()

    isPressed = QtCore.Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    key = QtCore.Property(str, fget=_get_key, notify=changed)


class LogicalDeviceActionModel(AbstractActionModel):

    changed = QtCore.Signal()

    def __init__(
        self,
        action: macro.LogicalDeviceAction,
        parent: ta.OQO=None
    ) -> None:
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "logical-device"

    def _get_logical_input_identifier(self) -> InputIdentifier:
        return InputIdentifier(
            LogicalDevice.device_guid,
            self._action.input_type,
            self._action.input_id,
            parent=self
        )

    def _set_logical_input_identifier(self, identifier: InputIdentifier) -> None:
        if (identifier.input_type != self._action.input_type) or \
                (identifier.input_id != self._action.input_id):
            self._action.input_id = identifier.input_id
            if identifier.input_type != self._action.input_type:
                self._action.input_type = identifier.input_type
                if identifier.input_type == InputType.JoystickAxis:
                    self._action.value = 0.0
                elif identifier.input_type == InputType.JoystickButton:
                    self._action.value = False
                elif identifier.input_type == InputType.JoystickHat:
                    self._action.value = HatDirection.Center
            self.changed.emit()

    def _get_input_type(self) -> str:
        return InputType.to_string(self._action.input_type)

    def _get_is_pressed(self) -> bool:
        if self._action.input_type == InputType.JoystickButton:
            return self._action.value

    def _set_is_pressed(self, value: bool) -> None:
        if self._action.input_type != InputType.JoystickButton:
            return
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_axis_value(self) -> float:
        if self._action.input_type == InputType.JoystickAxis:
            return self._action.value
        return 0.0

    def _set_axis_value(self, value: float) -> None:
        if self._action.input_type != InputType.JoystickAxis:
            return
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_axis_mode(self) -> str:
        return AxisMode.to_string(self._action.axis_mode)

    def _set_axis_mode(self, value: str) -> None:
        mode = AxisMode.to_enum(value)
        if mode != self._action.axis_mode:
            self._action.axis_mode = mode
            self.changed.emit()

    def _get_hat_direction(self) -> str:
        if self._action.input_type == InputType.JoystickHat:
            return HatDirection.to_string(self._action.value)
        return ""

    def _set_hat_direction(self, value: str) -> None:
        if self._action.input_type != InputType.JoystickHat:
            return
        direction = HatDirection.to_enum(value)
        if direction != self._action.value:
            self._action.value = direction
            self.changed.emit()

    logicalInputIdentifier = QtCore.Property(
        InputIdentifier,
        fget=_get_logical_input_identifier,
        fset=_set_logical_input_identifier,
        notify=changed
    )

    inputType = QtCore.Property(str, fget=_get_input_type, notify=changed)

    isPressed = QtCore.Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    axisValue = QtCore.Property(
        float,
        fget=_get_axis_value,
        fset=_set_axis_value,
        notify=changed
    )

    axisMode = QtCore.Property(
        str,
        fget=_get_axis_mode,
        fset=_set_axis_mode,
        notify=changed
    )

    hatDirection = QtCore.Property(
        str,
        fget=_get_hat_direction,
        fset=_set_hat_direction,
        notify=changed
    )


class MouseButtonActionModel(AbstractActionModel):

    changed = QtCore.Signal()

    def __init__(
        self,
        action: macro.MouseButtonAction,
        parent: ta.OQO=None
    ) -> None:
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
        return "" if self._action.button is None else \
            MouseButton.to_string(self._action.button)

    @QtCore.Slot(list)
    def updateButton(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        self._action.button = None if not data else data[0].identifier
        self.changed.emit()

    isPressed = QtCore.Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    button = QtCore.Property(str, fget=_get_button, notify=changed)


class MouseMotionActionModel(AbstractActionModel):

    changed = QtCore.Signal()

    def __init__(
        self,
        action: macro.MouseMotionAction,
        parent: ta.OQO=None
    ) -> None:
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

    dx = QtCore.Property(int, fget=_get_dx, fset=_set_dx, notify=changed)
    dy = QtCore.Property(int, fget=_get_dy, fset=_set_dy, notify=changed)


class PauseActionModel(AbstractActionModel):

    changed = QtCore.Signal()

    def __init__(self, action: macro.PauseAction, parent: ta.OQO=None) -> None:
        super().__init__(action, parent)

    def _action_type(self) -> str:
        return "pause"

    def _get_duration(self) -> float:
        return self._action.duration

    def _set_duration(self, value: float) -> None:
        if value != self._action.duration:
            self._action.duration = value
            self.changed.emit()

    duration = QtCore.Property(
        float,
        fget=_get_duration,
        fset=_set_duration,
        notify=changed
    )


class VJoyActionModel(AbstractActionModel):

    changed = QtCore.Signal()

    def __init__(self, action: macro.VJoyAction, parent: ta.OQO=None) -> None:
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
        return False

    def _set_is_pressed(self, value: bool) -> None:
        if self._action.input_type != InputType.JoystickButton:
            return
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_axis_value(self) -> float:
        if self._action.input_type == InputType.JoystickAxis:
            return self._action.value
        return 0.0

    def _set_axis_value(self, value: float) -> None:
        if self._action.input_type != InputType.JoystickAxis:
            return
        if value != self._action.value:
            self._action.value = value
            self.changed.emit()

    def _get_axis_mode(self) -> str:
        return AxisMode.to_string(self._action.axis_mode)

    def _set_axis_mode(self, value: str) -> None:
        mode = AxisMode.to_enum(value)
        if mode != self._action.axis_mode:
            self._action.axis_mode = mode
            self.changed.emit()

    def _get_hat_direction(self) -> str:
        if self._action.input_type == InputType.JoystickHat:
            return HatDirection.to_string(self._action.value)
        return ""

    def _set_hat_direction(self, value: str) -> None:
        if self._action.input_type != InputType.JoystickHat:
            return
        direction = HatDirection.to_enum(value)
        if direction != self._action.value:
            self._action.value = direction
            self.changed.emit()

    inputType = QtCore.Property(
        str,
        fget=_get_input_type,
        fset=_set_input_type,
        notify=changed
    )

    inputId = QtCore.Property(
        int,
        fget=_get_input_id,
        fset=_set_input_id,
        notify=changed
    )

    vjoyId = QtCore.Property(
        int,
        fget=_get_vjoy_id,
        fset=_set_vjoy_id,
        notify=changed
    )

    isPressed = QtCore.Property(
        bool,
        fget=_get_is_pressed,
        fset=_set_is_pressed,
        notify=changed
    )

    axisValue = QtCore.Property(
        float,
        fget=_get_axis_value,
        fset=_set_axis_value,
        notify=changed
    )

    axisMode = QtCore.Property(
        str,
        fget=_get_axis_mode,
        fset=_set_axis_mode,
        notify=changed
    )

    hatDirection = QtCore.Property(
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
        match value.lower():
            case "single":
                return MacroRepeatModes.Single
            case "count":
                return MacroRepeatModes.Count
            case "toggle":
                return MacroRepeatModes.Toggle
            case "hold":
                return MacroRepeatModes.Hold
            case _:
                raise GremlinError(f"Invalid macro repeat mode: {value}")


class MacroRepeatData:

    def __init__(self, delay: float=0.1, count: int=1) -> None:
        self.count = count
        self.delay = delay


class MacroFunctor(AbstractFunctor):

    """Implements the function executed of the Description action at runtime."""

    def __init__(self, action: MacroData) -> None:
        super().__init__(action)

        self.macro = macro.Macro()
        for action in self.data.actions:
            self.macro.add_action(action)
        self.macro.is_exclusive = self.data.is_exclusive
        match self.data.repeat_mode:
            case MacroRepeatModes.Count:
                self.macro.repeat = macro.CountRepeat(
                    self.data.repeat_data.count,
                    self.data.repeat_data.delay
                )
            case MacroRepeatModes.Hold:
                self.macro.repeat = macro.HoldRepeat(
                    self.data.repeat_data.delay
                )
            case MacroRepeatModes.Toggle:
                self.macro.repeat = macro.ToggleRepeat(
                    self.data.repeat_data.delay
                )

    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        if self._should_execute(value):
            macro.MacroManager().queue_macro(self.macro)
            if self.data.repeat_mode == MacroRepeatModes.Hold:
                device_helpers.ButtonReleaseActions().register_callback(
                    lambda: macro.MacroManager().terminate_macro(self.macro),
                    event
                )


class MacroModel(ActionModel):

    # Signal emitted when the description variable's content changes
    changed = QtCore.Signal()

    action_lookup = {
        "joystick": macro.JoystickAction.create,
        "key": macro.KeyAction.create,
        "logical-device": macro.LogicalDeviceAction.create,
        "mouse-button": macro.MouseButtonAction.create,
        "mouse-motion": macro.MouseMotionAction.create,
        "pause": macro.PauseAction.create,
        "vjoy": macro.VJoyAction.create,
    }

    model_lookup = {
        "joystick": JoystickActionModel,
        "logical-device": LogicalDeviceActionModel,
        "key": KeyActionModel,
        "mouse-button": MouseButtonActionModel,
        "mouse-motion": MouseMotionActionModel,
        "pause": PauseActionModel,
        "vjoy": VJoyActionModel
    }

    def __init__(
            self,
            data: AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:macro/MacroAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @QtCore.Property(list, notify=changed)
    def actions(self) -> List[AbstractActionModel]:
        model_instances = [
            self.model_lookup[action.tag](action, self)
            for action in self._data.actions
        ]
        return model_instances

    @QtCore.Slot(str)
    def addAction(self, name: str) -> None:
        self._data.actions.append(self.action_lookup[name]())
        self.changed.emit()

    @QtCore.Slot(int)
    def removeAction(self, index: int) -> None:
        if index < len(self._data.actions):
            del self._data.actions[index]
            self.changed.emit()

    @QtCore.Slot(int, int, str)
    def dropCallback(
        self,
        target_index: int,
        source_index: int,
        mode: str
    ) -> None:
        source_item = self._data.actions[source_index]
        target_item = self._data.actions[target_index]
        self._data.actions.remove(source_item)

        match mode:
            case "append":
                self._data.actions.insert(
                    self._data.actions.index(target_item) + 1,
                    source_item
                )
            case "prepend":
                self._data.actions.insert(0, source_item)
            case _:
                raise GremlinError(f"Invalid insertion mode '{mode}")

        self.changed.emit()

    def _get_repeat_count(self) -> int:
        if self._data.repeat_mode == MacroRepeatModes.Count:
            return self._data.repeat_data.count
        else:
            return 1

    def _set_repeat_count(self, value: int) -> None:
        if self._data.repeat_mode == MacroRepeatModes.Count and \
                value != self._data.repeat_data.count:
            self._data.repeat_data.count = value
            self.changed.emit()

    def _get_repeat_delay(self) -> float:
        if self._data.repeat_mode != MacroRepeatModes.Single:
            return self._data.repeat_data.delay
        else:
            return 0.0

    def _set_repeat_delay(self, value: float) -> None:
        if self._data.repeat_mode != MacroRepeatModes.Single and \
                value != self._data.repeat_data.delay:
            self._data.repeat_data.delay = value
            self.changed.emit()

    def _get_repeat_mode(self) -> str:
        return self._data.repeat_mode.name.lower()

    def _set_repeat_mode(self, value: str) -> None:
        mode = MacroRepeatModes.lookup(value)
        if mode != self._data.repeat_mode:
            self._data.repeat_mode = mode
            self.changed.emit()

    def _get_is_exclusive(self) -> bool:
        return self._data.is_exclusive

    def _set_is_exclusive(self, state: bool) -> None:
        if state != self._data.is_exclusive:
            self._data.is_exclusive = state
            self.changed.emit()

    repeatCount = QtCore.Property(
        int,
        fget=_get_repeat_count,
        fset=_set_repeat_count,
        notify=changed
    )

    repeatDelay = QtCore.Property(
        float,
        fget=_get_repeat_delay,
        fset=_set_repeat_delay,
        notify=changed
    )

    repeatMode = QtCore.Property(
        str,
        fget=_get_repeat_mode,
        fset=_set_repeat_mode,
        notify=changed
    )

    isExclusive = QtCore.Property(
        bool,
        fget=_get_is_exclusive,
        fset=_set_is_exclusive,
        notify=changed
    )


class MacroData(AbstractActionData):

    """Model of a macro action."""

    version = 1
    name = "Macro"
    tag = "macro"
    icon = "\uF585"

    functor = MacroFunctor
    model = MacroModel

    properties = (
        ActionProperty.ActivateOnPress,
    )
    input_types = (
        InputType.JoystickButton,
        InputType.Keyboard
    )

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ) -> None:
        super().__init__(behavior_type)

        # Model variables
        self.actions = []
        self.is_exclusive = False
        self.repeat_mode = MacroRepeatModes.Single
        self.repeat_data = MacroRepeatData()

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        type_lookup = {
            "joystick": macro.JoystickAction.create,
            "key": macro.KeyAction.create,
            "logical-device": macro.LogicalDeviceAction.create,
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
        self.repeat_data.count = util.read_property(
            node, "repeat-count", PropertyType.Int
        )
        self.repeat_data.delay = util.read_property(
            node, "repeat-delay", PropertyType.Float
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

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MacroData.tag, self._id)
        util.append_property_nodes(
            node,
            [
                ["is-exclusive", self.is_exclusive, PropertyType.Bool],
                ["repeat-mode", self.repeat_mode.name, PropertyType.String],
                ["repeat-count", self.repeat_data.count, PropertyType.Int],
                ["repeat-delay", self.repeat_data.delay, PropertyType.Float],
            ]
        )
        for entry in self.actions:
            if entry.is_valid():
                node.append(entry.to_xml())
        return node

    @override
    def user_feedback(self) -> List[UserFeedback]:
        return []

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

    @override
    def swap_uuid(self, old_uuid: uuid.UUID, new_uuid: uuid.UUID) -> bool:
        performed_swap = False
        for action in self.actions:
            if action.swap_uuid(old_uuid, new_uuid):
                performed_swap = True
        return performed_swap


create = MacroData
