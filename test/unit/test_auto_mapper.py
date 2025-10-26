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

import pytest

import dill
from gremlin import auto_mapper, device_initialization, profile, shared_state, types

_PROFILE_DEVICE_AXIS_COUNT = 4
_PROFILE_DEVICE_BUTTON_COUNT = 6
_PROFILE_DEVICE_HAT_COUNT = 1


@pytest.fixture
def register_profile_device() -> dill.DeviceSummary:
    """Registers the device in the test profile, and returns its DeviceSummary."""
    axis_map_array = (dill._AxisMap * 8)()
    for i, (linear_i, axis_i) in enumerate(
        [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)]
    ):
        axis_map_array[i] = dill._AxisMap(linear_index=linear_i, axis_index=axis_i)
    dev = dill.DeviceSummary(
        dill._DeviceSummary(
            device_guid=dill.GUID.from_str(
                "97b77b40-07d8-11f0-8028-444553540000"
            ).ctypes,
            vendor_id=0x5678,
            product_id=0xFACE,
            joystick_id=1,
            name=b"pJoy Pro",
            axis_count=_PROFILE_DEVICE_AXIS_COUNT,
            button_count=_PROFILE_DEVICE_BUTTON_COUNT,
            hat_count=_PROFILE_DEVICE_HAT_COUNT,
            axis_map=axis_map_array,
        )
    )

    for mocked_dev in device_initialization._joystick_devices:
        if mocked_dev.device_guid == dev.device_guid:
            yield dev
    else:
        device_initialization._joystick_devices.append(dev)
        yield dev
    for i, mocked_dev in enumerate(device_initialization._joystick_devices):
        if mocked_dev.device_guid == dev.device_guid:
            device_initialization._joystick_devices.pop(i)
            break


def test_get_used_vjoy_inputs_from_profile(
    subtests, xml_dir: pathlib.Path, register_profile_device: dill.DeviceSummary
):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    used_vjoy_inputs = mapper._get_used_vjoy_inputs("Default")

    assert len(used_vjoy_inputs) == 14

    with subtests.test("axis single mapping"):
        assert types.VjoyInput(1, types.InputType.JoystickAxis, 1) in used_vjoy_inputs

    with subtests.test("axis double mapping"):
        assert types.VjoyInput(2, types.InputType.JoystickAxis, 4) in used_vjoy_inputs
        assert types.VjoyInput(2, types.InputType.JoystickAxis, 5) in used_vjoy_inputs
        assert types.VjoyInput(1, types.InputType.JoystickAxis, 4) in used_vjoy_inputs
        assert types.VjoyInput(1, types.InputType.JoystickAxis, 5) in used_vjoy_inputs

    with subtests.test("button single mapping"):
        assert types.VjoyInput(1, types.InputType.JoystickButton, 1) in used_vjoy_inputs

    with subtests.test("button double mapping"):
        assert types.VjoyInput(2, types.InputType.JoystickButton, 5) in used_vjoy_inputs
        assert types.VjoyInput(2, types.InputType.JoystickButton, 6) in used_vjoy_inputs
        assert types.VjoyInput(1, types.InputType.JoystickButton, 5) in used_vjoy_inputs
        assert types.VjoyInput(1, types.InputType.JoystickButton, 6) in used_vjoy_inputs

    with subtests.test("hat mappings"):
        assert types.VjoyInput(1, types.InputType.JoystickHat, 1) in used_vjoy_inputs
        assert types.VjoyInput(1, types.InputType.JoystickHat, 2) in used_vjoy_inputs
        assert types.VjoyInput(2, types.InputType.JoystickHat, 1) in used_vjoy_inputs
        assert types.VjoyInput(2, types.InputType.JoystickHat, 2) in used_vjoy_inputs


def test_get_used_vjoy_inputs_from_empty_mode(
    xml_dir: pathlib.Path, register_profile_device: dill.DeviceSummary
):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    used_vjoy_inputs = mapper._get_used_vjoy_inputs("EmptyMode")

    assert len(used_vjoy_inputs) == 0


def test_get_unused_vjoy_inputs(
    subtests, xml_dir: pathlib.Path, register_profile_device: dill.DeviceSummary
):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    used_vjoy_inputs = mapper._get_used_vjoy_inputs("Default")
    unused_vjoy_axes = list(mapper._iter_unused_vjoy_axes([1], used_vjoy_inputs))
    unused_vjoy_buttons = list(mapper._iter_unused_vjoy_buttons([1], used_vjoy_inputs))
    unused_vjoy_hats = list(mapper._iter_unused_vjoy_hats([1], used_vjoy_inputs))

    # See conftest.py for stub device details.
    # 8 vJoy outputs are used by the profile for vJoy ID 1.
    # The device in the profile doesn't exactly match the unit test stub device but we
    # can still verify the logic below.
    with subtests.test("vJoy 1 unused axes"):
        assert len(unused_vjoy_axes) == 5
        assert types.VjoyInput(1, types.InputType.JoystickAxis, 2) in unused_vjoy_axes
        assert types.VjoyInput(1, types.InputType.JoystickAxis, 3) in unused_vjoy_axes
        assert types.VjoyInput(1, types.InputType.JoystickAxis, 6) in unused_vjoy_axes

    with subtests.test("vJoy 1 some unused buttons"):
        assert len(unused_vjoy_buttons) == 61
        assert (
            types.VjoyInput(1, types.InputType.JoystickButton, 2) in unused_vjoy_buttons
        )
        assert (
            types.VjoyInput(1, types.InputType.JoystickButton, 3) in unused_vjoy_buttons
        )
        assert (
            types.VjoyInput(1, types.InputType.JoystickButton, 4) in unused_vjoy_buttons
        )
        assert (
            types.VjoyInput(1, types.InputType.JoystickButton, 7) in unused_vjoy_buttons
        )
        assert (
            types.VjoyInput(1, types.InputType.JoystickButton, 63)
            in unused_vjoy_buttons
        )

    with subtests.test("vJoy 1 unavailable hats"):
        assert len(unused_vjoy_hats) == 0
        assert (
            types.VjoyInput(1, types.InputType.JoystickHat, 1) not in unused_vjoy_hats
        )
        assert (
            types.VjoyInput(1, types.InputType.JoystickHat, 2) not in unused_vjoy_hats
        )


# Intentionally not using the register_profile_device fixture in this test.
def test_get_used_vjoy_inputs_for_disconnected_device_in_profile(xml_dir: pathlib.Path):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    used_vjoy_inputs = mapper._get_used_vjoy_inputs("Default")

    assert not len(used_vjoy_inputs)


def test_iter_physical_inputs_exclude_used(
    subtests, xml_dir: pathlib.Path, register_profile_device: dill.DeviceSummary
):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    mapper._prepare_profile([register_profile_device], auto_mapper.AutoMapperOptions())
    physical_axes = list(
        mapper._iter_physical_axes(
            [register_profile_device], auto_mapper.AutoMapperOptions()
        )
    )
    physical_buttons = list(
        mapper._iter_physical_buttons(
            [register_profile_device], auto_mapper.AutoMapperOptions()
        )
    )
    physical_hats = list(
        mapper._iter_physical_hats(
            [register_profile_device], auto_mapper.AutoMapperOptions()
        )
    )

    with subtests.test("unused axis"):
        assert len(physical_axes) == 1
        unused_axis = physical_axes[0]
        assert unused_axis.input_type == types.InputType.JoystickAxis
        assert unused_axis.input_id == 4

    with subtests.test("unused button"):
        assert len(physical_buttons) == 1
        unused_button = physical_buttons[0]
        assert unused_button.input_type == types.InputType.JoystickButton
        assert unused_button.input_id == 6

    with subtests.test("no unused hats"):
        assert len(physical_hats) == 0


def test_iter_physical_inputs_overwrite_used(
    subtests, xml_dir: pathlib.Path, register_profile_device: dill.DeviceSummary
):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    mapper._prepare_profile(
        [register_profile_device],
        auto_mapper.AutoMapperOptions(overwrite_used_inputs=True),
    )
    physical_axes = list(
        mapper._iter_physical_axes(
            [register_profile_device],
            auto_mapper.AutoMapperOptions(overwrite_used_inputs=True),
        )
    )
    physical_buttons = list(
        mapper._iter_physical_buttons(
            [register_profile_device],
            auto_mapper.AutoMapperOptions(overwrite_used_inputs=True),
        )
    )
    physical_hats = list(
        mapper._iter_physical_hats(
            [register_profile_device],
            auto_mapper.AutoMapperOptions(overwrite_used_inputs=True),
        )
    )

    assert len(physical_axes) == _PROFILE_DEVICE_AXIS_COUNT

    for axis_i in range(_PROFILE_DEVICE_AXIS_COUNT):
        with subtests.test("axis", axis_i=axis_i):
            axis = physical_axes[axis_i]
            assert axis.input_type == types.InputType.JoystickAxis
            assert axis.input_id == axis_i + 1

    for button_i in range(_PROFILE_DEVICE_BUTTON_COUNT):
        with subtests.test("button", button_i=button_i):
            button = physical_buttons[button_i]
            assert button.input_type == types.InputType.JoystickButton
            assert button.input_id == button_i + 1

    for hat_i in range(_PROFILE_DEVICE_HAT_COUNT):
        with subtests.test("hat", hat_i=hat_i):
            hat = physical_hats[hat_i]
            assert hat.input_type == types.InputType.JoystickHat
            assert hat.input_id == hat_i + 1


def test_iter_physical_inputs_for_new_device(
    subtests, xml_dir: pathlib.Path, register_profile_device: dill.DeviceSummary
):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    physical_axes = list(
        mapper._iter_physical_axes(
            [device_initialization.physical_devices()[0]],
            auto_mapper.AutoMapperOptions(),
        )
    )
    physical_buttons = list(
        mapper._iter_physical_buttons(
            [device_initialization.physical_devices()[0]],
            auto_mapper.AutoMapperOptions(),
        )
    )
    physical_hats = list(
        mapper._iter_physical_hats(
            [device_initialization.physical_devices()[0]],
            auto_mapper.AutoMapperOptions(),
        )
    )

    # See conftest.py for stub device details.
    assert len(physical_axes) == 6
    assert len(physical_buttons) == 64
    assert len(physical_hats) == 2
    for linear_i, axis_i in enumerate([1, 2, 3, 6, 7, 8]):
        with subtests.test("axis", axis_i=axis_i):
            axis = physical_axes[linear_i]
            assert axis.input_type == types.InputType.JoystickAxis
            assert axis.input_id == axis_i

    for button_i in range(64):
        with subtests.test("button", button_i=button_i):
            button = physical_buttons[button_i]
            assert button.input_type == types.InputType.JoystickButton
            assert button.input_id == button_i + 1

    for hat_i in range(2):
        with subtests.test("hat", hat_i=hat_i):
            hat = physical_hats[hat_i]
            assert hat.input_type == types.InputType.JoystickHat
            assert hat.input_id == hat_i + 1


def test_iter_physical_inputs_for_empty_mode(
    subtests, xml_dir: pathlib.Path, register_profile_device: dill.DeviceSummary
):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    mapper._prepare_profile(
        [register_profile_device],
        auto_mapper.AutoMapperOptions(),
    )
    physical_axes = list(
        mapper._iter_physical_axes(
            [register_profile_device],
            auto_mapper.AutoMapperOptions(mode="EmptyMode"),
        )
    )
    physical_buttons = list(
        mapper._iter_physical_buttons(
            [register_profile_device],
            auto_mapper.AutoMapperOptions(mode="EmptyMode"),
        )
    )
    physical_hats = list(
        mapper._iter_physical_hats(
            [register_profile_device],
            auto_mapper.AutoMapperOptions(mode="EmptyMode"),
        )
    )

    assert len(physical_axes) == _PROFILE_DEVICE_AXIS_COUNT

    for axis_i in range(_PROFILE_DEVICE_AXIS_COUNT):
        with subtests.test("axis", axis_i=axis_i):
            axis = physical_axes[axis_i]
            assert axis.input_type == types.InputType.JoystickAxis
            assert axis.input_id == axis_i + 1

    for button_i in range(_PROFILE_DEVICE_BUTTON_COUNT):
        with subtests.test("button", button_i=button_i):
            button = physical_buttons[button_i]
            assert button.input_type == types.InputType.JoystickButton
            assert button.input_id == button_i + 1

    for hat_i in range(_PROFILE_DEVICE_HAT_COUNT):
        with subtests.test("hat", hat_i=hat_i):
            hat = physical_hats[hat_i]
            assert hat.input_type == types.InputType.JoystickHat
            assert hat.input_id == hat_i + 1


def test_auto_map(subtests, xml_dir: pathlib.Path, register_profile_device: dill.DeviceSummary):
    p = profile.Profile()
    p.from_xml(str(xml_dir / "profile_auto_mapper.xml"))
    shared_state.current_profile = p

    mapper = auto_mapper.AutoMapper(p)
    with subtests.test("default profile"):
        assert mapper.generate_mappings(
                [register_profile_device.device_guid],
                [1],
                auto_mapper.AutoMapperOptions(),
        ) == "Created 2 mappings; 9 previous bindings retained."
    with subtests.test("EmptyMode"):
        assert mapper.generate_mappings(
                [register_profile_device.device_guid],
                [1],
                auto_mapper.AutoMapperOptions(mode="EmptyMode"),
        ) == "Created 13 mappings; 0 previous bindings retained."
