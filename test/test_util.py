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

import os
import pytest
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


def test_parse_property():
    doc = ElementTree.fromstring(xml_doc)

    properties = gremlin.util.parse_properties(doc)

    assert len(properties) == 4
    assert properties.get("description", None) == "This is a test"
    assert properties.get("answer-to-life-and-everything", None) == 42
    assert properties.get("pi", None) == 3.14
    assert properties.get("lies", None) == True