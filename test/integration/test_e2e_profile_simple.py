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

from collections.abc import Iterator
import contextlib
import itertools
import sys
import threading
from unittest import mock

sys.path.append(".")

import pytest

from action_plugins import map_to_vjoy
import dill
from gremlin import types
from gremlin import util
from test.integration import app_tester
from vjoy import vjoy
from vjoy import vjoy_interface


@pytest.fixture
def patched_time() -> Iterator[threading.Semaphore]:
    """Patches the time module in map_to_vjoy.

    The sleep() function is replaced with a mock that we can
    step through at will by calling release() on the yielded semaphore.
    The time() function is replaced by a counter that increments on each call.
    """
    time_stepper = threading.Semaphore(value=0)
    time_counter = itertools.count(
        step=map_to_vjoy.MapToVjoyFunctor.THREAD_SLEEP_DURATION_S
    )
    # Don't mock time() and sleep() globally; instead, mock out the "time" name
    # in the map_to_vjoy module only.
    with mock.patch.object(map_to_vjoy, "time", autospec=True) as mock_time:
        mock_time.sleep.side_effect = lambda _: time_stepper.acquire(timeout=2)
        mock_time.time.side_effect = lambda: next(time_counter)
        yield time_stepper


@pytest.fixture(scope="module")
def profile_name() -> str:
    return "e2e_profile_simple.xml"


class TestSimpleProfile:
    """Tests for a simple profile."""

    @pytest.mark.parametrize(
        "di_input",
        [
            32767,
            32766,
            32765,
            -2,
            -1,
            0,
            1,
            2,
            -32765,
            -32766,
            -32768,
        ],
    )
    def test_axis_sequential(
        self,
        subtests,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: int,
    ):
        """Applies groups of sequential inputs."""
        self._test_axis(
            subtests,
            tester,
            vjoy_control_device,
            vjoy_di_device,
            di_input,
        )

    @pytest.mark.parametrize(
        "di_input",
        [
            32767,
            -2,
            32766,
            -1,
            32765,
            22937,
            16384,
            6554,
            0,
            -32766,
            1,
            -32767,
            2,
            -6554,
            -16384,
            -22940,
            0,
            -32768,
        ],
    )
    def test_axis_large_steps(
        self,
        subtests,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: int,
    ):
        """Applies fixed sequence of inputs with large steps."""
        self._test_axis(
            subtests,
            tester,
            vjoy_control_device,
            vjoy_di_device,
            di_input,
        )

    def _test_axis(
        self,
        subtests,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: int,
    ):
        input_axis_id = 1
        output_axis_id = 3
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
                vjoy_di_device.device_guid.uuid, output_axis_id, calibrated_value
            )
        tester.assert_axis_eventually_equals(
            vjoy_di_device.device_guid, output_axis_id, di_input
        )

    def test_axis_relative(
        self,
        subtests,
        patched_time: threading.Semaphore,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
    ):
        """Verifies relative axis changes over time."""
        input_axis_id = 2
        output_axis_id = 4
        sleep_calls_per_subtest = 10
        # The thread updating output axis values takes one step before we can pause it with
        # our semaphore, hence the +1 in the values below.
        for di_input, steps in [
            (tester.AXIS_MAX_INT, [11, 21, 31]),
            (-tester.AXIS_MAX_INT, [21, 11, 1, -9, -19, -29]),
        ]:
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
            for step in steps:
                absolute_change = (
                    step
                    * map_to_vjoy.MapToVjoyFunctor.SCALING_MULTIPLIER
                    * map_to_vjoy.MapToVjoyData.DEFAULT_SCALING
                )
                with subtests.test(
                    "output",
                    di_input=di_input,
                    step=step,
                    absolute_change=absolute_change,
                ):
                    patched_time.release(sleep_calls_per_subtest)
                    tester.assert_cached_axis_eventually_equals(
                        vjoy_di_device.device_guid.uuid,
                        output_axis_id,
                        absolute_change,
                    )
                    tester.assert_axis_eventually_equals(
                        vjoy_di_device.device_guid,
                        output_axis_id,
                        absolute_change * tester.AXIS_MAX_INT,
                    )

    @pytest.mark.parametrize(
        ("di_input", "vjoy_output", "cached_value"),
        [(False, 0, False), (True, 1, True), (False, 0, False), (True, 1, True)],
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
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
        di_input: types.HatDirection,
        vjoy_output: int,
        cached_value: types.HatDirection | None,
    ):
        input_hat_id = 1
        output_hat_id = 3
        vjoy_control_device.hat(index=input_hat_id).direction = di_input
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
            (678, -1, types.HatDirection.Center),
            (1234, -1, types.HatDirection.Center),
            (12340, -1, types.HatDirection.Center),
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
