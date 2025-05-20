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

import os
import pytest
import uuid
from xml.etree import ElementTree

import gremlin.plugin_manager
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.types import AxisMode, InputType

from gremlin.profile import Profile

# Ensure config entries are generated
import action_plugins.tempo


def test_constructor_invalid(xml_dir: str):
    p = Profile()
    with pytest.raises(ValueError):
        p.from_xml(os.path.join(xml_dir, "profile_invalid.xml"))


def test_simple_action(xml_dir: str):
    gremlin.plugin_manager.PluginManager()

    p = Profile()
    p.from_xml(os.path.join(xml_dir, "profile_simple.xml"))

    guid = uuid.UUID("{af3d9175-30a7-4d77-aed5-e1b5e0b71efc}")

    action_sequences = p.inputs[guid][0].action_sequences
    assert len(action_sequences) == 1
    assert isinstance(action_sequences[0], gremlin.profile.InputItemBinding)

    actions = action_sequences[0].root_action.get_actions()[0]
    assert len(actions) == 3
    assert actions[0].tag == "description"
    assert actions[0].description == "This is a test"
    assert actions[0].id == uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133608")

    assert actions[1].tag == "description"
    assert actions[1].description == "Different test"
    assert actions[1].id == uuid.UUID("f6d6a7af-baef-4b42-ab93-44608dedc859")

    assert actions[2].tag == "map-to-vjoy"
    assert actions[2].vjoy_device_id == 2
    assert actions[2].vjoy_input_id == 6
    assert actions[2].vjoy_input_type == InputType.JoystickAxis
    assert actions[2].axis_mode == AxisMode.Relative
    assert actions[2].axis_scaling == 1.5
    assert actions[2].id == uuid.UUID("d67cbad2-da3f-4b59-b434-2d493e7e6185")


def test_hierarchy(xml_dir: str):
    gremlin.plugin_manager.PluginManager()

    c = Configuration()
    p = Profile()
    p.from_xml(os.path.join(xml_dir, "profile_hierarchy.xml"))

    root = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))
    assert len(root.get_actions()[0]) == 3

    n1 = root.get_actions()[0][0]
    n2 = root.get_actions()[0][1]
    n3 = root.get_actions()[0][2]

    assert n1.tag == "description"
    assert n1.description == "Node 1"
    assert n2.tag == "tempo"
    assert n3.tag == "description"
    assert n3.description == "Node 3"

    n4 = n2.get_actions()[0][0]
    assert len(n2.get_actions()) == 2
    assert n4.tag == "description"
    assert n4.description == "Node 4"


def test_mode_hierarchy(xml_dir: str):
    p = Profile()
    p.from_xml(os.path.join(xml_dir, "profile_mode_hierarchy.xml"))

    assert p.modes.mode_names() == ["Child", "Deep", "Default", "Levels", "Separate", "Three"]
    assert p.modes.first_mode == "Default"

    assert p.modes.find_mode("Levels").value == "Levels"
    assert p.modes.find_mode("Levels").parent.value == "Three"

    assert p.modes.find_mode("Default").parent.value == ""
    assert p.modes.find_mode("Default").parent == p.modes._hierarchy
