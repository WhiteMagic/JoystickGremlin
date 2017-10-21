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

import gremlin


# CallbackData = collections.namedtuple(
#     "CallbackData",
#     [
#         "input_item",
#         "decorator_name",
#         "mode_index",
#         "parameter_list",
#         "device_name",
#         "code_block"
#     ]
# )


# DecoratorData = collections.namedtuple(
#     "DecoratorData",
#     [
#         "decorator_name",
#         "device_name"
#     ]
# )


# def decorator_name(mode, index):
#     """Returns the decorator name corresponding to the provided data.
#
#     :param mode the profile.Mode object for which to generate the name
#     :param index the index to use in the decorator name
#     :return name of the decorator matching the provided mode
#     """
#     assert(isinstance(mode, profile.Mode))
#     hid, wid = util.extract_ids(util.device_id(mode.parent))
#     if wid != -1:
#         return "{}_{}_{}".format(
#             util.format_name(mode.parent.name),
#             wid,
#             index
#         )
#     else:
#         return "{}_{}".format(
#             util.format_name(mode.parent.name),
#             index
#         )


# def generate_parameter_list(input_item):
#     """Generates the parameter list of a callback function.
#
#     :param input_item the item for whose actions to generate the
#         parameter list
#     :return string representation of the parameter list needed for the
#         provided input_item
#     """
#     params = []
#     vjoy_required = gremlin.plugin_manager.ActionPlugins() \
#         .plugins_requiring_parameter("vjoy")
#     for container in input_item.containers:
#         for action_set in container.action_sets:
#             for action in action_set:
#                 if type(action) in vjoy_required:
#                     params.append("vjoy")
#     params = list(set(params))
#     params.insert(0, "event")
#     return ", ".join(params)


# def input_item_identifier_string(input_item):
#     """Returns the identifier string for a given InputItem.
#
#     :param input_item the item for which to generate the identifier
#     :return identifier for this InputItem
#     """
#     hid, wid = util.extract_ids(util.device_id(input_item.parent.parent))
#     if wid != -1:
#         return "_{}".format(wid)
#     else:
#         return ""


class CodeGenerator:

    """Generates a Python script representing the entire configuration."""

    def __init__(self, config_profile):
        """Creates a new code generator for the given configuration.

        :param config_profile profile for which to generate code
        """
        self.code = ""
        self.generate_from_profile(config_profile)

    def generate_from_profile(self, config_profile):
        """Generates the code for the given configuration.

        :param config_profile the profile for which to generate the code
        """
        assert (isinstance(config_profile, gremlin.profile.Profile))

        # Create output by rendering it via the template system
        tpl_lookup = TemplateLookup(directories=["."])
        tpl = Template(
            filename="templates/gremlin_code.tpl",
            lookup=tpl_lookup
        )
        self.code = tpl.render(
            gremlin=gremlin,
            profile=config_profile,
        )

    def write_code(self, fname):
        """Writes the generated code to the given file.

        :param fname path to the file into which to write the code
        """
        code = re.sub("\r", "", self.code)
        with open(fname, "w") as out:
            out.write(code)
