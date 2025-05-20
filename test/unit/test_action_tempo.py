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

import os.path
import pytest
import uuid
from xml.etree import ElementTree

from gremlin.types import DataInsertionMode
from gremlin.config import Configuration
from gremlin.error import GremlinError
import gremlin.types as types
from gremlin.profile import Library, Profile

import action_plugins.tempo as tempo
from action_plugins.description import DescriptionData

_ACTION_TEMPO_SIMPLE = "action_tempo_simple.xml"


def test_from_xml(xml_dir: str):
    p = Profile()
    p.from_xml(os.path.join(xml_dir, _ACTION_TEMPO_SIMPLE))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    assert len(a.short_actions) == 2
    assert len(a.long_actions) == 1
    assert a.activate_on == "press"
    assert a.threshold == 0.123
    assert a.short_actions[0].id == uuid.UUID("fbe6be7b-07c9-4400-94f2-caa245ebcc7e")
    assert a.short_actions[1].id == uuid.UUID("80e29257-f2ad-43bf-b5ab-9229d01e64d7")
    assert a.long_actions[0].id == uuid.UUID("2bf10c03-a9d3-4410-a56a-70643e2c05b8")


def test_to_xml():
    d = DescriptionData()
    d._id = uuid.UUID("fbe6be7b-07c9-4400-94f2-caa245ebcc7e")

    a = tempo.TempoData(types.InputType.JoystickButton)
    a.insert_action(d, "short")
    a.threshold = 0.42

    node = a._to_xml()
    assert node.find(
            "./property/name[.='activate-on']/../value"
        ).text == "release"
    assert node.find(
            "./property/name[.='threshold']/../value"
    ).text == "0.42"
    assert node.find(
            "./short-actions/action-id"
    ).text == "fbe6be7b-07c9-4400-94f2-caa245ebcc7e"


def test_action_methods(xml_dir: str):
    p = Profile()
    p.from_xml(os.path.join(xml_dir, _ACTION_TEMPO_SIMPLE))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    # Get action testing
    assert len(a.get_actions()[0]) == 3
    assert len(a.get_actions("short")[0]) == 2
    assert len(a.get_actions("long")[0]) == 1
    with pytest.raises(GremlinError):
        assert a.get_actions("invalid options")

    # Remove and insert testing
    a1 = a.get_actions("short")[0][0]
    a.remove_action(0, "short")
    assert len(a.get_actions("short")[0]) == 1
    a.insert_action(a1, "long", DataInsertionMode.Prepend)
    assert len(a.get_actions("long")[0]) == 2
    assert a.get_actions("long")[0][0].id == a1.id


def test_ctor():
    a = tempo.TempoData(types.InputType.JoystickButton)
    c = Configuration()

    assert len(a.short_actions) == 0
    assert len(a.long_actions) == 0
    assert a.threshold == c.value("action", "tempo", "duration")
    assert a.activate_on == "release"
    assert a.is_valid() == True
