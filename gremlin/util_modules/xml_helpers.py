# -*- coding: utf-8; -*-

"""XML parsing and property handling utilities.

This module contains utilities for XML parsing, property handling,
and type conversion. Extracted from gremlin.util for better organization.

Functions are categorized by purpose:
- Boolean parsing: read_bool, parse_bool
- Type-safe reading: safe_read, safe_format
- Property handling: read_property, create_property_node
- Subelement handling: read_subelement, create_subelement_node
- Action handling: read_action_id, read_action_ids
- UUID handling: read_uuid
- General XML: create_node_from_data

Note: This is a planned extraction. Implementation pending to avoid
breaking changes. See REFACTORING_STRATEGY.md for full plan.
"""

from typing import Any, Callable, List, Optional, Tuple
from xml.etree import ElementTree
import uuid

from gremlin import error
from gremlin.types import PropertyType

# This module will contain approximately 20 functions from util.py:
# - read_bool()
# - parse_bool()
# - parse_id_or_uuid()
# - safe_read()
# - safe_format()
# - read_property()
# - read_properties()
# - _process_property()
# - create_property_node()
# - append_property_nodes()
# - create_node_from_data()
# - create_subelement_node()
# - read_subelement()
# - create_action_node()
# - read_action_id()
# - read_action_ids()
# - read_uuid()
# - determine_value_type()
# - property_to_string()
# - Plus supporting dictionaries (_property_from_string, etc.)

__all__ = [
    # To be populated during implementation
]

# Implementation note:
# Functions will be extracted from gremlin/util.py lines ~86-686
# with all supporting dictionaries and type converters.
