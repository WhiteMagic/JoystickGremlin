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

"""Utility functions for Joystick Gremlin.

This module provides backward-compatible re-exports from the refactored
util_modules package. All functionality has been split into focused modules:

- util_modules.xml_helpers: XML parsing and property handling
- util_modules.calibration: Axis calibration utilities
- util_modules.path_utils: Path and resource resolution
- util_modules.file_operations: File I/O and monitoring
- util_modules.misc: Miscellaneous utilities

For new code, prefer importing directly from the specific modules.
This module maintains compatibility with existing code.
"""

# Re-export all functions from util_modules for backward compatibility
from gremlin.util_modules.xml_helpers import (
    read_bool,
    parse_bool,
    parse_id_or_uuid,
    safe_read,
    safe_format,
    read_property,
    read_properties,
    create_property_node,
    append_property_nodes,
    create_node_from_data,
    create_subelement_node,
    read_subelement,
    create_action_node,
    read_action_id,
    read_action_ids,
    create_action_ids,
    read_uuid,
    determine_value_type,
    property_from_string,
    property_to_string,
)

from gremlin.util_modules.calibration import (
    create_calibration_function,
    with_center_calibration,
    no_center_calibration,
)

from gremlin.util_modules.path_utils import (
    resource_path,
    userprofile_path,
)

from gremlin.util_modules.file_operations import (
    FileWatcher,
)

from gremlin.util_modules.misc import (
    clamp,
    rad2deg,
    deg2rad,
    hat_tuple_to_direction,
    hat_direction_to_tuple,
    dill_hat_lookup,
    format_name,
    valid_python_identifier,
    display_error,
    log,
    get_guid,
    load_module,
    truncate,
    setup_userprofile,
    file_exists_and_is_accessible,
)

# Export all for backward compatibility
__all__ = [
    # XML helpers
    "read_bool",
    "parse_bool",
    "parse_id_or_uuid",
    "safe_read",
    "safe_format",
    "read_property",
    "read_properties",
    "create_property_node",
    "append_property_nodes",
    "create_node_from_data",
    "create_subelement_node",
    "read_subelement",
    "create_action_node",
    "read_action_id",
    "read_action_ids",
    "create_action_ids",
    "read_uuid",
    "determine_value_type",
    "property_from_string",
    "property_to_string",
    # Calibration
    "create_calibration_function",
    "with_center_calibration",
    "no_center_calibration",
    # Path utilities
    "resource_path",
    "userprofile_path",
    # File operations
    "FileWatcher",
    # Miscellaneous
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
