# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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


import logging
import threading

import dill
import gremlin.types

from . import common, error, util
from vjoy import vjoy


# List of all joystick devices
_joystick_devices = []

# Joystick initialization lock
_joystick_init_lock = threading.Lock()


class VJoyProxy:

    """Manages the usage of vJoy and allows shared access all callbacks."""

    vjoy_devices = {}

    def __getitem__(self, key):
        """Returns the requested vJoy instance.

        :param key id of the vjoy device
        :return the corresponding vjoy device
        """
        if key in VJoyProxy.vjoy_devices:
            return VJoyProxy.vjoy_devices[key]
        else:
            if not isinstance(key, int):
                raise error.GremlinError(
                    "Integer ID for vjoy device ID expected"
                )

            try:
                device = vjoy.VJoy(key)
                VJoyProxy.vjoy_devices[key] = device
                return device
            except error.VJoyError as e:
                logging.getLogger("system").error(
                    "Failed accessing vJoy id={}, error is: {}".format(
                        key,
                        e
                    )
                )
                raise e

    @classmethod
    def reset(cls):
        """Relinquishes control over all held VJoy devices."""
        for device in VJoyProxy.vjoy_devices.values():
            device.invalidate()
        VJoyProxy.vjoy_devices = {}


def joystick_devices():
    """Returns the list of joystick like devices.

    :return list containing information about all joystick like devices
    """
    return _joystick_devices


def vjoy_devices():
    """Returns the list of vJoy devices.

    :return list of vJoy devices
    """
    return [dev for dev in _joystick_devices if dev.is_virtual]


def physical_devices():
    """Returns the list of physical devices.

    :return list of physical devices
    """
    return [dev for dev in _joystick_devices if not dev.is_virtual]


def select_first_valid_vjoy_input(valid_types):
    """Returns the first valid vjoy input.

    Parameters
    ==========
    valid_types : list
        List of common.InputType values that are valid type to be returned

    Return
    ======
    dict
        Dictionary containing the information about the selected vJoy input
    """
    for dev in vjoy_devices():
        if gremlin.types.InputType.JoystickAxis in valid_types and dev.axis_count > 0:
            return {
                "device_id": dev.vjoy_id,
                "input_type": gremlin.types.InputType.JoystickAxis,
                "input_id": dev.axis_map[0].axis_index
            }
        elif gremlin.types.InputType.JoystickButton in valid_types and dev.button_count > 0:
            return {
                "device_id": dev.vjoy_id,
                "input_type": gremlin.types.InputType.JoystickButton,
                "input_id": 1
            }
        elif gremlin.types.InputType.JoystickHat in valid_types and dev.hat_count > 0:
            return {
                "device_id": dev.vjoy_id,
                "input_type": gremlin.types.InputType.JoystickHat,
                "input_id": 1
            }
    return None


def vjoy_id_from_guid(guid):
    """Returns the vJoy id corresponding to the given device GUID.

    Parameters
    ==========
    guid : GUID
        guid of the vjoy device in windows

    Return
    ======
    int
        vJoy id corresponding to the provided device
    """
    for dev in vjoy_devices():
        if dev.device_guid == guid:
            return dev.vjoy_id

    logging.getLogger("system").error(
        "Could not find vJoy matching guid {}".format(str(guid))
    )
    return 1


def linear_axis_index(axis_map, axis_index):
    """Returns the linear index for an axis based on the axis index.

    Parameters
    ==========
    axis_map : dill.AxisMap
        AxisMap instance which contains the mapping between linear and
        axis indices
    axis_index : int
        Index of the axis for which to return the linear index

    Return
    ======
    int
        Linear axis index
    """
    for entry in axis_map:
        if entry.axis_index == axis_index:
            return entry.linear_index
    raise error.GremlinError("Linear axis lookup failed")


def joystick_devices_initialization():
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
    syslog.debug(
        "{:d} joysticks detected".format(dill.DILL.get_device_count())
    )

    # Process all connected devices in order to properly initialize the
    # device registry
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
        if new_dev not in _joystick_devices:
            device_added = True
            syslog.debug("Added: name={} guid={}".format(
                new_dev.name,
                new_dev.device_guid
            ))
    for old_dev in _joystick_devices:
        if old_dev not in devices:
            device_removed = True
            syslog.debug("Removed: name={} guid={}".format(
                old_dev.name,
                old_dev.device_guid
            ))

    # Terminate if no change occurred
    if not device_added and not device_removed:
        _joystick_init_lock.release()
        return

    # In order to associate vJoy devices and their ids correctly with SDL
    # device ids a hash is constructed from the number of axes, buttons, and
    # hats. This information is used to attempt to find unambiguous mappings
    # between vJoy and SDL devices. If this is not possible Gremlin will
    # terminate as this is a non-recoverable error.

    vjoy_lookup = {}
    for dev in [dev for dev in devices if dev.is_virtual]:
        hash_value = (dev.axis_count, dev.button_count, dev.hat_count)
        syslog.debug(
            "vJoy guid={}: {}".format(dev.device_guid, hash_value)
        )

        # Only unique combinations of axes, buttons, and hats are allowed
        # for vJoy devices
        if hash_value in vjoy_lookup:
            raise error.GremlinError(
                "Indistinguishable vJoy devices present.\n\n"
                "vJoy devices have to differ in the number of "
                "(at least one of) axes, buttons, or hats in order to work "
                "properly with Joystick Gremlin."
            )

        vjoy_lookup[hash_value] = dev

    # Query all vJoy devices in sequence until all have been processed and
    # their matching SDL counterparts have been found.
    vjoy_proxy = VJoyProxy()
    should_terminate = False
    for i in range(1, 17):
        # Only process devices that actually exist
        if not vjoy.device_exists(i):
            continue

        # Compute a hash for the vJoy device and match it against the SDL
        # device hashes
        hash_value = (
            vjoy.axis_count(i),
            vjoy.button_count(i),
            vjoy.hat_count(i)
        )

        if not vjoy.hat_configuration_valid(i):
            error_string = "vJoy id {:d}: Hats are set to discrete but have " \
                           "to be set as continuous.".format(i)
            syslog.debug(error_string)
            util.display_error(error_string)

        # As we are ensured that no duplicate vJoy devices exist from
        # the previous step we can directly link the SDL and vJoy device
        if hash_value in vjoy_lookup:
            vjoy_lookup[hash_value].set_vjoy_id(i)
            syslog.debug("vjoy id {:d}: {} - MATCH".format(i, hash_value))
        else:
            should_terminate = True
            syslog.debug(
                "vjoy id {:d}: {} - ERROR - vJoy device exists "
                "but DILL does not see it".format(i, hash_value)
            )

        # If the device can be acquired, configure the mapping from
        # vJoy axis id, which may not be sequential, to the
        # sequential SDL axis id
        if hash_value in vjoy_lookup:
            try:
                vjoy_dev = vjoy_proxy[i]
            except error.VJoyError as e:
                syslog.debug("vJoy id {:} can't be acquired".format(i))

    if should_terminate:
        raise error.GremlinError(
            "Unable to match vJoy devices to windows devices."
        )

    # Reset all devices so we don't hog the ones we aren't actually using
    vjoy_proxy.reset()

    # Update device list which will be used when queries for joystick devices
    # are made
    _joystick_devices = devices

    _joystick_init_lock.release()
