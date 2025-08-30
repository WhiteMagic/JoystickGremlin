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

from collections.abc import Callable, Iterator

import pytest

from action_plugins import map_to_logical_device
import dill
from gremlin import logical_device, plugin_manager, profile, shared_state
from gremlin.ui import backend, device

LogicalActionCallableT = Callable[
    [logical_device.LogicalDevice.Input.Identifier | str],
    map_to_logical_device.MapToLogicalDeviceData,
]
LogicalIdentifierCallableT = Callable[
    [logical_device.LogicalDevice.Input.Identifier | str], device.InputIdentifier
]


@pytest.fixture(scope="module")
def profile_for_test() -> profile.Profile:
    # This is important for locally-run tests where the last used profile could
    # get loaded, if present in configuration.
    backend_ = backend.Backend()
    backend_.newProfile()
    return backend_.profile


@pytest.fixture(scope="module")
def logical_device_for_test(
    profile_for_test: profile.Profile,
) -> logical_device.LogicalDevice:
    # Depends on profile_for_test fixture because the latter resets the
    # LogicalDevice singleton.
    del profile_for_test
    return logical_device.LogicalDevice()


@pytest.fixture(scope="module")
def get_logical_input_action(
    logical_device_for_test: logical_device.LogicalDevice,
) -> LogicalActionCallableT:
    """Returns a function that creates or retrieves a logical input action."""
    action_for_label = {}

    def _create_or_get_action(
        identifier_or_label: logical_device.LogicalDevice.Input.Identifier | str,
    ) -> map_to_logical_device.MapToLogicalDeviceData:
        if identifier_or_label in action_for_label:
            return action_for_label[identifier_or_label]
        input_ = logical_device_for_test[identifier_or_label]
        p_manager = plugin_manager.PluginManager()
        action = p_manager.create_instance(
            map_to_logical_device.MapToLogicalDeviceData.name, input_.type
        )
        action.logical_input_id = input_.id
        action_for_label[identifier_or_label] = action
        return action

    return _create_or_get_action


@pytest.fixture(scope="module")
def get_logical_input_identifier(
    logical_device_for_test: logical_device.LogicalDevice,
) -> LogicalIdentifierCallableT:
    """Returns a function that creates or retrieves a logical input identifier."""
    identifier_for_label = {}

    def _create_or_get_identifier(
        identifier_or_label: logical_device.LogicalDevice.Input.Identifier | str,
    ) -> device.InputIdentifier:
        if identifier_or_label in identifier_for_label:
            return identifier_for_label[identifier_or_label]
        input_ = logical_device_for_test[identifier_or_label]
        identifier_for_label[identifier_or_label] = device.InputIdentifier(
            dill.UUID_LogicalDevice, input_.type, input_.id
        )
        return identifier_for_label[identifier_or_label]

    return _create_or_get_identifier


# Do not use directly, see app_tester fixture instead.
@pytest.fixture(scope="module", autouse=True)
def _activate_gremlin(profile_setup: None) -> Iterator[None]:
    """Activates Gremlin using the profile created by profile_setup.

    profile_setup is a fixture that should be created by individual tests,
    creating the necessary LogicalDevice objects, actions, and
    InputItemBindings.
    """
    del profile_setup
    backend_ = backend.Backend()
    backend_.activate_gremlin(True)
    backend_.minimize()
    yield
    backend_.activate_gremlin(False)
