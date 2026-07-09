# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import uuid

import dill
from gremlin.types import (
    AxisNames,
    InputType,
)


def joystick_label(device_guid: uuid.UUID, input_type: InputType, input_id: int) -> str:
    device = dill.DILL().get_device_information_by_guid(
        dill.GUID.from_uuid(device_guid)
    )
    label = f"{device.name}"
    if input_type == InputType.JoystickAxis:
        label += f" - {AxisNames.to_string(AxisNames(input_id))}"
    elif input_type == InputType.JoystickButton:
        label += f" - Button {input_id}"
    elif input_type == InputType.JoystickHat:
        label += f" - Hat {input_id}"

    return label
