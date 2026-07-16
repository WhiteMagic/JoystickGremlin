# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid

import action_plugins.merge_axis as merge_axis
import gremlin.types as types
from action_plugins.description import DescriptionData
from gremlin.profile import Profile
from gremlin.ui.device import InputIdentifier

# Test UUIDs
_ACTION_ID = uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
_DESCRIPTION_ID = uuid.UUID("fbe6be7b-07c9-4400-94f2-caa245ebcc7e")
_DEVICE_GUID_1 = uuid.UUID("4DCB3090-97EC-11EB-8003-444553540001")
_DEVICE_GUID_2 = uuid.UUID("4DCB3090-97EC-11EB-8003-444553540002")


def test_ctor() -> None:
    a = merge_axis.MergeAxisData(types.InputType.JoystickAxis)

    assert len(a.children) == 0
    assert a.label == ""
    assert a.operation == merge_axis.MergeOperation.Average
    assert a.axis_in1 == InputIdentifier()
    assert a.axis_in2 == InputIdentifier()


def test_from_xml(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / "action_merge_axis.xml"))

    a = p.library.get_action(_ACTION_ID)

    assert len(a.children) == 1
    assert a.label == "test axis merge"
    assert a.operation == merge_axis.MergeOperation.Minimum
    assert a.axis_in1.device_guid == _DEVICE_GUID_1
    assert a.axis_in1.input_type == types.InputType.JoystickAxis
    assert a.axis_in1.input_id == 1
    assert a.axis_in2.device_guid == _DEVICE_GUID_2
    assert a.axis_in2.input_type == types.InputType.JoystickAxis
    assert a.axis_in2.input_id == 2


def test_to_xml() -> None:
    d = DescriptionData()
    d._id = _DESCRIPTION_ID

    a = merge_axis.MergeAxisData(types.InputType.JoystickAxis)
    a.label = "This is a test"
    a.operation = merge_axis.MergeOperation.Maximum
    a.insert_action(d, "children")

    a.axis_in1.device_guid = _DEVICE_GUID_1
    a.axis_in1.input_type = types.InputType.JoystickAxis
    a.axis_in2.device_guid = _DEVICE_GUID_2
    a.axis_in1.input_id = 1
    a.axis_in2.input_type = types.InputType.JoystickAxis
    a.axis_in2.input_id = 2

    node = a._to_xml()
    assert node.find("./property/name[.='label']/../value").text == "This is a test"
    assert node.find("./property/name[.='operation']/../value").text == "maximum"
    assert node.find("./property/name[.='axis1-axis']/../value").text == "1"
    assert (
        node.find("./property/name[.='axis1-guid']/../value").text.upper()
        == str(_DEVICE_GUID_1).upper()
    )


def test_swap_first_uuid(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / "action_merge_axis.xml"))

    a = p.library.get_action(_ACTION_ID)
    new_device_uuid = uuid.uuid4()
    a.swap_uuid(_DEVICE_GUID_1, new_device_uuid)
    assert a.axis_in1.device_guid == new_device_uuid
    assert a.axis_in2.device_guid == _DEVICE_GUID_2


def test_swap_second_uuid(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / "action_merge_axis.xml"))

    a = p.library.get_action(_ACTION_ID)
    new_device_uuid = uuid.uuid4()
    a.swap_uuid(_DEVICE_GUID_2, new_device_uuid)
    assert a.axis_in1.device_guid == _DEVICE_GUID_1
    assert a.axis_in2.device_guid == new_device_uuid
