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

from gremlin import event_handler
sys.path.append(".")

import pathlib
import pytest
import uuid
from xml.etree import ElementTree

from gremlin.error import GremlinError
from gremlin.event_handler import Event
from gremlin.types import HatDirection, InputType, DataInsertionMode

from gremlin.profile import Library, InputItem, InputItemBinding, Profile
from action_plugins.condition import ConditionData, ConditionModel

from action_plugins.root import RootData
from action_plugins.description import DescriptionData
import action_plugins.condition as condition

_PROFILE_SIMPLE = "action_condition_simple.xml"


def test_from_xml(xml_dir: pathlib.Path):
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE_SIMPLE))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    assert len(a.conditions) == 1
    assert a.logical_operator == condition.LogicalOperator.All
    assert a.is_valid()

    assert len(a.conditions[0]._inputs) == 1

    cond = a.conditions[0]
    assert isinstance(cond, condition.JoystickCondition)
    assert isinstance(cond._comparator, condition.comparator.PressedComparator)
    assert cond._inputs[0].event_type == InputType.JoystickButton
    assert cond._comparator.is_pressed == False
    assert cond.is_valid()


def test_from_xml_complex(xml_dir: pathlib.Path):
    p = Profile()
    p.from_xml(str(xml_dir / "action_condition_complex.xml"))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    # General information
    assert len(a.conditions) == 4
    assert a.logical_operator == condition.LogicalOperator.Any
    assert a.is_valid()

    # Input item data
    assert len(a.conditions[0]._inputs) == 2
    in1 = a.conditions[0]._inputs[0]
    assert in1.event_type == InputType.JoystickButton
    assert in1.identifier == 2
    assert in1.device_guid == uuid.UUID("4DCB3090-97EC-11EB-8003-444553540000")
    in2 = a.conditions[0]._inputs[1]
    assert in2.event_type == InputType.JoystickButton
    assert in2.identifier == 42
    assert in2.device_guid == uuid.UUID("4DCB3090-97EC-11EB-8003-444553540024")
    in3 = a.conditions[2]._inputs[0]
    assert in3.event_type == InputType.JoystickHat
    assert in3.identifier == 1
    assert in3.device_guid == uuid.UUID("4DCB3090-97EC-11EB-8003-444553540000")
    in4 = a.conditions[3]._inputs[0]
    in4.scan_code = 42
    in4.is_extended = True

    # Condition data
    assert len(a.conditions[0]._inputs) == 2
    c1 = a.conditions[0]
    assert isinstance(c1, condition.JoystickCondition)
    assert isinstance(c1._comparator, condition.comparator.PressedComparator)
    assert c1._inputs[0].event_type == InputType.JoystickButton
    assert c1._comparator.is_pressed == False
    assert c1.is_valid()

    c2 = a.conditions[1]
    assert isinstance(c2, condition.JoystickCondition)
    assert isinstance(c2._comparator, condition.comparator.RangeComparator)
    assert c2._inputs[0].event_type == InputType.JoystickAxis
    assert c2._comparator.lower == 0.2
    assert c2._comparator.upper == 0.9
    assert c2.is_valid()

    c3 = a.conditions[2]
    assert isinstance(c3, condition.JoystickCondition)
    assert isinstance(c3._comparator, condition.comparator.DirectionComparator)
    assert c3._inputs[0].event_type == InputType.JoystickHat
    assert len(c3._comparator.directions) == 3
    assert c3._comparator.directions[0] == HatDirection.North
    assert c3._comparator.directions[1] == HatDirection.East
    assert c3._comparator.directions[2] == HatDirection.NorthEast

    c4 = a.conditions[3]
    assert isinstance(c4, condition.KeyboardCondition)
    assert isinstance(c4._comparator, condition.comparator.PressedComparator)
    assert c4._comparator.is_pressed == False


def test_to_xml():
    a = condition.ConditionData(InputType.JoystickButton)

    cond = condition.JoystickCondition()
    input_dev = Event(
        InputType.JoystickButton,
        37,
        uuid.UUID("4DCB3090-97EC-11EB-8003-444553540000"),
        "Default"
    )
    cond._inputs.append(input_dev)
    cond._comparator = condition.comparator.PressedComparator(True)
    a.conditions.append(cond)

    node = a.to_xml()
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


def test_action_methods(xml_dir: pathlib.Path):
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE_SIMPLE))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    assert len(a.get_actions()[0]) == 3
    assert len(a.get_actions("true")[0]) == 2
    assert len(a.get_actions("false")[0]) == 1
    with pytest.raises(GremlinError):
        a.get_actions("invalid options")

    d1 = DescriptionData()
    d2 = DescriptionData()
    a.insert_action(d1, "false", DataInsertionMode.Prepend)
    a.insert_action(d2, "false", DataInsertionMode.Append, 0)
    assert len(a.get_actions("false")[0]) == 3
    assert a.get_actions("false")[0][0] == d1
    assert a.get_actions("false")[0][1] == d2

    a.remove_action(0, "false")
    assert len(a.get_actions("false")[0]) == 2
    assert a.get_actions("false")[0][0] == d2


def test_ctor():
    a = ConditionData(InputType.JoystickButton)

    assert len(a.conditions) == 0
    assert a.logical_operator == condition.LogicalOperator.All
    assert a.is_valid() == True
