# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2025 Lionel Ott
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

"""
Performs a simple swap of two devices in the profile.
"""

import dataclasses
import uuid

from gremlin import device_initialization, profile


@dataclasses.dataclass
class ProfileDeviceInfo:
    device_uuid: uuid.UUID
    name: str = ""
    num_bindings: int = 0


def get_profile_devices(pr: profile.Profile) -> list[ProfileDeviceInfo]:
    profile_devices = {}
    for device_uuid, inputs in pr.inputs.items():
        if device_uuid in profile_devices:
            profile_devices[device_uuid].num_bindings += len(inputs)
        else:
            profile_devices[device_uuid] = ProfileDeviceInfo(
                device_uuid, num_bindings=len(inputs)
            )

    # We can get names for connected devices (only).
    for d in device_initialization.physical_devices():
        if d.device_guid.uuid in profile_devices:
            profile_devices[d.device_guid.uuid].name = d.name
    return list(profile_devices.values())


@dataclasses.dataclass
class SwapDevicesResult:
    action_swaps: int
    input_swaps: int

    def as_string(self) -> str:
        return f"Swapped {self.action_swaps} actions and {self.input_swaps} inputs."


def _swap_device_inputs(
    profile: profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> int:
    swap_count = 0
    source_device_inputs = profile.inputs.get(source_device_uuid)
    target_device_inputs = profile.inputs.get(target_device_uuid)

    if source_device_inputs:
        for input_item in source_device_inputs:
            input_item.device_id = target_device_uuid
            swap_count += 1
        profile.inputs[target_device_uuid] = source_device_inputs
    if target_device_inputs:
        for input_item in target_device_inputs:
            input_item.device_id = source_device_uuid
            swap_count += 1
        profile.inputs[source_device_uuid] = target_device_inputs
    return swap_count


def _swap_device_actions(
    profile: profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> int:
    swap_count = 0
    for action in profile.library.actions_by_predicate(lambda x: True):
        swap_count += int(action.swap_uuid(source_device_uuid, target_device_uuid))
    return swap_count


def swap_devices(
    profile: profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> SwapDevicesResult:
    """Swaps two devices in the profile (from a device in the profile to a connected device).

    It is the caller's responsibility to ensure that the devices UUIDs are valid.

    Args:
        profile: The Profile to perform the swap on.
        source_device_uuid: The UUID of the source (from profile) device.
        target_device_uuid: The UUID of the target (connected) device.

    Returns:
        The SwapDevicesResult object containing stats on the swaps performed.
    """
    return SwapDevicesResult(
        _swap_device_actions(profile, source_device_uuid, target_device_uuid),
        _swap_device_inputs(profile, source_device_uuid, target_device_uuid),
    )
