# -*- coding: utf-8; -*-

"""Miscellaneous utility functions.

This module contains various utility functions that don't fit into
other categories. Extracted from gremlin.util.

Functions:
- clamp() - Clamp value to range
- rad2deg(), deg2rad() - Angle conversions  
- axis_value_to_direction() - Convert axis value to direction
- hat_tuple_to_direction(), hat_direction_to_tuple() - Hat conversions
- format_name() - Format string for display
- valid_mode_name() - Validate mode names
- display_error() - Display error dialogs
- get_guid() - Generate GUIDs
- And more utility functions
"""

import math
from typing import Any, Tuple, Optional

from PySide6 import QtWidgets
import uuid

from gremlin.types import AxisButtonDirection, HatDirection, Point2D

__all__ = [
    # To be populated during implementation
]

# Implementation note:
# Approximately 17 miscellaneous utility functions will be extracted
# from gremlin/util.py including:
# - Math utilities (clamp, angle conversions)
# - Direction/Hat utilities
# - String formatting utilities
# - Error display utilities
# - GUID generation
# - Module loading utilities
