# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import itertools
import logging
import threading
import time
import uuid
from abc import (
    ABC,
    abstractmethod,
)
from collections.abc import Callable
from typing import override
from xml.etree import ElementTree

import dill
from gremlin import (
    device_initialization,
    error,
    event_handler,
    mode_manager,
    sendinput,
    util,
)
from gremlin.common import SingletonMetaclass
from gremlin.config import Configuration
from gremlin.keyboard import (
    Key,
    key_from_code,
    key_from_name,
    send_key_down,
    send_key_up,
)
from gremlin.logical_device import LogicalDevice
from gremlin.types import (
    AxisMode,
    Event,
    HatDirection,
    InputType,
    MouseButton,
    PropertyType,
)
from vjoy.vjoy import VJoyProxy

# Seconds macro sequences get to finish their current repetition when the manager stops.
STOP_GRACE_PERIOD = 1.0


def _preempts_others(macro: Macro) -> bool:
    """Returns whether the macro pauses all other macros while it executes.

    Args:
        macro: the macro to check

    Returns:
        True if the macro is exclusive and preemptive
    """
    return macro.is_exclusive and macro.is_preempting


def _with_default_pauses(
    sequence: list[AbstractAction], delay: float
) -> list[AbstractAction]:
    """Returns the sequence with a pause between consecutive non-pause actions.

    Args:
        sequence: the actions of a macro
        delay: duration in seconds of the inserted pauses

    Returns:
        Copy of the sequence including the inserted pauses
    """
    with_added_pauses: list[AbstractAction] = []
    for current_action, next_action in itertools.pairwise(sequence):
        with_added_pauses.append(current_action)
        if not isinstance(current_action, PauseAction) and not isinstance(
            next_action, PauseAction
        ):
            with_added_pauses.append(PauseAction(delay))
    with_added_pauses.extend(sequence[-1:])
    return with_added_pauses


class MacroExecution:
    """A single execution of a macro, from being triggered until it ends."""

    def __init__(self, macro: Macro, execute: Callable[[MacroExecution], None]) -> None:
        """Creates a new macro execution that has not started yet.

        Args:
            macro: the macro to execute
            execute: function performing the execution on its own thread
        """
        self.macro = macro
        # Ends the execution after its current repetition.
        self.stop_requested = threading.Event()
        # Aborts the execution as soon as possible.
        self.abort_requested = threading.Event()
        self.thread = threading.Thread(target=execute, args=(self,), daemon=True)

    def request_abort(self) -> None:
        """Ends the execution before its next action."""
        self.abort_requested.set()
        self.stop_requested.set()


class MacroManager(metaclass=SingletonMetaclass):
    """Manages the proper dispatching and scheduling of macros.

    Commands arrive on the event handling thread and only change the bookkeeping. Each
    macro executes in its own thread.
    """

    def __init__(self) -> None:
        """Initializes the instance."""
        # Guards all bookkeeping, executions also wait on it while being preempted.
        self._condition = threading.Condition()
        self._waiting_macros: list[MacroExecution] = []
        self._running_macros: dict[int, MacroExecution] = {}
        self._is_running = False

    def start(self) -> None:
        """Starts accepting macros."""
        with self._condition:
            self._is_running = True

    def stop(self) -> None:
        """Stops all macros.

        Running macros get a grace period to finish their current repetition before
        being aborted.
        """
        with self._condition:
            self._is_running = False
            self._waiting_macros.clear()
            running_macros = list(self._running_macros.values())
            for macro in running_macros:
                macro.stop_requested.set()
        self._join(running_macros)

        with self._condition:
            for macro in running_macros:
                macro.request_abort()
            self._condition.notify_all()
        self._join(running_macros)

        for macro in running_macros:
            if macro.thread.is_alive():
                logging.getLogger("system").warning(
                    f"Macro {macro.macro.id} did not stop in time."
                )
        with self._condition:
            self._running_macros.clear()

    def run_macro(self, macro: Macro) -> None:
        """Triggers an execution of the macro.

        Every trigger results in an execution, except for an already active hold macro.

        Args:
            macro: the macro to execute
        """
        with self._condition:
            is_ignored = isinstance(macro.repeat, HoldRepeat) and self._is_active(macro)
            if self._is_running and not is_ignored:
                self._waiting_macros.append(MacroExecution(macro, self._execute))
                self._dispatch_waiting()

    def stop_macro(self, macro: Macro) -> None:
        """Ends the macro after its current repetition and drops its waiting executions.

        Args:
            macro: the macro to stop
        """
        with self._condition:
            self._stop(macro)
            self._dispatch_waiting()

    def toggle_macro(self, macro: Macro) -> None:
        """Stops the macro if it is active and triggers an execution of it otherwise.

        Args:
            macro: the macro to toggle
        """
        with self._condition:
            if self._is_active(macro):
                self._stop(macro)
            elif self._is_running:
                self._waiting_macros.append(MacroExecution(macro, self._execute))
            self._dispatch_waiting()

    def _is_active(self, macro: Macro) -> bool:
        """Returns whether the macro waits to start or executes without a stop request.

        Args:
            macro: the macro to check

        Returns:
            True if the macro is active from the user's point of view
        """
        execution = self._running_macros.get(macro.id)
        is_waiting = any(waiting.macro is macro for waiting in self._waiting_macros)
        return is_waiting or (
            execution is not None and not execution.stop_requested.is_set()
        )

    def _stop(self, macro: Macro) -> None:
        """Drops waiting executions of the macro and requests its running one to stop.

        Args:
            macro: the macro to stop
        """
        self._waiting_macros = [
            execution
            for execution in self._waiting_macros
            if execution.macro is not macro
        ]
        execution = self._running_macros.get(macro.id)
        if execution is not None:
            execution.stop_requested.set()

    def _dispatch_waiting(self) -> None:
        """Starts every waiting execution taking ordering and exclusivity rules into
        account.

        Executions of one macro start in order, everything queued behind an exclusive
        macro waits. Requires the lock to be held.
        """
        is_behind_exclusive = False
        still_waiting = []
        for execution in self._waiting_macros:
            if self._can_start(execution, is_behind_exclusive):
                self._running_macros[execution.macro.id] = execution
                execution.thread.start()
            else:
                still_waiting.append(execution)
            is_behind_exclusive = is_behind_exclusive or execution.macro.is_exclusive
        self._waiting_macros = still_waiting

    def _can_start(self, execution: MacroExecution, is_behind_exclusive: bool) -> bool:
        """Returns whether the waiting execution may start now.

        Args:
            execution: the waiting execution to check
            is_behind_exclusive: True if an exclusive execution waits ahead of this one

        Returns:
            True if the execution may start
        """
        running_macros = [other.macro for other in self._running_macros.values()]
        is_free = execution.macro.id not in self._running_macros
        if _preempts_others(execution.macro):
            return is_free and not any(
                _preempts_others(running_macro) for running_macro in running_macros
            )
        if execution.macro.is_exclusive:
            return is_free and len(running_macros) == 0
        return (
            is_free
            and not is_behind_exclusive
            and not any(running_macro.is_exclusive for running_macro in running_macros)
        )

    def _execute(self, execution: MacroExecution) -> None:
        """Executes the macro's repetitions, called on the execution's thread.

        Args:
            execution: the execution to perform
        """
        try:
            sequence = _with_default_pauses(
                execution.macro.sequence,
                Configuration().value("action", "macro", "default-delay"),
            )
            repeat = execution.macro.repeat
            match repeat:
                case CountRepeat():
                    limit = repeat.count
                case HoldRepeat() | ToggleRepeat():
                    limit = None
                case _:
                    limit = 1
            delay = repeat.delay if repeat is not None else 0.0

            repetition = 0
            while limit is None or repetition < limit:
                if repetition > 0 and execution.stop_requested.wait(delay):
                    break
                self._execute_sequence(execution, sequence)
                repetition += 1
        finally:
            with self._condition:
                if self._running_macros.get(execution.macro.id) is execution:
                    del self._running_macros[execution.macro.id]
                self._condition.notify_all()
                self._dispatch_waiting()

    def _execute_sequence(
        self, execution: MacroExecution, sequence: list[AbstractAction]
    ) -> None:
        """Executes one repetition of the sequence.

        Args:
            execution: the execution the sequence belongs to
            sequence: the actions to execute
        """
        for action in sequence:
            self._wait_while_preempted(execution)
            if execution.abort_requested.is_set():
                break
            if isinstance(action, PauseAction):
                execution.abort_requested.wait(action.duration)
            else:
                action()

    def _wait_while_preempted(self, execution: MacroExecution) -> None:
        """Blocks while a different macro executes preemptively.

        Args:
            execution: the execution whose thread calls this method
        """
        with self._condition:
            self._condition.wait_for(
                lambda: (
                    execution.abort_requested.is_set()
                    or _preempts_others(execution.macro)
                    or not any(
                        _preempts_others(other.macro)
                        for other in self._running_macros.values()
                    )
                )
            )

    def _join(self, executions: list[MacroExecution]) -> None:
        """Waits up to the grace period for the executions' threads to end.

        Args:
            executions: the executions to wait for
        """
        deadline = time.monotonic() + STOP_GRACE_PERIOD
        for execution in executions:
            execution.thread.join(max(0.0, deadline - time.monotonic()))


class Macro:
    """Represents a macro which can be executed."""

    # Unique identifier for each macro
    _next_macro_id = 0

    def __init__(self) -> None:
        """Creates a new macro instance."""
        self._sequence: list[AbstractAction] = []
        self._id = Macro._next_macro_id
        Macro._next_macro_id += 1
        self.repeat: AbstractRepeat | None = None
        self.is_exclusive = False
        self.is_preempting = False

    @property
    def id(self) -> int:
        """Returns the unique id of this macro.

        Returns:
            unique id of this macro
        """
        return self._id

    @property
    def sequence(self) -> list[AbstractAction]:
        """Returns the action sequence of this macro.

        Returns:
            Sequence of actions comprising the macro
        """
        return self._sequence

    def add_action(self, action: AbstractAction) -> None:
        """Adds an action to the list of actions to perform.

        Args:
            action: the action to add
        """
        self._sequence.append(action)

    def pause(self, duration: float) -> None:
        """Adds a pause of the given duration to the macro.

        Args:
            duration: the duration of the pause in seconds
        """
        self._sequence.append(PauseAction(duration))

    def press(self, key: Key) -> None:
        """Presses the specified key down.

        Args:
            key: the key to press
        """
        self.action(key, True)

    def release(self, key: Key) -> None:
        """Releases the specified key.

        Args:
            key; the key to release
        """
        self.action(key, False)

    def tap(self, key: Key) -> None:
        """Taps the specified key.

        Args:
            key: the key to tap
        """
        self.action(key, True)
        self.action(key, False)

    def action(self, key: Key | str, is_pressed: bool) -> None:
        """Adds the specified action to the sequence.

        Args:
            key: the key involved in the action
            is_pressed: boolean indicating if the key is pressed
                (True) or released (False)
        """
        if isinstance(key, str):
            key = key_from_name(key)
        elif isinstance(key, Key):
            pass
        else:
            raise error.KeyboardError("Invalid key specified")

        self._sequence.append(KeyAction(key, is_pressed))


class AbstractAction(ABC):
    """Base class for all macro action."""

    @abstractmethod
    def __call__(self) -> None:
        pass

    @classmethod
    @abstractmethod
    def create(cls) -> AbstractAction:
        """Creates an empty, likely invalid instance, of the action."""

    @abstractmethod
    def to_xml(self) -> ElementTree.Element:
        pass

    @abstractmethod
    def from_xml(self, node: ElementTree.Element) -> None:
        pass

    @abstractmethod
    def is_valid() -> bool:
        pass

    def _create_node(self, type_name: str) -> ElementTree.Element:
        """Creates an action node of the given type.

        Args:
            type_name: name of the type of this action node

        Returns:
            An action node typed as request
        """
        node = ElementTree.Element("macro-action")
        node.set("type", type_name)
        return node

    def swap_uuid(self, old_uuid: uuid.UUID, new_uuid: uuid.UUID) -> bool:
        """Swaps occurrences of the old UUID with the new one for this action."""
        return False


class JoystickAction(AbstractAction):
    """Joystick input action for a macro."""

    tag = "joystick"

    def __init__(
        self,
        device_guid: uuid.UUID,
        input_type: InputType,
        input_id: int | uuid.UUID,
        value: bool | float | tuple[int, int],
        axis_mode: AxisMode = AxisMode.Absolute,
    ) -> None:
        """Creates a new JoystickAction instance for use in a macro.

        Args:
            device_guid: GUID of the device generating the input
            input_type: type of input being generated
            input_id: id of the input being generated
            value: the value of the generated input
            axis_mode: if an axis is used, how to interpret the value
        """
        self.device_guid = device_guid
        self.input_type = input_type
        self.input_id = input_id
        self.value = value
        self.axis_mode = axis_mode

    @classmethod
    def create(cls) -> JoystickAction:
        return JoystickAction(dill.UUID_Invalid, InputType.JoystickButton, 0, True)

    def __call__(self) -> None:
        """Emits an Event instance through the EventListener system."""
        el = event_handler.EventListener()
        if self.input_type == InputType.JoystickAxis:
            event = Event(
                event_type=self.input_type,
                device_guid=self.device_guid,
                identifier=self.input_id,
                mode=mode_manager.ModeManager().current.name,
                value=self.value,
            )
        elif self.input_type == InputType.JoystickButton:
            event = Event(
                event_type=self.input_type,
                device_guid=self.device_guid,
                identifier=self.input_id,
                mode=mode_manager.ModeManager().current.name,
                is_pressed=self.value,
            )
        elif self.input_type == InputType.JoystickHat:
            event = Event(
                event_type=self.input_type,
                device_guid=self.device_guid,
                identifier=self.input_id,
                mode=mode_manager.ModeManager().current.name,
                value=self.value,
            )

        el.joystick_event.emit(event)

    def to_xml(self) -> ElementTree.Element:
        node = self._create_node(self.tag)
        util.append_property_nodes(
            node,
            [
                ["device-guid", self.device_guid, PropertyType.UUID],
                ["input-type", self.input_type, PropertyType.InputType],
                ["input-id", self.input_id, PropertyType.Int],
            ],
        )
        if self.input_type == InputType.JoystickAxis:
            util.append_property_nodes(
                node,
                [
                    ["value", self.value, PropertyType.Float],
                    ["axis-mode", self.axis_mode, PropertyType.AxisMode],
                ],
            )
        elif self.input_type == InputType.JoystickButton:
            node.append(
                util.create_property_node("value", self.value, PropertyType.Bool)
            )
        elif self.input_type == InputType.JoystickHat:
            node.append(
                util.create_property_node(
                    "value", self.value, PropertyType.HatDirection
                )
            )
        return node

    def from_xml(self, node: ElementTree.Element) -> None:
        self.device_guid = util.read_property(node, "device-guid", PropertyType.UUID)
        self.input_type = util.read_property(node, "input-type", PropertyType.InputType)
        self.input_id = util.read_property(node, "input-id", PropertyType.Int)
        if self.input_type == InputType.JoystickAxis:
            self.value = util.read_property(node, "value", PropertyType.Float)
            self.axis_mode = util.read_property(
                node, "axis-mode", PropertyType.AxisMode
            )
        elif self.input_type == InputType.JoystickButton:
            self.value = util.read_property(node, "value", PropertyType.Bool)
        elif self.input_type == InputType.JoystickHat:
            self.value = util.read_property(node, "value", PropertyType.HatDirection)

    def is_valid(self) -> bool:
        return self.device_guid != dill.UUID_Invalid

    @override
    def swap_uuid(self, old_uuid: uuid.UUID, new_uuid: uuid.UUID) -> bool:
        if self.device_guid == old_uuid:
            self.device_guid = new_uuid
            return True
        return False


class KeyAction(AbstractAction):
    """Key to press or release by a macro."""

    tag = "key"

    def __init__(self, key: Key | None, is_pressed: bool) -> None:
        """Creates a new KeyAction object for use in a macro.

        Args:
            key: the key to use in the action
            is_pressed: True if the key should be pressed, False otherwise
        """
        if not (isinstance(key, Key) or key is None):
            raise error.KeyboardError("Invalid Key instance provided")

        self.key = key
        self.is_pressed = is_pressed

    @classmethod
    def create(cls) -> KeyAction:
        return KeyAction(None, True)

    def __call__(self) -> None:
        if self.key is None:
            return

        if self.is_pressed:
            send_key_down(self.key)
        else:
            send_key_up(self.key)

    def to_xml(self) -> ElementTree.Element:
        node = self._create_node(self.tag)
        util.append_property_nodes(
            node,
            [
                ["scan-code", self.key.scan_code, PropertyType.Int],
                ["is-extended", self.key.is_extended, PropertyType.Bool],
                ["is-pressed", self.is_pressed, PropertyType.Bool],
            ],
        )
        return node

    def from_xml(self, node: ElementTree.Element) -> None:
        self.key = key_from_code(
            util.read_property(node, "scan-code", PropertyType.Int),
            util.read_property(node, "is-extended", PropertyType.Bool),
        )
        self.is_pressed = util.read_property(node, "is-pressed", PropertyType.Bool)

    def is_valid(self) -> bool:
        return self.key is not None


class LogicalDeviceAction(AbstractAction):
    """Logical device input action."""

    tag = "logical-device"

    def __init__(
        self,
        input_type: InputType,
        input_id: int,
        value: bool | float | tuple[int, int],
        axis_mode: AxisMode = AxisMode.Absolute,
    ) -> None:
        """Creates a new LogicalDeviceAction instance for use in a macro.

        Args:
            input_type: type of input being generated
            input_id: id of the input being generated
            value: the value of the generated input
            axis_mode: if an axis is used, how to interpret the value
        """
        self.input_type = input_type
        self.input_id = input_id
        self.value = value
        self.axis_mode = axis_mode
        self._event_listener = event_handler.EventListener()
        self._mode_manager = mode_manager.ModeManager()

    @classmethod
    def create(cls) -> LogicalDeviceAction:
        if len(LogicalDevice().inputs_of_type()) == 0:
            LogicalDevice().create(InputType.JoystickButton)
        first_input = LogicalDevice().inputs_of_type()[0]
        return LogicalDeviceAction(
            first_input.type,
            first_input.id,
            True
            if first_input.type == InputType.JoystickButton
            else first_input._value,
        )

    def __call__(self) -> None:
        ld = LogicalDevice()[
            LogicalDevice.Input.Identifier(self.input_type, self.input_id)
        ]
        # Update the state of the logical device and then emit the corresponding
        # event to trigger further processing.
        value = None
        match self.input_type:
            case InputType.JoystickAxis:
                if self.axis_mode == AxisMode.Absolute:
                    ld.update(self.value)
                elif self.axis_mode == AxisMode.Relative:
                    ld.update(max(-1.0, min(1.0, ld.value + self.value)))
                value = ld.value
            case InputType.JoystickButton:
                ld.update(self.value)
            case InputType.JoystickHat:
                ld.update(self.value)
                value = ld.direction

        is_pressed = (
            ld.is_pressed if self.input_type == InputType.JoystickButton else None
        )

        self._event_listener.joystick_event.emit(
            Event(
                event_type=self.input_type,
                identifier=self.input_id,
                device_guid=LogicalDevice.device_guid,
                mode=self._mode_manager.current.name,
                value=value,
                is_pressed=is_pressed,
                raw_value=value,
            )
        )

    def to_xml(self) -> ElementTree.Element:
        node = self._create_node(self.tag)
        util.append_property_nodes(
            node,
            [
                ["input-type", self.input_type, PropertyType.InputType],
                ["input-id", self.input_id, PropertyType.Int],
            ],
        )
        if self.input_type == InputType.JoystickAxis:
            util.append_property_nodes(
                node,
                [
                    ["value", self.value, PropertyType.Float],
                    ["axis-mode", self.axis_mode, PropertyType.AxisMode],
                ],
            )
        elif self.input_type == InputType.JoystickButton:
            node.append(
                util.create_property_node("value", self.value, PropertyType.Bool)
            )
        elif self.input_type == InputType.JoystickHat:
            node.append(
                util.create_property_node(
                    "value", self.value, PropertyType.HatDirection
                )
            )
        return node

    def from_xml(self, node: ElementTree.Element) -> None:
        self.input_type = util.read_property(node, "input-type", PropertyType.InputType)
        self.input_id = util.read_property(node, "input-id", PropertyType.Int)
        if self.input_type == InputType.JoystickAxis:
            self.value = util.read_property(node, "value", PropertyType.Float)
            self.axis_mode = util.read_property(
                node, "axis-mode", PropertyType.AxisMode
            )
        elif self.input_type == InputType.JoystickButton:
            self.value = util.read_property(node, "value", PropertyType.Bool)
        elif self.input_type == InputType.JoystickHat:
            self.value = util.read_property(node, "value", PropertyType.HatDirection)

    def is_valid(self) -> bool:
        return True


class MouseButtonAction(AbstractAction):
    """Mouse button action."""

    tag = "mouse-button"

    def __init__(self, button: MouseButton, is_pressed: bool) -> None:
        """Creates a new MouseButtonAction object for use in a macro.

        Args:
            button: the button to use in the action
            is_pressed: True if the button should be pressed, False otherwise
        """
        if not isinstance(button, MouseButton):
            raise error.MouseError("Invalid mouse button provided")

        self.button = button
        self.is_pressed = is_pressed

    @classmethod
    def create(cls) -> MouseButtonAction:
        return MouseButtonAction(MouseButton.Left, True)

    def __call__(self) -> None:
        if self.button == MouseButton.WheelDown:
            sendinput.mouse_wheel(1)
        elif self.button == MouseButton.WheelUp:
            sendinput.mouse_wheel(-1)
        else:
            if self.is_pressed:
                sendinput.mouse_press(self.button)
            else:
                sendinput.mouse_release(self.button)

    def to_xml(self) -> ElementTree.Element:
        node = self._create_node(self.tag)
        util.append_property_nodes(
            node,
            [
                ["button", MouseButton.to_string(self.button), PropertyType.String],
                ["is-pressed", self.is_pressed, PropertyType.Bool],
            ],
        )
        return node

    def from_xml(self, node: ElementTree.Element) -> None:
        self.button = MouseButton.to_enum(
            util.read_property(node, "button", PropertyType.String)
        )
        self.is_pressed = util.read_property(node, "is-pressed", PropertyType.Bool)

    def is_valid(self) -> bool:
        return self.button is not None


class MouseMotionAction(AbstractAction):
    """Mouse motion action."""

    tag = "mouse-motion"

    def __init__(self, dx: float, dy: float) -> None:
        """Creates a new MouseMotionAction object for use in a macro.

        Args:
            dx: change along the X axis
            dy: change along the Y axis
        """
        self.dx = int(dx)
        self.dy = int(dy)

    @classmethod
    def create(cls) -> MouseMotionAction:
        return MouseMotionAction(0, 0)

    def __call__(self) -> None:
        sendinput.mouse_relative_motion(self.dx, self.dy)

    def to_xml(self) -> ElementTree.Element:
        node = self._create_node(self.tag)
        util.append_property_nodes(
            node,
            [
                ["dx", self.dx, PropertyType.Int],
                ["dy", self.dy, PropertyType.Int],
            ],
        )
        return node

    def from_xml(self, node: ElementTree.Element) -> None:
        self.dx = util.read_property(node, "dx", PropertyType.Int)
        self.dy = util.read_property(node, "dy", PropertyType.Int)

    def is_valid(self) -> bool:
        return True


class PauseAction(AbstractAction):
    """Represents the pause in a macro between pressed."""

    tag = "pause"

    def __init__(self, duration: float) -> None:
        """Creates a new Pause object for use in a macro.

        Args:
            duration: the duration in seconds of the pause
        """
        self.duration = duration

    @classmethod
    def create(cls) -> PauseAction:
        return PauseAction(0.0)

    def __call__(self) -> None:
        time.sleep(self.duration)

    def to_xml(self) -> ElementTree.Element:
        node = self._create_node(self.tag)
        node.append(
            util.create_property_node("duration", self.duration, PropertyType.Float)
        )
        return node

    def from_xml(self, node: ElementTree.Element) -> None:
        self.duration = util.read_property(node, "duration", PropertyType.Float)

    def is_valid(self) -> bool:
        return True


class VJoyAction(AbstractAction):
    """VJoy input action for a macro."""

    tag = "vjoy"

    def __init__(
        self,
        vjoy_id: int,
        input_type: InputType,
        input_id: int,
        value: bool | float | tuple[int, int],
        axis_mode: AxisMode = AxisMode.Absolute,
    ) -> None:
        """Creates a new VJoyAction instance for use in a macro.

        Args:
            vjoy_id: id of the vjoy device which is to be modified
            input_type: type of input being generated
            input_id: id of the input being generated
            value: the value of the generated input
            axis_type: if an axis is used, how to interpret the value
        """
        self.vjoy_id = vjoy_id
        self.input_type = input_type
        self.input_id = input_id
        self.value = value
        self.axis_mode = axis_mode

    @classmethod
    def create(cls) -> VJoyAction:
        # Attempt to find a valid vJoy input.
        choice = util.first_available_input(
            device_initialization.output_vjoy_devices(),
            [InputType.JoystickButton, InputType.JoystickAxis, InputType.JoystickHat],
        )
        if choice is None:
            raise error.GremlinError("No vJoy device with usable outputs is available")

        device, input_type, input_id = choice
        default_value = {
            InputType.JoystickAxis: 0.0,
            InputType.JoystickButton: True,
            InputType.JoystickHat: HatDirection.Center,
        }[input_type]
        return VJoyAction(device.vjoy_id, input_type, input_id, default_value)

    def __call__(self) -> None:
        try:
            vjoy = VJoyProxy()[self.vjoy_id]
            if self.input_type == InputType.JoystickAxis:
                if self.axis_mode == AxisMode.Absolute:
                    vjoy.axis(self.input_id).value = self.value
                elif self.axis_mode == AxisMode.Relative:
                    vjoy.axis(self.input_id).value = max(
                        -1.0, min(1.0, vjoy.axis(self.input_id).value + self.value)
                    )
            elif self.input_type == InputType.JoystickButton:
                vjoy.button(self.input_id).is_pressed = self.value
            elif self.input_type == InputType.JoystickHat:
                vjoy.hat(self.input_id).direction = self.value
        except Exception as e:  # noqa: BLE001
            logging.getLogger("event").error(
                f"Failed to execute vJoy macro entry due to: {e}"
            )

    def to_xml(self) -> ElementTree.Element:
        node = self._create_node(self.tag)
        util.append_property_nodes(
            node,
            [
                ["vjoy-id", self.vjoy_id, PropertyType.Int],
                ["input-type", self.input_type, PropertyType.InputType],
                ["input-id", self.input_id, PropertyType.Int],
            ],
        )
        if self.input_type == InputType.JoystickAxis:
            util.append_property_nodes(
                node,
                [
                    ["value", self.value, PropertyType.Float],
                    ["axis-mode", self.axis_mode, PropertyType.AxisMode],
                ],
            )
        elif self.input_type == InputType.JoystickButton:
            node.append(
                util.create_property_node("value", self.value, PropertyType.Bool)
            )
        elif self.input_type == InputType.JoystickHat:
            node.append(
                util.create_property_node(
                    "value", self.value, PropertyType.HatDirection
                )
            )
        return node

    def from_xml(self, node: ElementTree.Element) -> None:
        self.vjoy_id = util.read_property(node, "vjoy-id", PropertyType.Int)
        self.input_type = util.read_property(node, "input-type", PropertyType.InputType)
        self.input_id = util.read_property(node, "input-id", PropertyType.Int)
        if self.input_type == InputType.JoystickAxis:
            self.value = util.read_property(node, "value", PropertyType.Float)
            self.axis_mode = util.read_property(
                node, "axis-mode", PropertyType.AxisMode
            )
        elif self.input_type == InputType.JoystickButton:
            self.value = util.read_property(node, "value", PropertyType.Bool)
        elif self.input_type == InputType.JoystickHat:
            self.value = util.read_property(node, "value", PropertyType.HatDirection)

    def is_valid(self) -> bool:
        return True


class AbstractRepeat(ABC):
    """Base class for all macro repeat modes."""

    def __init__(self, delay: float) -> None:
        """Creates a new instance.

        Args:
            delay the delay between repetitions
        """
        self.delay = delay

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the repeat information.

        Returns:
            XML node containing the instance's information
        """
        node = ElementTree.Element("repeat")
        node.append(util.create_property_node("delay", self.delay, PropertyType.Float))
        self._to_xml_additional(node)
        return node

    def from_xml(self, node: ElementTree.Element) -> None:
        """Populates the instance's data from the provided XML node.

        Args:
            node: XML node containing data with which to populate the instance
        """
        self.delay = util.read_property(node, "delay", PropertyType.Float)
        self._from_xml_additional(node)

    @abstractmethod
    def _to_xml_additional(self, node: ElementTree.Element) -> None:
        pass

    @abstractmethod
    def _from_xml_additional(self, node: ElementTree.Element) -> None:
        pass


class CountRepeat(AbstractRepeat):
    """Repeat mode which repeats the macro a fixed number of times."""

    def __init__(self, count: int = 1, delay: float = 0.1) -> None:
        """Creates a new instance.

        Args:
            count: the number of times to repeat the macro
            delay: the delay between repetitions
        """
        super().__init__(delay)
        self.count = count

    def _to_xml_additional(self, node: ElementTree.Element) -> None:
        """Returns an XML node encoding the repeat information.

        Args:
            node: XML node containing the instance's information
        """
        node.set("type", "count")
        node.append(util.create_property_node("count", self.count, PropertyType.Int))

    def _from_xml_additional(self, node: ElementTree.Element) -> None:
        """Populates the instance's data from the provided XML node.

        Args:
            node: XML node containing data with which to populate the instance
        """
        self.count = util.read_property(node, "count", PropertyType.Int)


class ToggleRepeat(AbstractRepeat):
    """Repeat mode which repeats the macro as long as it hasn't been toggled
    off again after being toggled on."""

    def __init__(self, delay: float = 0.1) -> None:
        """Creates a new instance.

        Args:
            delay the delay between repetitions
        """
        super().__init__(delay)

    def _to_xml_additional(self, node: ElementTree.Element) -> None:
        """Returns an XML node encoding the repeat information.

        Args:
            node: XML node containing the instance's information
        """
        node.set("type", "toggle")

    def _from_xml_additional(self, node: ElementTree.Element) -> None:
        """Populates the instance's data from the provided XML node.

        Args:
            node: XML node containing data with which to populate the instance
        """


class HoldRepeat(AbstractRepeat):
    """Repeat mode which repeats the macro as long as the activation condition
    is being fulfilled or held down."""

    def __init__(self, delay: float = 0.1) -> None:
        """Creates a new instance.

        Args:
            delay the delay between repetitions
        """
        super().__init__(delay)

    def _to_xml_additional(self, node: ElementTree.Element) -> None:
        """Returns an XML node encoding the repeat information.

        Args:
            node: XML node containing the instance's information
        """
        node.set("type", "hold")

    def _from_xml_additional(self, node: ElementTree.Element) -> None:
        """Populates the instance's data from the provided XML node.

        Args:
            node XML node containing data with which to populate the instance
        """


Configuration().register(
    "action",
    "macro",
    "default-delay",
    PropertyType.Float,
    0.05,
    "The default time (in seconds) the macro system waits between emitting "
    + "subsequent actions when no pauses are present.",
    {"min": 0.0, "max": 10.0},
    True,
)
