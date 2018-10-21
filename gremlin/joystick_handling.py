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
import time

import sdl2

from . import error, util
from vjoy import vjoy

# List of all joystick devices
_joystick_devices = []


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

    def set_vjoy_id(self, vjoy_id):
        self._vjoy_id = vjoy_id

    def __hash__(self):
        return hash((self.hardware_id, self.windows_id))

    def __eq__(self, other):
        return hash(self) == hash(other)


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
    global _joystick_devices
    syslog = logging.getLogger("system")

    syslog.debug("{:d} joysticks found".format(sdl2.SDL_NumJoysticks()))

    # Get all connected devices
    devices = []
    for i in range(sdl2.SDL_NumJoysticks()):
        joy = sdl2.SDL_JoystickOpen(i)
        if joy is None:
            syslog.error("Invalid joystick device at id {}".format(i))
        else:
            devices.append(JoystickDeviceData(joy))

    # Compare existing versus observed devices and only proceed if there
    # is a difference
    device_added = False
    device_removed = False
    for new_dev in devices:
        if new_dev not in _joystick_devices:
            device_added = True
            syslog.debug("Added: name={} windows_id={:d}".format(
                new_dev.name,
                new_dev.windows_id
            ))
    for old_dev in _joystick_devices:
        if old_dev not in devices:
            device_removed = True
            syslog.debug("Removed: name={} windows_id={:d}".format(
                old_dev.name,
                old_dev.windows_id
            ))

    if not device_added and not device_removed:
        return _joystick_devices

    # Create hashes based on number of inputs for each virtual device. As we
    # absolutely need to be able to assign the SDL device to the correct
    # vJoy device we will not proceed if this mapping cannot be made without
    # ambiguity.
    vjoy_lookup = {}
    for i, dev in enumerate(devices):
        if not dev.is_virtual:
            continue
        hash_value = (dev.axis_count, dev.buttons, dev.hats)
        syslog.debug("vjoy windows id {:d}: {}".format(dev.windows_id, hash_value))
        if hash_value in vjoy_lookup:
            raise error.GremlinError(
                "Indistinguishable vJoy devices present.\n\n"
                "vJoy devices have to differ in the number of "
                "(at least one of) axis, buttons, or hats in order to work "
                "properly with Joystick Gremlin."
            )
        vjoy_lookup[hash_value] = i

    # For virtual joysticks query them id by id until we have found all active
    # devices
    vjoy_proxy = VJoyProxy()

    # Try each possible vJoy device and if it exists find the matching device
    # as detected by SDL
    should_terminate = False
    for i in range(1, 17):
        if vjoy.device_exists(i):
            hash_value = (
                vjoy.axis_count(i),
                vjoy.button_count(i),
                vjoy.hat_count(i)
            )
            devices[vjoy_lookup[hash_value]].set_vjoy_id(i)
            syslog.debug("vJoy id {:d} exists".format(i))
        else:
            continue

        if not vjoy.device_available(i):
            syslog.debug("vJoy id {:} can't be acquired".format(i))
            continue

        vjoy_dev = vjoy_proxy[i]
        hash_value = (
            vjoy_dev.axis_count,
            vjoy_dev.button_count,
            vjoy_dev.hat_count
        )
        if hash_value in vjoy_lookup:
            # Set vJoy id and correctly setup the axis id mapping
            # devices[vjoy_lookup[hash_value]]._vjoy_id = vjoy_dev.vjoy_id
            axis_mapping = []
            for j in range(vjoy_dev.axis_count):
                axis_mapping.append((j+1, vjoy_dev.axis_id(j+1)))
            devices[vjoy_lookup[hash_value]].set_axis_mapping(axis_mapping)
            syslog.debug("vjoy id {:d}: {} - MATCH".format(i, hash_value))

        if hash_value not in vjoy_lookup:
            syslog.debug("vjoy id {:d}: {} - ERROR".format(i, hash_value))
            should_terminate = True

    if should_terminate:
        raise error.GremlinError(
            "Unable to match vJoy devices to windows devices."
        )

    # Reset all devices so we don't hog the ones we aren't actually using
    vjoy_proxy.reset()

    _joystick_devices = devices
    return _joystick_devices
