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
Integration test for response curve action using intermediate output devices.
"""
import uuid

import pytest

from action_plugins import response_curve
from action_plugins import root
from action_plugins import map_to_io
import dill
from gremlin.ui import backend
from gremlin import event_handler
from gremlin import intermediate_output
from gremlin import plugin_manager
from gremlin import profile
from gremlin import shared_state
from gremlin import types
from gremlin import mode_manager
from test.integration import app_tester

_INPUT_IO_AXIS_LABEL = "InputAxis1"
_OUTPUT_IO_AXIS_LABEL = "OutputAxis1"


@pytest.fixture(scope="module")
def profile_setup() -> None:
    # This is important for locally-run tests where the last used profile could
    # get loaded, if present in configuration.
    backend.Backend().profile = pr = profile.Profile()
    shared_state.current_profile = pr

    # Create intermediate output axis for both input and output.
    io = intermediate_output.IntermediateOutput()
    io.reset()
    io.create(types.InputType.JoystickAxis, label=_INPUT_IO_AXIS_LABEL)
    io.create(types.InputType.JoystickAxis, label=_OUTPUT_IO_AXIS_LABEL)

    p_manager = plugin_manager.PluginManager()
    # Create response curve action.
    response_curve_action = p_manager.create_instance(
        response_curve.ResponseCurveData.name,
        types.InputType.JoystickAxis
    )

    # Create intermediate output mapping action.
    map_to_io_action = p_manager.create_instance(
        map_to_io.MapToIOData.name,
        types.InputType.JoystickAxis
    )
    map_to_io_action.io_input_guid = io[_OUTPUT_IO_AXIS_LABEL].guid

    # Add actions to profile.
    root_action = p_manager.create_instance(root.RootData.name, types.InputType.JoystickAxis)
    root_action.insert_action(response_curve_action, "children")
    root_action.insert_action(map_to_io_action, "children")
    # Add input item and its binding.
    input_item = profile.InputItem(pr.library)
    input_item.device_id = dill.UUID_IntermediateOutput
    input_item.input_id = io[_INPUT_IO_AXIS_LABEL].guid
    input_item.input_type = types.InputType.JoystickAxis
    input_item.mode = mode_manager.ModeManager().current.name
    input_item_binding = profile.InputItemBinding(input_item)
    input_item_binding.root_action = root_action
    input_item_binding.behavior = types.InputType.JoystickAxis
    input_item.action_sequences.append(input_item_binding)
    pr.inputs.setdefault(dill.UUID_IntermediateOutput, []).append(input_item)


@pytest.fixture
def input_axis_uuid() -> uuid.UUID:
    return intermediate_output.IntermediateOutput()[_INPUT_IO_AXIS_LABEL].guid


@pytest.fixture
def output_axis_uuid() -> uuid.UUID:
    return intermediate_output.IntermediateOutput()[_OUTPUT_IO_AXIS_LABEL].guid


class TestResponseCurve:
    """Tests for response curve action."""

    @pytest.mark.parametrize(
        "axis_input",
        [
            1,
            0,
            -1,
        ],
    )
    def test_axis_sequential(
        self,
        tester: app_tester.GremlinAppTester,
        axis_input: int,
        input_axis_uuid: uuid.UUID,
        output_axis_uuid: uuid.UUID,
    ):
        """Applies groups of sequential inputs."""
        tester.send_event(
            event_handler.Event(
                event_type=types.InputType.JoystickAxis,
                identifier=input_axis_uuid,
                device_guid=dill.UUID_IntermediateOutput,
                mode=mode_manager.ModeManager().current.name,
                value=axis_input,
            )
        )
        tester.assert_io_axis_eventually_equals(
            output_axis_uuid,
            pytest.approx(axis_input, abs=8),
            0,
            1,
        )
