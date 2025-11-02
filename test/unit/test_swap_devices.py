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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pathlib
import uuid

from gremlin import profile, swap_devices

_PROFILE_DEVICE_UUID = uuid.UUID('97b77b40-07d8-11f0-8028-444553540000')


def test_swap_devices_from_data_xml(xml_dir: pathlib.Path):
    p = profile.Profile()
    existing_uuid = _PROFILE_DEVICE_UUID
    new_uuid = uuid.uuid4()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    result = swap_devices.swap_devices(p, existing_uuid, new_uuid)
    assert result.input_swaps == 9
    assert result.action_swaps == 2
