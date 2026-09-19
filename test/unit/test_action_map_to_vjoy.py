# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid
from xml.etree import ElementTree

import pytest

from action_plugins.description import DescriptionData
from action_plugins.map_to_vjoy import MapToVjoyData
from action_plugins.root import RootData
from gremlin import (
    shared_state,
    types,
)
from gremlin.error import GremlinError
from gremlin.profile import (
    InputItem,
    InputItemBinding,
    Library,
    Profile,
)

_ACTION_MAP_BUTTON = "action_map_to_vjoy_button.xml"
_ACTION_MAP_AXIS = "action_map_to_vjoy_axis.xml"


def _profile_with_mappings(
    monkeypatch: pytest.MonkeyPatch,
    input_type: types.InputType,
    bound_ids: list[int],
    unbound_ids: list[int] | None = None,
) -> None:
    """Sets a current profile mapping vJoy 1 inputs by bound or library-only actions."""
    profile = Profile()
    monkeypatch.setattr(shared_state, "current_profile", profile)
    input_item = InputItem(profile.library)
    binding = InputItemBinding(input_item)
    binding.root_action = RootData(input_type)
    input_item.action_sequences.append(binding)
    profile.inputs[uuid.uuid4()] = [input_item]

    for input_id in bound_ids + (unbound_ids or []):
        action = MapToVjoyData(input_type)
        action.vjoy_input_id = input_id
        profile.library.add_action(action)
        if input_id in bound_ids:
            binding.root_action.insert_action(action, "children")


def test_ctor(joystick_init: None) -> None:
    r = MapToVjoyData(types.InputType.JoystickButton)

    assert r.vjoy_device_id == 1
    assert r.vjoy_input_id == 1
    assert r.vjoy_input_type == types.InputType.JoystickButton
    assert r.axis_mode == types.AxisMode.Absolute
    assert r.axis_scaling == 1.0


def test_actions(xml_dir: pathlib.Path) -> None:
    library = Library()
    a = MapToVjoyData(types.InputType.JoystickButton)
    a.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_MAP_BUTTON).read_text()),
        library,
    )

    assert len(a.get_actions()[0]) == 0
    with pytest.raises(GremlinError):
        d = DescriptionData()
        a.insert_action(d, "something")
    with pytest.raises(GremlinError):
        a.remove_action(0, "something")


def test_from_xml(xml_dir: pathlib.Path) -> None:
    library = Library()
    r = MapToVjoyData(types.InputType.JoystickButton)
    r.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_MAP_BUTTON).read_text()),
        library,
    )
    assert r.vjoy_device_id == 1
    assert r.vjoy_input_id == 12
    assert r.vjoy_input_type == types.InputType.JoystickButton
    assert r.axis_mode == types.AxisMode.Absolute
    assert r.axis_scaling == 1.0

    r = MapToVjoyData(types.InputType.JoystickButton)
    r.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_MAP_AXIS).read_text()), library
    )
    assert r.vjoy_device_id == 2
    assert r.vjoy_input_id == 6
    assert r.vjoy_input_type == types.InputType.JoystickAxis
    assert r.axis_mode == types.AxisMode.Relative
    assert r.axis_scaling == 1.5


def test_to_xml() -> None:
    r = MapToVjoyData(types.InputType.JoystickButton)

    r._id = uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")
    r.vjoy_device_id = 2
    r.vjoy_input_id = 14
    r.vjoy_input_type = types.InputType.JoystickButton

    node = r._to_xml()
    assert node.find("./property/name[.='vjoy-device-id']/../value").text == "2"
    assert node.find("./property/name[.='vjoy-input-id']/../value").text == "14"
    assert node.find("./property/name[.='vjoy-input-type']/../value").text == "button"
    assert node.find("./property/name[.='axis-mode']") is None
    assert node.find("./property/name[.='axis-scaling']") is None

    r.vjoy_input_type = types.InputType.JoystickAxis
    r.axis_mode = types.AxisMode.Absolute
    r.axis_scaling = 0.75

    node = r._to_xml()
    assert node.find("./property/name[.='vjoy-device-id']/../value").text == "2"
    assert node.find("./property/name[.='vjoy-input-id']/../value").text == "14"
    assert node.find("./property/name[.='vjoy-input-type']/../value").text == "axis"
    assert node.find("./property/name[.='axis-mode']/../value").text == "absolute"
    assert node.find("./property/name[.='axis-scaling']/../value").text == "0.75"


@pytest.mark.parametrize(
    ("input_type", "bound_ids", "unbound_ids", "expected_id"),
    [
        (types.InputType.JoystickButton, [1, 2, 3, 5], [], 4),
        (types.InputType.JoystickButton, [1], [2], 2),
        (types.InputType.JoystickButton, list(range(1, 65)), [], 1),
        (types.InputType.JoystickAxis, [1, 2, 3], [], 6),
        (types.InputType.JoystickHat, [1], [], 2),
    ],
    ids=["gap", "unbound ignored", "all used", "axis gap", "hat"],
)
def test_create_selects_first_unused_input(
    monkeypatch: pytest.MonkeyPatch,
    input_type: types.InputType,
    bound_ids: list[int],
    unbound_ids: list[int],
    expected_id: int,
) -> None:
    _profile_with_mappings(monkeypatch, input_type, bound_ids, unbound_ids)

    action = MapToVjoyData.create(types.DataCreationMode.Create, input_type)

    assert isinstance(action, MapToVjoyData)
    assert action.vjoy_device_id == 1
    assert action.vjoy_input_type == input_type
    assert action.vjoy_input_id == expected_id
