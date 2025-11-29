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

import ctypes
import importlib
import logging
import math
import os
from pathlib import Path
import re
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore, QtWidgets

import dill
from dill import GUID

from gremlin import error
from gremlin.types import AxisButtonDirection, AxisMode, HatDirection, \
    InputType, Point2D, PropertyType, ActionActivationMode, ScriptVariableType

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


def read_bool(node: ElementTree.Element, key: str, default_value: bool = False) -> bool:
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
    except error.ProfileError:
        return default_value


def parse_id_or_uuid(value: str) -> int | uuid.UUID:
    """Attempts to parse an identifier value.

    Exects the string to represent either an integer or UUID value.

    Args:
        value: the string to parse

    Returns:
        The integer or UUID representation of the provided string
    """
    if value.isdigit():
        return int(value)
    else:
        try:
            return uuid.UUID(value)
        except ValueError:
            raise error.ProfileError(f"Invalid type for value '{value}'")



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
    elif isinstance(value, bool):
        return value

    # Attempt to parse the value
    if value.isnumeric():
        int_value = int(value)
        if int(value) in [0, 1]:
            return int_value == 1
        else:
            raise error.ProfileError(f"Invalid bool value used: {value}")
    elif value.lower() in ["true", "false"]:
        return True if value.lower() == "true" else False
    else:
        raise error.ProfileError(
            f"Invalid bool type/value used: {type(value)}/{value}"
        )


def safe_read(
        node: ElementTree.Element,
        key: str,
        type_cast: Optional[Callable[[str], Any]] = None,
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
            raise error.ProfileError(msg)
    else:
        value = node.get(key)

    if type_cast is not None:
        try:
            value = type_cast(value)
        except ValueError:
            msg = f"Failed casting '{value}' to type '{str(type_cast)}'"
            logging.getLogger("system").error(msg)
            raise error.ProfileError(msg)
    return value


def safe_format(
        value: Any,
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
        raise error.ProfileError(
            f"Value '{value}' has type {type(value)} "
            f"when {data_type} is expected"
        )


# Mapping between property types and the function converting the string
# representation into the correct data type
_property_from_string = {
    PropertyType.String: str,
    PropertyType.Int: int,
    PropertyType.Float: float,
    PropertyType.Bool: lambda x: parse_bool(x, False),
    PropertyType.InputType: lambda x: InputType.to_enum(x),
    PropertyType.AxisMode: lambda x: AxisMode.to_enum(x),
    PropertyType.HatDirection: lambda x: HatDirection.to_enum(x),
    PropertyType.UUID: lambda x: uuid.UUID(x),
    PropertyType.Selection: str,
    PropertyType.ActionActivationMode: lambda x: ActionActivationMode.to_enum(x),
    PropertyType.Point2D: lambda x: Point2D.from_string(x),
    PropertyType.Path: Path,
}

def property_from_string(data_type: PropertyType, value: str) -> Any:
    """Converts the provided string to the indicated type.

    Args:
        data_type: type of data into which to convert the string representation
        value: string representation of the data to convert

    Returns:
        Converted data
    """
    if data_type not in _property_from_string:
        raise error.GremlinError(
            f"No known conversion from string to data type '{data_type}'"
        )
    return _property_from_string[data_type](value)


_property_to_string = {
    PropertyType.String: str,
    PropertyType.Int: str,
    PropertyType.Float: str,
    PropertyType.Bool: str,
    PropertyType.InputType: lambda x: InputType.to_string(x),
    PropertyType.AxisMode: lambda x: AxisMode.to_string(x),
    PropertyType.HatDirection: lambda x: HatDirection.to_string(x),
    PropertyType.UUID: str,
    PropertyType.Selection: str,
    PropertyType.ActionActivationMode: lambda x: ActionActivationMode.to_string(x),
    PropertyType.Point2D: lambda x: x.to_string(),
    PropertyType.Path: str,
}

def property_to_string(data_type: PropertyType, value: Any) -> str:
    """Converts a value of a given data type into a string representation.

    Args:
        data_type: type of data to convert into a string representation
        value: data to be converted to a string

    Returns:
        String representation of the original data
    """
    if data_type not in _property_to_string:
        raise error.GremlinError(
            f"No known conversion to string for data of type '{data_type}"
        )

    return _property_to_string[data_type](value)


_type_lookup = {
    PropertyType.String: str,
    PropertyType.Int: int,
    PropertyType.Float: float,
    PropertyType.Bool: bool,
    PropertyType.AxisValue: None,
    PropertyType.IntRange: None,
    PropertyType.FloatRange: None,
    PropertyType.AxisRange: None,
    PropertyType.InputType: InputType,
    PropertyType.KeyboardKey: None,
    PropertyType.MouseInput: None,
    PropertyType.UUID: uuid.UUID,
    PropertyType.AxisMode: AxisMode,
    PropertyType.HatDirection: HatDirection,
    PropertyType.List: list,
    PropertyType.Selection: str,
    PropertyType.ActionActivationMode: ActionActivationMode,
    PropertyType.Point2D: Point2D,
    PropertyType.ScriptVariableType: ScriptVariableType,
    PropertyType.Path: Path,
}

_element_parsers = {
    "device-id": lambda x: uuid.UUID(x.text),
    "device-name": lambda x: str(x.text),
    "input-type": lambda x: InputType.to_enum(x.text),
    "input-id": lambda x: parse_id_or_uuid(x.text),
    "mode": lambda x: str(x.text),
    "description": lambda x: str(x.text) if x.text else "",
    "behavior": lambda x: InputType.to_enum(x.text),
    "root-action": lambda x: uuid.UUID(x.text),
    "lower-limit": lambda x: float(x.text),
    "upper-limit": lambda x: float(x.text),
    "axis-button-direction": lambda x: AxisButtonDirection.to_enum(x.text),
    "hat-direction": lambda x: HatDirection.to_enum(x.text),
    "label": lambda x: str(x.text),
    "plugin-variable-type": lambda x: ScriptVariableType.to_enum(x.text),
}

_element_types = {
    "device-id": [uuid.UUID],
    "device-name": [str],
    "input-type": [InputType],
    "input-id": [int, uuid.UUID],
    "mode": [str],
    "description": [str],
    "behavior": [InputType],
    "root-action": [uuid.UUID],
    "lower-limit": [float],
    "upper-limit": [float],
    "axis-button-direction": [AxisButtonDirection],
    "hat-direction": [HatDirection],
    "label": [str],
    "plugin-variable-type": [ScriptVariableType],
}

_element_to_string = {
    "device-id": str,
    "device-name": str,
    "input-type": lambda x: InputType.to_string(x),
    "input-id": str,
    "mode": str,
    "description": str,
    "behavior": lambda x: InputType.to_string(x),
    "root-action": str,
    "lower-limit": str,
    "upper-limit": str,
    "axis-button-direction": lambda x: AxisButtonDirection.to_string(x),
    "hat-direction": lambda x: HatDirection.to_string(x),
    "label": str,
    "plugin-variable-type": lambda x: ScriptVariableType.to_string(x),
}

def create_subelement_node(
        name: str,
        value: Any
) -> ElementTree.Element:
    """Creates an <input> subelement.

    Args:
        name: name of the element being created
        value: content of the element being created
    """
    if name not in _element_types:
        raise error.ProfileError(
            f"No input subelement with name '{name} exists"
        )
    if type(value) not in _element_types[name]:
        raise error.ProfileError(
            f"Incorrect value type for subelement with name '{name}"
        )

    node = ElementTree.Element(name)
    node.text = _element_to_string[name](value)
    return node


def create_node_from_data(
        node_name: str,
        properties: List[Tuple[str, Any, PropertyType]]
) -> ElementTree.Element:
    """Returns an XML node with the given name and property elements.

    Args:
        node_name: name of the node to create
        properties: list of values from which to create property entries

    Returns:
        XML element node with the given name and property nodes
    """
    node = ElementTree.Element(node_name)
    for entry in properties:
        node.append(create_property_node(entry[0], entry[1], entry[2]))
    return node


def create_property_node(
        name: str,
        value: Any,
        property_type: PropertyType | List[PropertyType]
) -> ElementTree.Element:
    """Creates a <property> profile element.

    Args:
        name: content of the name element
        value: content of the value element
        property_type: type or list of types the property value should be of

    Returns:
        A property element containing the provided name and value data.
    """
    value_type, is_valid = determine_value_type(value, property_type)
    if not is_valid:
        raise error.ProfileError(
            f"Property '{name}' has wrong type, got '{type(value)}' "
            f"for '{property_type}'."
        )

    p_node = ElementTree.Element("property")
    p_node.set("type", PropertyType.to_string(value_type))
    n_node = ElementTree.Element("name")
    n_node.text = name
    v_node = ElementTree.Element("value")
    v_node.text = property_to_string(value_type, value)
    p_node.append(n_node)
    p_node.append(v_node)
    return p_node


def append_property_nodes(
        root_node: ElementTree.Element,
        properties: List[TypeVar("PropertyData", str, Any, PropertyType)]
) -> None:
    """Creates and adds property nodes to the given root node.

    Args:
        root_node: XML node to which to append the newly created property nodes
        properties: data from which to create property nodes
    """
    for entry in properties:
        root_node.append(create_property_node(entry[0], entry[1], entry[2]))

def create_action_node(
        action_type: str,
        action_id: uuid.UUID
) -> ElementTree.Element:
    """Returns an action element populated with the provided data.

    Args:
        action_type: name of the action
        action_id: id associated with the action

    Returns:
        XML element containing the provided data
    """
    node = ElementTree.Element("action")
    node.set("id", safe_format(action_id, uuid.UUID))
    node.set("type", action_type)
    return node


def read_action_id(node: ElementTree.Element) -> uuid.UUID:
    """Returns the id associated with the given action element.

    Args:
        node: XML element which contains the id attribute

    Returns:
        UUID associated with this element
    """
    if node.tag not in ["action"]:
        raise error.ProfileError(
            f"Attempted to read id from unexpected element '{node.tag}'."
        )

    id_value = node.get("id")
    if id_value is None:
        raise error.ProfileError(
            f"Reading id entry failed due to it not being present."
        )

    try:
        return uuid.UUID(id_value)
    except Exception:
        raise error.ProfileError(
            f"Failed parsing id from value: '{id_value}'."
        )


def read_uuid(node: ElementTree.Element, tag: str, key: str) -> uuid.UUID:
    """Returns the id associated with the given action element.

    Args:
        node: XML element which contains the id attribute
        tag: expected tag of the node element
        key: key under which the id is stored

    Returns:
        UUID associated with this element
    """
    if node.tag not in [tag]:
        raise error.ProfileError(
            f"Attempted to read id from unexpected element '{node.tag}'."
        )

    id_value = node.get(key)
    if id_value is None:
        raise error.ProfileError(
            f"Reading id entry failed due to it not being present."
        )

    try:
        return uuid.UUID(id_value)
    except Exception:
        raise error.ProfileError(
            f"Failed parsing id from value: '{id_value}'."
        )


def read_subelement(node: ElementTree.Element, name: str) -> Any:
    """Returns the value of a subelement of the given element node.

    This function knows how to parse the values of a variety of standardized
    subelement names. If it is called with an unknown name an exception is
    raised. Similar if the subelement is present but of the wrong type an
    exception is raised.

    Args:
        node: the node whose subelement should be read and parsed
        name: the name of the subelement to parse

    Returns:
        Parsed value of the subelement of the given name present in the
        provided element node.
    """
    # Ensure there is a parser for the provided subelement
    if name not in _element_parsers:
        raise error.ProfileError(
            f"No parser available for subelement with name {name}"
        )

    # Ensure the subelement exists in the provided node
    element = node.find(name)
    if element is None:
        raise error.ProfileError(
            f"Element {node.tag} has no subelement with name {name}"
        )

    # Parse subelement
    return _element_parsers[name](element)


def read_property(
        action_node: ElementTree.Element,
        name: str,
        property_type: PropertyType | List[PropertyType]
) -> Any:
    """Returns the value of the property with the given name.

    Args:
        action_node: element from which to extract the property value
        name: name of the property element to return the value of
        property_type: valid PropertyType or list of valid types of the value

    Returns:
        The value of the property element of the given name
    """
    # Retrieve the individual elements
    if isinstance(property_type, PropertyType):
        property_type = [property_type]
    return _process_property(
        action_node.find(f"./property/name[.='{name}']/.."),
        name,
        property_type
    )


def read_properties(
        action_node: ElementTree.Element,
        name: str,
        property_type: PropertyType | List[PropertyType]
) -> List[Any]:
    """Returns the values of all properties with the given name.

    Args:
        action_node: element from which to extract the property values
        name: name of the property element to return the values for
        property_type: valid PropertyType or list of valid types of the value

    Returns:
        List of values corresponding to the property element of the given name
    """
    # Retrieve the individual elements
    p_nodes = action_node.findall(f"./property/name[.='{name}']/..")
    if isinstance(property_type, PropertyType):
        property_type = [property_type]
    return [_process_property(node, name, property_type) for node in p_nodes]


def _process_property(
        property_node: ElementTree.Element,
        name: str,
        property_types: List[PropertyType]
) -> Any:
    """Processes a single XML node corresponding to a specific property.

    Args:
        property_node: element which contains the value to extract
        name: name of the property element to return the value of
        property_types: List of acceptable PropertyType for the value

    Returns:
        The value of the given property element
    """
    if property_node is None:
        raise error.ProfileError(f"A property named '{name}' is missing.")

    v_node = property_node.find(f"./value")
    if v_node is None:
        raise error.ProfileError(
            f"Value element of property '{name}' is missing"
        )
    if "type" not in property_node.keys():
        raise error.ProfileError(
            f"Property element is missing the 'type' attribute."
        )

    p_type = PropertyType.to_enum(property_node.get("type"))
    if p_type not in property_types:
        raise error.ProfileError(
            f"Property type mismatch, got '{p_type}' expected one of: " +
            f"[{', '.join([str(v) for v in property_types])}]"
        )
    try:
        return _property_from_string[p_type](v_node.text)
    except Exception as e:
        raise error.ProfileError(
            f"Failed parsing property value '{v_node.text}' which "
            f"should be of type '{p_type}"
        ) from e


def read_action_ids(node: ElementTree.Element) -> List[uuid.UUID]:
    """Returns all action-id child nodes from the provided node.

    Args:
        node: XML node to parse

    Returns:
        List containing found action-id entries
    """
    ids = []
    for entry in node.iter("action-id"):
        ids.append(uuid.UUID(entry.text))
    return ids


def create_action_ids(name: str, action_ids: List[uuid.UUID]) -> ElementTree.Element:
    """Returns a node containing the given action ids.

    Args:
        name: name of the node to generate
        action_ids: uuid to enter as action ids
    Returns:
        XML node containing the action ids grouped under a single node
    """
    node = ElementTree.Element(name)
    for uuid in action_ids:
        entry = ElementTree.Element("action-id")
        entry.text = str(uuid)
        node.append(entry)
    return node


def determine_value_type(
        value: Any,
        property_type: PropertyType | List[PropertyType]
) -> [PropertyType, bool]:
    """Returns whether a value is of the correct type and the type..

    Args:
        value: the value to check for type correctness
        property_type: the type or list of types valid for the given value

    Returns:
        The property type of the value from the list of properties and if
        a valid value type was present.
    """
    is_valid = False
    value_type = None
    if isinstance(property_type, PropertyType):
        is_valid = isinstance(value, _type_lookup[property_type])
        if is_valid:
            value_type = property_type
    else:
        for pt in property_type:
            if isinstance(value, _type_lookup[pt]):
                is_valid = True
                value_type = pt
                break
    return value_type, is_valid


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
    """Returns if the user has admin privileges.

    Returns:
        True if user has admin rights, False otherwise
    """
    return ctypes.windll.shell32.IsUserAnAdmin() == 1


def with_center_calibration(
        value: int,
        low: int,
        centerLow: int,
        centerHigh: int,
        high:int
) -> float:
    """Returns the calibrated value for a normal style axis.

    Args:
        value: the raw value to process
        low: the minimum value of the axis
        centerLow: the center low value of the axis
        centerHigh: the center high value of the axis
        high: the maximum value of the axis

    Returns:
        the calibrated value in [-1, 1] corresponding to the provided raw value
    """
    value = clamp(value, low, high)
    if value < centerLow:
        return (value - centerLow) / float(centerLow - low)
    elif centerLow <= value <= centerHigh:
        return 0.0
    else:
        return (value - centerHigh) / float(high - centerHigh)


def with_default_center_calibration(value: int) -> float:
    """Returns with_center_calibration with DirectInput default values."""
    return with_center_calibration(value, -32768, 0, 0, 32767)


def no_center_calibration(value: int, minimum: int, maximum: int) -> float:
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
        low: int,
        centerLow: int,
        centerHigh: int,
        high:int,
        has_center: bool
) -> Callable[[int], float]:
    """Returns a calibration function appropriate for the provided data.

    Args:
        low: the lower bound of the calibration function
        centerLow: the lower value around the center of the calibration function
        centerHigh: the upper value around the center of the calibration function
        high: the upper bound of the calibration function
        has_center: True if the calibration is for an axis with a center

    Returns:
        function which returns a value in [-1, 1] corresponding
        to the provided raw input value
    """
    if has_center:
        return lambda x: with_center_calibration(x, low, centerLow, centerHigh, high)
    else:
        return lambda x: no_center_calibration(x, low, high)


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


def userprofile_path() -> str:
    """Returns the path to the user's profile folder, %userprofile%.

    Returns:
        Path to the user's profile folder
    """
    return str((Path(os.getenv("userprofile")) / "Joystick Gremlin").resolve())


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, handling development and pyinstaller
    based usage.

    Args:
        relative_path: the relative path to the file of interest

    Returns:
        properly normalized resource path
    """
    gremlin_root = Path(__file__).resolve().parent.parent
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if "_MEIPASS" in sys.__dict__:
        gremlin_root = Path(sys._MEIPASS).resolve()

    return str(gremlin_root / relative_path)


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


def clamp_analog_axis(value: float) -> float:
    """Returns the value clamped to the Gremlin standard range of [-1, 1].

    Args:
        value: The value to clamp.

    Returns:
        The value, clamped to [-1, 1].
    """
    return clamp(value, -1.0, 1.0)


def setup_userprofile() -> None:
    """Initializes the data folder in the user's profile folder."""
    folder = userprofile_path()
    if not os.path.exists(folder):
        try:
            os.mkdir(folder)
        except Exception as e:
            raise error.GremlinError(f"Unable to create data folder: {str(e)}")
    elif not os.path.isdir(folder):
        raise error.GremlinError("Data folder exists but is not a folder")


_dill_hat_lookup = {
    -1: HatDirection.Center,
    0: HatDirection.North,
    4500: HatDirection.NorthEast,
    9000: HatDirection.East,
    13500: HatDirection.SouthEast,
    18000: HatDirection.South,
    22500: HatDirection.SouthWest,
    27000: HatDirection.West,
    31500: HatDirection.NorthWest
}

def dill_hat_lookup(value: int) -> HatDirection:
    """Returns the HatDirection corresponding to the raw value if exact, else "Center".

    Args:
        value: raw hat value to convert

    Returns:
        HatDirection corresponding to the raw value if exact, else "Center".
    """
    return _dill_hat_lookup.get(value, HatDirection.Center)


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


def file_exists_and_is_accessible(filename: str) -> bool:
    """Returns true when a provided filename exists and can be read."""

    return (
        isinstance(filename, str) and
        len(filename) > 0 and
        os.path.isfile(filename) and
        os.access(filename, os.R_OK)
        )
