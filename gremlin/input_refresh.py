# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from gremlin import (
    device_initialization,
    event_handler,
    input_cache,
    logical_device,
    mode_manager,
)
from gremlin.types import (
    Event,
    InputType,
)


class RefreshPhysicalInputs:
    """Emits input events using cached device information to trigger Gremlin
    action execution."""

    @classmethod
    def refresh_axes(cls) -> None:
        """Refreshes input and logical device axes using cached values."""
        cache = input_cache.Joystick()
        listener = event_handler.EventListener()
        modes = mode_manager.ModeManager()
        for dev in device_initialization.input_devices():
            joy = cache[dev.device_guid.uuid]
            for index in range(joy.axis_count):
                axis_id = dev.axis_map[index].axis_index
                listener.joystick_event.emit(
                    Event(
                        event_type=InputType.JoystickAxis,
                        device_guid=dev.device_guid.uuid,
                        identifier=axis_id,
                        mode=modes.current.name,
                        value=joy.axis(axis_id).value,
                    )
                )

        logical = logical_device.LogicalDevice()
        for axis in logical.inputs_of_type([InputType.JoystickAxis]):
            listener.joystick_event.emit(
                Event(
                    event_type=InputType.JoystickAxis,
                    device_guid=logical.device_guid,
                    identifier=axis.id,
                    mode=modes.current.name,
                    value=axis.value,
                )
            )
