# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
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

import re

from mako.template import Template

import action_plugins
import gremlin
from gremlin.common import UiInputType
from gremlin import error, profile, util


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
    for entry in input_item.actions:
        if type(entry) in vjoy_required:
            params.append("vjoy")
        if isinstance(entry.condition, action_plugins.common.ButtonCondition) \
                and entry.condition.shift_button is not None:
            if entry.condition.shift_button["hardware_id"] == 0:
                params.append("keyboard")
            else:
                params.append("joy")
    params = list(set(params))
    params.insert(0, "event")
    return ", ".join(params)


def sanitize_code(code):
    """Returns a sanitized version of the code.

    This removes extraneous line breaks while ensuring proper line
    spacing.

    :param code the code to sanitize
    :return sanitized version of the provided code
    """
    code = re.sub("\r", "", code)
    new_code = ""
    for line in code.split("\n"):
        if line == "#newline":
            new_code += "\n"
        elif len(line) > 0:
            new_code += line + "\n"

    return new_code


def actions_to_code(actions, code):
    """Generates code corresponding to a list of actions.

    :param actions list of action instances from which to generate code
    :param code output storage for the generated code
    :return code corresponding to the provided list of actions
    """
    for entry in actions:
        if not isinstance(entry, action_plugins.remap.Remap):
            for key, value in entry.to_code().items():
                assert(key in code)
                code[key].append(value)
    for entry in actions:
        if isinstance(entry, action_plugins.remap.Remap):
            for key, value in entry.to_code().items():
                assert(key in code)
                code[key].append(value)


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


class CodeGenerator(object):

    """Generates python code corresponding to the provided XML data."""

    def __init__(self, config_profile):
        """Creates a new object.

        :param config_profile the Profile object containing the
            configuration
        """
        self.code = {
            "import": [],
            "decorator": [],
            "global": [],
            "callback": [],
        }
        self.decorator_map = {}
        self.decorator_usage_counts = {}
        self.decorator_templates = {}

        try:
            self.generate_from_profile(config_profile)
        except error.GremlinError as err:
            util.display_error(str(err))

    def write_code(self, fname):
        """Writes the generated code to the given file.

        :param fname name of the file to write the generated code to
        """
        with open(fname, "w") as out:
            for line in self.code["import"]:
                out.write(sanitize_code(line))
            out.write("\n")
            for line in self.code["decorator"]:
                out.write(sanitize_code(line))
            out.write("\n")
            for line in self.code["global"]:
                out.write(sanitize_code(line))
            out.write("\n")
            for block in self.code["callback"]:
                out.write(sanitize_code(block))
                out.write("\n")

    def generate_from_profile(self, config_profile):
        """Turns the Profile object's contents into python code.

        :param config_profile the Profile to turn into code
        """
        assert(isinstance(config_profile, profile.Profile))

        # Custom modules
        tpl = Template(filename="templates/import.tpl")
        self.code["import"].append(tpl.render(
            user_imports=config_profile.imports
        ))

        # Device, mode, actions
        for device in config_profile.devices.values():
            for i, mode in enumerate(device.modes.values()):
                self.process_device_mode(mode, i)

        # Merge axes
        for i, entry in enumerate(config_profile.merge_axes):
            self.process_merge_axis(i, entry)

        # Add required decorator definitions into the code
        for dev_id in self.decorator_usage_counts:
            for mode, count in self.decorator_usage_counts[dev_id].items():
                if count > 0:
                    self.code["global"].append(
                        self.decorator_templates[dev_id][mode]
                    )

        # Vjoy response curve switching
        tpl = Template(filename="templates/vjoy_curves.tpl")
        self.code["global"].append(tpl.render(
            vjoy_devices=config_profile.vjoy_devices,
            vjoy_ids=[joy.vjoy_id for joy in gremlin.util.joystick_devices()
                      if joy.is_virtual],
            UiInputType=gremlin.common.UiInputType
        ))

    def process_merge_axis(self, idx, entry):
        """Processes a merge axis entry.

        :param idx the id of the entry
        :param entry the entry to turn into code
        """
        tpl_main = Template(filename="templates/merge_axis_main.tpl")
        tpl_cb = Template(filename="templates/merge_axis_callback.tpl")

        self.code["global"].append(tpl_main.render(
            entry=entry,
            idx=idx
        ))
        self.code["callback"].append(tpl_cb.render(
            entry=entry,
            idx=idx,
            decorator_map=self.decorator_map
        ))

        # Account for axis merging needing certain decorators which otherwise
        # might appear unused
        self.decorator_usage_counts[entry["lower"][0]][entry["mode"]] += 1
        self.decorator_usage_counts[entry["upper"][0]][entry["mode"]] += 1

    def process_device_mode(self, mode, index):
        """Processes a single Mode object and turns its contents into code.

        :param mode the profile.Mode object to process
        :param index the index to use in the decorator name
        """
        assert(isinstance(mode, profile.Mode))

        dev_id = util.device_id(mode.parent)
        if dev_id not in self.decorator_map:
            self.decorator_map[dev_id] = {}
            self.decorator_usage_counts[dev_id] = {}
            self.decorator_templates[dev_id] = {}
        self.decorator_map[dev_id][mode.name] = decorator_name(mode, index)

        items_added = 0
        for input_type, input_items in mode.config.items():
            for entry in input_items.values():
                self.generate_input_item(entry, mode, index)
                items_added += len(entry.actions)

        # Generate decorator code and keep track of how often they are used
        # to later decide which ones to include in the final code
        tpl = Template(filename="templates/mode.tpl")
        self.decorator_templates[dev_id][mode.name] = tpl.render(
            decorator=decorator_name(mode, index),
            mode=mode
        )
        self.decorator_usage_counts[dev_id][mode.name] = items_added

    def generate_input_item(self, input_item, mode, index):
        """Generates code for the provided profile.InputItem object.

        :param input_item profile.InputItem object to process into code
        :param mode the profile.Mode object corresponding to
            this input_item
        :param index the index to use for the decorator name
        """
        assert(isinstance(input_item, profile.InputItem))
        assert(isinstance(mode, profile.Mode))
        assert(input_item.parent == mode)

        if len(input_item.actions) == 0:
            return {}

        input_type_templates = {
            UiInputType.JoystickAxis: "templates/axis.tpl",
            UiInputType.JoystickButton: "templates/button.tpl",
            UiInputType.JoystickHat: "templates/hat.tpl",
            UiInputType.Keyboard: "templates/key.tpl",
        }

        # Generate code for the actions associated with the item
        code = {
            "body": [],
            "global": [],
        }
        actions_to_code(input_item.actions, code)
        self.code["global"].extend(code["global"])

        tpl = Template(filename=input_type_templates[input_item.input_type])
        helpers = {
            "wid": input_item_identifier_string,
        }

        self.code["callback"].append(tpl.render(
            device_name=util.format_name(mode.parent.name),
            decorator=decorator_name(mode, index),
            mode=mode.name,
            mode_index=index,
            input_item=input_item,
            code=code,
            param_list=generate_parameter_list(input_item),
            helpers=helpers,
            gremlin=gremlin
        ))
