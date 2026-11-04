# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pytest

from gremlin import (
    device_initialization,
    event_handler,
    input_cache,
    shared_state,
)
from gremlin.input_refresh import RefreshPhysicalInputs
from gremlin.logical_device import LogicalDevice
from gremlin.types import Event, InputType


def test_refresh_emits_physical_axes_by_axis_index(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    device_uuid = device_initialization.physical_devices()[0].device_guid.uuid
    cached_joystick = input_cache.Joystick()[device_uuid]
    # Axis indices on the conftest device, which skip 4 and 5; axis 7 never moved.
    axis_values = {1: 0.25, 2: -0.5, 3: 0.75, 6: -0.25, 8: -0.75}
    for axis_id, value in axis_values.items():
        cached_joystick.axis(axis_id).update(value)

    def reset_axes() -> None:
        for axis_id in axis_values:
            cached_joystick.axis(axis_id).update(0.0)

    request.addfinalizer(reset_axes)
    monkeypatch.setattr(shared_state, "current_profile", None)
    LogicalDevice().reset()

    received: list[Event] = []

    def record(event: Event) -> None:
        received.append(event)

    signal = event_handler.EventListener().joystick_event
    signal.connect(record)
    try:
        RefreshPhysicalInputs.refresh_axes()
    finally:
        signal.disconnect(record)

    assert [
        (event.event_type, event.device_guid, event.identifier, event.value)
        for event in received
    ] == [
        (InputType.JoystickAxis, device_uuid, 1, 0.25),
        (InputType.JoystickAxis, device_uuid, 2, -0.5),
        (InputType.JoystickAxis, device_uuid, 3, 0.75),
        (InputType.JoystickAxis, device_uuid, 6, -0.25),
        (InputType.JoystickAxis, device_uuid, 7, 0.0),
        (InputType.JoystickAxis, device_uuid, 8, -0.75),
    ]
