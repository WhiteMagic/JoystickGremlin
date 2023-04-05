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

import gremlin.error as error
import gremlin.types as types
import gremlin.profile_library as profile_library

import action_plugins.tempo as tempo


xml_simple = """
  <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="tempo">
    <short-actions>
      <action-id>fbe6be7b-07c9-4400-94f2-caa245ebcc7e</action-id>
      <action-id>80e29257-f2ad-43bf-b5ab-9229d01e64d7</action-id>
    </short-actions>
    <long-actions>
      <action-id>2bf10c03-a9d3-4410-a56a-70643e2c05b8</action-id>
    </long-actions>
    <property type="string">
      <name>activate-on</name>
      <value>press</value>
    </property>
    <property type="float">
      <name>threshold</name>
      <value>0.123</value>
    </property>
  </action>
"""


def test_from_xml():
    a = tempo.TempoModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )
    a.from_xml(ElementTree.fromstring(xml_simple))

    assert len(a._short_action_ids) == 2
    assert len(a._long_action_ids) == 1
    assert a._activate_on == "press"
    assert a._threshold == 0.123


def test_to_xml():
    a = tempo.TempoModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )

    a._short_action_ids.append(uuid.UUID("fbe6be7b-07c9-4400-94f2-caa245ebcc7e"))
    a._threshold = 0.42

    node = a.to_xml()
    assert node.find(
            "./property/name[.='activate-on']/../value"
        ).text == "release"
    assert node.find(
            "./property/name[.='threshold']/../value"
    ).text == "0.42"
    assert node.find(
            "./short-actions/action-id"
    ).text == "fbe6be7b-07c9-4400-94f2-caa245ebcc7e"


def test_ctor():
    a = tempo.TempoModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )

    assert len(a._short_action_ids) == 0
    assert len(a._long_action_ids) == 0
    assert a._threshold == 0.5
    assert a._activate_on == "release"
    assert a.is_valid() == True