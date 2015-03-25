# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
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

import action
from mako.template import Template
from gremlin.event_handler import InputType
from gremlin import error, profile, util


def decorator_name(mode):
    """Returns the decorator name corresponding to the provided data.

    :param mode the profile.Mode object for which to generate the name
    :return name of the decorator matching the provided mode
    """
    assert(isinstance(mode, profile.Mode))
    hid, wid = util.extract_ids(util.device_id(mode.parent))
    if wid != -1:
        return "{}_{}_{}".format(
            util.format_name(mode.parent.name),
            wid,
            util.format_name(mode.name)
        )
    else:
        return "{}_{}".format(
            util.format_name(mode.parent.name),
            util.format_name(mode.name)
        )


def generate_parameter_list(input_item):
    """Generates the parameter list of a callback function.

    :param input_item the item for whose actions to generate the
        parameter list
    :return string representation of the parameter list needed for the
        provided input_item
    """
    params = []
    for entry in input_item.actions:
        if isinstance(entry, action.remap.Remap):
            params.append("vjoy")
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
        if len(line) > 0:
            new_code += line + "\n"
    return new_code


def actions_to_code(actions, code):
    """Generates code corresponding to a list of actions.

    :param actions list of action instances from which to generate code
    :return code corresponding to the provided list of actions
    """
    for entry in actions:
        if not isinstance(entry, action.remap.Remap):
            for key, value in entry.to_code().items():
                assert(key in code)
                code[key].append(value)
    for entry in actions:
        if isinstance(entry, action.remap.Remap):
            for key, value in entry.to_code().items():
                assert(key in code)
                code[key].append(value)


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
        tpl = Template(filename="templates/import.tpl")
        self.code["import"].append(tpl.render(
            user_imports=config_profile.imports
        ))

        for device in config_profile.devices.values():
            for mode in device.modes.values():
                self.process_device_mode(mode)

    def process_device_mode(self, mode):
        """Processes a single Mode object and turns it's contents to
        code.

        :param mode the profile.Mode object to process
        """
        assert(isinstance(mode, profile.Mode))
        tpl = Template(filename="templates/mode.tpl")
        self.code["decorator"].append(tpl.render(
            decorator=decorator_name(mode),
            mode=mode
        ))

        for input_type, input_items in mode._config.items():
            for entry in input_items.values():
                self.generate_input_item(entry, mode)

    def generate_input_item(self, input_item, mode):
        """Generates code for the provided profile.InputItem object.

        :param input_item profile.InpuItem object to processs into code
        :param mode the profile.Mode object corresponding to
            this input_item
        """
        assert(isinstance(input_item, profile.InputItem))
        assert(isinstance(mode, profile.Mode))
        assert(input_item.parent == mode)
        if len(input_item.actions) == 0:
            return {}

        input_type_templates = {
            InputType.JoystickAxis: "templates/axis.tpl",
            InputType.JoystickButton: "templates/button.tpl",
            InputType.JoystickHat: "templates/hat.tpl",
            InputType.Keyboard: "templates/key.tpl",
        }

        code = {
            "body": [],
            "global": [],
        }
        actions_to_code(input_item.actions, code)
        self.code["global"].extend(code["global"])

        tpl = Template(filename=input_type_templates[input_item.input_type])
        self.code["callback"].append(tpl.render(
            device_name=util.format_name(mode.parent.name),
            decorator=decorator_name(mode),
            mode=util.format_name(mode.name),
            input_item=input_item,
            code=code,
            param_list=generate_parameter_list(input_item)
        ))