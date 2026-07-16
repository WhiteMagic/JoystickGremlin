# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib
import uuid

import gremlin.profile
from gremlin import swap_devices

_PROFILE_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540000")


def test_swap_devices_from_data_xml(xml_dir: pathlib.Path) -> None:
    profile = gremlin.profile.Profile()
    existing_uuid = _PROFILE_DEVICE_UUID
    new_uuid = uuid.uuid4()
    profile.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    result = swap_devices.swap_devices(profile, existing_uuid, new_uuid)
    assert result.input_swaps == 9
    assert result.action_swaps == 2
