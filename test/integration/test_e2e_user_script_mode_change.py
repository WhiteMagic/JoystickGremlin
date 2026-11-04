# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import time

import pytest

import dill
from gremlin import (
    mode_manager,
    profile,
    types,
    util,
)
from test.integration import app_tester
from vjoy import vjoy


@pytest.fixture(scope="module")
def profile_name() -> str:
    return "e2e_user_script_mode_change.xml"


@pytest.fixture(scope="module")
def edited_profile(
    edited_profile: profile.Profile,
    vjoy_di_device: dill.DeviceSummary,
) -> profile.Profile:
    """Binds the script to the vJoy device on top of the common device swap."""
    script = edited_profile.scripts.scripts[0]
    script.get_variable("A physical axis input variable").value = (
        vjoy_di_device.device_guid.uuid,
        types.InputType.JoystickAxis,
        1,
    )
    return edited_profile


class TestUserScriptModeChange:
    """Tests for mode changes with script and action sharing an axis."""

    def test_mode_change_resets_action_and_keeps_script_working(
        self,
        tester: app_tester.GremlinAppTester,
        vjoy_control_device: vjoy.VJoy,
        vjoy_di_device: dill.DeviceSummary,
    ) -> None:
        input_axis_id = 1
        script_output_axis_id = 2
        action_output_axis_id = 3
        device_guid = vjoy_di_device.device_guid
        manager = mode_manager.ModeManager()

        # Start from the low end, moving the input from center to guarantee events.
        vjoy_control_device.axis(linear_index=action_output_axis_id).value = -1.0
        vjoy_control_device.axis(linear_index=input_axis_id).value = 0.0
        tester.assert_cached_axis_eventually_equals(
            device_guid.uuid, input_axis_id, 0.0
        )

        vjoy_control_device.axis(
            linear_index=input_axis_id
        ).value = util.with_default_center_calibration(tester.AXIS_MAX_INT)
        tester.assert_axis_eventually_equals(device_guid, script_output_axis_id, 16383)
        time.sleep(0.1)

        manager.switch_to(mode_manager.Mode("Other", "Default"), refresh_axes=False)
        # Lets the relative motion thread see the reset.
        time.sleep(0.05)
        stopped_value = dill.DILL.get_axis(device_guid, action_output_axis_id)
        time.sleep(0.1)

        tester.assert_axis_eventually_equals(
            device_guid, action_output_axis_id, stopped_value
        )

        manager.switch_to(mode_manager.Mode("Default", "Other"), refresh_axes=False)
        vjoy_control_device.axis(
            linear_index=input_axis_id
        ).value = util.with_default_center_calibration(16384)

        tester.assert_axis_eventually_equals(device_guid, script_output_axis_id, 8192)
