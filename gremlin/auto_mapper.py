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
Auto-mapping from physical DirectInput to vJoy devices.
"""

from collections.abc import Iterable
import dataclasses
import itertools
import logging
from typing import Self

from action_plugins import map_to_vjoy, root
import dill
from gremlin import (
    device_initialization,
    mode_manager,
    plugin_manager,
    profile,
    shared_state,
    types,
)
from vjoy import vjoy


@dataclasses.dataclass
class AutoMapperOptions:
    """Options for the auto-mapper.

    More flags may be added here to further customize auto-mapper behavior.
    """

    repeat_vjoy_inputs: bool = False
    overwrite_used_inputs: bool = False


class AutoMapper:
    """Generates "map to vJoy' actions for physical input devices.

    The primary purpose is to help users with new profiles get started with
    simple mappings for their input devices. The common use case is to map "available"
    physical inputs to "available" vJoy inputs.

    To keep things simple, a vJoy input is considered "available" even if there's a binding
    to it in the profile, but:
    1. The binding is from a disconnected device.
    2. The binding is from a macro, a sub-action (usually temp, chain, or condition), or in a
       user script.

    A physical input is considered "available" if it has no binding in the profile. An option
    is provided to overwrite unavailable inputs, in which case any existing bindings are removed,
    unless they are direct vJoy mappings (which could have been created by this tool).

    Bindings are generated for the current active mode only; bindings from other modes are
    not checked (i.e. any physical and vJoy inputs used only in other modes are considered
    available in the current mode).

    This class should be instantiated after the current profile has been loaded/generated.
    Functions should be called after device initialization is complete.
    """

    def __init__(self, profile: profile.Profile):
        self._profile = profile
        # For debug, testing and creating a report for the user.
        self._created_mappings: list[map_to_vjoy.MapToVjoyData] = []

    @classmethod
    def from_current_profile(cls) -> Self:
        return cls(shared_state.current_profile)

    def generate_mappings(
        self,
        input_devices_guids: list[dill.GUID],
        output_vjoy_ids: list[int],
        options: AutoMapperOptions,
    ) -> str:
        """Generates mappings for the profile.

        Args:
            input_devices_guids: List of GUIDs representing the input devices to map from.
            output_vjoy_ids: List of DeviceSummary objects representing the vJoy devices to map to.
            options: Options for the auto-mapper.
        
        Returns:
            A string report for the user summarizing new mappings.
        """
        input_devices = [
            dev
            for dev in device_initialization.physical_devices()
            if dev.device_guid in input_devices_guids
        ]

        self._prepare_profile(input_devices, options)
        used_vjoy_inputs = set(self._get_used_vjoy_inputs())
        vjoy_axes = self._iter_unused_vjoy_axes(output_vjoy_ids, used_vjoy_inputs)
        vjoy_buttons = self._iter_unused_vjoy_buttons(output_vjoy_ids, used_vjoy_inputs)
        vjoy_hats = self._iter_unused_vjoy_hats(output_vjoy_ids, used_vjoy_inputs)
        if options.repeat_vjoy_inputs:
            vjoy_axes = itertools.cycle(vjoy_axes)
            vjoy_buttons = itertools.cycle(vjoy_buttons)
            vjoy_hats = itertools.cycle(vjoy_hats)
        for physical_axis, vjoy_axis in zip(
            self._iter_physical_axes(input_devices, options), vjoy_axes
        ):
            self._create_new_mapping(physical_axis, vjoy_axis)
        for physical_button, vjoy_button in zip(
            self._iter_physical_buttons(input_devices, options), vjoy_buttons
        ):
            self._create_new_mapping(physical_button, vjoy_button)
        for physical_hat, vjoy_hat in zip(
            self._iter_physical_hats(input_devices, options), vjoy_hats
        ):
            self._create_new_mapping(physical_hat, vjoy_hat)
        return self._create_mappings_report()

    def _prepare_profile(
        self, input_devices: list[dill.DeviceSummary], options: AutoMapperOptions
    ):
        """Prepares the profile for an auto-map run."""
        if options.overwrite_used_inputs:
            for dev in input_devices:
                self._profile.inputs.pop(dev.device_guid.uuid, None)

    def _iter_physical_axes(
        self, input_devices: list[dill.DeviceSummary], options: AutoMapperOptions
    ) -> Iterable[profile.InputItem]:
        """Iterates over physical axes that need to be mapped in a prepared profile."""
        current_mode = mode_manager.ModeManager().current.name

        for dev in input_devices:
            for linear_index in range(dev.axis_count):
                axis_index = dev.axis_map[linear_index].axis_index
                input_item = self._profile.get_input_item(
                    dev.device_guid.uuid,
                    types.InputType.JoystickAxis,
                    axis_index,
                    current_mode,
                    create_if_missing=True,
                )
                if not input_item.action_sequences:
                    yield input_item

    def _iter_physical_buttons(
        self, input_devices: list[dill.DeviceSummary], options: AutoMapperOptions
    ) -> Iterable[profile.InputItem]:
        """Iterates over physical buttons that need to be mapped in a prepared profile."""
        current_mode = mode_manager.ModeManager().current.name

        for dev in input_devices:
            for button in range(1, dev.button_count + 1):
                input_item = self._profile.get_input_item(
                    dev.device_guid.uuid,
                    types.InputType.JoystickButton,
                    button,
                    current_mode,
                    create_if_missing=True,
                )
                if not input_item.action_sequences:
                    yield input_item

    def _iter_physical_hats(
        self, input_devices: list[dill.DeviceSummary], options: AutoMapperOptions
    ) -> Iterable[profile.InputItem]:
        """Iterates over physical hats that need to be mapped in a prepared profile."""
        current_mode = mode_manager.ModeManager().current.name

        for dev in input_devices:
            for hat in range(1, dev.hat_count + 1):
                input_item = self._profile.get_input_item(
                    dev.device_guid.uuid,
                    types.InputType.JoystickHat,
                    hat,
                    current_mode,
                    create_if_missing=True,
                )
                if not input_item.action_sequences:
                    yield input_item

    def _get_used_vjoy_inputs(self) -> list[vjoy.VjoyInput]:
        """Returns a list of all vJoy inputs that are already used in the prepared profile."""
        used_vjoy_inputs = []
        connected_device_uuids = set(
            [dev.device_guid.uuid for dev in device_initialization.physical_devices()]
        )
        for device_uuid, input_items in self._profile.inputs.items():
            if device_uuid not in connected_device_uuids:
                logging.getLogger("system").debug(
                    f"vJoy mappings from disconnected device {device_uuid=} "
                    "are considered unused."
                )
                continue
            for input_item in input_items:
                if input_item.mode != mode_manager.ModeManager().current.name:
                    logging.getLogger("system").debug(
                        f"vJoy mapping from other mode {input_item.mode=} "
                        "is considered unused."
                    )
                    continue
                for binding in input_item.action_sequences:
                    assert isinstance(binding.root_action, root.RootData)
                    child_actions = binding.root_action.children
                    for child_action in child_actions:
                        if isinstance(child_action, map_to_vjoy.MapToVjoyData):
                            used_vjoy_inputs.append(
                                vjoy.VjoyInput(
                                    child_action.vjoy_device_id,
                                    child_action.vjoy_input_type,
                                    child_action.vjoy_input_id,
                                )
                            )
                        else:
                            logging.getLogger("system").debug(
                                f"Auto-mapper will reuse vJoy mappings in {child_action=}"
                            )
        return used_vjoy_inputs

    def _iter_unused_vjoy_axes(
        self, vjoy_ids: list[int], used_vjoy_inputs: set[vjoy.VjoyInput]
    ) -> Iterable[vjoy.VjoyInput]:
        """Returns a list of all vJoy inputs that are not used in the prepared profile."""
        for vjoy_dev in device_initialization.vjoy_devices():
            if vjoy_dev.vjoy_id not in vjoy_ids:
                continue
            for linear_index in range(vjoy_dev.axis_count):
                axis_index = vjoy_dev.axis_map[linear_index].axis_index
                vjoy_axis = vjoy.VjoyInput(
                    vjoy_dev.vjoy_id, types.InputType.JoystickAxis, axis_index
                )
                if vjoy_axis not in used_vjoy_inputs:
                    yield vjoy_axis

    def _iter_unused_vjoy_buttons(
        self, vjoy_ids: list[int], used_vjoy_inputs: set[vjoy.VjoyInput]
    ) -> Iterable[vjoy.VjoyInput]:
        for vjoy_dev in device_initialization.vjoy_devices():
            if vjoy_dev.vjoy_id not in vjoy_ids:
                continue
            for button_id in range(1, vjoy_dev.button_count + 1):
                vjoy_button = vjoy.VjoyInput(
                    vjoy_dev.vjoy_id, types.InputType.JoystickButton, button_id
                )
                if vjoy_button not in used_vjoy_inputs:
                    yield vjoy_button

    def _iter_unused_vjoy_hats(
        self, vjoy_ids: list[int], used_vjoy_inputs: set[vjoy.VjoyInput]
    ) -> Iterable[vjoy.VjoyInput]:
        for vjoy_dev in device_initialization.vjoy_devices():
            if vjoy_dev.vjoy_id not in vjoy_ids:
                continue
            for hat_id in range(1, vjoy_dev.hat_count + 1):
                vjoy_hat = vjoy.VjoyInput(
                    vjoy_dev.vjoy_id, types.InputType.JoystickHat, hat_id
                )
                if vjoy_hat not in used_vjoy_inputs:
                    yield vjoy_hat

    def _create_new_mapping(
        self, physical_input: profile.InputItem, vjoy_input: vjoy.VjoyInput
    ):
        """Creates a new mapping from physical_input to vjoy_input."""
        p_manager = plugin_manager.PluginManager()
        root_action = p_manager.create_instance(
            root.RootData.name, physical_input.input_type
        )
        vjoy_action = p_manager.create_instance(
            map_to_vjoy.MapToVjoyData.name, physical_input.input_type
        )
        vjoy_action.vjoy_device_id = vjoy_input.vjoy_id
        vjoy_action.vjoy_input_id = vjoy_input.input_id
        vjoy_action.vjoy_input_type = vjoy_input.input_type
        root_action.insert_action(vjoy_action, "children")
        binding = profile.InputItemBinding(physical_input)
        binding.root_action = root_action
        binding.behavior = physical_input.input_type
        physical_input.action_sequences.append(binding)
        self._created_mappings.append(vjoy_action)
    
    def _create_mappings_report(self) -> str:
        """Creates a text report for the user after a mapping operation."""
        return f"Created {len(self._created_mappings)} mappings."
