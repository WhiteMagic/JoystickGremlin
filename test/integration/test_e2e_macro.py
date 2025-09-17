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
Integration tests with a profile with macros that have vJoy outputs.
"""

import sys

sys.path.append(".")

import pytest

import dill
from test.integration import app_tester
from vjoy import vjoy


@pytest.fixture(scope="module")
def profile_name() -> str:
    """Returns the name of the profile to be used for the macro test.

    The profile maps button 1 press to vJoy actions of each type: button press,
    hat direction set, absolute axis set, and relative axis change.
    """
    return "e2e_macros.xml"


class TestMacro:
    """Tests the vJoy actions of macro.py."""

    def test_macro_sequence(
        self,
        subtests,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
    ):
        """Verifies multiple macro executions triggered by a single button press."""
        input_button_id = 1
        vjoy_output = 1
        cached_value = True
        vjoy_control_device.button(index=input_button_id).is_pressed = True
        tester.assert_button_eventually_equals(
            vjoy_di_device.device_guid, input_button_id, vjoy_output
        )
        tester.assert_cached_button_eventually_equals(
            vjoy_di_device.device_guid.uuid, input_button_id, cached_value
        )

        def assert_fixed_outputs(step: int):
            with subtests.test("hat northeast", step=step):
                tester.assert_hat_eventually_equals(vjoy_di_device.device_guid, 1, 4500)
            with subtests.test("hat west", step=step):
                tester.assert_hat_eventually_equals(
                    vjoy_di_device.device_guid, 2, 27000
                )
            with subtests.test("button", step=step):
                tester.assert_button_eventually_equals(vjoy_di_device.device_guid, 3, 1)
            with subtests.test("axis absolute positive", step=step):
                tester.assert_axis_eventually_equals(
                    vjoy_di_device.device_guid, 2, tester.AXIS_MAX_INT * 0.7
                )
            with subtests.test("axis absolute negative", step=step):
                tester.assert_axis_eventually_equals(
                    vjoy_di_device.device_guid, 3, tester.AXIS_MAX_INT * -0.5
                )

        assert_fixed_outputs(step=1)
        with subtests.test("axis relative positive", step=1):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, 5, tester.AXIS_MAX_INT * 0.2
            )
        with subtests.test("axis relative negative", step=1):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, 6, tester.AXIS_MAX_INT * -0.1
            )

        vjoy_control_device.button(index=input_button_id).is_pressed = False
        assert_fixed_outputs(step=2)
        with subtests.test("axis relative positive", step=2):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, 5, tester.AXIS_MAX_INT * 0.2
            )
        with subtests.test("axis relative negative", step=2):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, 6, tester.AXIS_MAX_INT * -0.1
            )

        vjoy_control_device.button(index=input_button_id).is_pressed = True
        assert_fixed_outputs(step=3)
        with subtests.test("axis relative positive", step=3):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, 5, tester.AXIS_MAX_INT * 0.2 * 2
            )
        with subtests.test("axis relative negative", step=3):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, 6, tester.AXIS_MAX_INT * -0.1 * 2
            )

        vjoy_control_device.button(index=input_button_id).is_pressed = False
        assert_fixed_outputs(step=4)
        vjoy_control_device.button(index=input_button_id).is_pressed = True
        assert_fixed_outputs(step=5)
        with subtests.test("axis relative positive", step=5):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, 5, tester.AXIS_MAX_INT * 0.2 * 3
            )
        with subtests.test("axis relative negative", step=5):
            tester.assert_axis_eventually_equals(
                vjoy_di_device.device_guid, 6, tester.AXIS_MAX_INT * -0.1 * 3
            )
