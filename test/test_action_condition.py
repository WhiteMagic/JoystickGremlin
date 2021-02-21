# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2021 Lionel Ott
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

import action_plugins.condition as condition


xml_simple = """
  <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="condition">
    <if-actions>
      <action-id>fbe6be7b-07c9-4400-94f2-caa245ebcc7e</action-id>
      <action-id>80e29257-f2ad-43bf-b5ab-9229d01e64d7</action-id>
    </if-actions>
    <else-actions>
      <action-id>2bf10c03-a9d3-4410-a56a-70643e2c05b8</action-id>
    </else-actions>
    <property type="string">
      <name>logical-operator</name>
      <value>all</value>
    </property>
    <condition>
      <property type="string">
        <name>condition-type</name>
        <value>input-state</value>
      </property>
      <property type="input_type">
        <name>input-type</name>
        <value>button</value>
      </property>
      <property type="bool">
        <name>is-pressed</name>
        <value>false</value>
      </property>
    </condition>
  </action>
"""


def test_from_xml():
    c = condition.ConditionModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )
    c.from_xml(ElementTree.fromstring(xml_simple))

    assert len(c._conditions) == 1
    assert c._logical_operator == condition.LogicalOperators.All
    assert c.is_valid()
    
    cond = c._conditions[0]
    assert isinstance(cond, condition.InputStateCondition)
    assert isinstance(cond.comparator, condition.InputStateCondition.ButtonComparator)
    assert cond._input_type == types.InputType.JoystickButton
    assert cond.comparator.is_pressed == False
    assert cond.is_valid()


def test_to_xml():
    c = condition.ConditionModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )

    cond = condition.InputStateCondition()
    cond._input_type = types.InputType.JoystickButton
    cond.comparator = condition.InputStateCondition.ButtonComparator(True)
    c._conditions.append(cond)

    node = c.to_xml()
    assert node.find(
            "./property/name[.='logical-operator']/../value"
        ).text == "all"
    assert node.find(
            "./condition/property/name[.='condition-type']/../value"
        ).text == "input-state"
    assert node.find(
            "./condition/property/name[.='input-type']/../value"
        ).text == "button"
    assert node.find(
            "./condition/property/name[.='is-pressed']/../value"
        ).text == "True"



def test_ctor():
    c = condition.ConditionModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )

    assert len(c._conditions) == 0
    assert c._logical_operator == condition.LogicalOperators.All
    assert c.is_valid() == True