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
Integration test for response curve action using logical output devices.
"""
import pytest

from action_plugins import response_curve
from action_plugins import root
from action_plugins import map_to_logical_device
import dill
from gremlin import logical_device
from gremlin import plugin_manager
from gremlin import profile
from gremlin import spline
from gremlin import types
from gremlin import mode_manager
from test.integration import app_tester
from test.integration.action_plugins.conftest import (
    LogicalActionCallableT,
    LogicalIdentifierCallableT,
)

_LOGICAL_INPUT_AXIS_LABEL = "InputAxis1"
_LOGICAL_OUTPUT_AXIS_LABEL = "OutputAxis1"


@pytest.fixture(scope="module")
def response_curve_action() -> response_curve.ResponseCurveData:
    """Create response curve action instance for testing.
    
    Response curves should be modifiable while Gremlin is running, so making
    this fixture "module" scoped indirectly tests that feature as well.

    Returns:
        Response curve action instance for this test session.
    """
    p_manager = plugin_manager.PluginManager()
    return p_manager.create_instance(
        response_curve.ResponseCurveData.name,
        types.InputType.JoystickAxis
    )


@pytest.fixture(scope="module")
def profile_setup(
    profile_for_test: profile.Profile,
    response_curve_action: response_curve.ResponseCurveData,
    logical_device_for_test: logical_device.LogicalDevice,
):
    """Sets up the profile for testing response curve action via intermediate outputs."""
    # Create logical device action to map response curve to an output logical axis.
    p_manager = plugin_manager.PluginManager()
    map_to_logical_action: map_to_logical_device.MapToLogicalDeviceData = (
        p_manager.create_instance(
            map_to_logical_device.MapToLogicalDeviceData.name,
            types.InputType.JoystickAxis,
        )
    )

    # Create logical device action to map response curve to an output logical axis.
    logical_output_axis = logical_device_for_test.create(
        types.InputType.JoystickAxis, label=_LOGICAL_OUTPUT_AXIS_LABEL
    )
    map_to_logical_action.logical_input_id = logical_output_axis.id

    # Add actions to profile.
    root_action = p_manager.create_instance(
        root.RootData.name, types.InputType.JoystickAxis
    )
    root_action.insert_action(response_curve_action, "children")
    root_action.insert_action(map_to_logical_action, "children")
    # Create the input axis.
    logical_axis_1 = logical_device_for_test.create(
        types.InputType.JoystickAxis, label=_LOGICAL_INPUT_AXIS_LABEL
    )
    # Add input item and its binding.
    input_item = profile.InputItem(profile_for_test.library)
    input_item.device_id = dill.UUID_LogicalDevice
    input_item.input_id = logical_axis_1.id
    input_item.input_type = types.InputType.JoystickAxis
    input_item.mode = mode_manager.ModeManager().current.name
    input_item_binding = profile.InputItemBinding(input_item)
    input_item_binding.root_action = root_action
    input_item_binding.behavior = types.InputType.JoystickAxis
    input_item.action_sequences.append(input_item_binding)
    profile_for_test.inputs.setdefault(dill.UUID_LogicalDevice, []).append(input_item)


class TestResponseCurve:
    """Tests for response curve action."""

    @pytest.mark.parametrize(
        "axis_input",
        [
            1,
            0.33,
            0,
            -0.22,
            -1,
        ],
    )
    def test_default_curve(
        self,
        tester: app_tester.GremlinAppTester,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
    ):
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            axis_input,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1),
            (0.75, 0.55),
            (0.5, 0.1),
            (0.25, 0.05),
            (0, 0),
            (-0.25, -0.05),
            (-0.5, -0.1),
            (-0.75, -0.55),
            (-1, -1),
        ],
    )
    def test_piecewise_linear_symmetric(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.PiecewiseLinear()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.1)
        curve.fit()
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1),
            (0.75, 0.7),
            (0.5, 0.4),
            (0.25, 0.2),
            (0, 0),
            (-0.25, -0.05),
            (-0.5, -0.1),
            (-0.75, -0.55),
            (-1, -1),
        ],
    )
    def test_piecewise_linear_asymmetric(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.PiecewiseLinear()
        curve.is_symmetric = False
        curve.add_control_point(-0.5, -0.1)
        curve.add_control_point(0.5, 0.4)
        curve.add_control_point(0, 0)
        curve.fit()
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1.0),
            (0.71, 1.0),
            (0.7, 1.0),
            (0.69, 0.97),
            (0.5, 0.4),
            (0.25, 0.05),
            (0.11, 0.0033),
            (0.1, 0.0),
            (0.09, 0.0),
            (0, 0),
            (-0.25, 0.0),
            (-0.29, 0.0),
            (-0.3, 0.0),
            (-0.31, -0.004),
            (-0.5, -0.08),
            (-0.79, -0.964),
            (-0.8, -1.0),
            (-0.81, -1.0),
            (-1, -1),
        ],
    )
    def test_piecewise_linear_with_deadzones(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        monkeypatch,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.PiecewiseLinear()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.1)
        curve.fit()
        # The action is shared for all tests; only change deadzone for
        # this function.
        monkeypatch.setattr(response_curve_action, "deadzone", [-0.8, -0.3, 0.1, 0.7])
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1),
            (0.75, 0.475),
            (0.5, 0.1),
            (0.25, -0.025),
            (0, 0),
            (-0.25, 0.025),
            (-0.5, -0.1),
            (-0.75, -0.475),
            (-1, -1),
        ],
    )
    def test_cubic_spline_symmetric(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.CubicSpline()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.1)
        curve.fit()
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1),
            (0.75, 0.6933),
            (0.5, 0.4),
            (0.25, 0.1451),
            (0, 0),
            (-0.25, -0.0112),
            (-0.5, -0.1),
            (-0.75, -0.463),
            (-1, -1),
        ],
    )
    def test_cubic_spline_asymmetric(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.CubicSpline()
        curve.is_symmetric = False
        curve.add_control_point(-0.5, -0.1)
        curve.add_control_point(0.0, 0.0)
        curve.add_control_point(0.5, 0.4)
        curve.fit()
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1.0),
            (0.75, 0.58125),
            (0.5, 0.2),
            (0.25, 0.1),
            (0, 0.0),
            (-0.25, -0.1),
            (-0.5, -0.2),
            (-0.75, -0.58125),
            (-1, -1.0),
        ],
    )
    def test_cubic_bezier_spline_symmetric(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.CubicBezierSpline()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.2)
        curve.fit()
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1.0),
            (0.75, 0.68125),
            (0.5, 0.4),
            (0.25, 0.2),
            (0, 0.0),
            (-0.25, -0.1),
            (-0.5, -0.2),
            (-0.75, -0.58125),
            (-1, -1.0),
        ],
    )
    def test_cubic_bezier_spline_asymmetric(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.CubicBezierSpline()
        curve.is_symmetric = False
        curve.add_control_point(-0.5, -0.2)
        curve.add_control_point(0.0, 0.0)
        curve.add_control_point(0.5, 0.4)
        curve.fit()
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1.0),
            (0.75, 0.25),
            (0.5, -0.5),
            (0.25, -0.25),
            (0, 0.0),
            (-0.25, 0.25),
            (-0.5, 0.5),
            (-0.75, -0.25),
            (-1, -1.0),
        ],
    )
    def test_control_point_change_symmetric(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.PiecewiseLinear()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.2)
        curve.fit()
        curve.set_control_point(-0.5, 0.5, 1)
        curve.fit()
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    @pytest.mark.parametrize(
        "axis_input, expected_output",
        [
            (1, 1.0),
            (0.75, 0.91667),
            (0.5, 0.83333),
            (0.25, 0.75),
            (0, 0.66667),
            (-0.25, 0.58333),
            (-0.5, 0.5),
            (-0.75, -0.25),
            (-1, -1.0),
        ],
    )
    def test_control_point_change_asymmetric(
        self,
        tester: app_tester.GremlinAppTester,
        response_curve_action: response_curve.ResponseCurveData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        axis_input: int,
        expected_output: int,
    ):
        response_curve_action.curve = curve = spline.PiecewiseLinear()
        curve.is_symmetric = False
        curve.add_control_point(-0.5, -0.2)
        curve.fit()
        curve.set_control_point(-0.5, 0.5, 1)
        curve.fit()
        tester.inject_logical_input(
            get_logical_input_action(_LOGICAL_INPUT_AXIS_LABEL), axis_input
        )
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )
