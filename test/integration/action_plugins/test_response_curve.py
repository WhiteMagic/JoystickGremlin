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

from action_plugins import map_to_io
import dill
from gremlin import event_handler
from gremlin import profile
from gremlin import types
from gremlin import mode_manager
from test.integration import app_tester


@pytest.fixture(scope="module", autouse=True)
def profile_name() -> str:
    return "action_response_curve.xml"


@pytest.fixture
def input_axis_uuid(loaded_profile: profile.Profile) -> uuid.UUID:
    return loaded_profile.inputs[dill.UUID_IntermediateOutput][0].input_id

@pytest.fixture
def output_axis_uuid(loaded_profile: profile.Profile) -> uuid.UUID:
    return loaded_profile.library.actions_by_type(map_to_io.MapToIOData)[0].io_input_guid


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
        event = event_handler.Event(
            event_type=types.InputType.JoystickAxis,
            identifier=input_axis_uuid,
            device_guid=dill.UUID_IntermediateOutput,
            mode=mode_manager.ModeManager().current.name,
            value=axis_input
        )
        tester.send_event(event)
        joystick_cache = input_cache.Joystick()[dill.GUID_IntermediateOutput.uuid][output_axis_uuid]
        # Note that, because of the way we created and injected the event, the input cache will
        # not have a value for the input axis.
        tester._assert_input_eventually_equals(
            lambda: joystick_cache.value,
            pytest.approx(axis_input, abs=8),
            0,
            1,
        )
