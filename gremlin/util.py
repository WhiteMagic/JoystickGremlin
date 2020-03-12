# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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
import math
import os
import re
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import uuid
from xml.etree import ElementTree

from PySide2 import QtCore, QtWidgets

import dill

import gremlin.error


# Table storing which modules have been imported already
g_loaded_modules = {}


class FileWatcher(QtCore.QObject):

    """Watches files in the filesystem for changes."""

    # Signal emitted when the watched file is modified
    file_changed = QtCore.Signal(str)

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


def read_bool(node: ElementTree, key: str, default_value: bool = False) -> bool:
    """Attempts to read a boolean value.

    If there is an error when reading the given field from the node
    the default value is returned instead.

    Args:
        node: the node from which to read the value
        key: the attribute key to read from the node
        default_value: the default value to return in case of errors

    Returns:
         Boolean representation of the attribute value
    """
    try:
        return parse_bool(node.get(key), default_value)
    except gremlin.error.ProfileError:
        return default_value


def parse_bool(value: str, default_value: bool = False) -> bool:
    """Returns the boolean representation of the provided value.

    Args:
        value: the value as string to parse
        default_value: value to return in case no valid value was provided

    Returns:
        Representation of value as either True or False
    """
    # Terminate early if the value is None to start with, i.e. we know it will
    # fail
    if value is None:
        return default_value

    # Attempt to parse the value
    try:
        int_value = int(value)
        if int_value in [0, 1]:
            return int_value == 1
        else:
            raise gremlin.error.ProfileError(
                f"Invalid bool value used: {value}"
            )
    except ValueError:
        if value.lower() in ["true", "false"]:
            return True if value.lower() == "true" else False
        else:
            raise gremlin.error.ProfileError(
                f"Invalid bool value used: {value}"
            )
    except TypeError:
        raise gremlin.error.ProfileError(
            f"Invalid type provided: {type(value)}"
        )


def parse_guid(value: str) -> dill.GUID:
    """Reads a string GUID representation into the internal data format.

    This transforms a GUID of the form {B4CA5720-11D0-11E9-8002-444553540000}
    into the underlying raw and exposed objects used within Gremlin.

    Args:
        value: the string representation of the GUID

    Returns:
        dill.GUID object representing the provided value
    """
    try:
        tmp = uuid.UUID(value)
        raw_guid = dill._GUID()
        raw_guid.Data1 = int.from_bytes(tmp.bytes[0:4], "big")
        raw_guid.Data2 = int.from_bytes(tmp.bytes[4:6], "big")
        raw_guid.Data3 = int.from_bytes(tmp.bytes[6:8], "big")
        for i in range(8):
            raw_guid.Data4[i] = tmp.bytes[8 + i]

        return dill.GUID(raw_guid)
    except (ValueError, AttributeError) as e:
        raise gremlin.error.GremlinError(
            f"Failed parsing GUID from value {value}"
        )


def write_guid(guid: dill.GUID) -> str:
    """Returns the string representation of a GUID object.

    Args:
        guid: the GUID object to turn into a string

    Returns:
        string representation of the guid object
    """
    return str(guid)


def safe_read(
        node: ElementTree,
        key: str,
        type_cast: Callable[[str], Any],
        default_value: Optional[Any] = None
) -> Any:
    """Safely reads an attribute from an XML node.

    If the attempt at reading the attribute fails, due to the attribute not
    being present, an exception will be thrown.

    Args:
        node: the XML node from which to read an attribute
        key: the attribute to read
        type_cast: the type to which to cast the read value, if specified
        default_value: value to return in case the key is not present

    Returns:
        the value stored in the node with the given key
    """
    # Attempt to read the value and if present use the provided default value
    # in case reading fails
    value = default_value
    if key not in node.keys():
        if default_value is None:
            msg = f"Attempted to read attribute '{key}' which does not exist."
            logging.getLogger("system").error(msg)
            raise gremlin.error.ProfileError(msg)
    else:
        value = node.get(key)

    if type_cast is not None:
        try:
            value = type_cast(value)
        except ValueError:
            msg = f"Failed casting '{value}' to type '{str(type_cast)}'"
            logging.getLogger("system").error(msg)
            raise gremlin.error.ProfileError(msg)
    return value


def safe_format(
        value: str,
        data_type: Any,
        formatter: Callable[[Any], str] = str
) -> str:
    """Returns a formatted value ensuring type correctness.

    This function ensures that the value being formatted is of correct type
    before attempting formatting. Raises an exception on non-matching data
    types.

    Args:
        value: the value to format
        data_type: expected data type of the value
        formatter: function to format value with

    Returns:
        value formatted according to formatter
    """
    if isinstance(value, data_type):
        return formatter(value)
    else:
        raise gremlin.error.ProfileError(
            f"Value '{value}' has type {type(value)} when {data_type} is expected")


# Mapping between property types and the function converting the string
# representation into the correct data type
_property_conversion = {
    "string": str,
    "int": int,
    "float": float,
    "bool": lambda x: parse_bool(x, False)
}


def parse_properties(node: ElementTree) -> Dict[str, Any]:
    """Extracts all property entries below the given node.

    This function will extract all property elements that are child elements
    of the given node and perform data validity checks based on the property
    information.

    Args:
        node: XML node whose child property element contents are to be extracted

    Returns:
        dictionary containing key valud pairs representing the properties
    """
    properties = {}
    for pnode in node.findall("./property"):
        # Ensure the property element contains the required information
        if "type" not in pnode.keys():
            raise gremlin.error.ProfileError("Invalid property element.")
        value_type = pnode.get("type")
        if value_type not in _property_conversion:
            raise gremlin.error.ProfileError(
                f"Invalid property type {value_type} present"
            )
        name_node = pnode.find("./name")
        value_node = pnode.find("./value")
        if name_node is None:
            raise gremlin.error.ProfileError(
                "<name> element missing property element"
            )
        if value_node is None:
            raise gremlin.error.ProfileError(
                "<value> element missing property element"
            )

        # Extract data and store it in the dictionary
        try:
            properties[name_node.text] = \
                _property_conversion[value_type](value_node.text)
        except Exception as e:
            raise gremlin.error.ProfileError(
                f"Type conversion of value '{value_node.text}' to type "
                f"'{value_type}' failed"
            )
    return properties


def all_properties_present(keys: List[str], properties: Dict[str, Any]) -> bool:
    """Checks if all listed keys are present in the properties dictionary.

    Args:
        keys: list of dictionary keys that have to exist
        properties: dictionary with properties

    Returns:
        True if all provided keys exist in the properties dictionary, False
        otherwise
    """
    for key in keys:
        if key not in properties:
            return False
    return True


def is_user_admin():
    """Returns whether or not the user has admin privileges.

    Returns:
        True if user has admin rights, False otherwise
    """
    return ctypes.windll.shell32.IsUserAnAdmin() == 1


def axis_calibration(
        value: float,
        minimum: float,
        center: float,
        maximum: float
) -> float:
    """Returns the calibrated value for a normal style axis.

    Args:
        value: the raw value to process
        minimum: the minimum value of the axis
        center: the center value of the axis
        maximum: the maximum value of the axis

    Returns:
        the calibrated value in [-1, 1] corresponding to the provided raw value
    """
    value = clamp(value, minimum, maximum)
    if value < center:
        return (value - center) / float(center - minimum)
    else:
        return (value - center) / float(maximum - center)


def slider_calibration(value: float, minimum: float, maximum: float) -> float:
    """Returns the calibrated value for a slider type axis.

    Args:
        value: the raw value to process
        minimum: the minimum value of the axis
        maximum: the maximum value of the axis

    Returns:
        the calibrated value in [-1, 1] corresponding to the provided raw value
    """
    value = clamp(value, minimum, maximum)
    return (value - minimum) / float(maximum - minimum) * 2.0 - 1.0


def create_calibration_function(
        minimum: float,
        center: float,
        maximum:float
) -> Callable[[float], float]:
    """Returns a calibration function appropriate for the provided data.

    Args:
        minimum: the minimal value ever reported
        center: the value in the neutral position
        maximum: the maximal value ever reported

    Returns:
        function which returns a value in [-1, 1] corresponding
        to the provided raw input value
    """
    if minimum == center or maximum == center:
        return lambda x: slider_calibration(x, minimum, maximum)
    else:
        return lambda x: axis_calibration(x, minimum, center, maximum)


def truncate(text: str, left_size: int, right_size: int) -> str:
    """Returns a truncated string matching the specified character counts.

    Args:
        text: the text to truncate
        left_size: number of characters on the left side
        right_size: number of characters on the right side

    Returns:
        string truncated to the specified character counts if required
    """
    if len(text) < left_size + right_size:
        return text

    return f"{text[:left_size]}...{text[-right_size:]}"


def script_path() -> str:
    """Returns the path to the scripts location.

    Returns:
        path to the scripts location
    """
    return os.path.normcase(
        os.path.dirname(os.path.abspath(os.path.realpath(sys.argv[0])))
    )


def userprofile_path() -> str:
    """Returns the path to the user's profile folder, %userprofile%.

    Returns:
        Path to the user's profile folder
    """
    return os.path.normcase(os.path.abspath(os.path.join(
        os.getenv("userprofile"),
        "Joystick Gremlin")
    ))


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, handling development and pyinstaller
    based usage.

    Args:
        relative_path: the relative path to the file of interest

    Returns:
        properly normalized resource path
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = script_path()

    return os.path.normcase(os.path.join(base_path, relative_path))


def display_error(msg: str) -> None:
    """Displays the provided error message to the user.

    Args:
        msg: the error message to display
    """
    box = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Critical,
        "Error",
        msg,
        QtWidgets.QMessageBox.Ok
    )
    box.exec()


def log(msg: str) -> None:
    """Logs the provided message to the user log file.

    Args:
        msg: the message to log
    """
    logging.getLogger("user").debug(str(msg))


def format_name(name: str) -> str:
    """Returns the name formatted as valid python variable name.

    Args:
        name: the name to format

    Returns:
        name formatted to be suitable as a python variable name
    """
    return re.sub("[^A-Za-z]", "", name.lower()[0]) + \
        re.sub("[^A-Za-z0-9]", "", name.lower()[1:])


def valid_python_identifier(name: str) -> bool:
    """Returns whether a given name is a valid python identifier.

    Args:
        name: the name to check for validity

    Returns:
        True if the name is a valid identifier, False otherwise
    """
    return re.match(r"^[^\d\W]\w*\Z", name) is not None


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Returns the value clamped to the provided range.

    Args:
        value: the input value
        min_val: minimum value
        max_val: maximum value

    Returns:
        the input value clamped to the provided range
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


def setup_userprofile() -> None:
    """Initializes the data folder in the user's profile folder."""
    folder = userprofile_path()
    if not os.path.exists(folder):
        try:
            os.mkdir(folder)
        except Exception as e:
            raise gremlin.error.GremlinError(
                f"Unable to create data folder: {str(e)}"
            )
    elif not os.path.isdir(folder):
        raise gremlin.error.GremlinError(
            "Data folder exists but is not a folder"
        )


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


dill_hat_lookup = {
    -1: (0, 0),
    0: (0, 1),
    4500: (1, 1),
    9000: (1, 0),
    13500: (1, -1),
    18000: (0, -1),
    22500: (-1, -1),
    27000: (-1, 0),
    31500: (-1, 1)
}


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


def deg2rad(angle: float) -> float:
    """Returns radian value of the provided angle in degree.

    Args:
        angle: angle in degrees

    Returns:
        angle in radian
    """
    return angle * (math.pi / 180.0)


def rad2deg(angle: float) -> float:
    """Returns degree value of the provided angle in radian.

    Args:
        angle: angle in radian

    Returns:
        angle in degree
    """
    return angle * (180.0 / math.pi)
