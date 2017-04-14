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
from . import common, error, joystick_handling, profile, util


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


def list_to_string(params):
    """Returns a textual representing of a list.

    :param params the parameters to turn into a lists
    :return textual representation of the parameters
    """
    if len(params) == 0:
        return ""
    elif len(params) == 1:
        return "\"{0}\"".format(params[0])
    else:
        return "[" + ", ".join(["\"{0}\"".format(v) for v in params]) + "]"


def string_to_bool(text):
    """Returns text into a boolean variable.

    :param text the text to convert
    :return bool representing the text
    """
    return text.lower() in ["true", "yes", "t", "1"]


def coords_to_string(container):
    """Returns a textual representation of a sequence of coordinates.

    :param container container holding the coordinates
    :return textual representing of the coordinates
    """
    return "[{}]".format(", ".join(
        ["({:.4f}, {:.4f})".format(e[0], e[1]) for e in container])
    )


# Dictionary containing template helper functions
template_helpers = {
    # "format_condition": format_condition,
    "list_tostring": list_to_string,
    "string_to_bool": string_to_bool,
    "coords_to_string": coords_to_string,
}


class CodeGeneratorV2:

    def __init__(self, config_profile):
        self.decorators = {}
        self.setup = []
        self.callbacks = {}

        self.code = ""
        try:
            self.generate_from_profile(config_profile)
        except error.GremlinError as err:
            util.display_error(str(err))

    def generate_from_profile(self, config_profile):
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
        code = re.sub("\r", "", self.code)
        with open(fname, "w") as out:
            out.write(code)

    def _process_device(self, device):
        for i, mode in enumerate(device.modes.values()):
            self._process_mode(mode, i)

    def _process_mode(self, mode, index):
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
        # Grab required information
        mode = input_item.parent
        device_id = util.device_id(mode.parent)

        # Abort if there are no actions associated with this item
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
                if "setup" in code.keys():
                    self.setup.append(action.to_code().setup)

    def _reset_code_cache(self, config_profile):
        for device in config_profile.devices.values():
            for mode in device.modes.values():
                for input_items in mode.config.values():
                    for input_item in input_items.values():
                        for container in input_item.containers:
                            container.code = None
                            for action in container.actions:
                                action.code = None


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
        vjoy_ids = []
        for joy in joystick_handling.joystick_devices():
            if joy.is_virtual:
                vjoy_ids.append(joy.vjoy_id)

        tpl = Template(filename="templates/vjoy_curves.tpl")
        self.code["global"].append(tpl.render(
            vjoy_devices=config_profile.vjoy_devices,
            vjoy_ids=vjoy_ids,
            UiInputType=gremlin.common.InputType
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
            decorator_map=self.decorator_map,
            get_device_id=util.get_device_id
        ))

        # Account for axis merging needing certain decorators which otherwise
        # might appear unused
        dev_id_lower = util.get_device_id(
            entry["lower"]["hardware_id"],
            entry["lower"]["windows_id"]
        )
        dev_id_upper = util.get_device_id(
            entry["upper"]["hardware_id"],
            entry["upper"]["windows_id"]
        )
        self.decorator_usage_counts[dev_id_lower][entry["mode"]] += 1
        self.decorator_usage_counts[dev_id_upper][entry["mode"]] += 1

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
            common.InputType.JoystickAxis: "templates/axis.tpl",
            common.InputType.JoystickButton: "templates/button_callback.tpl",
            common.InputType.JoystickHat: "templates/hat.tpl",
            common.InputType.Keyboard: "templates/key.tpl",
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
            #code=code,
            code_blocks=code["body"],
            param_list=generate_parameter_list(input_item),
            helpers=helpers,
            gremlin=gremlin
        ))
