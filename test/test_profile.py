# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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
import tempfile
import uuid
from xml.etree import ElementTree

import gremlin.error
import gremlin.plugin_manager
from gremlin.profile import Profile
import gremlin.profile_library
import gremlin.types
import gremlin.util


xml_description = """
<profile version="14">
    <inputs>
        <input>
            <device-id>af3d9175-30a7-4d77-aed5-e1b5e0b71efc</device-id>
            <input-type>button</input-type>
            <input-id>6</input-id>
            <mode>Default</mode>
            <action-configuration>
                <library-reference>ac905a47-9ad3-4b65-b702-fbae1d133609</library-reference>
                <behavior>button</behavior>
                <description></description>
            </action-configuration>
        </input>
    </inputs>
    
    <library>
        <library-item id="ac905a47-9ad3-4b65-b702-fbae1d133609">
            <action-tree root="ec663ba4-264a-4c76-98c0-6054058cae9f">
                <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="description">
                    <property type="string">
                        <name>description</name>
                        <value>This is a test</value>
                    </property>
                </action>
                <action id="f6d6a7af-baef-4b42-ab93-44608dedc859" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="description">
                    <property type="string">
                        <name>description</name>
                        <value>Feuer frei!</value>
                    </property>
                </action>
                <action id="d67cbad2-da3f-4b59-b434-2d493e7e6185" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="remap">
                    <property type="int">
                        <name>vjoy-device-id</name>
                        <value>2</value>
                    </property>
                    <property type="int">
                        <name>vjoy-input-id</name>
                        <value>6</value>
                    </property>
                    <property type="input_type">
                        <name>vjoy-input-type</name>
                        <value>axis</value>
                    </property>
                    <property type="axis_mode">
                        <name>axis-mode</name>
                        <value>relative</value>
                    </property>
                    <property type="float">
                        <name>axis-scaling</name>
                        <value>1.5</value>
                    </property>
                </action>
            </action-tree>
        </library-item>
    </library>
</profile>
"""

xml_hierarchy = """
<profile version="14">
    <inputs>
        <input>
            <device-id>23AB4520-6C28-11EA-8001-444553540000</device-id>
            <input-type>button</input-type>
            <input-id>1</input-id>
            <mode>Default</mode>
            <action-configuration>
                <library-reference>ac905a47-9ad3-4b65-b702-fbae1d133609</library-reference>
                <behavior>button</behavior>
                <description></description>
            </action-configuration>
        </input>
    </inputs>

    <library>
        <library-item id="ac905a47-9ad3-4b65-b702-fbae1d133609">
            <action-tree root="ec663ba4-264a-4c76-98c0-6054058cae9f">
                <action id="0c905a47-9ad3-4b65-b702-fbae1d133600" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="description">
                    <property type="string">
                        <name>description</name>
                        <value>Node 1</value>
                    </property>
                </action>
                <action id="0c905a47-9ad3-4b65-b702-fbae1d133601" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="description">
                    <property type="string">
                        <name>description</name>
                        <value>Node 2</value>
                    </property>
                </action>
                <action id="0c905a47-9ad3-4b65-b702-fbae1d133602" parent="0c905a47-9ad3-4b65-b702-fbae1d133603" type="description">
                    <property type="string">
                        <name>description</name>
                        <value>Node 4</value>
                    </property>
                </action>
                <action id="0c905a47-9ad3-4b65-b702-fbae1d133603" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="description">
                    <property type="string">
                        <name>description</name>
                        <value>Node 3</value>
                    </property>
                </action>
            </action-tree>
        </library-item>
    </library>
</profile>
"""

xml_invalid = """
<profile version="14">
    <inputs>
        <input>
            <device-id>{af3d9175-30a7-4d77-e1b5e0b71efc}</device-id>
            <input-type>button34</input-type>
            <mode>Default</mode>
            <actions>
            </actions>
        </input>
    </inputs>
</profile>
"""


def _store_in_tmpfile(text: str) -> str:
    """Stores the provided text in a temporary file and returns the path.

    Args:
        text: the text to store in a temporary file

    Returns:
        Path to the temporary file
    """
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)
    tmp.write(text)
    fpath = tmp.name
    tmp.close()
    return fpath



def test_constructor_invalid():
    fpath = _store_in_tmpfile(xml_invalid)

    p = Profile()
    with pytest.raises(gremlin.error.GremlinError, match=r".*Failed parsing GUID.*"):
        p.from_xml(fpath)

    os.remove(fpath)


def test_simple_action():
    gremlin.plugin_manager.ActionPlugins()
    fpath = _store_in_tmpfile(xml_description)

    p = Profile()
    p.from_xml(fpath)

    guid = gremlin.util.parse_guid("{af3d9175-30a7-4d77-aed5-e1b5e0b71efc}")

    action_configurations = p.inputs[guid][0].action_configurations
    assert len(action_configurations) == 1
    assert isinstance(action_configurations[0], gremlin.profile.InputItemBinding)

    actions = action_configurations[0].library_reference.action_tree.root.children
    assert len(actions) == 3
    assert actions[0].value.tag == "description"
    assert actions[0].value.description == "This is a test"
    assert actions[0].value.id == uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
    assert actions[1].value.tag == "description"
    assert actions[1].value.description == "Feuer frei!"
    assert actions[1].value.id == uuid.UUID("f6d6a7af-baef-4b42-ab93-44608dedc859")
    assert actions[2].value.tag == "remap"
    assert actions[2].value.vjoy_device_id == 2
    assert actions[2].value.vjoy_input_id == 6
    assert actions[2].value.vjoy_input_type == gremlin.types.InputType.JoystickAxis
    assert actions[2].value.axis_mode == gremlin.types.AxisMode.Relative
    assert actions[2].value.axis_scaling == 1.5
    assert actions[2].value.id == uuid.UUID("d67cbad2-da3f-4b59-b434-2d493e7e6185")

    os.remove(fpath)


def test_hierarchy():
    gremlin.plugin_manager.ActionPlugins()
    fpath = _store_in_tmpfile(xml_hierarchy)

    p = Profile()
    p.from_xml(fpath)

    item_uuid = uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
    root = p.library[item_uuid].action_tree.root
    assert root.node_count == 5

    n1 = root.node_at_index(1)
    n2 = root.node_at_index(2)
    n3 = root.node_at_index(3)
    n4 = root.node_at_index(4)

    assert n1.parent == root
    assert n2.parent == root
    assert n3.parent == root
    assert n4.parent == n3

    assert n1.value.description == "Node 1"
    assert n2.value.description == "Node 2"
    assert n3.value.description == "Node 3"
    assert n4.value.description == "Node 4"

    os.remove(fpath)


def test_mode_hierarchy():
    xml = """
    <profile>
        <modes>
            <mode>Default</mode>
            <mode>Separate</mode>
            <mode parent="Default">Child</mode>
            <mode>Three</mode>
            <mode parent="Three">Levels</mode>
            <mode parent="Levels">Deep</mode>
        </modes>
    </profile>
    """
    fpath = _store_in_tmpfile(xml)

    tree = ElementTree.parse(fpath)
    root = tree.getroot()


    mh = gremlin.profile.ModeHierarchy()
    mh.from_xml(root)

    assert mh.mode_list() == ["Child", "Deep", "Default", "Levels", "Separate", "Three"]
    assert mh.first_mode == "Default"