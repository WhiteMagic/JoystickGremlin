# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""
Performs a simple swap of two devices in the profile.
"""

import dataclasses
import uuid

import gremlin.profile
from gremlin import device_initialization


@dataclasses.dataclass
class ProfileDeviceInfo:
    device_uuid: uuid.UUID
    name: str = ""
    num_bindings: int = 0


def get_profile_devices(
    profile: gremlin.profile.Profile
) -> list[ProfileDeviceInfo]:
    # Retrieve all devices that have input bindings in the profile and count
    # the number of bindings for each.
    profile_devices = {}
    for device_uuid, inputs in profile.inputs.items():
        if device_uuid in profile_devices:
            profile_devices[device_uuid].num_bindings += len(inputs)
        else:
            profile_devices[device_uuid] = ProfileDeviceInfo(
                device_uuid, num_bindings=len(inputs)
            )

    # Attempt to retrieve device name from the database.
    for dev_info in profile.device_database.devices.values():
        if dev_info.device_uuid in profile_devices:
            profile_devices[dev_info.device_uuid].name = dev_info.name

    return list(profile_devices.values())


@dataclasses.dataclass
class SwapDevicesResult:
    action_swaps: int
    input_swaps: int
    user_script_swaps: int

    def as_string(self) -> str:
        return (
            f"Swapped {self.action_swaps} actions, "
            f"{self.input_swaps} inputs, and {self.user_script_swaps} user script vars."
        )


def _swap_device_inputs(
    profile: gremlin.profile.Profile,
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
    profile: gremlin.profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> int:
    swap_count = 0
    for action in profile.library.actions_by_predicate(lambda x: True):
        swap_count += int(action.swap_uuid(source_device_uuid, target_device_uuid))
    return swap_count


def _swap_device_user_script_vars(
    profile: gremlin.profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> int:
    swap_count = 0
    for script in profile.scripts.scripts:
        swap_count += script.swap_uuid(source_device_uuid, target_device_uuid)
    return swap_count


def swap_devices(
    profile: gremlin.profile.Profile,
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
        _swap_device_user_script_vars(profile, source_device_uuid, target_device_uuid),
    )
