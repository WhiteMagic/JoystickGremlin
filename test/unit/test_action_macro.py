# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib
import uuid

import pytest

from action_plugins import macro
from gremlin.profile import Profile

_PROFILE = "action_macro.xml"
_ACTION_UUID = uuid.UUID("8759f48d-8879-488a-9895-07503bf0dc0c")
_INPUT_1_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540000")
_INPUT_2_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540001")


def test_from_xml(subtests: pytest.Subtests, xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))

    a = p.library.get_action(_ACTION_UUID)

    assert isinstance(a, macro.MacroData)
    with subtests.test("macro high level data"):
        assert not a.is_exclusive
        assert a.repeat_mode == macro.MacroRepeatModes.Single
        assert a.repeat_data.count == 1
        assert a.repeat_data.delay == 0.1
        assert a.is_valid()
        assert len(a.actions) == 10


def test_swap_uuid(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))

    a = p.library.get_action(_ACTION_UUID)

    new_device_uuid = uuid.uuid4()
    assert a.swap_uuid(_INPUT_1_DEVICE_UUID, new_device_uuid)
    assert a.actions[0].device_guid == new_device_uuid
    assert a.actions[2].device_guid == _INPUT_2_DEVICE_UUID
