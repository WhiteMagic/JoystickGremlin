# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib
import uuid

import pytest

from action_plugins import (
    dual_axis_deadzone,
    map_to_vjoy,
)
from gremlin.profile import Profile

_PROFILE = "action_dual_axis_deadzone.xml"
_ACTION_UUID = uuid.UUID("20465c1e-afb3-49f9-9e43-1d7087f0e8ce")
_INPUT_1_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540000")
_INPUT_2_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540001")


def test_from_xml(subtests: pytest.Subtests, xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))

    a = p.library.get_action(_ACTION_UUID)

    assert isinstance(a, dual_axis_deadzone.DualAxisDeadzoneData)
    with subtests.test("action inputs"):
        assert a.inner_deadzone == 0.0
        assert a.outer_deadzone == 1.0
        assert a.axis1.device_guid == _INPUT_1_DEVICE_UUID
        assert a.axis1.input_id == 1
        assert a.axis2.device_guid == _INPUT_2_DEVICE_UUID
        assert a.axis2.input_id == 2
        assert a.is_valid()

    with subtests.test("action outputs"):
        assert len(a.output1_actions) == 1
        assert len(a.output2_actions) == 1
        assert isinstance(a.output1_actions[0], map_to_vjoy.MapToVjoyData)
        assert a.output1_actions[0].vjoy_device_id == 1
        assert a.output1_actions[0].vjoy_input_id == 1
        assert isinstance(a.output2_actions[0], map_to_vjoy.MapToVjoyData)
        assert a.output2_actions[0].vjoy_device_id == 1
        assert a.output2_actions[0].vjoy_input_id == 2


def test_swap_uuid(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))

    a = p.library.get_action(_ACTION_UUID)

    new_device_uuid = uuid.uuid4()
    a.swap_uuid(_INPUT_1_DEVICE_UUID, new_device_uuid)
    assert a.axis1.device_guid == new_device_uuid
    assert a.axis2.device_guid == _INPUT_2_DEVICE_UUID
