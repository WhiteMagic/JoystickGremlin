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

import uuid

import dill

from gremlin.event_handler import Event
from gremlin.types import AxisNames, InputType


def joystick_label(
        device_guid: uuid.UUID,
        input_type: InputType,
        input_id: int
) -> str:
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