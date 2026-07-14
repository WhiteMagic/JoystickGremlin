# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""
Performs a simple swap of two devices in the profile.
"""

from __future__ import annotations

import dataclasses
import uuid

import gremlin.profile


@dataclasses.dataclass
class ProfileDeviceInfo:
    device_uuid: uuid.UUID
    name: str = ""
    num_bindings: int = 0


@dataclasses.dataclass
class SwapDevicesResult:
    action_swaps: int = 0
    input_swaps: int = 0
    user_script_swaps: int = 0

    def as_string(self) -> str:
        return (
            f"Swapped {self.input_swaps} input(s), {self.action_swaps} "
            f"actions, and {self.user_script_swaps} user script variables."
        )


def get_profile_devices(profile: gremlin.profile.Profile) -> list[ProfileDeviceInfo]:
    """Returns ProfileDeviceInfo for all devices present in the profile.

    Args:
        profile: The Profile to analyze.

    Returns:
        A list of ProfileDeviceInfo objects for all devices present in the
        profile.
    """
    # Count the number of non-empty bindings.
    profile_devices = {}
    for device_uuid, inputs in profile.inputs.items():
        if device_uuid not in profile_devices:
            profile_devices[device_uuid] = ProfileDeviceInfo(device_uuid)

        binding_count = sum(1 for e in inputs if e.action_sequences)
        profile_devices[device_uuid].num_bindings += binding_count

    # Attempt to retrieve device name from the database.
    for dev_info in profile.device_database.devices.values():
        if dev_info.device_uuid in profile_devices:
            profile_devices[dev_info.device_uuid].name = dev_info.name

    return list(profile_devices.values())


def _swap_device_inputs(
    profile: gremlin.profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> int:
    swap_count = 0
    source_device_inputs = profile.inputs.get(source_device_uuid, [])
    target_device_inputs = profile.inputs.get(target_device_uuid, [])

    for input_item in [e for e in source_device_inputs if e.action_sequences]:
        input_item.device_id = target_device_uuid
        swap_count += 1
    profile.inputs[target_device_uuid] = source_device_inputs
    for input_item in [e for e in target_device_inputs if e.action_sequences]:
        input_item.device_id = source_device_uuid
        swap_count += 1
    profile.inputs[source_device_uuid] = target_device_inputs
    return swap_count


def _swap_device_actions(
    profile: gremlin.profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> int:
    return [
        a.swap_uuid(source_device_uuid, target_device_uuid)
        for a in profile.library.actions_by_predicate(lambda _: True)
    ].count(True)


def _swap_device_user_script_vars(
    profile: gremlin.profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> int:
    return [
        script.swap_uuid(source_device_uuid, target_device_uuid)
        for script in profile.scripts.scripts
    ].count(True)


def swap_devices(
    profile: gremlin.profile.Profile,
    source_device_uuid: uuid.UUID,
    target_device_uuid: uuid.UUID,
) -> SwapDevicesResult:
    """Swaps two devices in the profile, from a device in the profile to a
    connected device.

    It is the caller's responsibility to ensure that the devices UUIDs are
    valid.

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
