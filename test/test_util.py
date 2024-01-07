# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import sys
sys.path.append(".")

import os
import pytest
import uuid
from xml.etree import ElementTree

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

def test_read_action_id():
    doc = ElementTree.fromstring(xml_doc)
    assert gremlin.util.read_action_id(doc) == \
           uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")

    xml_bad = """
        <action id="ac905a47-9ad3-4b65-b702" type="description"></action>
    """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(gremlin.error.ProfileError,
                       match=r"Failed parsing id from"):
        gremlin.util.read_action_id(doc)

    xml_bad = """
            <action type="description"></action>
        """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(gremlin.error.ProfileError,
                       match=r"Reading id entry failed due"):
        gremlin.util.read_action_id(doc)


def test_read_property():
    doc = ElementTree.fromstring(xml_doc)

    assert gremlin.util.read_property(
        doc, "description", gremlin.types.PropertyType.String
    ) == "This is a test"
    assert gremlin.util.read_property(
        doc, "answer-to-life-and-everything", gremlin.types.PropertyType.Int
    ) == 42
    assert gremlin.util.read_property(
        doc, "pi", gremlin.types.PropertyType.Float
    ) == 3.14
    assert gremlin.util.read_property(
        doc, "lies", gremlin.types.PropertyType.Bool
    ) == True


    with pytest.raises(gremlin.error.ProfileError, match=r"A property named"):
        gremlin.util.read_property(
            doc, "does not exist", gremlin.types.PropertyType.Bool
        )
    with pytest.raises(gremlin.error.ProfileError, match=r"Property type mismatch"):
        gremlin.util.read_property(
            doc, "lies", gremlin.types.PropertyType.Float
        )

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
        gremlin.util.read_property(
            doc, "value", gremlin.types.PropertyType.Int
        )

    xml_bad = """
        <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" type="description">
            <property type="int">
                <name>value</name>
            </property>
        </action>
    """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(gremlin.error.ProfileError, match=r"Value element of property"):
        gremlin.util.read_property(
            doc, "value", gremlin.types.PropertyType.Int
        )

    xml_bad = """
        <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" type="description">
            <property>
                <name>value</name>
                <value>3.14</value>
            </property>
        </action>
    """
    doc = ElementTree.fromstring(xml_bad)
    with pytest.raises(gremlin.error.ProfileError, match=r"Property element is missing"):
        gremlin.util.read_property(
            doc, "value", gremlin.types.PropertyType.Int
        )