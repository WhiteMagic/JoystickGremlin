# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import uuid
from collections.abc import Iterator

import pytest

from action_plugins.map_to_logical_device import (
    MapToLogicalDeviceData,
    MapToLogicalDeviceFunctor,
)
from gremlin.base_classes import Value
from gremlin.logical_device import LogicalDevice
from gremlin.types import (
    Event,
    InputType,
    ModeType,
)


@pytest.fixture(autouse=True)
def reset_logical() -> Iterator[None]:
    LogicalDevice().reset()
    yield
    LogicalDevice().reset()


def test_foreign_press_turns_inverted_logical_button_off() -> None:
    action = MapToLogicalDeviceData(InputType.JoystickButton)
    action.button_inverted = True
    functor = MapToLogicalDeviceFunctor(action)
    button = LogicalDevice()[
        LogicalDevice.Input.Identifier(
            InputType.JoystickButton, action.logical_input_id
        )
    ]
    release = Event(
        event_type=InputType.JoystickButton,
        identifier=1,
        device_guid=uuid.uuid4(),
        mode="Default",
        is_pressed=False,
    )
    press = release.clone()
    press.is_pressed = True

    assert functor(release, Value(False, ModeType.Native))
    assert button.is_pressed
    assert not functor(press, Value(True, ModeType.Foreign))
    assert not button.is_pressed
