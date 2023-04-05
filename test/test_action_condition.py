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

from gremlin import event_handler
sys.path.append(".")

import pytest
import uuid
from xml.etree import ElementTree

import gremlin.error as error
import gremlin.types as types
import gremlin.profile_library as profile_library
import gremlin.util as util

import action_plugins.condition as condition


def test_from_xml():
    c = condition.ConditionModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )
    c.from_xml(ElementTree.fromstring(open("test/action_condition_simple.xml").read()))

    assert len(c._conditions) == 1
    assert c._logical_operator == condition.LogicalOperator.All
    assert c.is_valid()

    assert len(c._conditions[0]._inputs) == 1

    cond = c._conditions[0]
    assert isinstance(cond, condition.JoystickCondition)
    assert isinstance(cond._comparator, condition.comparator.PressedComparator)
    assert cond._inputs[0].event_type == types.InputType.JoystickButton
    assert cond._comparator.is_pressed == False
    assert cond.is_valid()


def test_from_xml_complex():
    c = condition.ConditionModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )
    c.from_xml(ElementTree.fromstring(open("test/action_condition_complex.xml").read()))

    # General information
    assert len(c._conditions) == 4
    assert c._logical_operator == condition.LogicalOperator.Any
    assert c.is_valid()

    # Input item data
    assert len(c._conditions[0]._inputs) == 2
    in1 = c._conditions[0]._inputs[0]
    assert in1.event_type == types.InputType.JoystickButton
    assert in1.identifier == 2
    assert in1.device_guid == util.parse_guid("4DCB3090-97EC-11EB-8003-444553540000")
    in2 = c._conditions[0]._inputs[1]
    assert in2.event_type == types.InputType.JoystickButton
    assert in2.identifier == 42
    assert in2.device_guid == util.parse_guid("4DCB3090-97EC-11EB-8003-444553540024")
    in3 = c._conditions[2]._inputs[0]
    assert in3.event_type == types.InputType.JoystickHat
    assert in3.identifier == 1
    assert in3.device_guid == util.parse_guid("4DCB3090-97EC-11EB-8003-444553540000")
    in4 = c._conditions[3]._inputs[0]
    in4.scan_code = 42
    in4.is_extended = True

    # Condition data
    assert len(c._conditions[0]._inputs) == 2
    c1 = c._conditions[0]
    assert isinstance(c1, condition.JoystickCondition)
    assert isinstance(c1._comparator, condition.comparator.PressedComparator)
    assert c1._inputs[0].event_type == types.InputType.JoystickButton
    assert c1._comparator.is_pressed == False
    assert c1.is_valid()

    c2 = c._conditions[1]
    assert isinstance(c2, condition.JoystickCondition)
    assert isinstance(c2._comparator, condition.comparator.RangeComparator)
    assert c2._inputs[0].event_type == types.InputType.JoystickAxis
    assert c2._comparator.lower == 0.2
    assert c2._comparator.upper == 0.9
    assert c2.is_valid()

    c3 = c._conditions[2]
    assert isinstance(c3, condition.JoystickCondition)
    assert isinstance(c3._comparator, condition.comparator.DirectionComparator)
    assert c3._inputs[0].event_type == types.InputType.JoystickHat
    assert len(c3._comparator.directions) == 3
    assert c3._comparator.directions[0] == types.HatDirection.North
    assert c3._comparator.directions[1] == types.HatDirection.East
    assert c3._comparator.directions[2] == types.HatDirection.NorthEast

    c4 = c._conditions[3]
    assert isinstance(c4, condition.KeyboardCondition)
    assert isinstance(c4._comparator, condition.comparator.PressedComparator)
    assert c4._comparator.is_pressed == False


def test_to_xml():
    c = condition.ConditionModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )

    cond = condition.JoystickCondition()
    input_dev = event_handler.Event(
        types.InputType.JoystickButton,
        37,
        util.parse_guid("4DCB3090-97EC-11EB-8003-444553540000")
    )
    cond._inputs.append(input_dev)
    cond._comparator = condition.comparator.PressedComparator(True)
    c._conditions.append(cond)

    node = c.to_xml()
    assert node.find(
            "./property/name[.='logical-operator']/../value"
        ).text == "all"
    assert node.find(
            "./condition/property/name[.='condition-type']/../value"
        ).text == "joystick"
    assert node.find(
            "./condition/input/property/name[.='input-type']/../value"
        ).text == "button"
    assert node.find(
            "./condition/comparator/property/name[.='is-pressed']/../value"
        ).text == "True"


def test_ctor():
    c = condition.ConditionModel(
        profile_library.ActionTree(),
        types.InputType.JoystickButton
    )

    assert len(c._conditions) == 0
    assert c._logical_operator == condition.LogicalOperator.All
    assert c.is_valid() == True