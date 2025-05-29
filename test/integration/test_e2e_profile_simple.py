# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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
Integration tests with a profile that does simple input forwarding.
"""

import sys

sys.path.append(".")

import pytest

import dill
from gremlin import types
from test.integration import app_tester
from vjoy import vjoy
from vjoy import vjoy_interface


@pytest.fixture(scope="module")
def profile_name() -> str:
    return "e2e_profile_simple.xml"


class TestSimpleProfile:
    """Tests for a simple profile."""

    @pytest.mark.parametrize(
        "di_input, vjoy_input, cached_input, cached_output, di_output",
        [
            (22937/32767, 22936, 22934/32767, 22931/32767, 22930),
            (16384/32767, 16380, 16381/32767, 16377/32767, 16378),
            (6554/32767, 6549, 6549/32767, 6545/32767, 6545),
            (0/32767, 0, -2/32767, -6/32767, -6),
            (32767/32767, 32767, 32764/32767, 32763/32767, 32763),
            (-6554/32767, -6554, -6574/32767, -6593/32767, -6576),
            (-16384/32767, -16384, -16431/32767, -16479/32767, -16434),
            (-22940/32767, -22940, -23005/32767, -23069/32767, -23004),
            (-32767/32767, -32767, -32767/32767, -32767/32767, -32767),
        ],
    )
    def test_axis(
        self,
        subtests,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: float,
        vjoy_input: int,
        cached_input: float,
        cached_output: float,
        di_output: int,
    ):
        input_axis_id = 1
        output_axis_id = 3
        vjoy_control_device.axis(linear_index=input_axis_id).set_absolute_value(
            di_input
        )
        with subtests.test("input readback"):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, input_axis_id, vjoy_input
            )
        with subtests.test("input axis cache"):
            tester.assert_cached_axis_eventually_equals(
                vjoy_di_device.device_guid.uuid, input_axis_id, cached_input
            )
        with subtests.test("output axis cache"):
            tester.assert_cached_axis_eventually_equals(
                vjoy_di_device.device_guid.uuid, output_axis_id, cached_output
            )
        tester.assert_axis_eventually_equals(
            vjoy_di_device.device_guid, output_axis_id, di_output
        )

    @pytest.mark.parametrize(
        ("di_input", "vjoy_output", "cached_value"),
        [(False, 0, None), (True, 1, True), (False, 0, False), (True, 1, True)],
    )
    def test_button(
        self,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: bool,
        vjoy_output: int,
        cached_value: bool | None,
    ):
        input_button_id = 1
        output_button_id = 3
        vjoy_control_device.button(index=input_button_id).is_pressed = di_input
        tester.assert_button_eventually_equals(
            vjoy_di_device.device_guid, input_button_id, vjoy_output
        )
        tester.assert_cached_button_eventually_equals(
            vjoy_di_device.device_guid.uuid, input_button_id, cached_value
        )
        tester.assert_cached_button_eventually_equals(
            vjoy_di_device.device_guid.uuid, output_button_id, cached_value
        )
        tester.assert_button_eventually_equals(
            vjoy_di_device.device_guid, output_button_id, vjoy_output
        )

    @pytest.mark.parametrize(
        ("di_input", "vjoy_output", "cached_value"),
        [
            (types.HatDirection.Center, -1, None),
            (types.HatDirection.North, 0, types.HatDirection.North.value),
            (types.HatDirection.NorthEast, 4500, types.HatDirection.NorthEast.value),
            (types.HatDirection.East, 9000, types.HatDirection.East.value),
            (types.HatDirection.SouthEast, 13500, types.HatDirection.SouthEast.value),
            (types.HatDirection.South, 18000, types.HatDirection.South.value),
            (types.HatDirection.SouthWest, 22500, types.HatDirection.SouthWest.value),
            (types.HatDirection.West, 27000, types.HatDirection.West.value),
            (types.HatDirection.NorthWest, 31500, types.HatDirection.NorthWest.value),
            (types.HatDirection.North, 0, types.HatDirection.North.value),
        ],
    )
    def test_hat(
        self,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: types.HatDirection,
        vjoy_output: int,
        cached_value: types.HatDirection | None,
    ):
        input_hat_id = 1
        output_hat_id = 3
        vjoy_control_device.hat(index=input_hat_id).direction = di_input.value
        tester.assert_hat_eventually_equals(
            vjoy_di_device.device_guid, input_hat_id, vjoy_output
        )
        tester.assert_cached_hat_eventually_equals(
            vjoy_di_device.device_guid.uuid, input_hat_id, cached_value
        )
        tester.assert_cached_hat_eventually_equals(
            vjoy_di_device.device_guid.uuid, output_hat_id, cached_value
        )
        tester.assert_hat_eventually_equals(
            vjoy_di_device.device_guid, output_hat_id, vjoy_output
        )

    @pytest.mark.parametrize(
        ("di_input", "vjoy_output", "cached_value"),
        [
            (678, -1, types.HatDirection.Center.value),
            (1234, -1, types.HatDirection.Center.value),
            (12340, -1, types.HatDirection.Center.value),
        ],
    )
    def test_hat_analog_values(
        self,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: int,
        vjoy_output: int,
        cached_value: types.HatDirection | None,
    ):
        """Tests the scenario where the input device has non-enum hat values."""
        input_hat_id = 1
        output_hat_id = 3
        if (
            vjoy_control_device.hat(index=input_hat_id).hat_type
            != vjoy.HatType.Continuous
        ):
            pytest.skip(
                "Skipping analog hat values test - vJoy device needs to be configured as such."
            )
        # Use the vJoy device directly to set a non-enum continuous value.
        vjoy_interface.VJoyInterface.SetContPov(
            di_input, vjoy_control_device.vjoy_id, input_hat_id
        )
        tester.assert_hat_eventually_equals(
            vjoy_di_device.device_guid, input_hat_id, di_input
        )
        tester.assert_cached_hat_eventually_equals(
            vjoy_di_device.device_guid.uuid, input_hat_id, cached_value
        )
        tester.assert_cached_hat_eventually_equals(
            vjoy_di_device.device_guid.uuid, output_hat_id, cached_value
        )
        tester.assert_hat_eventually_equals(
            vjoy_di_device.device_guid, output_hat_id, vjoy_output
        )
