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

import dill
from gremlin.error import GremlinError
import gremlin.types as types
from gremlin.profile import Library

from action_plugins.description import DescriptionData
from action_plugins.map_to_vjoy import MapToVjoyData

_ACTION_MAP_BUTTON = "action_map_to_vjoy_button.xml"
_ACTION_MAP_AXIS = "action_map_to_vjoy_axis.xml"


def test_ctor(joystick_init: None) -> None:
    r = MapToVjoyData(types.InputType.JoystickButton)

    assert r.vjoy_device_id == 1
    assert r.vjoy_input_id == 1
    assert r.vjoy_input_type == types.InputType.JoystickButton
    assert r.axis_mode == types.AxisMode.Absolute
    assert r.axis_scaling == 1.0


def test_actions(xml_dir: pathlib.Path):
    l = Library()
    a = MapToVjoyData(types.InputType.JoystickButton)
    a.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_MAP_BUTTON).read_text()),
        l,
    )

    assert len(a.get_actions()[0]) == 0
    with pytest.raises(GremlinError):
        d = DescriptionData()
        a.insert_action(d, "something")
    with pytest.raises(GremlinError):
        a.remove_action(0, "something")


def test_from_xml(xml_dir: pathlib.Path):
    l = Library()
    r = MapToVjoyData(types.InputType.JoystickButton)
    r.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_MAP_BUTTON).read_text()),
        l,
    )
    assert r.vjoy_device_id == 1
    assert r.vjoy_input_id == 12
    assert r.vjoy_input_type == types.InputType.JoystickButton
    assert r.axis_mode == types.AxisMode.Absolute
    assert r.axis_scaling == 1.0

    r = MapToVjoyData(types.InputType.JoystickButton)
    r.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_MAP_AXIS).read_text()), l
    )
    assert r.vjoy_device_id == 2
    assert r.vjoy_input_id == 6
    assert r.vjoy_input_type == types.InputType.JoystickAxis
    assert r.axis_mode == types.AxisMode.Relative
    assert r.axis_scaling == 1.5


def test_to_xml():
    r = MapToVjoyData(types.InputType.JoystickButton)

    r._id = uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
    r.vjoy_device_id = 2
    r.vjoy_input_id = 14
    r.vjoy_input_type = types.InputType.JoystickButton

    node = r._to_xml()
    assert node.find(
            "./property/name[.='vjoy-device-id']/../value"
        ).text == "2"
    assert node.find(
            "./property/name[.='vjoy-input-id']/../value"
        ).text == "14"
    assert node.find(
            "./property/name[.='vjoy-input-type']/../value"
        ).text == "button"
    assert node.find("./property/name[.='axis-mode']") == None
    assert node.find("./property/name[.='axis-scaling']") == None

    r.vjoy_input_type = types.InputType.JoystickAxis
    r.axis_mode = types.AxisMode.Absolute
    r.axis_scaling = 0.75

    node = r._to_xml()
    assert node.find(
        "./property/name[.='vjoy-device-id']/../value"
    ).text == "2"
    assert node.find(
        "./property/name[.='vjoy-input-id']/../value"
    ).text == "14"
    assert node.find(
        "./property/name[.='vjoy-input-type']/../value"
    ).text == "axis"
    assert node.find(
        "./property/name[.='axis-mode']/../value"
    ).text == "absolute"
    assert node.find(
        "./property/name[.='axis-scaling']/../value"
    ).text == "0.75"
