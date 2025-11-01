# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2025 Lionel Ott
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

import pathlib
import uuid
from gremlin.profile import Profile
from action_plugins import macro

_PROFILE = "action_macro.xml"
_ACTION_UUID = uuid.UUID("8759f48d-8879-488a-9895-07503bf0dc0c")
_INPUT_1_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540000")
_INPUT_2_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540001")


def test_from_xml(subtests, xml_dir: pathlib.Path):
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))

    a = p.library.get_action(_ACTION_UUID)

    assert isinstance(a, macro.MacroData)
    with subtests.test("macro high level data"):
        assert a.is_exclusive == False
        assert a.repeat_mode == macro.MacroRepeatModes.Single
        assert a.repeat_data.count == 1
        assert a.repeat_data.delay == 0.1
        assert a.is_valid()
        assert len(a.actions) == 10


def test_swap_uuid(xml_dir: pathlib.Path):
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))

    a = p.library.get_action(_ACTION_UUID)

    new_device_uuid = uuid.uuid4()
    assert a.swap_uuid(_INPUT_1_DEVICE_UUID, new_device_uuid)
    assert a.actions[0].device_guid == new_device_uuid
    assert a.actions[2].device_guid == _INPUT_2_DEVICE_UUID
    