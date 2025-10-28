# -*- coding: utf-8; -*-

"""Miscellaneous utility functions.

This module contains various utility functions that don't fit into
other categories. Extracted from gremlin.util.

Functions:
- clamp() - Clamp value to range
- rad2deg(), deg2rad() - Angle conversions  
- hat_tuple_to_direction(), hat_direction_to_tuple() - Hat conversions
- dill_hat_lookup() - DILL hat value conversion
- format_name() - Format string for valid Python identifier
- valid_python_identifier() - Validate Python identifier names
- display_error() - Display error dialogs
- log() - Log messages to user log
- get_guid() - Generate GUIDs
- load_module() - Dynamic module loading
- truncate() - String truncation with ellipsis
- setup_userprofile() - Initialize user profile folder
- file_exists_and_is_accessible() - Check file accessibility
"""

import importlib
import logging
import math
import os
import re
from typing import Any, Tuple
import uuid

from PySide6 import QtWidgets

from gremlin import error

# Table storing which modules have been imported already
g_loaded_modules = {}

__all__ = [
    "clamp",
    "rad2deg",
    "deg2rad",
    "hat_tuple_to_direction",
    "hat_direction_to_tuple",
    "dill_hat_lookup",
    "format_name",
    "valid_python_identifier",
    "display_error",
    "log",
    "get_guid",
    "load_module",
    "truncate",
    "setup_userprofile",
    "file_exists_and_is_accessible",
]


# =============================================================================
# Math Utilities
# =============================================================================

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


# =============================================================================
# Hat Direction Utilities
# =============================================================================

def hat_tuple_to_direction(value: Tuple[int, int]) -> str:
    """Converts a hat event direction value to it's textual equivalent.

    Args:
        value: direction tuple from a hat event

    Returns:
        textual equivalent of the event tuple
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
    return lookup.get(value, "center")


def hat_direction_to_tuple(value: str) -> Tuple[int, int]:
    """Converts a direction string to a tuple value.

    Args:
        value: textual representation of a hat direction

    Returns:
        tuple corresponding to the textual direction
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
    return lookup.get(value, (0, 0))


_dill_hat_lookup_table = {
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


def dill_hat_lookup(value: int) -> Tuple[int, int]:
    """Returns the tuple representation of a hat direction from raw value.

    Args:
        value: raw hat value to convert

    Returns:
        Tuple representing the hat direction
    """
    return _dill_hat_lookup_table.get(value, (0, 0))


# =============================================================================
# String Utilities
# =============================================================================

def format_name(name: str) -> str:
    """Returns the name formatted as valid python variable name.

    Args:
        name: the name to format

    Returns:
        name formatted to be suitable as a python variable name
    """
    if not name:
        return ""
    
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


# =============================================================================
# UI Utilities
# =============================================================================

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


# =============================================================================
# Logging and Debugging
# =============================================================================

def log(msg: str) -> None:
    """Logs the provided message to the user log file.

    Args:
        msg: the message to log
    """
    logging.getLogger("user").debug(str(msg))


# =============================================================================
# ID Generation
# =============================================================================

def get_guid() -> uuid.UUID:
    """Generates and returns a new GUID.

    Returns:
        A new UUID4 identifier
    """
    return uuid.uuid4()


# =============================================================================
# Module Loading
# =============================================================================

def load_module(name: str) -> Any:
    """Imports the given module.

    Args:
        name: the name of the module to import

    Returns:
        the loaded module
    """
    global g_loaded_modules
    if name in g_loaded_modules:
        importlib.reload(g_loaded_modules[name])
    else:
        g_loaded_modules[name] = importlib.import_module(name)
    return g_loaded_modules[name]


# =============================================================================
# File and Path Utilities
# =============================================================================

def file_exists_and_is_accessible(filename: str) -> bool:
    """Returns true when a provided filename exists and can be read.

    Args:
        filename: path to the file to check

    Returns:
        True if file exists and is readable, False otherwise
    """
    return (
        isinstance(filename, str) and
        len(filename) > 0 and
        os.path.isfile(filename) and
        os.access(filename, os.R_OK)
    )


def setup_userprofile() -> None:
    """Initializes the data folder in the user's profile folder.

    Raises:
        GremlinError: If folder creation fails
    """
    from .path_utils import userprofile_path
    
    folder = userprofile_path()
    if not os.path.exists(folder):
        try:
            os.mkdir(folder)
        except Exception as e:
            raise error.GremlinError(f"Unable to create data folder: {str(e)}")
    elif not os.path.isdir(folder):
        raise error.GremlinError("Data folder exists but is not a folder")
