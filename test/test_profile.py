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

import gremlin.error
import gremlin.plugin_manager
from gremlin.profile import Profile
import gremlin.profile_library
import gremlin.types
import gremlin.util


xml_simple = """
<profile version="14">
    <inputs>
        <input>
            <device-id>{af3d9175-30a7-4d77-aed5-e1b5e0b71efc}</device-id>
            <input-type>button</input-type>
            <input-id>6</input-id>
            <mode>Default</mode>
            <actions>
                <action-tree id="ec663ba4-264a-4c76-98c0-6054058cae9f">
                    <action id="ac905a47-9ad3-4b65-b702-fbae1d133609" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="condition">
                        <property type="string">
                            <name>type</name>
                            <value>activation-range</value>
                        </property>
                        <property type="axis-range">
                            <name>activation-range</name>
                            <low>0.4</low>
                            <high>0.8</high>
                        </property>
                    </action>
                    <action id="f6d6a7af-baef-4b42-ab93-44608dedc859" parent="ec663ba4-264a-4c76-98c0-6054058cae9f" type="library">
                        <property type="guid">
                            <name>reference</name>
                            <value>1234</value>
                        </property>
                    </action>
                </action-tree>
            </actions>
        </input>
    </inputs>
</profile>
"""

xml_description = """
<profile version="14">
    <inputs>
        <input>
            <device-id>af3d9175-30a7-4d77-aed5-e1b5e0b71efc</device-id>
            <input-type>button</input-type>
            <input-id>6</input-id>
            <mode>Default</mode>
            <library-reference>ac905a47-9ad3-4b65-b702-fbae1d133609</library-reference>
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
                        <name>input-type</name>
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


# def test_constructor_simple():
#     fpath = _store_in_tmpfile(xml_simple)
#
#     p = Profile()
#     p.from_xml(fpath)
#
#     os.remove(fpath)
#
#     guid = gremlin.util.parse_guid("{af3d9175-30a7-4d77-aed5-e1b5e0b71efc}")
#     assert len(p.inputs) == 1
#     assert p.inputs[guid][0].device_id == guid
#     assert p.inputs[guid][0].input_type == gremlin.types.InputType.JoystickButton
#     assert p.inputs[guid][0].input_id == 6
#     assert p.inputs[guid][0].mode == "Default"


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

    library_items = p.inputs[guid][0].actions
    assert len(library_items) == 1
    assert isinstance(library_items[0], gremlin.profile_library.LibraryItem)

    actions = library_items[0].action_tree.root.children
    assert len(actions) == 3
    assert actions[0].value.tag == "description"
    assert actions[0].value.description == "This is a test"
    assert actions[0].value.id == uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
    assert actions[1].value.tag == "description"
    assert actions[1].value.description == "Feuer frei!"
    assert actions[1].value.id == uuid.UUID("f6d6a7af-baef-4b42-ab93-44608dedc859")
    assert actions[2].value.tag == "remap"
    assert actions[2].value._vjoy_device_id == 2
    assert actions[2].value._vjoy_input_id == 6
    assert actions[2].value._input_type == gremlin.types.InputType.JoystickAxis
    assert actions[2].value._axis_mode == gremlin.types.AxisMode.Relative
    assert actions[2].value._axis_scaling == 1.5
    assert actions[2].value.id == uuid.UUID("d67cbad2-da3f-4b59-b434-2d493e7e6185")

    os.remove(fpath)
