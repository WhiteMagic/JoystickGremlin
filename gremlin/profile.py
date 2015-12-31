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

import enum
from xml.etree import ElementTree
from xml.dom import minidom

import action
import gremlin
from gremlin.common import UiInputType


def tag_to_input_type(tag):
    """Returns the input type enum corresponding to the given XML tag.

    :param tag xml tag for which to return the InputType enum
    :return InputType enum corresponding to the given XML tag
    """
    lookup = {
        "axis": UiInputType.JoystickAxis,
        "button": UiInputType.JoystickButton,
        "hat": UiInputType.JoystickHat,
        "key": UiInputType.Keyboard,
    }
    if tag.lower() in lookup:
        return lookup[tag.lower()]
    else:
        raise gremlin.error.ProfileError(
            "Invalid input type specified {}".format(tag)
        )


def input_type_to_tag(input_type):
    """Returns the tag corresponding to the given input tpye.

    :param input_type the input type to convert
    :return text representation of the input type
    """
    lookup = {
        UiInputType.JoystickAxis: "axis",
        UiInputType.JoystickButton: "button",
        UiInputType.JoystickHat: "hat",
        UiInputType.Keyboard: "key"
    }
    if input_type in lookup:
        return lookup[input_type]
    else:
        raise gremlin.error.ProfileError(
            "Invalid input type specified {}".format(input_type)
        )


def _parse_bool(value):
    """Returns the boolean representation of the provided value.

    :param value the value as string to parse
    :return representation of value as either True or False
    """
    try:
        int_value = int(value)
        if int_value in [0, 1]:
            return int_value == 1
        else:
            raise gremlin.error.ProfileError(
                "Invalid bool value used: {}".format(value)
            )
    except ValueError:
        if value.lower() in ["true", "false"]:
            return True if value.lower() == "true" else False
        else:
            raise gremlin.error.ProfileError(
                "Invalid bool value used: {}".format(value)
            )
    except TypeError:
        raise gremlin.error.ProfileError(
            "Invalid type provided: {}".format(type(value))
        )


action_lookup = {
    # Input actions
    "macro": action.macro.Macro,
    "remap": action.remap.Remap,
    "response-curve": action.response_curve.ResponseCurve,
    # Control actions
    "cycle-modes": action.mode_control.CycleModes,
    "pause-action": action.pause_resume.PauseAction,
    "resume-action": action.pause_resume.ResumeAction,
    "toggle-pause-resume-action": action.pause_resume.TogglePauseResumeAction,
    "switch-mode": action.mode_control.SwitchMode,
    "switch-to-previous-mode": action.mode_control.SwitchPreviousMode,
    # Other actions
    "text-to-speech": action.text_to_speech.TextToSpeech,
}


def create_action(type_name, input_item):
    """Creates an action object of the requested type.

    :param type_name name of the action to create
    :param input_item the item with which to associated the action
    :return the requested action
    """
    return action_lookup[type_name](input_item)


class DeviceType(enum.Enum):

    """Enumeration of the different possible input types."""

    Keyboard = 1
    Joystick = 2


class Profile(object):

    """Stores the contents of an entire configuration profile.

    This includes configurations for each device's modes.
    """

    def __init__(self):
        """Constructor creating a new instance."""
        self.devices = {}
        self.imports = []
        self.parent = None

    def build_inheritance_tree(self):
        """Returns a tree structure encoding the inheritance between the
        various modes.

        :return tree encoding mode inheritance
        """
        tree = {}
        for dev_id, device in self.devices.items():
            for mode_name, mode in device.modes.items():
                if mode.inherit is None and mode_name not in tree:
                    tree[mode_name] = {}
                elif mode.inherit:
                    stack = [mode_name, ]
                    parent = device.modes[mode.inherit]
                    stack.append(parent.name)
                    while parent.inherit is not None:
                        parent = device.modes[parent.inherit]
                        stack.append(parent.name)

                    stack = list(reversed(stack))
                    branch = tree
                    for entry in stack:
                        if entry not in branch:
                            branch[entry] = {}
                        branch = branch[entry]

        return tree

    def get_root_modes(self):
        """Returns a list of root modes.

        :return list of root modes
        """
        root_modes = []
        for device in self.devices.values():
            if device.type != DeviceType.Keyboard:
                continue
            for mode_name, mode in device.modes.items():
                if mode.inherit is None:
                    root_modes.append(mode_name)
        return list(set(root_modes))

    def list_unused_vjoy_inputs(self, vjoy_data):
        """Returns a list of unused vjoy inputs for the given profile.

        :param vjoy_data vjoy devices information
        :return dictionary of unused inputs for each input type
        """
        # Create list of all inputs provided by the vjoy devices
        vjoy = {}
        for i, entry in enumerate(vjoy_data):
            vjoy[i+1] = {"axis": [], "button": [], "hat": []}
            for j in range(entry.axes):
                vjoy[i+1]["axis"].append(j+1)
            for j in range(entry.buttons):
                vjoy[i+1]["button"].append(j+1)
            for j in range(entry.hats):
                vjoy[i+1]["hat"].append(j+1)

        # Create a list of all used remap actions
        remap_actions = []
        for dev in self.devices.values():
            for mode in dev.modes.values():
                for item in mode._config[UiInputType.JoystickAxis].values():
                    remap_actions.extend(
                        [e for e in item.actions if isinstance(e, action.remap.Remap)]
                    )
                for item in mode._config[UiInputType.JoystickButton].values():
                    remap_actions.extend(
                        [e for e in item.actions if isinstance(e, action.remap.Remap)]
                    )
                for item in mode._config[UiInputType.JoystickHat].values():
                    remap_actions.extend(
                        [e for e in item.actions if isinstance(e, action.remap.Remap)]
                    )

        # Remove all remap actions from the list of available inputs
        for act in remap_actions:
            type_name = input_type_to_tag(act.input_type)
            if act.vjoy_input_id in [0, None] \
                    or act.vjoy_device_id in [0, None] \
                    or act.vjoy_input_id not in vjoy[act.vjoy_device_id][type_name]:
                continue
            idx = vjoy[act.vjoy_device_id][type_name].index(act.vjoy_input_id)
            del vjoy[act.vjoy_device_id][type_name][idx]

        return vjoy

    def from_xml(self, fname):
        """Parses the global XML document into the profile data structure.

        :param fname the path to the XML file to parse
        """
        tree = ElementTree.parse(fname)
        root = tree.getroot()

        # Parse each device into separate DeviceConfiguration objects
        for child in root.iter("device"):
            device = Device(self)
            device.from_xml(child)
            self.devices[gremlin.util.device_id(device)] = device

        # Ensure that the profile contains an entry for every existing
        # device even if it was not part of the loaded XML and
        # replicate the modes present in the profile.
        devices = gremlin.util.joystick_devices()
        for dev in devices:
            if not dev.is_virtual and gremlin.util.device_id(dev) not in self.devices:
                new_device = Device(self)
                new_device.name = dev.name
                new_device.hardware_id = dev.hardware_id
                new_device.windows_id = dev.windows_id
                new_device.type = DeviceType.Joystick
                self.devices[gremlin.util.device_id(new_device)] = new_device

                # Create required modes
                mode_list = gremlin.util.mode_list(new_device)
                for mode in mode_list:
                    if mode not in new_device.modes:
                        new_device.modes[mode] = Mode(new_device)
                        new_device.modes[mode].name = mode

        # Parse list of user modules to import
        for child in root.iter("import"):
            for entry in child:
                self.imports.append(entry.get("name"))

    def to_xml(self, fname):
        """Generates XML code corresponding to this profile.

        :param fname name of the file to save the XML to
        """
        # Generate XML document
        root = ElementTree.Element("devices")
        root.set("version", "1")
        for device in self.devices.values():
            root.append(device.to_xml())
        import_node = ElementTree.Element("import")
        for entry in self.imports:
            node = ElementTree.Element("module")
            node.set("name", entry)
            import_node.append(node)
        root.append(import_node)

        # Serialize XML document
        ugly_xml = ElementTree.tostring(root, encoding="unicode")
        dom_xml = minidom.parseString(ugly_xml)
        with open(fname, "w") as out:
            out.write(dom_xml.toprettyxml(indent="    "))

    def get_device_modes(self, device_id, device_name=None):
        """Returns the modes associated with the given device.

        :param device_id the key composed of hardware and windows id
        :param device_name the name of the device
        :return all modes for the specified device
        """
        if device_id not in self.devices:
            # Create the device
            hid, wid = gremlin.util.extract_ids(device_id)
            device = Device(self)
            device.name = device_name
            device.hardware_id = hid
            device.windows_id = wid

            # Set the correct device type
            device.type = DeviceType.Joystick
            if device_name == "keyboard":
                device.type = DeviceType.Keyboard
            self.devices[device_id] = device
        return self.devices[device_id]


class Device(object):

    """Stores the information about a single device including it's modes."""

    def __init__(self, parent):
        """Creates a new instance.

        :param parent the parent profile of this device
        """
        self.parent = parent
        self.name = None
        self.hardware_id = None
        self.windows_id = None
        self.modes = {}
        self.type = None

    def ensure_mode_exists(self, mode_name):
        if mode_name in self.modes:
            return
        mode = Mode(self)
        mode.name = mode_name
        self.modes[mode.name] = mode

    def from_xml(self, node):
        """Populates this device based on the xml data.

        :param node the xml node to parse to populate this device
        """
        self.name = node.get("name")
        self.hardware_id = int(node.get("id"))
        self.windows_id = int(node.get("windows_id"))
        if self.name == "keyboard" and self.hardware_id == 0:
            self.type = DeviceType.Keyboard
        else:
            self.type = DeviceType.Joystick

        for child in node:
            mode = Mode(self)
            mode.from_xml(child)
            self.modes[mode.name] = mode

    def to_xml(self):
        """Returns a XML node representing this device's contents.

        :return xml node of this device's contents
        """
        node = ElementTree.Element("device")
        node.set("name", self.name)
        node.set("id", str(self.hardware_id))
        node.set("windows_id", str(self.windows_id))
        for mode in self.modes.values():
            node.append(mode.to_xml())
        return node


class Mode(object):

    """Represents the configuration of the mode of a single device."""

    def __init__(self, parent):
        """Creates a new DeviceConfiguration instance.

        :param parent the parent device of this mode
        """
        self.parent = parent
        self.inherit = None
        self.name = None

        self._config = {
            UiInputType.JoystickAxis: {},
            UiInputType.JoystickButton: {},
            UiInputType.JoystickHat: {},
            UiInputType.Keyboard: {}
        }

    def from_xml(self, node):
        """Parses the XML mode data.

        :param node XML node to parse
        """
        self.name = node.get("name")
        self.inherit = node.get("inherit", None)
        for child in node:
            item = InputItem(self)
            item.from_xml(child)
            self._config[item.input_type][item.input_id] = item

    def to_xml(self):
        """Generates XML code for this DeviceConfiguration.

        :return XML node representing this object's data
        """
        node = ElementTree.Element("mode")
        node.set("name", self.name)
        if self.inherit is not None:
            node.set("inherit", self.inherit)
        for input_items in self._config.values():
            for item in input_items.values():
                node.append(item.to_xml())
        return node

    def delete_data(self, input_type, input_id):
        """Deletes the data associated with the provided
        input item entry.

        :param input_type the type of the input
        :param input_id the index of the input
        """
        if input_id in self._config[input_type]:
            del self._config[input_type][input_id]

    def get_data(self, input_type, input_id):
        """Returns the configuration data associated with the provided
        InputItem entry.

        :param input_type the type of input
        :param input_id the id of the given input type
        :return InputItem corresponding to the provided combination of
            type and id
        """
        assert(input_type in self._config)
        if input_id not in self._config[input_type]:
            entry = InputItem(self)
            entry.input_type = input_type
            entry.input_id = input_id
            self._config[input_type][input_id] = entry
        return self._config[input_type][input_id]

    def set_data(self, input_type, input_id, data):
        """Sets the data of an InputItem.

        :param input_type the type of the InputItem
        :param input_id the id of the InputItem
        :param data the data of the InputItem
        """
        assert(input_type in self._config)
        self._config[input_type][input_id] = data

    def has_data(self, input_type, input_id):
        """Returns True if data for the given input exists, False otherwise.

        :param input_type the type of the InputItem
        :param input_id the id of the InputItem
        :return True if data exists, False otherwise
        """
        return input_id in self._config[input_type]


class InputItem(object):

    """Represents a single input item such as a button or axis."""

    def __init__(self, parent):
        """Creates a new InputItem instance.

        :param parent the parent mode of this input item
        """
        self.parent = parent
        self.input_type = None
        self.input_id = None
        self.always_execute = False
        self.description = ""
        self.actions = []

    def from_xml(self, node):
        """Parses an InputItem node.

        :param node XML node to parse
        """
        self.input_type = tag_to_input_type(node.tag)
        self.input_id = int(node.get("id"))
        self.description = node.get("description")
        self.always_execute = _parse_bool(node.get("always-execute", "False"))
        if self.input_type == UiInputType.Keyboard:
            self.input_id = (self.input_id, _parse_bool(node.get("extended")))
        for child in node:
            if child.tag not in action_lookup:
                print("Unknown node: ", child.tag)
                continue
            entry = action_lookup[child.tag](self)
            entry.from_xml(child)
            self.actions.append(entry)

    def to_xml(self):
        """Generates a XML node representing this object's data.

        :return XML node representing this object
        """
        node = ElementTree.Element(
            action.common.input_type_to_tag(self.input_type)
        )
        if self.input_type == UiInputType.Keyboard:
            node.set("id", str(self.input_id[0]))
            node.set("extended", str(self.input_id[1]))
        else:
            node.set("id", str(self.input_id))

        if self.always_execute:
            node.set("always-execute", "True")

        if self.description:
            node.set("description", self.description)
        else:
            node.set("description", "")

        for entry in self.actions:
            node.append(entry.to_xml())

        return node
