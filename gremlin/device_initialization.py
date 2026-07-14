# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import collections
import logging
import threading
import uuid

import dill
from gremlin import (
    error,
    shared_state,
)
from vjoy import vjoy
from vjoy.vjoy import VJoyProxy

_joystick_devices: dict[uuid.UUID, dill.DeviceSummary] = collections.OrderedDict()
_joystick_init_lock = threading.Lock()


def joystick_devices_initialization() -> None:
    """Initializes joystick device information.

    This function retrieves information about various joystick devices and
    associates them and collates their information as required.

    Amongst other things this also ensures that each vJoy device has a correct
    windows id assigned to it.
    """
    global _joystick_devices, _joystick_init_lock

    _joystick_init_lock.acquire()

    syslog = logging.getLogger("system")
    syslog.info("Initializing joystick devices")
    syslog.debug(f"{dill.DILL.get_device_count():d} joysticks detected")

    # Process all connected devices in order to properly initialize the
    # device registry.
    devices = []
    for i in range(dill.DILL.get_device_count()):
        info = dill.DILL.get_device_information_by_index(i)
        devices.append(info)

    # Process all devices again to detect those that have been added and those
    # that have been removed since the last time this function ran.

    # Compare existing versus observed devices and only proceed if there
    # is a change to avoid unnecessary work.
    device_added = False
    device_removed = False
    for new_dev in devices:
        if new_dev.device_guid.uuid not in _joystick_devices:
            device_added = True
            syslog.debug(f"Added: name={new_dev.name} guid={new_dev.device_guid}")
    for old_dev in _joystick_devices.values():
        if old_dev not in devices:
            device_removed = True
            syslog.debug(f"Removed: name={old_dev.name} guid={old_dev.device_guid}")

    # Terminate if no change occurred.
    if not device_added and not device_removed:
        _joystick_init_lock.release()
        return

    # In order to associate vJoy devices and their ids correctly with DILL
    # device ids a hash is constructed from the number of axes, buttons, and
    # hats. This information is used to attempt to find unambiguous mappings
    # between vJoy and Direct Input devices. If this is not possible Gremlin
    # will terminate as this is a non-recoverable error.

    vjoy_lookup = {}
    for dev in [dev for dev in devices if dev.is_virtual]:
        hash_value = (dev.axis_count, dev.button_count, dev.hat_count)
        syslog.debug(f"vJoy guid={dev.device_guid}: {hash_value}")

        # Only unique combinations of axes, buttons, and hats are allowed
        # for vJoy devices.
        if hash_value in vjoy_lookup:
            raise error.GremlinError(
                "Indistinguishable vJoy devices present. vJoy devices have "
                "to differ in the number of (at least one of) axes, buttons, "
                "or hats in order to work properly with Joystick Gremlin."
            )

        vjoy_lookup[hash_value] = dev

    # Query all vJoy devices in sequence until all have been processed and
    # their matching Direct Input counterparts have been found.
    vjoy_proxy = VJoyProxy()
    for i in range(1, 17):
        # Only process devices that actually exist.
        if not vjoy.device_exists(i):
            continue

        # Compute a hash for the vJoy device and match it against the DILL
        # device hashes.
        hash_value = (vjoy.axis_count(i), vjoy.button_count(i), vjoy.hat_count(i))

        if not vjoy.hat_configuration_valid(i):
            raise error.GremlinError(
                f"vJoy id {i}: Hats are set to discrete but have to be set "
                f"to continuous."
            )

        # As we are ensured that no duplicate vJoy devices exist from
        # the previous step we can directly link the Direct Input and
        # vJoy device.
        if hash_value in vjoy_lookup:
            vjoy_lookup[hash_value].set_vjoy_id(i)
            syslog.debug(f"vjoy id {i}: {hash_value} - MATCH")
        else:
            raise error.GremlinError(
                f"vJoy id {i}: {hash_value} - vJoy device exists but "
                "DILL does not see it."
            )

    # Reset all devices so we don't hog the ones we aren't actually using.
    vjoy_proxy.reset()

    # Update device list which will be used when queries for joystick devices
    # are made. Order the devices such that vJoy devices are last and the
    # physical devices are ordered by name.
    sorted_devices = sorted(
        [dev for dev in devices if not dev.is_virtual], key=lambda x: x.name
    )
    sorted_devices.extend(
        sorted([dev for dev in devices if dev.is_virtual], key=lambda x: x.vjoy_id)
    )
    # This is an ordered dict, that allows access via device uuid but its
    # values are enumerate in insertion order.
    _joystick_devices.clear()
    for dev in sorted_devices:
        _joystick_devices[dev.device_guid.uuid] = dev
    _joystick_init_lock.release()


def joystick_devices() -> list[dill.DeviceSummary]:
    """Returns the list of joystick like devices.

    Returns:
        List containing information about all joystick devices
    """
    return list(_joystick_devices.values())


def vjoy_devices() -> list[dill.DeviceSummary]:
    """Returns the list of vJoy devices.

    Returns:
        List of vJoy devices
    """
    return [dev for dev in _joystick_devices.values() if dev.is_virtual]


def physical_devices() -> list[dill.DeviceSummary]:
    """Returns the list of physical devices.

    Returns:
        List of physical devices
    """
    return [dev for dev in _joystick_devices.values() if not dev.is_virtual]


def input_devices() -> list[dill.DeviceSummary]:
    """Returns the list of input devices, that is physical and vJoy devices
    that are marked as inputs.

    Returns:
        List of input devices
    """
    vjoy_as_input = {}
    if shared_state.current_profile:
        vjoy_as_input = shared_state.current_profile.settings.vjoy_as_input

    return [
        dev
        for dev in _joystick_devices.values()
        if not dev.is_virtual or vjoy_as_input.get(dev.vjoy_id, False)
    ]


def output_vjoy_devices() -> list[dill.DeviceSummary]:
    """Returns the list of vJoy devices that can be used as outputs.

    Returns:
        List of output vJoy devices
    """
    vjoy_as_input = {}
    if shared_state.current_profile:
        vjoy_as_input = shared_state.current_profile.settings.vjoy_as_input

    return [dev for dev in vjoy_devices() if not vjoy_as_input.get(dev.vjoy_id, False)]


def device_for_uuid(device_uuid: uuid.UUID) -> dill.DeviceSummary:
    return _joystick_devices[device_uuid]
