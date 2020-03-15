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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import sys
sys.path.append(".")

import pytest
import uuid
from xml.etree import ElementTree

import gremlin.error
# import gremlin.plugin_manager
# from gremlin.profile import Profile
# import gremlin.types
# import gremlin.util

import action_plugins.description as apd


xml = """
    <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="description">
        <property type="string">
            <name>description</name>
            <value>This is a test</value>
        </property>
    </action>
"""


def test_model_ctor():
    m = apd.DescriptionModel()

    assert m.description == ""


def test_model_setter_getter():
    m = apd.DescriptionModel()

    assert m.description == ""
    m.description = "Test"
    assert m.description == "Test"


def test_model_from_xml():
    doc = ElementTree.fromstring(xml)
    m = apd.DescriptionModel()
    m.from_xml(doc)

    assert m.description == "This is a test"
    assert m.id == uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")


def test_model_to_xml():
    m = apd.DescriptionModel()
    m.description = "Test"
    m.to_xml()

    # Should not raise an exception because we implicitely convert the value
    # to its string representation
    m.description = 42
    m.to_xml()

    m.description = "This is a test"
    m._id = uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
    node = m.to_xml()
    # ElementTree.dump(node)
    assert node.find("property/name").text == "description"
    assert node.find("property/value").text == "This is a test"
    assert node.find("property").attrib["type"] == "string"
    assert node.attrib["id"] == "ac905a47-9ad3-4b65-b702-fbae1d133609"
    assert node.attrib["type"] == "description"
