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

from action_plugins import merge_axis
from action_plugins import root
from action_plugins import map_to_logical_device
import dill
from gremlin import logical_device
from gremlin import plugin_manager
from gremlin import profile
from gremlin import types
from gremlin import mode_manager
from test.integration import app_tester
from test.integration.action_plugins.conftest import LogicalActionCallableT, LogicalIdentifierCallableT

_LOGICAL_INPUT_AXIS1_LABEL = "InputAxis1"
_LOGICAL_INPUT_AXIS2_LABEL = "InputAxis2"
_LOGICAL_OUTPUT_AXIS_LABEL = "OutputAxis"


@pytest.fixture(scope="module")
def merge_axis_action() -> merge_axis.MergeAxisData:
    """Create merge axis action instance for testing.
    
    Merge axis should be modifiable while Gremlin is running, so making
    this fixture "module" scoped indirectly tests that feature as well.

    Returns:
        Merge axis action instance for this test session.
    """
    p_manager = plugin_manager.PluginManager()
    return p_manager.create_instance(
        merge_axis.MergeAxisData.name,
        types.InputType.JoystickAxis
    )


@pytest.fixture(scope="module")
def profile_setup(profile_for_test: profile.Profile,
                  merge_axis_action: merge_axis.MergeAxisData,
                  logical_device_for_test: logical_device.LogicalDevice,
                  get_logical_input_identifier: LogicalIdentifierCallableT,
                  ):
    """Sets up the profile for testing merge axis action via intermediate outputs."""
    # Configure the merge axis action.
    logical_input_axis_1 = logical_device_for_test.create(
                types.InputType.JoystickAxis, label=_LOGICAL_INPUT_AXIS1_LABEL
            )
    merge_axis_action.axis_in1 = get_logical_input_identifier(_LOGICAL_INPUT_AXIS1_LABEL)
    logical_input_axis_2 = logical_device_for_test.create(
                types.InputType.JoystickAxis, label=_LOGICAL_INPUT_AXIS2_LABEL
            )
    merge_axis_action.axis_in2 = get_logical_input_identifier(_LOGICAL_INPUT_AXIS2_LABEL)

    # Create logical device action to map merged axes to an output logical axis.
    p_manager = plugin_manager.PluginManager()
    map_to_logical_action: map_to_logical_device.MapToLogicalDeviceData = (
        p_manager.create_instance(
            map_to_logical_device.MapToLogicalDeviceData.name,
            types.InputType.JoystickAxis,
        )
    )
    logical_output_axis = logical_device_for_test.create(
                types.InputType.JoystickAxis, label=_LOGICAL_OUTPUT_AXIS_LABEL
            )
    map_to_logical_action.logical_input_id = logical_output_axis.id

    # Add actions to profile.
    root_action = p_manager.create_instance(
        root.RootData.name, types.InputType.JoystickAxis
    )
    root_action.insert_action(merge_axis_action, "children")
    # Unlike most other actions, for merge axis the "output" action is a child
    # of the merge action and not the root action.
    merge_axis_action.insert_action(map_to_logical_action, "children")
    for input_id in [logical_input_axis_1.id, logical_input_axis_2.id]:
        # Add input item and its binding.
        input_item = profile.InputItem(profile_for_test.library)
        input_item.device_id = dill.UUID_LogicalDevice
        input_item.input_id = input_id
        input_item.input_type = types.InputType.JoystickAxis
        input_item.mode = mode_manager.ModeManager().current.name
        input_item_binding = profile.InputItemBinding(input_item)
        input_item_binding.root_action = root_action
        input_item_binding.behavior = types.InputType.JoystickAxis
        input_item.action_sequences.append(input_item_binding)
        profile_for_test.inputs.setdefault(dill.UUID_LogicalDevice, []).append(input_item)


class TestMergeAxis:
    """Tests for merge axis action."""

    @pytest.mark.parametrize(
        "value_input1,value_input2,expected_output",
        [
            (0, 0, 0),
            (1, 1, 1),
            (0.33, 0.33, 0.33),
            (0, 0, 0),
            (-0.22, -0.22, -0.22),
            (-1, -1, -1),
            (1, -1, 0),
            (-1, 1, 0),
            (1, 0, 0.5),
            (0, 1, 0.5),
        ],
    )
    def test_default_merge_and_input_ordering(
        self,
        tester: app_tester.GremlinAppTester,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        subtests,
        value_input1: int,
        value_input2: int,
        expected_output: int,
    ):
        with subtests.test("first_input_before_second"):
            tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS1_LABEL), value_input1)
            tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS2_LABEL), value_input2)
            tester.assert_logical_axis_eventually_equals(
                logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
                expected_output,
            )
        with subtests.test("second_input_before_first"):
            tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS2_LABEL), value_input2)
            tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS1_LABEL), value_input1)
            tester.assert_logical_axis_eventually_equals(
                logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
                expected_output,
            )
    
    @pytest.mark.parametrize(
        "value_input1,value_input2,expected_output",
        [
            (0, 0, 0),
            (1, 1, 1),
            (0.33, 0.33, 0.33),
            (0, 0, 0),
            (-0.22, -0.22, -0.22),
            (-1, -1, -1),
            (1, -1, -1),
            (-1, 1, -1),
            (1, 0, 0),
            (0, 1, 0),
            (-0.33, -0.34, -0.34),
            (0.33, 0.34, 0.33),
        ],
    )
    def test_merge_with_operation_minimum(
        self,
        tester: app_tester.GremlinAppTester,
        merge_axis_action: merge_axis.MergeAxisData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        value_input1: int,
        value_input2: int,
        expected_output: int,
    ):
        merge_axis_action.operation = merge_axis.MergeOperation.Minimum
        tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS1_LABEL), value_input1)
        tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS2_LABEL), value_input2)
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )
    
    @pytest.mark.parametrize(
        "value_input1,value_input2,expected_output",
        [
            (0, 0, 0),
            (1, 1, 1),
            (0.33, 0.33, 0.33),
            (0, 0, 0),
            (-0.22, -0.22, -0.22),
            (-1, -1, -1),
            (1, -1, 1),
            (-1, 1, 1),
            (1, 0, 1),
            (0, 1, 1),
            (-0.33, -0.34, -0.33),
            (0.33, 0.34, 0.34),
        ],
    )
    def test_merge_with_operation_maximum(
        self,
        tester: app_tester.GremlinAppTester,
        merge_axis_action: merge_axis.MergeAxisData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        value_input1: int,
        value_input2: int,
        expected_output: int,
    ):
        merge_axis_action.operation = merge_axis.MergeOperation.Maximum
        tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS1_LABEL), value_input1)
        tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS2_LABEL), value_input2)
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )

    
    @pytest.mark.parametrize(
        "value_input1,value_input2,expected_output",
        [
            (0, 0, 0),
            (1, 1, 1),
            (0.33, 0.33, 0.66),
            (-0.22, -0.22, -0.44),
            (-1, -1, -1),
            (1, -1, 0),
            (-1, 1, 0),
            (1, 0, 1),
            (0, 1, 1),
        ],
    )
    def test_merge_with_operation_sum(
        self,
        tester: app_tester.GremlinAppTester,
        merge_axis_action: merge_axis.MergeAxisData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        value_input1: int,
        value_input2: int,
        expected_output: int,
    ):
        merge_axis_action.operation = merge_axis.MergeOperation.Sum
        tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS1_LABEL), value_input1)
        tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS2_LABEL), value_input2)
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )
    
    
    @pytest.mark.parametrize(
        "value_input1,value_input2,expected_output",
        [
            (0, 0, 0),
            (1, 1, 0),
            (0.33, 0.33, 0.0),
            (-0.22, -0.22, 0.0),
            (-1, -1, 0.0),
            (1, -1, -1),
            (-1, 1, 1),
            (1, 0, -0.5),
            (0, 1, 0.5),
        ],
    )
    def test_merge_with_operation_bidirectional(
        self,
        tester: app_tester.GremlinAppTester,
        merge_axis_action: merge_axis.MergeAxisData,
        logical_device_for_test: logical_device.LogicalDevice,
        get_logical_input_action: LogicalActionCallableT,
        value_input1: int,
        value_input2: int,
        expected_output: int,
    ):
        merge_axis_action.operation = merge_axis.MergeOperation.Bidirectional
        tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS1_LABEL), value_input1)
        tester.inject_logical_input(get_logical_input_action(_LOGICAL_INPUT_AXIS2_LABEL), value_input2)
        tester.assert_logical_axis_eventually_equals(
            logical_device_for_test[_LOGICAL_OUTPUT_AXIS_LABEL].id,
            expected_output,
        )
