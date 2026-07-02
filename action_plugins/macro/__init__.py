# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import enum
import uuid
from typing import (
    TYPE_CHECKING,
    List,
    cast,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore

import dill
from action_plugins import common
from gremlin import (
    event_handler,
    event_helpers,
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
from gremlin.config import Configuration
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
from gremlin.ui.util import MacroRecorder

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta
    from gremlin.ui.profile import InputItemBindingModel


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
                event_helpers.ButtonReleaseActions().register_callback(
                    lambda _event: macro.MacroManager().terminate_macro(self.macro),
                    event
                )


class ActionListModel(QtCore.QAbstractListModel):
    """Model of the list of actions that constitute a macro.

    Keeps the action data and action representation in sync.
    """

    actionAdded = QtCore.Signal()

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"modelData"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"actionType"),
    }

    def __init__(
            self,
            actions: list[macro.AbstractAction],
            parent: QtCore.QObject
    ) -> None:
        super().__init__(parent)
        self._actions = actions
        self._wrappers: list[AbstractActionModel] = [
            self._create_action_model(action) for action in self._actions
        ]

    def rowCount(self, parent: ta.MI = QtCore.QModelIndex()) -> int:
        return len(self._actions)

    def data(
        self,
        index: ta.MI,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> AbstractActionModel | str | None:
        if not index.isValid() or not (0 <= index.row() < len(self._actions)):
            return None
        match cast(str, self.roles.get(role, "")):
            case "modelData":
                return self._wrappers[index.row()]
            case "actionType":
                return self._actions[index.row()].tag
            case _:
                return None

    def roleNames(self) -> dict:
        return self.roles

    def append(self, action: macro.AbstractAction) -> None:
        """Adds the given action at the end of the list.

        Args:
            action: The action added to the end of the list.
        """
        row = len(self._actions)
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self._actions.append(action)
        self._wrappers.append(self._create_action_model(action))
        self.endInsertRows()
        self.actionAdded.emit()

    def remove(self, index: int) -> None:
        """Removes the action at the specified index.

        Args:
            index: The index of the action to remove.
        """
        if not (0 <= index < len(self._actions)):
            return
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        del self._actions[index]
        del self._wrappers[index]
        self.endRemoveRows()

    def move_from_to(self, source_index: int, destination_index: int) -> None:
        """Move an item from a source to a destination index.

        Args:
            source_index: The index of the item to move.
            destination_index: The index to move the item to.
        """
        if not (0 <= source_index < len(self._actions)):
            return

        if not self.beginMoveRows(
            QtCore.QModelIndex(), source_index, source_index,
            QtCore.QModelIndex(), destination_index
        ):
            return

        action = self._actions.pop(source_index)
        wrapper = self._wrappers.pop(source_index)
        insert_pos = destination_index - 1 if destination_index > source_index \
            else destination_index
        self._actions.insert(insert_pos, action)
        self._wrappers.insert(insert_pos, wrapper)
        self.endMoveRows()

    def _create_action_model(self, action: macro.AbstractAction) -> AbstractActionModel:
        """Returns the action model corresponding to the given action.

        Args:
            action: The action to return the model for.

        Returns:
            QML model instance for the given action instance.
        """
        return MacroModel.model_lookup[action.tag](action, self)


class MacroModel(ActionModel):

    # Signal emitted when the description variable's content changes
    changed = QtCore.Signal()
    recordingChanged = QtCore.Signal()

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
            data:  AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)
        self._action_list_model = ActionListModel(cast(MacroData, data).actions, self)
        self._recorder = MacroRecorder(self._action_list_model.append)

        self._events_to_record: list[InputType] = [
            InputType.to_enum(s)
            for s in Configuration().value("action", "macro", "record-event-types")
        ]
        self._record_timings: bool = Configuration().value(
            "action", "macro", "record-timings")

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:macro/MacroAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @QtCore.Slot(str)
    def addAction(self, name: str) -> None:
        self._action_list_model.append(self.action_lookup[name]())
        self.changed.emit()

    @QtCore.Slot(int)
    def removeAction(self, index: int) -> None:
        self._action_list_model.remove(index)
        self.changed.emit()

    @QtCore.Slot(int, int, str)
    def dropCallback(
        self,
        target_index: int,
        source_index: int,
        mode: str
    ) -> None:
        match mode:
            case "append":
                self._action_list_model.move_from_to(source_index, target_index + 1)
            case "prepend":
                self._action_list_model.move_from_to(source_index, 0)
            case _:
                raise GremlinError(f"Macro: Invalid insertion mode '{mode}'")
        self.changed.emit()

    @QtCore.Slot()
    def startRecording(self) -> None:
        if not self._recorder.is_recording:
            self._recorder.start(self._events_to_record, self._record_timings)
            self.recordingChanged.emit()

    @QtCore.Slot()
    def stopRecording(self) -> None:
        if self._recorder.is_recording:
            self._recorder.stop()
            self.recordingChanged.emit()

    def _get_record_event(self, event_type: InputType) -> bool:
        return event_type in self._events_to_record

    def _set_record_event(
        self, event_types: InputType | tuple[InputType, ...], value: bool
    ) -> None:
        types = event_types if isinstance(event_types, tuple) else (event_types,)
        if any((event_type in self._events_to_record) != value for event_type in types):
            if value:
                for event_type in types:
                    if event_type not in self._events_to_record:
                        self._events_to_record.append(event_type)
            else:
                self._events_to_record = [
                    event_type for event_type in self._events_to_record
                    if event_type not in types
                ]
            Configuration().set(
                "action", "macro", "record-event-types",
                [InputType.to_string(t) for t in self._events_to_record]
            )
            self.recordingChanged.emit()

    def _get_record_timings(self) -> bool:
        return self._record_timings

    def _set_record_timings(self, value: bool) -> None:
        if value != self._record_timings:
            self._record_timings = value
            Configuration().set("action", "macro", "record-timings", value)
            self.recordingChanged.emit()

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

    actions = QtCore.Property(
        QtCore.QObject,
        fget=lambda self: self._action_list_model,
        constant=True,
    )

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

    isRecording = QtCore.Property(
        bool,
        fget=lambda self: self._recorder.is_recording,
        notify=recordingChanged
    )
    recordKeyboard = QtCore.Property(
        bool,
        fget=lambda self: self._get_record_event(InputType.Keyboard),
        fset=lambda self, value: self._set_record_event(InputType.Keyboard, value),
        notify=recordingChanged
    )
    recordMouse = QtCore.Property(
        bool,
        fget=lambda self: self._get_record_event(InputType.Mouse),
        fset=lambda self, value: self._set_record_event(InputType.Mouse, value),
        notify=recordingChanged
    )
    recordJoystickButton = QtCore.Property(
        bool,
        fget=lambda self: self._get_record_event(InputType.JoystickButton),
        fset=lambda self, value: self._set_record_event(
            InputType.JoystickButton, value
        ),
        notify=recordingChanged
    )
    recordJoystickAxis = QtCore.Property(
        bool,
        fget=lambda self: self._get_record_event(InputType.JoystickAxis),
        fset=lambda self, value: self._set_record_event(InputType.JoystickAxis, value),
        notify=recordingChanged
    )
    recordJoystickHat = QtCore.Property(
        bool,
        fget=lambda self: self._get_record_event(InputType.JoystickHat),
        fset=lambda self, value: self._set_record_event(InputType.JoystickHat, value),
        notify=recordingChanged
    )
    recordTimings = QtCore.Property(
        bool,
        fget=_get_record_timings,
        fset=_set_record_timings,
        notify=recordingChanged
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

Configuration().register(
    "action",
    "macro",
    "axis-minimum-change-amount",
    PropertyType.Float,
    0.05,
    "Minimum amount of change required for a joystick axis event to be recorded "
    "during macro recording.",
    {
        "min": 0.0,
        "max": 1.0
    },
    True
)

Configuration().register(
    "action",
    "macro",
    "axis-minimum-time-interval",
    PropertyType.Float,
    0.01,
    "Minimum time in seconds between subsequent axis events of the same input in order "
    "to record a new macro action.",
    {
        "min": 0.0,
        "max": 100.0
    },
    True
)

Configuration().register(
    "action",
    "macro",
    "record-event-types",
    PropertyType.List,
    ["axis", "button", "hat"],
    "Input event types recorded during macro recording.",
    {},
    False
)

Configuration().register(
    "action",
    "macro",
    "record-timings",
    PropertyType.Bool,
    False,
    "Whether to record timing pauses between inputs during macro recording.",
    {},
    False
)
