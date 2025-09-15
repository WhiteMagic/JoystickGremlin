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
"""
Integration tests for user scripts - device I/O only.
"""

import pytest

import dill
from gremlin import profile, types, util
from test.integration import app_tester
from vjoy import vjoy


@pytest.fixture(scope="module")
def profile_name() -> str:
    return "e2e_user_script.xml"


@pytest.fixture(scope="module")
def edited_profile(
    profile_from_file: profile.Profile,
    vjoy_di_device: dill.DeviceSummary,
    vjoy_control_device,
) -> profile.Profile:
    """Replaces the input device loaded from file with the vJoy device."""
    script = profile_from_file.scripts.scripts[0]
    physical_axis_var = script.get_variable("A physical axis input variable")
    physical_axis_var.value = (
        vjoy_di_device.device_guid.uuid,
        types.InputType.JoystickAxis,
        1,
    )
    physical_button_var = script.get_variable("A physical button input variable")
    physical_button_var.value = (
        vjoy_di_device.device_guid.uuid,
        types.InputType.JoystickButton,
        1,
    )
    physical_hat_var = script.get_variable("A physical hat input variable")
    physical_hat_var.value = (
        vjoy_di_device.device_guid.uuid,
        types.InputType.JoystickHat,
        1,
    )
    return profile_from_file


class TestUserScript:
    """Tests for user scripts, device I/O only."""

    @pytest.mark.parametrize(
        ("di_input", "vjoy_output"),
        [
            (32767, 16383),
            (16384, 8192),
            (8192, 4096),
            (-2, -1),
            (0, 0),
            (2, 1),
            (8192, 4096),
            (-16384, -8192),
            (-32768, -16384),
        ],
    )
    def test_axis_sequential(
        self,
        subtests,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: int,
        vjoy_output: int,
    ):
        input_axis_id = 1
        output_axis_id = 2
        calibrated_value = util.with_default_center_calibration(di_input)
        vjoy_control_device.axis(linear_index=input_axis_id).set_absolute_value(
            calibrated_value
        )
        with subtests.test("input readback"):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, input_axis_id, di_input
            )
        with subtests.test("input axis cache"):
            tester.assert_cached_axis_eventually_equals(
                vjoy_di_device.device_guid.uuid, input_axis_id, calibrated_value
            )
        with subtests.test("output axis cache"):
            tester.assert_cached_axis_eventually_equals(
                vjoy_di_device.device_guid.uuid, output_axis_id, util.with_default_center_calibration(vjoy_output)
            )
        tester.assert_axis_eventually_equals(
            vjoy_di_device.device_guid, output_axis_id, vjoy_output
        )

    @pytest.mark.parametrize(
        ("di_input", "cached_input", "cached_output", "vjoy_output"),
        [
            # Example script XORs input value with True.
            (True, True, False, 0),
            (False, False, True, 1),
            (True, True, False, 0),
            (False, False, True, 1),
        ],
    )
    def test_button(
        self,
        subtests,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: bool,
        cached_input: bool,
        cached_output: bool,
        vjoy_output: int,
    ):
        input_button_id = 1
        output_button_id = 2
        vjoy_control_device.button(index=input_button_id).is_pressed = di_input
        with subtests.test("input readback"):
            tester.assert_button_eventually_equals(
                vjoy_di_device.device_guid, input_button_id, di_input
            )
        with subtests.test("input button cache"):
            tester.assert_cached_button_eventually_equals(
                vjoy_di_device.device_guid.uuid, input_button_id, cached_input
            )
        with subtests.test("output button cache"):
            tester.assert_cached_button_eventually_equals(
                vjoy_di_device.device_guid.uuid, output_button_id, cached_output
            )
        tester.assert_button_eventually_equals(
            vjoy_di_device.device_guid, output_button_id, vjoy_output
        )

    @pytest.mark.parametrize(
        ("di_input", "vjoy_output", "cached_value"),
        [
            (types.HatDirection.Center, -1, types.HatDirection.Center),
            (types.HatDirection.North, 0, types.HatDirection.North),
            (types.HatDirection.NorthEast, 4500, types.HatDirection.NorthEast),
            (types.HatDirection.East, 9000, types.HatDirection.East),
            (types.HatDirection.SouthEast, 13500, types.HatDirection.SouthEast),
            (types.HatDirection.South, 18000, types.HatDirection.South),
            (types.HatDirection.SouthWest, 22500, types.HatDirection.SouthWest),
            (types.HatDirection.West, 27000, types.HatDirection.West),
            (types.HatDirection.NorthWest, 31500, types.HatDirection.NorthWest),
            (types.HatDirection.North, 0, types.HatDirection.North),
        ],
    )
    def test_hat(
        self,
        subtests,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: types.HatDirection,
        vjoy_output: int,
        cached_value: types.HatDirection | None,
    ):
        input_hat_id = 1
        output_hat_id = 2
        vjoy_control_device.hat(index=input_hat_id).direction = di_input
        with subtests.test("input readback"):
            tester.assert_hat_eventually_equals(
                vjoy_di_device.device_guid, input_hat_id, vjoy_output
            )
        with subtests.test("input hat cache"):
            tester.assert_cached_hat_eventually_equals(
                vjoy_di_device.device_guid.uuid, input_hat_id, cached_value
            )
        with subtests.test("output hat cache"):
            tester.assert_cached_hat_eventually_equals(
                vjoy_di_device.device_guid.uuid, output_hat_id, cached_value
            )
        tester.assert_hat_eventually_equals(
            vjoy_di_device.device_guid, output_hat_id, vjoy_output
        )
