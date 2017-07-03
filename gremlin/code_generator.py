# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2017 Lionel Ott
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

import collections
import re

import gremlin.common
from mako.lookup import TemplateLookup
from mako.template import Template

import action_plugins.remap
import action_plugins.response_curve
import action_plugins.common
import gremlin
from . import error, profile, util


CallbackData = collections.namedtuple(
    "CallbackData",
    [
        "input_item",
        "decorator_name",
        "mode_index",
        "parameter_list",
        "device_name",
        "code_block"
    ]
)

DecoratorData = collections.namedtuple(
    "DecoratorData",
    [
        "decorator_name",
        "device_name"
    ]
)


def decorator_name(mode, index):
    """Returns the decorator name corresponding to the provided data.

    :param mode the profile.Mode object for which to generate the name
    :param index the index to use in the decorator name
    :return name of the decorator matching the provided mode
    """
    assert(isinstance(mode, profile.Mode))
    hid, wid = util.extract_ids(util.device_id(mode.parent))
    if wid != -1:
        return "{}_{}_{}".format(
            util.format_name(mode.parent.name),
            wid,
            index
        )
    else:
        return "{}_{}".format(
            util.format_name(mode.parent.name),
            index
        )


def generate_parameter_list(input_item):
    """Generates the parameter list of a callback function.

    :param input_item the item for whose actions to generate the
        parameter list
    :return string representation of the parameter list needed for the
        provided input_item
    """
    params = []
    vjoy_required = gremlin.plugin_manager.ActionPlugins() \
        .plugins_requiring_parameter("vjoy")
    for container in input_item.containers:
        for action in container.actions:
            if type(action) in vjoy_required:
                params.append("vjoy")
    params = list(set(params))
    params.insert(0, "event")
    return ", ".join(params)


def input_item_identifier_string(input_item):
    """Returns the identifier string for a given InputItem.

    :param input_item the item for which to generate the identifier
    :return identifier for this InputItem
    """
    hid, wid = util.extract_ids(util.device_id(input_item.parent.parent))
    if wid != -1:
        return "_{}".format(wid)
    else:
        return ""


class CodeGenerator:

    """Generates a Python script representing the entire configuration."""

    def __init__(self, config_profile):
        """Creates a new code generator for the given configuration.

        :param config_profile profile for which to generate code
        """
        self.decorators = {}
        self.setup = []
        self.callbacks = {}

        self.code = ""
        try:
            self.generate_from_profile(config_profile)
        except error.GremlinError as err:
            util.display_error(str(err))

    def generate_from_profile(self, config_profile):
        """Generates the code for the given configuration.

        :param config_profile the profile for which to generate the code
        """
        assert (isinstance(config_profile, profile.Profile))

        # Reset the profile code cache
        self._reset_code_cache(config_profile)

        # Device, mode, actions
        for device in config_profile.devices.values():
            self._process_device(device)

        # Create output by rendering it via the template system
        tpl_lookup = TemplateLookup(directories=["."])
        tpl = Template(
            filename="templates/gremlin_code.tpl",
            lookup=tpl_lookup
        )
        self.code = tpl.render(
            gremlin=gremlin,
            profile=config_profile,
            decorators=self.decorators,
            callbacks=self.callbacks,
            setup=self.setup
        )

    def write_code(self, fname):
        """Writes the generated code to the given file.

        :param fname path to the file into which to write the code
        """
        code = re.sub("\r", "", self.code)
        with open(fname, "w") as out:
            out.write(code)

    def _process_device(self, device):
        """Processes the profile data of a single device.

        :param device the device profile to process
        """
        for i, mode in enumerate(device.modes.values()):
            self._process_mode(mode, i)

    def _process_mode(self, mode, index):
        """Processes a single mode's profile.

        :param mode the mode profile to process
        :param index the index associated with this mode
        """
        device_id = util.device_id(mode.parent)

        # Ensure data storage is properly initialized
        if device_id not in self.decorators:
            self.decorators[device_id] = {}
        if device_id not in self.callbacks:
            self.callbacks[device_id] = {}
        if mode not in self.callbacks[device_id]:
            self.callbacks[device_id][mode.name] = []

        # Gather data required to generate decorator definitions
        if mode.parent.type != gremlin.common.DeviceType.Keyboard:
            self.decorators[device_id][mode.name] = DecoratorData(
                decorator_name(mode, index),
                mode.parent.name
            )

        # Gather data required to generate callback related code
        for input_type, input_items in mode.config.items():
            for input_item in input_items.values():
                self._process_input_item(input_item, index)

    def _process_input_item(self, input_item, index):
        """Process an individual input item's profile data.

        :param input_item the input item profile to process
        :param index the index associated with this input item
        """
        # Grab required information
        mode = input_item.parent
        device_id = util.device_id(mode.parent)

        # Discard any container that is not valid, i.e. contains not enough
        # or invalid actions.
        input_item.containers = \
            [c for c in input_item.containers if c.is_valid()]

        # Abort if there are no valid actions associated with this item
        if len(input_item.containers) == 0:
            return

        # Generate callback code
        code_block = profile.CodeBlock()
        # First process containers which contain response curve actions as
        # those have to be executed before any remap can occur
        skipped_containers = []
        for container in input_item.containers:
            skip_container = True
            for action in container.actions:
                if isinstance(action, action_plugins.response_curve.ResponseCurve):
                    skip_container = False
            if skip_container:
                skipped_containers.append(container)
            else:
                code_block.combine(container.to_code())
        for container in skipped_containers:
            code_block.combine(container.to_code())

        # Store data required to integrate the code into the global file
        self.callbacks[device_id][mode.name].append(CallbackData(
            input_item,
            decorator_name(mode, index),
            index,
            generate_parameter_list(input_item),
            "{}{}".format(
                util.format_name(mode.parent.name),
                input_item_identifier_string(input_item)
            ),
            code_block
        ))

        # Generate action setup stuff
        for container in input_item.containers:
            for action in container.actions:
                code = action.to_code()
                if "setup" in code.keys() and len(code.setup) > 0:
                    self.setup.append(code.setup.strip())

    def _reset_code_cache(self, config_profile):
        """Empties the code cache of a profile.

        :param config_profile the profile whose cache is to be reset
        """
        profile.ProfileData.next_code_id = 0
        for device in config_profile.devices.values():
            for mode in device.modes.values():
                for input_items in mode.config.values():
                    for input_item in input_items.values():
                        for container in input_item.containers:
                            container.code = None
                            for action in container.actions:
                                action.code = None
