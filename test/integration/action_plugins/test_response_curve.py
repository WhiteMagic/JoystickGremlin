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
import uuid

import pytest

from action_plugins import response_curve
from action_plugins import root
from action_plugins import map_to_logical_device
import dill
from gremlin.ui import backend
from gremlin import event_handler
from gremlin import logical_device
from gremlin import plugin_manager
from gremlin import profile
from gremlin import shared_state
from gremlin import spline
from gremlin import types
from gremlin import mode_manager
from test.integration import app_tester

_INPUT_LOGICAL_AXIS_LABEL = "InputAxis1"
_OUTPUT_LOGICAL_AXIS_LABEL = "OutputAxis1"


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
def profile_setup(response_curve_action: response_curve.ResponseCurveData) -> None:
    # This is important for locally-run tests where the last used profile could
    # get loaded, if present in configuration.
    backend.Backend().profile = pr = profile.Profile()
    shared_state.current_profile = pr

    # Create logical device axis for both input and output.
    device = logical_device.LogicalDevice()
    device.reset()
    device.create(types.InputType.JoystickAxis, label=_INPUT_LOGICAL_AXIS_LABEL)
    device.create(types.InputType.JoystickAxis, label=_OUTPUT_LOGICAL_AXIS_LABEL)

    p_manager = plugin_manager.PluginManager()

    # Create logical device mapping action.
    map_to_logical_action: map_to_logical_device.MapToLogicalDeviceData = (
        p_manager.create_instance(
            map_to_logical_device.MapToLogicalDeviceData.name,
            types.InputType.JoystickAxis,
        )
    )
    map_to_logical_action.logical_input_id = device[_OUTPUT_LOGICAL_AXIS_LABEL].id

    # Add actions to profile.
    root_action = p_manager.create_instance(
        root.RootData.name, types.InputType.JoystickAxis
    )
    root_action.insert_action(response_curve_action, "children")
    root_action.insert_action(map_to_logical_action, "children")
    # Add input item and its binding.
    input_item = profile.InputItem(pr.library)
    input_item.device_id = dill.UUID_LogicalDevice
    input_item.input_id = device[_INPUT_LOGICAL_AXIS_LABEL].id
    input_item.input_type = types.InputType.JoystickAxis
    input_item.mode = mode_manager.ModeManager().current.name
    input_item_binding = profile.InputItemBinding(input_item)
    input_item_binding.root_action = root_action
    input_item_binding.behavior = types.InputType.JoystickAxis
    input_item.action_sequences.append(input_item_binding)
    pr.inputs.setdefault(dill.UUID_LogicalDevice, []).append(input_item)


@pytest.fixture
def input_axis_id() -> uuid.UUID:
    return logical_device.LogicalDevice()[_INPUT_LOGICAL_AXIS_LABEL].id


@pytest.fixture
def output_axis_id() -> uuid.UUID:
    return logical_device.LogicalDevice()[_OUTPUT_LOGICAL_AXIS_LABEL].id


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
        axis_input: int,
        input_axis_id: uuid.UUID,
        output_axis_id: uuid.UUID,
    ):
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_id,
                device_guid=dill.UUID_LogicalDevice,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_logical_axis_eventually_equals(
            output_axis_id,
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
        axis_input: int,
        expected_output: int,
        input_axis_id: uuid.UUID,
        output_axis_id: uuid.UUID,
    ):
        response_curve_action.curve = curve = spline.PiecewiseLinear()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.1)
        curve.fit()
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_id,
                device_guid=dill.UUID_LogicalDevice,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_logical_axis_eventually_equals(
            output_axis_id,
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
        axis_input: int,
        expected_output: int,
        input_axis_id: uuid.UUID,
        output_axis_id: uuid.UUID,
    ):
        response_curve_action.curve = curve = spline.PiecewiseLinear()
        curve.is_symmetric = False
        curve.add_control_point(-0.5, -0.1)
        curve.add_control_point(0.5, 0.4)
        curve.add_control_point(0, 0)
        curve.fit()
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_id,
                device_guid=dill.UUID_LogicalDevice,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_logical_axis_eventually_equals(
            output_axis_id,
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
        monkeypatch,
        axis_input: int,
        expected_output: int,
        input_axis_id: uuid.UUID,
        output_axis_id: uuid.UUID,
    ):
        response_curve_action.curve = curve = spline.PiecewiseLinear()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.1)
        curve.fit()
        # The action is shared for all tests; only change deadzone for
        # this function.
        monkeypatch.setattr(response_curve_action, "deadzone", [-0.8, -0.3, 0.1, 0.7])
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_id,
                device_guid=dill.UUID_LogicalDevice,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_logical_axis_eventually_equals(
            output_axis_id,
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
        axis_input: int,
        expected_output: int,
        input_axis_id: uuid.UUID,
        output_axis_id: uuid.UUID,
    ):
        response_curve_action.curve = curve = spline.CubicSpline()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.1)
        # TODO: The following control point should not be needed.
        curve.add_control_point(0.5, 0.1)
        curve.fit()
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_id,
                device_guid=dill.UUID_LogicalDevice,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_logical_axis_eventually_equals(
            output_axis_id,
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
        axis_input: int,
        expected_output: int,
        input_axis_id: uuid.UUID,
        output_axis_id: uuid.UUID,
    ):
        response_curve_action.curve = curve = spline.CubicSpline()
        curve.is_symmetric = False
        curve.add_control_point(-0.5, -0.1)
        # TODO: The following control point should not be needed.
        curve.add_control_point(0.0, 0.0)
        curve.add_control_point(0.5, 0.4)
        curve.fit()
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_id,
                device_guid=dill.UUID_LogicalDevice,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_logical_axis_eventually_equals(
            output_axis_id,
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
        axis_input: int,
        expected_output: int,
        input_axis_id: uuid.UUID,
        output_axis_id: uuid.UUID,
    ):
        response_curve_action.curve = curve = spline.CubicBezierSpline()
        curve.is_symmetric = True
        curve.add_control_point(-0.5, -0.2)
        curve.add_control_point(0.0, 0.0)
        curve.add_control_point(0.5, 0.2)
        curve.fit()
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_id,
                device_guid=dill.UUID_LogicalDevice,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_logical_axis_eventually_equals(
            output_axis_id,
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
        axis_input: int,
        expected_output: int,
        input_axis_id: uuid.UUID,
        output_axis_id: uuid.UUID,
    ):
        response_curve_action.curve = curve = spline.CubicBezierSpline()
        curve.is_symmetric = False
        curve.add_control_point(-0.5, -0.2)
        curve.add_control_point(0.0, 0.0)
        curve.add_control_point(0.5, 0.4)
        curve.fit()
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_id,
                device_guid=dill.UUID_LogicalDevice,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_logical_axis_eventually_equals(
            output_axis_id,
            expected_output,
        )
