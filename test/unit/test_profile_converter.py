# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid
from xml.etree import ElementTree

import pytest

from action_plugins.virtual_button import VirtualButtonData
from gremlin import util
from gremlin.profile import Profile
from gremlin.profile_migration import migrate_profile
from gremlin.types import (
    AxisButtonDirection,
    InputType,
    PropertyType,
)
from test.unit.conftest import get_fake_device_guid

_PROFILE = "profile_version_14.xml"


def _child_ids(root: ElementTree.Element, action_id: str) -> list[str]:
    return [
        str(aid)
        for aid in util.read_action_ids(
            root.find(f"./library/action[@id='{action_id}']/actions")
        )
    ]


def test_sequences_become_root_references(
    xml_dir: pathlib.Path,
) -> None:
    root = ElementTree.parse(xml_dir / _PROFILE).getroot()
    axis_input = root.findall("./inputs/input")[1]
    assert [
        node.text for node in axis_input.findall("action-configuration/root-action")
    ] == [
        "e4a10000-0000-4000-8000-000000000002",
        "e4a10000-0000-4000-8000-000000000003",
    ]

    migrate_profile(root, xml_dir / _PROFILE)

    assert axis_input.findall("action-configuration") == []
    assert [node.text for node in axis_input.findall("root-action")] == [
        "e4a10000-0000-4000-8000-000000000002",
        "e4a10000-0000-4000-8000-000000000003",
    ]
    assert root.get("version") == "17"


def test_root_records_input_type(xml_dir: pathlib.Path) -> None:
    root = ElementTree.parse(xml_dir / _PROFILE).getroot()
    root_action = root.find(
        "./library/action[@id='e4a10000-0000-4000-8000-000000000004']"
    )
    assert util.read_properties(root_action, "input-type", PropertyType.InputType) == []

    migrate_profile(root, xml_dir / _PROFILE)

    assert util.read_properties(root_action, "input-type", PropertyType.InputType) == [
        InputType.JoystickHat
    ]


def test_root_without_reference_is_dropped(xml_dir: pathlib.Path) -> None:
    root = ElementTree.parse(xml_dir / _PROFILE).getroot()
    orphan = "./library/action[@id='e4a10000-0000-4000-8000-000000000005']"
    assert root.find(orphan) is not None

    migrate_profile(root, xml_dir / _PROFILE)

    assert root.find(orphan) is None
    assert (
        root.find("./library/action[@id='e4b10000-0000-4000-8000-000000000005']")
        is not None
    )


def test_sequence_without_virtual_button_keeps_children(
    xml_dir: pathlib.Path,
) -> None:
    root = ElementTree.parse(xml_dir / _PROFILE).getroot()
    root_id = "e4a10000-0000-4000-8000-000000000002"
    assert _child_ids(root, root_id) == ["e4b10000-0000-4000-8000-000000000002"]

    migrate_profile(root, xml_dir / _PROFILE)

    assert _child_ids(root, root_id) == ["e4b10000-0000-4000-8000-000000000002"]


def test_axis_virtual_button_holds_root_children(
    xml_dir: pathlib.Path,
) -> None:
    root = ElementTree.parse(xml_dir / _PROFILE).getroot()
    root_id = "e4a10000-0000-4000-8000-000000000003"
    assert _child_ids(root, root_id) == ["e4b10000-0000-4000-8000-000000000003"]

    migrate_profile(root, xml_dir / _PROFILE)

    (virtual_button_id,) = _child_ids(root, root_id)
    virtual_button = root.find(f"./library/action[@id='{virtual_button_id}']")
    assert virtual_button.get("type") == "virtual-button"
    assert _child_ids(root, virtual_button_id) == [
        "e4b10000-0000-4000-8000-000000000003"
    ]
    assert util.read_property(
        virtual_button, "lower-limit", PropertyType.Float
    ) == pytest.approx(0.25)
    assert util.read_property(
        virtual_button, "upper-limit", PropertyType.Float
    ) == pytest.approx(0.75)
    assert (
        util.read_property(virtual_button, "axis-button-direction", PropertyType.String)
        == "below"
    )


def test_hat_virtual_button_keeps_directions(
    xml_dir: pathlib.Path,
) -> None:
    root = ElementTree.parse(xml_dir / _PROFILE).getroot()
    root_id = "e4a10000-0000-4000-8000-000000000004"

    migrate_profile(root, xml_dir / _PROFILE)

    (virtual_button_id,) = _child_ids(root, root_id)
    virtual_button = root.find(f"./library/action[@id='{virtual_button_id}']")
    assert [
        util.property_to_string(PropertyType.HatDirection, direction)
        for direction in util.read_properties(
            virtual_button, "hat-direction", PropertyType.HatDirection
        )
    ] == ["north", "south"]


def test_version_14_profile_loads_virtual_button_action(
    xml_dir: pathlib.Path,
) -> None:
    p = Profile()
    p.from_xml(xml_dir / _PROFILE)

    button_input, axis_input, _ = p.inputs[get_fake_device_guid(is_virtual=False).uuid]
    assert button_input.action_sequences[0].action_label == "Landing gear"
    (virtual_button,) = axis_input.action_sequences[1].get_actions()[0]
    assert isinstance(virtual_button, VirtualButtonData)
    assert virtual_button.direction == AxisButtonDirection.Below
    assert [child.id for child in virtual_button.children] == [
        uuid.UUID("e4b10000-0000-4000-8000-000000000003")
    ]


def test_version_14_profile_saves_current_version(
    xml_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    p = Profile()
    p.from_xml(xml_dir / _PROFILE)

    p.to_xml(tmp_path / "profile.xml")

    saved = ElementTree.parse(tmp_path / "profile.xml").getroot()
    assert saved.get("version") == str(Profile.current_version)
    assert saved.findall("./inputs/input/action-configuration") == []
