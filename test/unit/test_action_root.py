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

import pathlib
import pytest
import uuid
from xml.etree import ElementTree

from gremlin.error import GremlinError
from gremlin.profile import Library, Profile
from gremlin.types import InputType, DataInsertionMode

from action_plugins.description import DescriptionData
from action_plugins.root import RootData, RootModel

_PROFILE_HIERARCHY = "profile_hierarchy.xml"


def test_ctor():
    a = RootData(InputType.JoystickButton)

    assert len(a.children) == 0
    assert a.is_valid() == True


def test_from_xml(xml_dir: pathlib.Path):
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE_HIERARCHY))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    assert len(a.children) == 3
    assert a.children[0].id == uuid.UUID("0c905a47-9ad3-4b65-b702-fbae1d133600")
    assert a.children[1].id == uuid.UUID("0c905a47-9ad3-4b65-b702-fbae1d133601")
    assert a.children[2].id == uuid.UUID("0c905a47-9ad3-4b65-b702-fbae1d133603")


def test_action_methods(xml_dir: pathlib.Path):
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE_HIERARCHY))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    assert len(a.get_actions()[0]) == 3
    with pytest.raises(GremlinError):
        a.get_actions("invalid")
    assert len(a.get_actions("children")[0]) == 3

    d = DescriptionData()
    a.insert_action(d, "children", DataInsertionMode.Prepend)
    assert len(a.get_actions("children")[0]) == 4
    assert a.get_actions()[0][0].id == d.id
    with pytest.raises(GremlinError):
        a.remove_action(4, "children")
    a.remove_action(3, "children")
    assert len(a.get_actions("children")[0]) == 3
    assert d not in a.get_actions()
