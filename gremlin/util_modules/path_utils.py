# -*- coding: utf-8; -*-

"""Path and resource utilities.

This module contains utilities for path resolution and resource location.
Extracted from gremlin.util.

Functions:
- resource_path() - Resolves resource paths (PyInstaller compatible)
- userprofile_path() - Returns user profile directory path
"""

import os
from pathlib import Path
import sys

__all__ = [
    "resource_path",
    "userprofile_path",
]


def userprofile_path() -> str:
    """Returns the path to the user's profile folder, %userprofile%.

    Returns:
        Path to the user's profile folder
    """
    user_profile = os.getenv("userprofile")
    if user_profile:
        return str((Path(user_profile) / "Joystick Gremlin").resolve())
    else:
        # Fallback for non-Windows systems
        return str((Path.home() / "Joystick Gremlin").resolve())


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, handling development and pyinstaller
    based usage.

    Args:
        relative_path: the relative path to the file of interest

    Returns:
        properly normalized resource path
    """
    gremlin_root = Path(__file__).resolve().parent.parent.parent
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        gremlin_root = Path(getattr(sys, '_MEIPASS')).resolve()

    return str(gremlin_root / relative_path)
