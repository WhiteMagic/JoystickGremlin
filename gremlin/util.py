# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2017 Lionel Ott
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

import ctypes
import importlib
import logging
import os
import re
import sys
import threading
import time

from PyQt5 import QtCore, QtWidgets

import sdl2
from . import error, joystick_handling

# Flag indicating that multiple physical devices with the same name exist
g_duplicate_devices = False


# Symbol used for the function that will compute the device id. This
# will change based on whether or not multiple devices of the same
# type are connected
device_id = None


# Table storing which modules have been imported already
g_loaded_modules = {}


class FileWatcher(QtCore.QObject):

    """Watches files in the filesystem for changes."""

    # Signal emitted when the watched file is modified
    file_changed = QtCore.pyqtSignal(str)

    def __init__(self, file_names, parent=None):
        """Creates a new instance.

        :param file_names list of files to watch
        :param parent parent of this object
        """
        QtCore.QObject.__init__(self, parent)
        self._file_names = file_names
        self._last_size = {}
        for fname in self._file_names:
            self._last_size[fname] = 0

        self._is_running = True
        self._watch_thread = threading.Thread(target=self._monitor)
        self._watch_thread.start()

    def stop(self):
        """Terminates the thread monitoring files."""
        self._is_running = False
        if self._watch_thread.is_alive():
            self._watch_thread.join()

    def _monitor(self):
        """Continuously monitors files for change."""
        while self._is_running:
            for fname in self._file_names:
                stats = os.stat(fname)
                if stats.st_size != self._last_size[fname]:
                    self._last_size[fname] = stats.st_size
                    self.file_changed.emit(fname)
            time.sleep(1)


def is_user_admin():
    """Returns whether or not the user has admin privileges.

    :return True if user has admin rights, False otherwise
    """
    return ctypes.windll.shell32.IsUserAnAdmin() == 1


def setup_duplicate_devices(device_id_fn, duplicate_devices):
    """Configures the device id generation method.

    Depending on whether or not multiple identical devices are present on the
    system the function used to generate device IDs have to be swapped. This
    function does all the handling and setting of information for this.

    :param device_id_fn the function to use in order to generate device IDs
    :param duplicate_devices flag indicating if multiple identical devices
        are present in the system or not
    """
    global device_id
    global g_duplicate_devices

    device_id = device_id_fn
    g_duplicate_devices = duplicate_devices


def axis_calibration(value, minimum, center, maximum):
    """Returns the calibrated value for a normal style axis.

    :param value the raw value to process
    :param minimum the minimum value of the axis
    :param center the center value of the axis
    :param maximum the maximum value of the axis
    :return the calibrated value in [-1, 1] corresponding to the
        provided raw value
    """
    value = clamp(value, minimum, maximum)
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
    value = clamp(value, minimum, maximum)
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


def truncate(text, left_size, right_size):
    """Returns a truncated string matching the specified character counts.

    :param text the text to truncate
    :param left_size number of characters on the left side
    :param right_size number of characters on the right side
    :return string truncated to the specified character counts if required
    """
    if len(text) < left_size + right_size:
        return text

    return "{}...{}".format(text[:left_size], text[-right_size:])


def script_path():
    """Returns the path to the scripts location.

    :return path to the scripts location
    """
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def display_error(msg):
    """Displays the provided error message to the user.

    :param msg the error message to display
    """
    box = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Critical,
        "Error",
        msg,
        QtWidgets.QMessageBox.Ok
    )
    box.exec()


def log(msg):
    """Logs the provided message to the user log file.

    :param msg the message to log
    """
    logging.getLogger("user").debug(str(msg))


def format_name(name):
    """Returns the name formatted as valid python variable name.

    :param name the name to format
    :return name formatted to be suitable as a python variable name
    """
    return re.sub("[^A-Za-z]", "", name.lower()[0]) + \
        re.sub("[^A-Za-z0-9]", "", name.lower()[1:])


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


def hat_tuple_to_direction(value):
    """Converts a hat event direction value to it's textual equivalent.

    :param value direction tuple from a hat event
    :return textual equivalent of the event tuple
    """
    lookup = {
        ( 0,  0): "center",
        ( 0,  1): "north",
        ( 1,  1): "north-east",
        ( 1,  0): "east",
        ( 1, -1): "south-east",
        ( 0, -1): "south",
        (-1, -1): "south-west",
        (-1,  0): "west",
        (-1,  1): "north-west",
    }
    return lookup[value]


def hat_direction_to_tuple(value):
    """Converts a direction string to a tuple value.

    :param value textual representation of a hat direction
    :return tuple corresponding to the textual direction
    """
    lookup = {
        "center": (0, 0),
        "north": (0, 1),
        "north-east": (1, 1),
        "east": (1, 0),
        "south-east": (1, -1),
        "south": (0, -1),
        "south-west": (-1, -1),
        "west": (-1, 0),
        "north-west": (-1, 1)
    }
    return lookup[value]


def userprofile_path():
    """Returns the path to the user's profile folder, %userprofile%."""
    return os.path.abspath(os.path.join(
        os.getenv("userprofile"),
        "Joystick Gremlin")
    )


def setup_userprofile():
    """Initializes the data folder in the user's profile folder."""
    folder = userprofile_path()
    if not os.path.exists(folder):
        try:
            os.mkdir(folder)
        except Exception as e:
            raise error.GremlinError(
                "Unable to create data folder: {}".format(str(e))
            )
    elif not os.path.isdir(folder):
        raise error.GremlinError(
            "Data folder exists but is not a folder"
        )


def device_id_duplicates(device):
    """Returns a unique id for the provided device.

    This function is intended to be used when device of identical type
    are present.

    :param device the object with device related information
    :return unique identifier of this device
    """
    return device.hardware_id, device.windows_id


def device_id_unique(device):
    """Returns a unique id for the provided device.

    This function is intended to be used when all devices are
    distinguishable by their hardware id.

    :param device the object with device related information
    :return unique identifier of this device
    """
    return device.hardware_id


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


def get_device_id(hardware_id, windows_id):
    """Returns the correct device id given both hardware and windows id.

    :param hardware_id the hardware id of the device
    :param windows_id the windows id of the device
    :return correct combination of hardware and windows id
    """
    if g_duplicate_devices:
        return hardware_id, windows_id
    else:
        return hardware_id


def setup_duplicate_joysticks():
    """Detects if multiple identical devices are connected and performs
    appropriate setup.
    """
    devices = joystick_handling.joystick_devices()

    # Check if we have duplicate items
    entries = [dev.hardware_id for dev in devices]
    duplicate_devices = len(entries) != len(set(entries))

    # Create appropriate device_id generator
    if duplicate_devices:
        device_id_fn = device_id_duplicates
    else:
        device_id_fn = device_id_unique
    setup_duplicate_devices(device_id_fn, duplicate_devices)


def clear_layout(layout):
    """Removes all items from the given layout.

    :param layout the layout from which to remove all items
    """
    while layout.count() > 0:
        child = layout.takeAt(0)
        if child.layout():
            clear_layout(child.layout())
        elif child.widget():
            child.widget().hide()
            child.widget().deleteLater()
        layout.removeItem(child)


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


def load_module(name):
    """Imports  the given module.

    :param name the name of the module
    :return the loaded module
    """
    global g_loaded_modules
    if name in g_loaded_modules:
        importlib.reload(g_loaded_modules[name])
    else:
        g_loaded_modules[name] = importlib.import_module(name)
    return g_loaded_modules[name]
