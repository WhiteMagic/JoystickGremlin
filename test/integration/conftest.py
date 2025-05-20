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

import sys

sys.path.append(".")

from collections.abc import Iterator
import logging
import pathlib
import tempfile

from PySide6 import QtWidgets
import pytest

import dill
import gremlin.device_initialization
import gremlin.error
import gremlin.profile
import gremlin.ui.backend
import joystick_gremlin
from vjoy import vjoy
from action_plugins import map_to_vjoy

pytest.register_assert_rewrite("test.integration.app_tester")
from test.integration import app_tester


# +-------------------------------------------------------------------------
# | Common fixtures, override in modules as needed.
# +-------------------------------------------------------------------------


@pytest.fixture(scope="module")
def vjoy_di_device(
    vjoy_di_devices_or_skip: list[dill.DeviceSummary],
) -> dill.DeviceSummary:
    """Returns the DirectInput (vJoy) device to be used for this module."""
    assert vjoy_di_devices_or_skip
    for vjoy_device in vjoy_di_devices_or_skip:
        if (
            vjoy_device.axis_count >= 4
            and vjoy_device.button_count >= 4
            and vjoy_device.hat_count >= 2
        ):
            return vjoy_device
    pytest.skip("No vJoy device suitable for testing found")


@pytest.fixture(scope="module")
def vjoy_control_device_id(vjoy_ids_or_skip: list[int]) -> vjoy.VJoy:
    """Returns the vJoy control device to be used for this test."""
    assert vjoy_ids_or_skip
    for vjoy_id in vjoy_ids_or_skip:
        # TODO: Actually match them in case of multiple vJoy devices.
        return vjoy_id
    pytest.skip("No vJoy control device suitable for testing found")


@pytest.fixture(scope="module")
def profile_for_testing(
    vjoy_control_device: vjoy.VJoy,
    vjoy_di_device: dill.DeviceSummary,
    profile_path: str,
) -> gremlin.profile.Profile:
    """Returns a Gremlin profile for testing the current module.
    
    This implementation mutates the profile specified by 'profile_path', with
    inputs and outputs swapped with "real" devices. Alternatively, you can
    override this fixture in test modules to use a generated profile.

    (Where "real" means actual vJoy devices on this system.)
    """
    profile = gremlin.profile.Profile()
    profile.from_xml(profile_path)
    # Replace the (only) input device.
    assert len(profile.inputs) == 1
    _, input_items = profile.inputs.popitem()
    profile.inputs[vjoy_di_device.device_guid.uuid] = input_items
    for input_item in input_items:
      input_item.device_id = vjoy_di_device.device_guid.uuid

    # Replace the output device(s) with the single vJoy control device.
    for action in profile.library.actions_by_type(map_to_vjoy.MapToVjoyData):
        action.vjoy_device_id = vjoy_control_device.vjoy_id

    return profile


# +-------------------------------------------------------------------------
# | Common fixtures, typically there should be no need to override.
# +-------------------------------------------------------------------------


@pytest.fixture(scope="module")
def profile_path(profile_name: str) -> str:
    """Returns profile path. Requires test modules to define the profile_name fixture."""
    return pathlib.Path(__file__).parent / "xml" / profile_name


@pytest.fixture(scope="module")
def edited_profile_path(profile_for_testing: gremlin.profile.Profile) -> Iterator[str]:
    with tempfile.NamedTemporaryFile(delete_on_close=False) as f:
        f.close()
        profile_for_testing.to_xml(f.name)
        yield f.name


@pytest.fixture(scope="module", params=None)
def vjoy_control_device(vjoy_control_device_id: int) -> Iterator[vjoy.VJoy]:
    vjoy_control = vjoy.VJoyProxy()[vjoy_control_device_id]
    try:
        yield vjoy_control
    finally:
        vjoy_control.invalidate()
        vjoy.VJoyProxy.reset()


@pytest.fixture(scope="package")
def vjoy_di_devices_or_skip() -> list[dill.DeviceSummary]:
    """Returns list of DirectInput vJoy devices summaries if any, else skips dependent tests."""
    vjoy_devices = gremlin.device_initialization.vjoy_devices()
    if len(vjoy_devices) == 0:
        pytest.skip("No vJoy input devices found")
    return vjoy_devices


@pytest.fixture(scope="package")
def vjoy_ids_or_skip() -> list[int]:
    """Returns list of vJoy device IDs if any, else skips dependent tests.

    We return IDs instead of the control devices to not acquire vJoy devices a
    test might not actually use.
    """
    # TODO: Share this functionality with input_devices.py
    vjoy_ids = []
    vjoy_proxy = vjoy.VJoyProxy()
    for i in range(1, 17):
        if vjoy.device_exists(i):
            try:
                vjoy_proxy[i]
            except gremlin.error.VJoyError:
                logging.warning("vJoy device %d cannot be acquired", i)
            else:
                vjoy_ids.append(i)
    vjoy_proxy.reset()
    if len(vjoy_ids):
        return vjoy_ids
    pytest.skip("No usable vJoy control devices found")


# Do not use directly, see app_tester fixture instead.
@pytest.fixture(scope="package", autouse=True)
def _gremlin_app() -> Iterator[QtWidgets.QApplication]:
    """Yields the Gremlin app."""
    argv = [sys.argv[0]]
    app = joystick_gremlin.make_gremlin_app(argv)
    yield app
    app.exit()


# Do not use directly, see app_tester fixture instead.
@pytest.fixture(scope="module", autouse=True)
def _activate_gremlin(edited_profile_path: str) -> Iterator[None]:
    """Activates Gremlin."""
    backend = gremlin.ui.backend.Backend()
    backend.loadProfile(edited_profile_path)
    backend.activate_gremlin(True)
    backend.minimize()
    yield
    backend.activate_gremlin(False)


@pytest.fixture(scope="module", autouse=True)
def tear_down() -> Iterator[None]:
    """Performs package-level teardown for integration tests."""
    yield
    vjoy.VJoyProxy.reset()


# +-------------------------------------------------------------------------
# | Fixture used for assertions in integration tests.
# +-------------------------------------------------------------------------


@pytest.fixture
def tester(_gremlin_app: QtWidgets.QApplication) -> app_tester.GremlinAppTester:
    return app_tester.GremlinAppTester(_gremlin_app)
