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
"""

from typing import Any, Callable, List, Optional, Tuple
from xml.etree import ElementTree
import uuid

from gremlin import error
from gremlin.types import (
    PropertyType, InputType, AxisMode, HatDirection, AxisButtonDirection,
    ActionActivationMode, Point2D, ScriptVariableType
)

__all__ = [
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
]


# =============================================================================
# Type Conversion Dictionaries
# =============================================================================

_property_from_string = {
    PropertyType.String: str,
    PropertyType.Int: int,
    PropertyType.Float: float,
    PropertyType.Bool: lambda x: parse_bool(x, False),
    PropertyType.InputType: lambda x: InputType.to_enum(x),
    PropertyType.AxisMode: lambda x: AxisMode.to_enum(x),
    PropertyType.HatDirection: lambda x: HatDirection.to_enum(x),
    PropertyType.List: lambda x: x.split("|"),
    PropertyType.UUID: lambda x: uuid.UUID(x),
    PropertyType.Selection: str,
    PropertyType.ActionActivationMode: lambda x: ActionActivationMode.to_enum(x),
    PropertyType.Point2D: lambda x: Point2D.from_string(x),
}

_property_to_string = {
    PropertyType.String: str,
    PropertyType.Int: str,
    PropertyType.Float: str,
    PropertyType.Bool: str,
    PropertyType.InputType: lambda x: InputType.to_string(x),
    PropertyType.AxisMode: lambda x: AxisMode.to_string(x),
    PropertyType.HatDirection: lambda x: HatDirection.to_string(x),
    PropertyType.List: lambda x: "|".join([str(v) for v in x]),
    PropertyType.UUID: str,
    PropertyType.Selection: str,
    PropertyType.ActionActivationMode: lambda x: ActionActivationMode.to_string(x),
    PropertyType.Point2D: lambda x: x.to_string(),
}

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
    PropertyType.ScriptVariableType: ScriptVariableType
}

_element_parsers = {
    "device-id": lambda x: uuid.UUID(x.text),
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


# =============================================================================
# Boolean Parsing Functions
# =============================================================================

def read_bool(
        node: ElementTree.Element,
        key: str,
        default_value: bool = False
) -> bool:
    """Parses a boolean value from an XML attribute.

    Args:
        node: XML node from which to read the boolean
        key: attribute name containing the boolean value
        default_value: value to return if the key is not present

    Returns:
        Boolean value of the specified attribute
    """
    value = default_value
    if key in node.keys():
        attr_value = node.get(key)
        if attr_value is not None:
            value = True if attr_value.lower() == "true" else False
    return value


def parse_bool(value: str, default: bool = False) -> bool:
    """Parses a boolean value from a string.

    Args:
        value: string representation of a boolean value
        default: default value to use if conversion fails

    Returns:
        Boolean value represented by the provided string
    """
    # Handle None values
    if value is None:
        return default

    # Attempt conversion
    value_lower = value.lower()
    if value_lower == "true":
        return True
    elif value_lower == "false":
        return False
    else:
        try:
            return bool(int(value))
        except (ValueError, TypeError):
            return default


def parse_id_or_uuid(value: str) -> int | uuid.UUID:
    """Parses either an integer id or UUID from a string.

    Args:
        value: string containing either an integer or UUID

    Returns:
        Either an integer or UUID depending on content
    """
    try:
        return int(value)
    except ValueError:
        return uuid.UUID(value)


# =============================================================================
# Type-Safe Reading and Formatting
# =============================================================================

def safe_read(
        node: ElementTree.Element,
        key: str,
        data_type: type = str,
        default_value: Any = None
) -> Any:
    """Returns the value stored in the provided node.

    Args:
        node: XML node from which to read the value
        key: attribute name containing the value
        data_type: data type of the value
        default_value: default value to use if the attribute is not present

    Returns:
        Value of the specified attribute
    """
    value = node.get(key)

    # Use default value if the attribute doesn't exist
    if value is None:
        return default_value

    # Attempt type casting
    try:
        if data_type == bool:
            return parse_bool(value)
        else:
            return data_type(value)
    except (ValueError, TypeError):
        return default_value


def safe_format(value: Any, data_type: type) -> str:
    """Returns a formatted string representation of the value.

    Args:
        value: value to format
        data_type: data type of the value

    Returns:
        String representation of the value
    """
    try:
        if data_type == bool:
            return "True" if value else "False"
        else:
            return str(value)
    except (ValueError, TypeError):
        return ""


# =============================================================================
# Property Conversion Functions
# =============================================================================

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


# =============================================================================
# Property Reading Functions
# =============================================================================

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
    
    property_node = action_node.find(f"./property/name[.='{name}']/..")
    if property_node is None:
        raise error.ProfileError(f"A property named '{name}' is missing.")
    
    return _process_property(property_node, name, property_type)


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
    v_node = property_node.find(f"./value")
    if v_node is None:
        raise error.ProfileError(
            f"Value element of property '{name}' is missing"
        )
    if "type" not in property_node.keys():
        raise error.ProfileError(
            f"Property element is missing the 'type' attribute."
        )

    type_value = property_node.get("type")
    if type_value is None:
        raise error.ProfileError(
            f"Property element has no 'type' attribute value."
        )
    
    p_type = PropertyType.to_enum(type_value)
    if p_type not in property_types:
        raise error.ProfileError(
            f"Property type mismatch, got '{p_type}' expected on of: " +
            f"[{', '.join([str(v) for v in property_types])}]"
        )
    try:
        return _property_from_string[p_type](v_node.text)
    except Exception:
        raise error.ProfileError(
            f"Failed parsing property value '{v_node.text}' which "
            f"should be of type '{p_type}"
        )


# =============================================================================
# Property Creation Functions
# =============================================================================

def create_property_node(
        name: str,
        value: Any,
        property_type: PropertyType
) -> ElementTree.Element:
    """Creates a property node with the given data.

    Args:
        name: the name of the property
        value: the value of the property
        property_type: type of the property value

    Returns:
        XML node representing the property
    """
    node = ElementTree.Element("property")
    node.set("type", PropertyType.to_string(property_type))

    name_node = ElementTree.Element("name")
    name_node.text = name
    node.append(name_node)

    value_node = ElementTree.Element("value")
    value_node.text = property_to_string(property_type, value)
    node.append(value_node)

    return node


def append_property_nodes(
        parent: ElementTree.Element,
        properties: dict,
        property_map: dict
) -> None:
    """Appends property nodes to a parent element.

    Args:
        parent: parent element to add properties to
        properties: dictionary mapping property names to values
        property_map: dictionary mapping property names to PropertyType
    """
    for name, value in properties.items():
        if name in property_map:
            parent.append(create_property_node(
                name,
                value,
                property_map[name]
            ))


def create_node_from_data(
        name: str,
        value: Any,
        property_type: PropertyType
) -> ElementTree.Element:
    """Creates a simple node with the given data.

    Args:
        name: name of the XML element
        value: value to store in the element
        property_type: PropertyType of the value

    Returns:
        XML element with the given name and value
    """
    node = ElementTree.Element(name)
    node.text = property_to_string(property_type, value)
    return node


# =============================================================================
# Subelement Functions
# =============================================================================

def create_subelement_node(name: str, value: Any) -> ElementTree.Element:
    """Creates a subelement node.

    Args:
        name: name of the subelement
        value: value of the subelement

    Returns:
        XML element representing the subelement
    """
    if name not in _element_to_string:
        raise error.ProfileError(
            f"No valid subelement mapping exists for '{name}'"
        )

    node = ElementTree.Element(name)
    node.text = _element_to_string[name](value)
    return node


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


# =============================================================================
# Action Functions
# =============================================================================

def create_action_node() -> ElementTree.Element:
    """Creates a new action node with a UUID.

    Returns:
        XML element representing an action with a unique ID
    """
    node = ElementTree.Element("action")
    node.set("id", str(uuid.uuid4()))
    return node


def read_action_id(node: ElementTree.Element) -> uuid.UUID:
    """Returns the id attribute from the provided action node.

    Args:
        node: XML node to parse

    Returns:
        UUID corresponding to the action id
    """
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
    for action_uuid in action_ids:
        entry = ElementTree.Element("action-id")
        entry.text = str(action_uuid)
        node.append(entry)
    return node


# =============================================================================
# UUID Functions
# =============================================================================

def read_uuid(
        node: ElementTree.Element,
        attribute_name: str = "id"
) -> uuid.UUID:
    """Reads and validates a UUID from a node attribute.

    Args:
        node: XML node to read from
        attribute_name: name of the attribute containing the UUID

    Returns:
        UUID read from the attribute
    """
    uuid_str = node.get(attribute_name)
    if uuid_str is None:
        raise error.ProfileError(
            f"UUID attribute '{attribute_name}' not found in node {node.tag}"
        )

    try:
        return uuid.UUID(uuid_str)
    except ValueError:
        raise error.ProfileError(
            f"Invalid UUID format in attribute '{attribute_name}': {uuid_str}"
        )


# =============================================================================
# Type Determination
# =============================================================================

def determine_value_type(
        value: Any,
        property_type: PropertyType | List[PropertyType]
) -> Tuple[PropertyType, bool]:
    """Returns whether a value is of the correct type and the type.

    Args:
        value: value to check
        property_type: valid PropertyType or list of valid types

    Returns:
        Tuple of (PropertyType, is_valid)
    """
    if isinstance(property_type, PropertyType):
        property_type = [property_type]

    for p_type in property_type:
        expected_type = _type_lookup.get(p_type)
        if expected_type is None:
            continue
        if isinstance(value, expected_type):
            return p_type, True

    return property_type[0], False
