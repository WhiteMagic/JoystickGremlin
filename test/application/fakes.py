# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import (
    dataclass,
    field,
)
from types import SimpleNamespace
from typing import ClassVar
from unittest import mock

import dill
from gremlin import (
    event_handler,
    keyboard,
    mode_manager,
    util,
    windows_event_hook,
)
from gremlin.logical_device import LogicalDevice
from gremlin.types import (
    AxisNames,
    Event,
    HatDirection,
    InputType,
    MouseButton,
)


def fake_physical_device(
    index: int, name: str, axes: list[AxisNames]
) -> dill.DeviceSummary:
    """Creates a physical device whose inputs all fit the input list unscrolled."""
    axis_map = (dill._AxisMap * 8)()
    for linear_index, axis in enumerate(axes, start=1):
        axis_map[linear_index - 1] = dill._AxisMap(
            linear_index=linear_index, axis_index=axis.value
        )
    return dill.DeviceSummary(
        dill._DeviceSummary(
            device_guid=dill._GUID(
                Data1=0x6A0E0000 + index,
                Data2=264,
                Data3=4592,
                Data4=(128, 4, 68, 69, 83, 84, 0, 0),
            ),
            vendor_id=0xBEEF,
            product_id=index,
            joystick_id=index + 1,
            name=name.encode(),
            axis_count=len(axes),
            button_count=8,
            hat_count=2,
            axis_map=axis_map,
        )
    )


STICK = fake_physical_device(
    1, "Gremlin Stick", [AxisNames.X, AxisNames.Y, AxisNames.Z, AxisNames.RX]
)
THROTTLE = fake_physical_device(
    2, "Gremlin Throttle", [AxisNames.X, AxisNames.Y, AxisNames.RY, AxisNames.SLIDER]
)


class FakeVJoyDevice:
    """Standin for a vJoy device, storing the state of every input separately."""

    def __init__(self) -> None:
        self._axes = defaultdict(lambda: SimpleNamespace(value=0.0))
        self._linear_axes = defaultdict(lambda: SimpleNamespace(value=0.0))
        self._buttons = defaultdict(lambda: SimpleNamespace(is_pressed=False))
        self._hats = defaultdict(lambda: SimpleNamespace(direction=HatDirection.Center))

    def axis(
        self, axis_id: int | None = None, linear_index: int | None = None
    ) -> SimpleNamespace:
        if axis_id is not None:
            return self._axes[axis_id]
        return self._linear_axes[linear_index]

    def button(self, button_id: int) -> SimpleNamespace:
        return self._buttons[button_id]

    def hat(self, hat_id: int) -> SimpleNamespace:
        return self._hats[hat_id]

    def is_owned(self) -> bool:
        return True


@dataclass
class Outputs:
    """Mock standins for every output that would leave the process."""

    key_down: mock.MagicMock
    key_up: mock.MagicMock
    send_input: mock.MagicMock
    audio: dict[str, mock.MagicMock]
    tts: dict[str, mock.MagicMock]
    start_detached: mock.MagicMock
    vjoy: dict[int, FakeVJoyDevice] = field(
        default_factory=lambda: {1: FakeVJoyDevice()}
    )

    def reset(self) -> None:
        self.vjoy.clear()
        self.vjoy[1] = FakeVJoyDevice()
        for output in [
            self.key_down,
            self.key_up,
            self.send_input,
            *self.audio.values(),
            *self.tts.values(),
            self.start_detached,
        ]:
            output.reset_mock()


class LogicalInjector:
    """Injects input through the logical device, as MapToLogicalDeviceFunctor does."""

    def axis(self, label: str, value: float) -> None:
        self._emit(label, value)

    def button(self, label: str, is_pressed: bool) -> None:
        self._emit(label, is_pressed)

    def hat(self, label: str, direction: HatDirection) -> None:
        self._emit(label, direction)

    def _emit(self, label: str, value: float | bool | HatDirection) -> None:
        logical_input = LogicalDevice()[label]
        logical_input.update(value)

        is_pressed = value if logical_input.type == InputType.JoystickButton else None
        event_value = None if logical_input.type == InputType.JoystickButton else value
        event = Event(
            event_type=logical_input.type,
            identifier=logical_input.id,
            device_guid=LogicalDevice.device_guid,
            mode=mode_manager.ModeManager().current.name,
            value=event_value,
            is_pressed=is_pressed,
            raw_value=value,
        )
        _raise_slot_exceptions(
            lambda: event_handler.EventListener().joystick_event.emit(event)
        )


class PhysicalInjector:
    """Injects joystick input through DILL's input event callback."""

    _raw_directions: ClassVar[dict[HatDirection, int]] = {
        direction: raw_value for raw_value, direction in util._dill_hat_lookup.items()
    }

    # DILL's input type codes, as read by dill.InputType.from_ctype.
    _axis_code = 1
    _button_code = 2
    _hat_code = 3

    def axis(self, device: dill.DeviceSummary, axis_index: int, value: float) -> None:
        self._emit(device, self._axis_code, axis_index, round(value * 32767))

    def button(
        self, device: dill.DeviceSummary, button_id: int, is_pressed: bool
    ) -> None:
        self._emit(device, self._button_code, button_id, int(is_pressed))

    def hat(
        self, device: dill.DeviceSummary, hat_id: int, direction: HatDirection
    ) -> None:
        self._emit(device, self._hat_code, hat_id, self._raw_directions[direction])

    def _emit(
        self,
        device: dill.DeviceSummary,
        type_code: int,
        input_index: int,
        raw_value: int,
    ) -> None:
        data = dill._JoystickInputData(
            device_guid=device.device_guid.ctypes,
            input_type=type_code,
            input_index=input_index,
            value=raw_value,
        )
        _call_from_input_thread(
            lambda: event_handler.EventListener()._joystick_event_handler(data)
        )


class KeyboardInjector:
    """Injects key events through the keyboard hook's callback."""

    def key(self, name: str, is_pressed: bool) -> None:
        key = keyboard.key_from_name(name)
        event = windows_event_hook.KeyEvent(
            scan_code=key.scan_code,
            is_extended=key.is_extended,
            is_pressed=is_pressed,
            is_injected=False,
        )
        _call_from_input_thread(
            lambda: event_handler.EventListener()._keyboard_handler(event)
        )


class MouseInjector:
    """Injects mouse button events through the mouse hook's callback."""

    def button(self, button: MouseButton, is_pressed: bool) -> None:
        event = windows_event_hook.MouseEvent(
            button_id=button, is_pressed=is_pressed, is_injected=False
        )
        _call_from_input_thread(
            lambda: event_handler.EventListener()._mouse_handler(event)
        )


def _call_from_input_thread(callback: Callable[[], object]) -> None:
    """Calls callback from outside the main thread, mirroring how real input events
    arrive."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(callback).result()


def _raise_slot_exceptions(emit: Callable[[], object]) -> None:
    """Calls emit and raises the first exception a connected slot raised."""
    captured: list[BaseException] = []
    original_hook = sys.excepthook
    sys.excepthook = lambda _type, exc_value, _traceback: captured.append(exc_value)
    try:
        emit()
    finally:
        sys.excepthook = original_hook
    if captured:
        raise captured[0]
