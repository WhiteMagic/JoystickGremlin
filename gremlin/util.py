# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
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

import configparser
import os
from PyQt5 import QtWidgets
import re
import sdl2
import struct
import sys

import gremlin
from gremlin import error


# Flag indicating that multiple physical devices with the same name exist
g_duplicate_devices = False


# Symbol used for the function that will compute the device id. This
# will change based on whether or not multiple devices of the same
# type are connected
device_id = None


class SingletonDecorator:

    """Decorator turning a class into a singleton."""

    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance


class JoystickDeviceData(object):

    """Represents data about a joystick like input device."""

    def __init__(self, device):
        """Initializes the device data based on the given device.

        :param device pyGame joystick object
        """
        self._hardware_id = guid_to_number(sdl2.SDL_JoystickGetGUID(device))
        self._windows_id = sdl2.SDL_JoystickInstanceID(device)
        self._name = sdl2.SDL_JoystickName(device).decode("utf-8")
        self._is_virtual = self._name == "vJoy Device"
        self._axes = sdl2.SDL_JoystickNumAxes(device)
        self._buttons = sdl2.SDL_JoystickNumButtons(device)
        self._hats = sdl2.SDL_JoystickNumHats(device)

    @property
    def hardware_id(self):
        return self._hardware_id

    @property
    def windows_id(self):
        return self._windows_id

    @property
    def name(self):
        return self._name

    @property
    def is_virtual(self):
        return self._is_virtual

    @property
    def axes(self):
        return self._axes

    @property
    def buttons(self):
        return self._buttons

    @property
    def hats(self):
        return self._hats


class Configuration(object):

    """Responsible for loading and saving configuration data."""

    def __init__(self):
        """Creates a new instance, loading the current configuration."""
        self._parser = configparser.ConfigParser()
        self._parser.read_file(
            open(os.path.join(appdata_path(), "config.ini"))
        )

    def save(self):
        """Writes the configuration file to disk."""
        self._parser.write(
            open(os.path.join(appdata_path(), "config.ini"), "w")
        )

    def set_calibration(self, dev_id, limits):
        """Sets the calibration data for all axes of a device.

        :param dev_id the id of the device
        :param limits the calibration data for each of the axes
        """
        hid, wid = gremlin.util.extract_ids(dev_id)
        identifier = str(hid) if wid == -1 else "{}_{}".format(hid, wid)
        if identifier in self._parser:
            del self._parser[identifier]
        self._parser.add_section(identifier)

        for i, limit in enumerate(limits):
            if limit[2] - limit[0] == 0:
                continue
            self._parser[identifier]["axis_{}_min".format(i+1)] = str(limit[0])
            self._parser[identifier]["axis_{}_center".format(i+1)] = str(limit[1])
            self._parser[identifier]["axis_{}_max".format(i+1)] = str(limit[2])
        self.save()

    def get_calibration(self, dev_id, axis_id):
        """Returns the calibration data for the desired axis.

        :param dev_id the id of the device
        :param axis_id the id of the desired axis
        :return the calibration data for the desired axis
        """
        hid, wid = gremlin.util.extract_ids(dev_id)
        identifier = str(hid) if wid == -1 else "{}_{}".format(hid, wid)
        if identifier not in self._parser:
            return [-32768, 0, 32767]
        if "axis_{}_min".format(axis_id) not in self._parser[identifier]:
            return [-32768, 0, 32767]

        return [
            int(self._parser[identifier]["axis_{}_min".format(axis_id)]),
            int(self._parser[identifier]["axis_{}_center".format(axis_id)]),
            int(self._parser[identifier]["axis_{}_max".format(axis_id)])

        ]

    @property
    def default_profile(self):
        return self._get("profile", "default", None)

    @default_profile.setter
    def default_profile(self, value):
        self._parser["profile"]["default"] = value
        self.save()

    def _get(self, section, option, default):
        """Returns the value of the option in the provided section.

        If the option does not exist in the specified section the
        default value is returned.

        :param section the section of the configuration
        :param option the option within the section
        :param default the default value to return if the entry does
            not exist
        :return the value of the option within the given section
        """
        if section in self._parser and option in self._parser[section]:
            return self._parser[section][option]
        else:
            return default


def joystick_devices():
    """Returns the list of joystick like devices.

    :return list containing information about all joystick like devices
    """
    devices = []
    for i in range(sdl2.SDL_NumJoysticks()):
        joy = sdl2.SDL_JoystickOpen(i)
        devices.append(JoystickDeviceData(joy))

    return devices


def axis_calibration(value, minimum, center, maximum):
    """Returns the calibrated value for a normal style axis.

    :param value the raw value to process
    :param minimum the minimum value of the axis
    :param maximum the maximum value of the axis
    :return the calibrated value in [-1, 1] corresponding to the
        provided raw value
    """
    if value < center:
        return (value - center) / float(center - minimum)
    else:
        return (value - center) / float(maximum - center)


def slider_calibration(value, minimum, maximum):
    """Returns the calibrated value for a slider type axis.

    :param value the raw value to process
    :param minimum the minimum value of the axis
    :param maximum the maximum value of the axis
    :return the calibrated value in [-1, 1] corresponding to the
        provided raw value
    """
    return (value - minimum) / float(maximum - minimum) * 2.0 - 1.0


def create_calibration_function(minimum, center, maximum):
    """Returns a calibration function appropriate for the provided data.

    :param minimum the minimal value ever reported
    :param center the value in the neutral position
    :param maximum the maximal value ever reported
    :return function which returns a value in [-1, 1] corresponding
        to the provided raw input value
    """
    if minimum == center or maximum == center:
        return lambda x: slider_calibration(x, minimum, maximum)
    else:
        return lambda x: axis_calibration(x, minimum, center, maximum)


def script_path():
    """Returns the path to the scripts location.

    :return path to the scripts location
    """
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def display_error(msg):
    """Displays the provided error message to the user.

    :param msg the error message to display
    """
    QtWidgets.QErrorMessage.qtHandler().showMessage(msg)


def format_name(name):
    """Returns the name formatted as valid python variable name.

    :param name the name to format
    :return name formatted to be suitable as a python variable name
    """
    new_name = re.sub("[ \.,:()]", "_", name.lower())
    if valid_identifier(new_name):
        return new_name
    else:
        raise error.GremlinError(
            "Invalid string provided, only letters, numbers and white"
            " space supported, \"{}\".".format(new_name)
        )


def valid_identifier(name):
    """Returns whether or not a given name can be transformed into a
    valid python identifier.

    :param name the text to check
    :return True if name is a valid python identifier, false otherwise
    """
    return re.fullmatch("^[a-zA-Z0-9 _]+$", name) is not None


def valid_python_identifier(name):
    """Returns whether a given name is a valid python identifier.

    :param name the name to check for validity
    :return True if the name is a valid identifier, False otherwise
    """
    return re.match("^[^\d\W]\w*\Z", name) is not None


def clamp(value, min_val, max_val):
    """Returns the value clamped to the provided range.

    :param value the input value
    :param min_val minimum value
    :param max_val maximum value
    :return the input value clamped to the provided range
    """
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return min(max_val, max(min_val, value))


def guid_to_number(guid):
    """Converts a byte array GUID into a string.

    :param guid the byte array to convert
    :return hex string representation of the given guid
    """
    return struct.unpack(">4I", guid)[0]


def mode_list(node):
    """Returns a list of all modes based on the given node.

    :param node a node from a profile tree
    :return list of mode names
    """
    # Get profile root node
    parent = node
    while parent.parent is not None:
        parent = parent.parent
    assert(type(parent) == gremlin.profile.Profile)
    # Generate list of modes
    mode_names = []
    for device in parent.devices.values():
        mode_names.extend(device.modes.keys())

    return sorted(list(set(mode_names)))


def convert_sdl_hat(value):
    """Converts the SDL hat representation to the Gremlin one.

    :param value the hat state representation as used by SDL
    :return the hat representation corresponding to the SDL one
    """
    direction = [0, 0]
    if value & sdl2.SDL_HAT_UP:
        direction[1] = 1
    elif value & sdl2.SDL_HAT_DOWN:
        direction[1] = -1
    if value & sdl2.SDL_HAT_RIGHT:
        direction[0] = 1
    elif value & sdl2.SDL_HAT_LEFT:
        direction[0] = -1
    return tuple(direction)


def appdata_path():
    """Returns the path to the application data folder, %APPDATA%."""
    return os.path.abspath(os.path.join(
        os.getenv("APPDATA"),
        "Joystick Gremlin")
    )


def setup_appdata():
    """Initializes the data folder in the application data folder."""
    folder = appdata_path()
    if not os.path.exists(folder):
        try:
            os.mkdir(folder)
        except Exception as e:
            raise error.GremlinError(
                "Unable to create data folder: {}".format(str(e))
            )
    elif not os.path.isdir(folder):
        raise error.GremlinError("Data folder exists but is not a folder")


def device_id_duplicates(device):
    """Returns a unique id for the provided device.

    This function is intended to be used when device of identical type
    are present.

    :param device the object with device related information
    :return unique identifier of this device
    """
    return (device.hardware_id, device.windows_id)


def device_id_unique(device):
    """Returns a unique id for the provided device.

    This function is intended to be used when all devices are
    distinguishable by their hardware id.

    :param device the object with device related information
    :return unique identifier of this device
    """
    return device.hardware_id


def setup_duplicate_joysticks():
    """Detects if multiple identical devices are connected and performs
    appropriate setup.
    """
    global g_duplicate_devices
    global device_id
    devices = joystick_devices()

    # Check if we have duplicate items
    entries = [dev.hardware_id for dev in devices]
    g_duplicate_devices = len(entries) != len(set(entries))

    # Create appropriate device_id generator
    if g_duplicate_devices:
        device_id = device_id_duplicates
    else:
        device_id = device_id_unique


def extract_ids(dev_id):
    """Returns hardware and windows id of a device_id.

    Only if g_duplicate_devices is true will there be a windows id
    present. If it is not present -1 will be returned

    :param dev_id the device_id from which to extract the individual
        ids
    :return hardware_id and windows_id
    """
    if g_duplicate_devices:
        return dev_id[0], dev_id[1]
    else:
        return dev_id, -1


def clear_layout(layout):
    """Removes all items from the given layout.

    :param layout the layout from which to remove all items
    """
    while layout.count() > 0:
        child = layout.takeAt(0)
        if child.layout():
            clear_layout(child.layout())
        elif child.widget():
            child.widget().deleteLater()
        layout.removeItem(child)