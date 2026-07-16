# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid
from xml.etree import ElementTree

import pytest

from action_plugins.description import (
    DescriptionData,
    DescriptionModel,
)
from action_plugins.root import RootData
from gremlin.error import GremlinError
from gremlin.profile import (
    InputItem,
    InputItemBinding,
    Library,
    Profile,
)
from gremlin.ui.action_model import SequenceIndex
from gremlin.ui.profile import InputItemBindingModel

_ACTION_DESCRIPTION_SIMPLE = "action_description_simple.xml"


@pytest.fixture(scope="session", autouse=True)
def terminate_event_listener(request: pytest.FixtureRequest) -> None:
    import gremlin.event_handler

    request.addfinalizer(lambda: gremlin.event_handler.EventListener().terminate())


def test_model_ctor() -> None:
    a = DescriptionData()

    assert a.description == ""


def test_actions(xml_dir: pathlib.Path) -> None:
    library = Library()
    a = DescriptionData()
    a.from_xml(
        ElementTree.fromstring(
            (xml_dir / _ACTION_DESCRIPTION_SIMPLE).read_text(),
        ),
        library,
    )

    assert len(a.get_actions()[0]) == 0
    with pytest.raises(GremlinError):
        d = DescriptionData()
        a.insert_action(d, "something")
    with pytest.raises(GremlinError):
        a.remove_action(0, "something")


def test_model_setter_getter() -> None:
    p = Profile()
    ii = InputItem(p.library)
    iib = InputItemBinding(ii)
    iib.root_action = RootData()
    iibm = InputItemBindingModel(iib)
    a = DescriptionData()
    m = DescriptionModel(
        a, iibm, SequenceIndex(None, None, 0), SequenceIndex(None, None, 1), None
    )

    assert a.description == ""
    assert m.description == ""
    m.description = "Test"
    assert a.description == "Test"
    assert m.description == "Test"
    a.description = "Test 123"
    assert a.description == "Test 123"
    assert m.description == "Test 123"


def test_model_from_xml(xml_dir: pathlib.Path) -> None:
    library = Library()
    a = DescriptionData()
    a.from_xml(
        ElementTree.fromstring(
            (xml_dir / _ACTION_DESCRIPTION_SIMPLE).read_text(),
        ),
        library,
    )

    assert a.description == "This is a test"
    assert a._id == uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")


def test_model_to_xml() -> None:
    p = Profile()
    ii = InputItem(p.library)
    iib = InputItemBinding(ii)
    iib.root_action = RootData()
    iibm = InputItemBindingModel(iib)
    a = DescriptionData()
    m = DescriptionModel(
        a, iibm, SequenceIndex(None, None, 0), SequenceIndex(None, None, 1), None
    )

    m.description = "Test"
    a._to_xml()

    # Should not raise an exception because we implicitely convert the value
    # to its string representation
    m.description = 42
    a._to_xml()

    m.description = "This is a test"
    a._id = uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
    node = a._to_xml()
    # ElementTree.dump(node)
    assert node.find("property/name").text == "description"
    assert node.find("property/value").text == "This is a test"
    assert node.find("property").attrib["type"] == "string"
    assert node.attrib["id"] == "ac905a47-9ad3-4b65-b702-fbae1d133609"
    assert node.attrib["type"] == "description"
