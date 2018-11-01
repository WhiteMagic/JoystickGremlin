# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2018 Lionel Ott
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
import time

import sdl2

from . import common, error, util
from vjoy import vjoy


# List of all joystick devices
_joystick_devices = []

# Joystick initializataion lock
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
                    "Failed accesing vJoy id={}, error is: {}".format(
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


class JoystickDeviceData:

    """Represents data about a joystick like input device.

    Instances can be compared for equality which uses the DeviceIdentifier
    instance associated with this object.
    """

    def __init__(self, device):
        """Initializes the device data based on the given device.

        :param device pyGame joystick object
        """
        self._hardware_id = get_device_guid(device)
        self._windows_id = sdl2.SDL_JoystickInstanceID(device)
        self._vendor_id = sdl2.SDL_JoystickGetVendor(device)
        self._product_id = sdl2.SDL_JoystickGetProduct(device)
        name_object = sdl2.SDL_JoystickName(device)
        if name_object is None:
            self._name = "Unknown device"
            logging.getLogger("system").error(
                "Encountered an invalid device name for device {:d}".format(
                    self._windows_id
                )
            )
        else:
            self._name = name_object.decode("utf-8")
        self._is_virtual = self._name == "vJoy Device"

        # Default mapping from axis id to physical axis number. This defaults
        # to a linear 1:1 mapping but for vJoy devices can change
        self._axes = []
        for i in range(sdl2.SDL_JoystickNumAxes(device)):
            self._axes.append((i+1, i+1))
        self._buttons = sdl2.SDL_JoystickNumButtons(device)
        self._hats = sdl2.SDL_JoystickNumHats(device)
        self._vjoy_id = 0
        self._device_id = common.DeviceIdentifier(
            self._hardware_id,
            self._windows_id
        )

    @property
    def hardware_id(self):
        return self._hardware_id

    @property
    def windows_id(self):
        return self._windows_id

    @property
    def product_id(self):
        return self._product_id

    @property
    def vendor_id(self):
        return self._vendor_id

    @property
    def name(self):
        return self._name

    @property
    def is_virtual(self):
        return self._is_virtual

    def axis(self, index):
        return self._axes[index]

    @property
    def axis_count(self):
        return len(self._axes)

    def set_axis_mapping(self, mapping):
        self._axes = mapping

    @property
    def buttons(self):
        return self._buttons

    @property
    def hats(self):
        return self._hats

    @property
    def vjoy_id(self):
        return self._vjoy_id

    @property
    def device_id(self):
        return self._device_id

    def set_vjoy_id(self, vjoy_id):
        self._vjoy_id = vjoy_id

    def __hash__(self):
        return hash(self._device_id)

    def __eq__(self, other):
        return self._device_id == other.device_id


def get_device_guid(device):
    """Returns the GUID of the provided device.

    :param device SDL2 joystick device for which to get the GUID
    :return GUID for the provided device
    """
    vendor_id = sdl2.SDL_JoystickGetVendor(device)
    product_id = sdl2.SDL_JoystickGetProduct(device)
    return (vendor_id << 16) + product_id


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
    syslog.debug("{:d} joysticks detected".format(sdl2.SDL_NumJoysticks()))

    # Register all devices with the device registry to handle duplicate and
    # non duplicate devices transparently.
    devreg = common.DeviceRegistry()
    devreg.reset()
    # Register the fake keyboard device
    devreg.register(0, 0)

    # Process all connected devices in order to properly initialize the
    # device registry
    for i in range(sdl2.SDL_NumJoysticks()):
        joy = sdl2.SDL_JoystickOpen(i)
        if joy is None:
            syslog.error("Invalid joystick device at id {}".format(i))
        else:
            devreg.register(
                get_device_guid(joy),
                sdl2.SDL_JoystickInstanceID(joy)
            )


    # Process all devices again to detect those that have been added and those
    # that have been removed since the last time this function ran.

    # Accumulate all devices
    devices = []
    for i in range(sdl2.SDL_NumJoysticks()):
        joy = sdl2.SDL_JoystickOpen(i)
        if joy is not None:
            devices.append(JoystickDeviceData(joy))

    # Compare existing versus observed devices and only proceed if there
    # is a change to avoid unneccessary work.
    device_added = False
    device_removed = False
    for new_dev in devices:
        if new_dev not in _joystick_devices:
            device_added = True
            syslog.debug("Added: name={} windows_id={:d} hardware_id={:d}".format(
                new_dev.name,
                new_dev.windows_id,
                new_dev.hardware_id
            ))
    for old_dev in _joystick_devices:
        if old_dev not in devices:
            device_removed = True
            syslog.debug("Removed: name={} windows_id={:d} hardware_id={:d}".format(
                old_dev.name,
                old_dev.windows_id,
                old_dev.hardware_id
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
        hash_value = (dev.axis_count, dev.buttons, dev.hats)
        syslog.debug(
            "vJoy windows id {:d}: {}".format(dev.windows_id, hash_value)
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

        # As we are ensured that no duplicate vJoy devices exist from
        # the previous step we can directly link the SDL and vJoy device
        if hash_value in vjoy_lookup:
            vjoy_lookup[hash_value].set_vjoy_id(i)
            syslog.debug("vjoy id {:d}: {} - MATCH".format(i, hash_value))
        else:
            should_terminate = True
            syslog.debug(
                "vjoy id {:d}: {} - ERROR - vJoy device exists "
                "SDL is missing".format(i, hash_value)
            )

        # If the device can be acquired, configure the mapping from
        # vJoy axis id, which may not be sequential, to the
        # sequential SDL axis id
        if hash_value in vjoy_lookup:
            try:
                vjoy_dev = vjoy_proxy[i]

                axis_mapping = []
                for j in range(vjoy_dev.axis_count):
                    axis_mapping.append((j + 1, vjoy_dev.axis_id(j + 1)))
                vjoy_lookup[hash_value].set_axis_mapping(axis_mapping)
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