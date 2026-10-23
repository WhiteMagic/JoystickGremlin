# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import uuid

from action_plugins.map_to_logical_device import (
    MapToLogicalDeviceData,
    MapToLogicalDeviceFunctor,
)
from gremlin.base_classes import Value
from gremlin.logical_device import LogicalDevice
from gremlin.types import Event, InputType


def test_reset_turns_inverted_logical_button_off() -> None:
    logical = LogicalDevice()
    logical.reset()
    action = MapToLogicalDeviceData(InputType.JoystickButton)
    action.button_inverted = True
    functor = MapToLogicalDeviceFunctor(action)
    button = logical.inputs_of_type([InputType.JoystickButton])[0]
    release = Event(
        event_type=InputType.JoystickButton,
        identifier=1,
        device_guid=uuid.uuid4(),
        mode="Default",
        is_pressed=False,
    )

    try:
        functor(release, Value(False))
        assert button.is_pressed
        functor.reset()
        assert not button.is_pressed
    finally:
        logical.reset()
