# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid
from typing import Any
from xml.etree import ElementTree

import pytest

import gremlin.error
import gremlin.types
import gremlin.util

xml_doc = """
<action id="ac905a47-9ad3-4b65-b702-fbae1d133609" type="description">
    <property type="string">
        <name>description</name>
        <value>This is a test</value>
    </property>
    <property type="int">
        <name>answer-to-life-and-everything</name>
        <value>42</value>
    </property>
    <property type="float">
        <name>pi</name>
        <value>3.14</value>
    </property>
    <property type="bool">
        <name>lies</name>
        <value>true</value>
    </property>
    <property type="path">
        <name>path</name>
        <value>./test</value>
    </property>
</action>
"""

xml_bad = """
<action id="ac905a47-9ad3-4b65-b702-fbae1d133609" type="description">
    <property type="int">
        <name>value</name>
        <value>3.14</value>
    </property>
</action>
"""


def test_read_action_id() -> None:
    doc = ElementTree.fromstring(xml_doc)
    assert gremlin.util.read_action_id(doc) == uuid.UUID(
        "ac905a47-9ad3-4b65-b702-fbae1d133609"
    )

    xml_bad = """
        <action id="ac905a47-9ad3-4b65-b702" type="description"></action>
    """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(gremlin.error.ProfileError, match=r"Failed parsing id from"):
        gremlin.util.read_action_id(doc)

    xml_bad = """
            <action type="description"></action>
        """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(
        gremlin.error.ProfileError, match=r"Reading id entry failed due"
    ):
        gremlin.util.read_action_id(doc)


def test_read_property() -> None:
    doc = ElementTree.fromstring(xml_doc)

    assert (
        gremlin.util.read_property(
            doc, "description", gremlin.types.PropertyType.String
        )
        == "This is a test"
    )
    assert (
        gremlin.util.read_property(
            doc, "answer-to-life-and-everything", gremlin.types.PropertyType.Int
        )
        == 42
    )
    assert (
        gremlin.util.read_property(doc, "pi", gremlin.types.PropertyType.Float) == 3.14
    )
    assert gremlin.util.read_property(doc, "lies", gremlin.types.PropertyType.Bool)
    assert gremlin.util.read_property(
        doc, "path", gremlin.types.PropertyType.Path
    ) == pathlib.Path("./test")

    with pytest.raises(gremlin.error.ProfileError, match=r"A property named"):
        gremlin.util.read_property(
            doc, "does not exist", gremlin.types.PropertyType.Bool
        )
    with pytest.raises(gremlin.error.ProfileError, match=r"Property type mismatch"):
        gremlin.util.read_property(doc, "lies", gremlin.types.PropertyType.Float)

    xml_bad = """
        <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" type="description">
            <property type="int">
                <name>value</name>
                <value>3.14</value>
            </property>
        </action>
    """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(gremlin.error.ProfileError, match=r"Failed parsing property"):
        gremlin.util.read_property(doc, "value", gremlin.types.PropertyType.Int)

    xml_bad = """
        <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" type="description">
            <property type="int">
                <name>value</name>
            </property>
        </action>
    """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(gremlin.error.ProfileError, match=r"Value element of property"):
        gremlin.util.read_property(doc, "value", gremlin.types.PropertyType.Int)

    xml_bad = """
        <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" type="description">
            <property>
                <name>value</name>
                <value>3.14</value>
            </property>
        </action>
    """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(
        gremlin.error.ProfileError, match=r"Property element is missing"
    ):
        gremlin.util.read_property(doc, "value", gremlin.types.PropertyType.Int)


@pytest.mark.parametrize(
    "value, min_val, max_val, expected",
    [
        pytest.param(5, 0, 10, 5, id="within_range"),
        pytest.param(-1, 0, 10, 0, id="below_min"),
        pytest.param(11, 0, 10, 10, id="above_max"),
        pytest.param(0, 0, 10, 0, id="equal_to_min"),
        pytest.param(10, 0, 10, 10, id="equal_to_max"),
        pytest.param(5, 10, 0, 5, id="min_max_swapped"),
        pytest.param(3.14, 0.0, 5.0, 3.14, id="float_values_positive"),
        pytest.param(-3.14, -5.0, 5.0, -3.14, id="float_values_negative"),
        pytest.param(-10, -5, 5, -5, id="negative_range_below"),
        pytest.param(10, -5, 5, 5, id="negative_range_above"),
        pytest.param(-32766, -32768, 32767, -32766, id="negative_range_below"),
    ],
)
def test_clamp(value: float, min_val: float, max_val: float, expected: float) -> None:
    """Test that values are properly clamped to the specified range."""
    assert gremlin.util.clamp(value, min_val, max_val) == expected


@pytest.mark.parametrize(
    "value, property_type",
    [
        pytest.param("a valid string", gremlin.types.PropertyType.String),
        pytest.param(
            "a valid string",
            [gremlin.types.PropertyType.Int, gremlin.types.PropertyType.String],
        ),
        pytest.param(9, gremlin.types.PropertyType.Int),
        pytest.param(3.14, gremlin.types.PropertyType.Float),
        pytest.param(True, gremlin.types.PropertyType.Bool),
        pytest.param(uuid.uuid4(), gremlin.types.PropertyType.UUID),
        pytest.param(pathlib.Path("./test"), gremlin.types.PropertyType.Path),
    ],
)
def test_determine_value_type_valid_values(
    value: Any,  # noqa: ANN401
    property_type: gremlin.types.PropertyType | list[gremlin.types.PropertyType],
) -> None:
    property_type, is_valid = gremlin.util.determine_value_type(value, property_type)
    assert property_type == property_type
    assert is_valid


@pytest.mark.parametrize(
    "value, property_type",
    [
        pytest.param("a string", gremlin.types.PropertyType.Int),
        pytest.param(
            "a string",
            [gremlin.types.PropertyType.Int, gremlin.types.PropertyType.Bool],
        ),
        pytest.param(9.0, gremlin.types.PropertyType.Int),
        pytest.param(True, gremlin.types.PropertyType.Float),
        pytest.param(uuid.uuid4(), gremlin.types.PropertyType.Int),
        pytest.param(pathlib.Path("./test"), gremlin.types.PropertyType.String),
    ],
)
def test_determine_value_type_invalid_values(
    value: Any,  # noqa: ANN401
    property_type: gremlin.types.PropertyType | list[gremlin.types.PropertyType],
) -> None:
    property_type, is_valid = gremlin.util.determine_value_type(value, property_type)
    assert property_type is None
    assert not is_valid


@pytest.mark.parametrize(
    "property, property_value, property_string",
    [
        pytest.param(
            gremlin.types.PropertyType.String, "a valid string", "a valid string"
        ),
        pytest.param(gremlin.types.PropertyType.Int, 9, "9"),
        pytest.param(gremlin.types.PropertyType.Float, 3.14, "3.14"),
        pytest.param(gremlin.types.PropertyType.Bool, True, "True"),
        pytest.param(gremlin.types.PropertyType.Path, pathlib.Path("/test"), "\\test"),
    ],
)
def test_property_to_string(
    property: gremlin.types.PropertyType,
    property_value: Any,  # noqa: ANN401
    property_string: str,
) -> None:
    assert gremlin.util.property_to_string(property, property_value) == property_string
