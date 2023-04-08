# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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

from gremlin.error import GremlinError
from gremlin.profile import Library, InputItem, InputItemBinding, Profile

from action_plugins.description import DescriptionData, DescriptionModel



@pytest.fixture(scope="session", autouse=True)
def terminate_event_listener(request):
    import gremlin.event_handler
    request.addfinalizer(
        lambda: gremlin.event_handler.EventListener().terminate()
    )


def test_model_ctor():
    a = DescriptionData()

    assert a.description == ""


def test_actions():
    l = Library()
    a = DescriptionData()
    a.from_xml(
        ElementTree.fromstring(
            open("test/xml/action_description_simple.xml").read(),
        ),
        l
    )

    with pytest.raises(GremlinError):
        a.get_actions()
    with pytest.raises(GremlinError):
        d = DescriptionData()
        a.insert_action(d, "something")
    with pytest.raises(GremlinError):
        d = DescriptionData()
        a.remove_action(d, "something")

def test_model_setter_getter():
    p = Profile()
    ii = InputItem(p.library)
    ib = InputItemBinding(ii)
    a = DescriptionData()
    m = DescriptionModel(a, ib, None)

    assert a.description == ""
    assert m.description == ""
    m.description = "Test"
    assert a.description == "Test"
    assert m.description == "Test"
    a.description = "Test 123"
    assert a.description == "Test 123"
    assert m.description == "Test 123"


def test_model_from_xml():
    l = Library()
    a = DescriptionData()
    a.from_xml(
        ElementTree.fromstring(
            open("test/xml/action_description_simple.xml").read(),
        ),
        l
    )

    assert a.description == "This is a test"
    assert a._id == uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")


def test_model_to_xml():
    p = Profile()
    ii = InputItem(p.library)
    ib = InputItemBinding(ii)
    a = DescriptionData()
    m = DescriptionModel(a, ib, None)

    m.description = "Test"
    a.to_xml()

    # Should not raise an exception because we implicitely convert the value
    # to its string representation
    m.description = 42
    a.to_xml()

    m.description = "This is a test"
    a._id = uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
    node = a.to_xml()
    # ElementTree.dump(node)
    assert node.find("property/name").text == "description"
    assert node.find("property/value").text == "This is a test"
    assert node.find("property").attrib["type"] == "string"
    assert node.attrib["id"] == "ac905a47-9ad3-4b65-b702-fbae1d133609"
    assert node.attrib["type"] == "description"
