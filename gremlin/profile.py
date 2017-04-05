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

import copy
import logging
import shutil
from abc import abstractmethod, ABCMeta
from xml.dom import minidom
from xml.etree import ElementTree

import action_plugins
from gremlin.common import DeviceType, InputType
from . import error, joystick_handling, plugin_manager, util


def tag_to_input_type(tag):
    """Returns the input type enum corresponding to the given XML tag.

    :param tag xml tag for which to return the InputType enum
    :return InputType enum corresponding to the given XML tag
    """
    lookup = {
        "axis": InputType.JoystickAxis,
        "button": InputType.JoystickButton,
        "hat": InputType.JoystickHat,
        "key": InputType.Keyboard,
    }
    if tag.lower() in lookup:
        return lookup[tag.lower()]
    else:
        raise error.ProfileError(
            "Invalid input type specified {}".format(tag)
        )


def input_type_to_tag(input_type):
    """Returns the tag corresponding to the given input type.

    :param input_type the input type to convert
    :return text representation of the input type
    """
    lookup = {
        InputType.JoystickAxis: "axis",
        InputType.JoystickButton: "button",
        InputType.JoystickHat: "hat",
        InputType.Keyboard: "key"
    }
    if input_type in lookup:
        return lookup[input_type]
    else:
        raise error.ProfileError(
            "Invalid input type specified {}".format(input_type)
        )


def type_name_to_device_type(type_name):
    """Returns the DeviceType representing the provided textual value.

    :param type_name the DeviceType textual representation
    :return DeviceType enum value
    """
    lookup = {
        "keyboard": DeviceType.Keyboard,
        "joystick": DeviceType.Joystick,
        "vjoy": DeviceType.VJoy
    }
    if type_name in lookup:
        return lookup[type_name]
    else:
        raise error.ProfileError(
            "Invalid device type specified {}".format(type_name)
        )


def mode_list(node):
    """Returns a list of all modes based on the given node.

    :param node a node from a profile tree
    :return list of mode names
    """
    # Get profile root node
    parent = node
    while parent.parent is not None:
        parent = parent.parent
    assert(type(parent) == Profile)
    # Generate list of modes
    mode_names = []
    for device in parent.devices.values():
        mode_names.extend(device.modes.keys())

    return sorted(list(set(mode_names)), key=lambda x: x.lower())


def device_type_to_type_name(device_type):
    """Returns the textual representation of a DeviceType enum entry.

    :param device_type DeviceType enum entry to convert to string
    :return textual representation of the provided DeviceType enum
    """
    lookup = {
        DeviceType.Keyboard: "keyboard",
        DeviceType.Joystick: "joystick",
        DeviceType.VJoy: "vjoy"
    }
    if device_type in lookup:
        return lookup[device_type]
    else:
        raise error.ProfileError(
            "Invalid DeviceType enum entry provided {}".format(device_type)
        )


def read_bool(node, key, default_value=False):
    """Attempts to read a boolean value.

    If there is an error when reading the given field from the node
    the default value is returned instead.

    :param node the node from which to read the value
    :param key the key to read from the node
    :param default_value the default value to return in case of errors
    """
    try:
        return parse_bool(node.get(key))
    except error.ProfileError:
        return default_value


def parse_bool(value):
    """Returns the boolean representation of the provided value.

    :param value the value as string to parse
    :return representation of value as either True or False
    """
    try:
        int_value = int(value)
        if int_value in [0, 1]:
            return int_value == 1
        else:
            raise error.ProfileError(
                "Invalid bool value used: {}".format(value)
            )
    except ValueError:
        if value.lower() in ["true", "false"]:
            return True if value.lower() == "true" else False
        else:
            raise error.ProfileError(
                "Invalid bool value used: {}".format(value)
            )
    except TypeError:
        raise error.ProfileError(
            "Invalid type provided: {}".format(type(value))
        )


def parse_float(value):
    """Returns the float representation of the provided value.

    :param value the value as string to parse
    :return representation of value as float
    """
    try:
        return float(value)
    except ValueError:
        raise error.ProfileError(
            "Invalid float value used: {}".format(value)
        )
    except TypeError:
        raise error.ProfileError(
            "Invalid type provided: {}".format(type(value))
        )


def extract_remap_actions(action_list):
    remap_actions = []
    for entry in action_list:
        if isinstance(entry, action_plugins.remap.Remap):
            remap_actions.append(entry)
    return remap_actions


class ProfileConverter:

    """Handle converting and checking profiles."""

    current_version = 3

    def __init__(self):
        pass

    def is_current(self, fname):
        """Returns whether or not the provided profile is current.

        :param fname path to the profile to evaluate
        """
        tree = ElementTree.parse(fname)
        root = tree.getroot()

        return self._determine_version(root) == ProfileConverter.current_version

    def convert_profile(self, fname):
        """Converts the provided profile to the current version.

        :param fname path to the profile to convert
        """
        # Load the profile
        tree = ElementTree.parse(fname)
        root = tree.getroot()

        # Check if a conversion is required
        if self.is_current(fname):
            return

        # Create a backup of the outdated profile
        old_version = self._determine_version(root)
        shutil.copyfile(fname, "{}.v{:d}".format(fname, old_version))

        # Convert the profile
        new_root = None
        if old_version == 1:
            new_root = self._convert_from_v1(root)
            new_root = self._convert_from_v2(new_root)
        if old_version == 2:
            new_root = self._convert_from_v2(root)

        if new_root is not None:
            # Save converted version
            ugly_xml = ElementTree.tostring(new_root, encoding="unicode")
            ugly_xml = "".join([line.strip() for line in ugly_xml.split("\n")])
            dom_xml = minidom.parseString(ugly_xml)
            with open(fname, "w") as out:
                out.write(dom_xml.toprettyxml(indent="    ", newl="\n"))

            util.display_error(
                "Profile has been converted, please check the error log for "
                "potential issues."
            )
        else:
            raise error.ProfileError("Failed to convert profile")

    def _determine_version(self, root):
        """Returns the version of the provided profile.

        :param root root node of the profile to determine the version of
        :return version of the profile
        """
        if root.tag == "devices" and int(root.get("version")) == 1:
            return 1
        elif root.tag == "profile" and int(root.get("version")) == 2:
            return 2
        elif root.tag == "profile" and int(root.get("version")) == 3:
            return 3
        else:
            raise error.ProfileError(
                "Invalid profile version encountered"
            )

    def _convert_from_v1(self, root):
        """Converts v1 profiles to v2 profiles.

        :param root the v1 profile
        :return v2 representation of the profile
        """
        new_root = ElementTree.Element("profile")
        new_root.set("version", "2")

        # Device entries
        devices = ElementTree.Element("devices")
        for node in root.iter("device"):
            # Modify each node to include the correct type attribute
            if node.get("name") == "keyboard" and \
                    int(node.get("windows_id")) == 0:
                node.set("type", "keyboard")
            else:
                node.set("type", "joystick")
            devices.append(node)

        new_root.append(devices)

        # Module imports
        for node in root.iter("import"):
            new_root.append(node)

        return new_root

    def _convert_from_v2(self, root):
        """Converts v2 profiles to v3 profiles.

        :param root the v2 profile
        :return v3 representation of the profile
        """
        # Get hardware ids of the connected devices
        device_name_map = {}
        for device in joystick_handling.joystick_devices():
            device_name_map[device.name] = device.hardware_id

        # Fix the device entries in the provided document
        new_root = copy.deepcopy(root)
        new_root.set("version", "3")
        for device in new_root.iter("device"):
            if device.get("type") == "joystick":
                if device.get("name") in device_name_map:
                    device.set("id", str(device_name_map[device.get("name")]))
                else:
                    logging.getLogger("system").warning(
                        "Device '{}' missing, no conversion performed, ID"
                        " will be incorrect.".format(device.get("name"))
                    )
        return new_root


class Profile:

    """Stores the contents of an entire configuration profile.

    This includes configurations for each device's modes.
    """

    def __init__(self):
        """Constructor creating a new instance."""
        self.devices = {}
        self.vjoy_devices = {}
        self.imports = []
        self.merge_axes = []
        self.parent = None

    def initialize_joystick_device(self, device, modes):
        new_device = Device(self)
        new_device.name = device.name
        new_device.hardware_id = device.hardware_id
        new_device.windows_id = device.windows_id
        new_device.type = DeviceType.Joystick
        self.devices[util.device_id(new_device)] = new_device

        for mode in modes:
            new_device.ensure_mode_exists(mode)
            new_mode = new_device.modes[mode]
            for id in range(1, device.axes+1):
                new_mode.get_data(InputType.JoystickAxis, id)
            for id in range(1, device.buttons+1):
                new_mode.get_data(InputType.JoystickButton, id)
            for id in range(1, device.hats+1):
                new_mode.get_data(InputType.JoystickHat, id)

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
        for entry in vjoy_data:
            vjoy[entry.vjoy_id] = {"axis": [], "button": [], "hat": []}
            # TODO: the axis need not be sequential
            for i in range(entry.axes):
                vjoy[entry.vjoy_id]["axis"].append(i+1)
            for i in range(entry.buttons):
                vjoy[entry.vjoy_id]["button"].append(i+1)
            for i in range(entry.hats):
                vjoy[entry.vjoy_id]["hat"].append(i+1)

        # List all input types
        all_input_types = [
            InputType.JoystickAxis,
            InputType.JoystickButton,
            InputType.JoystickHat,
            InputType.Keyboard
        ]

        # Create a list of all used remap actions
        remap_actions = []
        for dev in self.devices.values():
            for mode in dev.modes.values():
                for input_type in all_input_types:
                    for item in mode.config[input_type].values():
                        for container in item.actions:
                            remap_actions.extend(
                                extract_remap_actions(container.actions)
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
        # Check for outdated profile structure and warn user / convert
        profile_converter = ProfileConverter()
        if not profile_converter.is_current(fname):
            logging.getLogger("system").warning("Outdated profile, converting")
            profile_converter.convert_profile(fname)

        tree = ElementTree.parse(fname)
        root = tree.getroot()

        # Parse each device into separate DeviceConfiguration objects
        for child in root.iter("device"):
            device = Device(self)
            device.from_xml(child)
            self.devices[util.device_id(device)] = device
        # Parse each vjoy device into separate DeviceConfiguration objects
        for child in root.iter("vjoy-device"):
            device = Device(self)
            device.from_xml(child)
            self.vjoy_devices[device.hardware_id] = device

        # Ensure that the profile contains an entry for every existing
        # device even if it was not part of the loaded XML and
        # replicate the modes present in the profile. This adds both entries
        # for physical and virtual joysticks.
        devices = joystick_handling.joystick_devices()
        for dev in devices:
            add_device = False
            if dev.is_virtual and dev.vjoy_id not in self.vjoy_devices:
                add_device = True
            elif not dev.is_virtual and \
                    util.device_id(dev) not in self.devices:
                add_device = True

            if add_device:
                new_device = Device(self)
                new_device.name = dev.name
                if dev.is_virtual:
                    new_device.type = DeviceType.VJoy
                    new_device.hardware_id = dev.vjoy_id
                    new_device.windows_id = dev.vjoy_id
                    self.vjoy_devices[dev.vjoy_id] = new_device
                else:
                    new_device.type = DeviceType.Joystick
                    new_device.hardware_id = dev.hardware_id
                    new_device.windows_id = dev.windows_id
                    self.devices[util.device_id(new_device)] = new_device

                # Create required modes
                for mode in mode_list(new_device):
                    if mode not in new_device.modes:
                        new_device.modes[mode] = Mode(new_device)
                        new_device.modes[mode].name = mode

        # Parse list of user modules to import
        for child in root.iter("import"):
            for entry in child:
                self.imports.append(entry.get("name"))

        # Parse merge axis entries
        for child in root.iter("merge-axis"):
            self.merge_axes.append(self._parse_merge_axis(child))

    def to_xml(self, fname):
        """Generates XML code corresponding to this profile.

        :param fname name of the file to save the XML to
        """
        # Generate XML document
        root = ElementTree.Element("profile")
        root.set("version", "3")

        # Device settings
        devices = ElementTree.Element("devices")
        for device in self.devices.values():
            devices.append(device.to_xml())
        root.append(devices)

        # VJoy settings
        vjoy_devices = ElementTree.Element("vjoy-devices")
        for device in self.vjoy_devices.values():
            vjoy_devices.append(device.to_xml())
        root.append(vjoy_devices)

        # Module imports
        import_node = ElementTree.Element("import")
        for entry in self.imports:
            node = ElementTree.Element("module")
            node.set("name", entry)
            import_node.append(node)
        root.append(import_node)

        # Merge axis data
        for entry in self.merge_axes:
            node = ElementTree.Element("merge-axis")
            node.set("mode", str(entry["mode"]))
            for tag in ["vjoy"]:
                sub_node = ElementTree.Element(tag)
                sub_node.set("device", str(entry[tag]["device_id"]))
                sub_node.set("axis", str(entry[tag]["axis_id"]))
                node.append(sub_node)
            for tag in ["lower", "upper"]:
                sub_node = ElementTree.Element(tag)
                sub_node.set("id", str(entry[tag]["hardware_id"]))
                sub_node.set("windows_id", str(entry[tag]["windows_id"]))
                sub_node.set("axis", str(entry[tag]["axis_id"]))
                node.append(sub_node)
            root.append(node)

        # Serialize XML document
        ugly_xml = ElementTree.tostring(root, encoding="unicode")
        dom_xml = minidom.parseString(ugly_xml)
        with open(fname, "w") as out:
            out.write(dom_xml.toprettyxml(indent="    "))

    def get_device_modes(self, device_id, device_type, device_name=None):
        """Returns the modes associated with the given device.

        :param device_id the key composed of hardware and windows id
        :param device_type the type of the device being queried
        :param device_name the name of the device
        :return all modes for the specified device
        """
        if device_type == DeviceType.VJoy:
            if device_id not in self.vjoy_devices:
                # Create the device
                device = Device(self)
                device.name = device_name
                device.hardware_id = device_id
                device.windows_id = device_id
                device.type = DeviceType.VJoy
                self.vjoy_devices[device_id] = device
            return self.vjoy_devices[device_id]

        else:
            if device_id not in self.devices:
                # Create the device
                hid, wid = util.extract_ids(device_id)
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

    def _parse_merge_axis(self, node):
        """Parses merge axis entries.

        :param node the node to process
        :return merge axis data structure parsed from the XML node
        """
        entry = {
            "mode": node.get("mode", None)
        }
        for tag in ["vjoy"]:
            entry[tag] = {
                "device_id": int(node.find(tag).get("device")),
                "axis_id": int(node.find(tag).get("axis"))
            }
        for tag in ["lower", "upper"]:
            entry[tag] = {
                "hardware_id": int(node.find(tag).get("id")),
                "windows_id": int(node.find(tag).get("windows_id")),
                "axis_id": int(node.find(tag).get("axis"))
            }

        # If we have duplicate devices check if this device is a duplicate, if
        # not fix the windows_id in case it no longer matches
        if util.g_duplicate_devices:
            device_counts = {}
            windows_ids = {}
            for dev in joystick_handling.joystick_devices():
                device_counts[dev.hardware_id] = \
                    device_counts.get(dev.hardware_id, 0) + 1
                windows_ids[dev.hardware_id] = dev.windows_id

            for tag in ["lower", "upper"]:
                # Only one device exists, override system id
                if device_counts.get(entry[tag]["hardware_id"], 0) == 1:
                    entry[tag]["windows_id"] = \
                        windows_ids[entry[tag]["hardware_id"]]

        return entry


class Device:

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

    def ensure_mode_exists(self, mode_name, device=None):
        if mode_name in self.modes:
            mode = self.modes[mode_name]
        else:
            mode = Mode(self)
            mode.name = mode_name
            self.modes[mode.name] = mode

        if device is not None:
            for id in range(1, device.axes + 1):
                mode.get_data(InputType.JoystickAxis, id)
            for id in range(1, device.buttons + 1):
                mode.get_data(InputType.JoystickButton, id)
            for id in range(1, device.hats + 1):
                mode.get_data(InputType.JoystickHat, id)

    def from_xml(self, node):
        """Populates this device based on the xml data.

        :param node the xml node to parse to populate this device
        """
        self.name = node.get("name")
        self.hardware_id = int(node.get("id"))
        self.windows_id = int(node.get("windows_id"))
        self.type = type_name_to_device_type(node.get("type"))

        # If we have duplicate devices check if this device is a duplicate, if
        # not fix the windows_id in case it no longer matches
        if util.g_duplicate_devices and self.type == DeviceType.Joystick:
            device_counts = {}
            windows_ids = {}
            for dev in joystick_handling.joystick_devices():
                device_counts[dev.hardware_id] = \
                    device_counts.get(dev.hardware_id, 0) + 1
                windows_ids[dev.hardware_id] = dev.windows_id
            if device_counts.get(self.hardware_id, 0) == 1:
                self.windows_id = windows_ids[self.hardware_id]

        for child in node:
            mode = Mode(self)
            mode.from_xml(child)
            self.modes[mode.name] = mode

    def to_xml(self):
        """Returns a XML node representing this device's contents.

        :return xml node of this device's contents
        """
        node_tag = "device" if self.type != DeviceType.VJoy else "vjoy-device"
        node = ElementTree.Element(node_tag)
        node.set("name", self.name)
        node.set("id", str(self.hardware_id))
        node.set("windows_id", str(self.windows_id))
        node.set("type", device_type_to_type_name(self.type))
        for mode in self.modes.values():
            node.append(mode.to_xml())
        return node


class Mode:

    """Represents the configuration of the mode of a single device."""

    def __init__(self, parent):
        """Creates a new DeviceConfiguration instance.

        :param parent the parent device of this mode
        """
        self.parent = parent
        self.inherit = None
        self.name = None

        self.config = {
            InputType.JoystickAxis: {},
            InputType.JoystickButton: {},
            InputType.JoystickHat: {},
            InputType.Keyboard: {}
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
            self.config[item.input_type][item.input_id] = item

    def to_xml(self):
        """Generates XML code for this DeviceConfiguration.

        :return XML node representing this object's data
        """
        node = ElementTree.Element("mode")
        node.set("name", self.name)
        if self.inherit is not None:
            node.set("inherit", self.inherit)
        for input_items in self.config.values():
            for item in input_items.values():
                node.append(item.to_xml())
        return node

    def delete_data(self, input_type, input_id):
        """Deletes the data associated with the provided
        input item entry.

        :param input_type the type of the input
        :param input_id the index of the input
        """
        if input_id in self.config[input_type]:
            del self.config[input_type][input_id]

    def get_data(self, input_type, input_id):
        """Returns the configuration data associated with the provided
        InputItem entry.

        :param input_type the type of input
        :param input_id the id of the given input type
        :return InputItem corresponding to the provided combination of
            type and id
        """
        assert(input_type in self.config)
        if input_id not in self.config[input_type]:
            entry = InputItem(self)
            entry.input_type = input_type
            entry.input_id = input_id
            self.config[input_type][input_id] = entry
        return self.config[input_type][input_id]

    def set_data(self, input_type, input_id, data):
        """Sets the data of an InputItem.

        :param input_type the type of the InputItem
        :param input_id the id of the InputItem
        :param data the data of the InputItem
        """
        assert(input_type in self.config)
        self.config[input_type][input_id] = data

    def has_data(self, input_type, input_id):
        """Returns True if data for the given input exists, False otherwise.

        :param input_type the type of the InputItem
        :param input_id the id of the InputItem
        :return True if data exists, False otherwise
        """
        return input_id in self.config[input_type]


class InputItem:

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
        container_name_map = plugin_manager.ContainerPlugins().tag_map
        self.input_type = tag_to_input_type(node.tag)
        self.input_id = int(node.get("id"))
        self.description = node.get("description")
        self.always_execute = parse_bool(node.get("always-execute", "False"))
        if self.input_type == InputType.Keyboard:
            self.input_id = (self.input_id, parse_bool(node.get("extended")))
        for child in node:
            # if child.tag not in action_name_map:
            #     logging.getLogger("system").warning(
            #         "Unknown node present: {}".format(child.tag)
            #     )
            #     continue
            # entry = action_name_map[child.tag](self)
            # entry.from_xml(child)
            container_type = child.attrib["type"]
            if container_type not in container_name_map:
                logging.getLogger("system").warning(
                    "Unknown container type used: {}".format(container_type)
                )
                continue
            entry = container_name_map[container_type](self)
            entry.from_xml(child)
            self.actions.append(entry)

    def to_xml(self):
        """Generates a XML node representing this object's data.

        :return XML node representing this object
        """
        node = ElementTree.Element(
            action_plugins.common.input_type_to_tag(self.input_type)
        )
        if self.input_type == InputType.Keyboard:
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
            if entry.is_valid():
                node.append(entry.to_xml())

        return node

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        """Returns the hash of this input item.

        The hash takes into account to which device and mode the input item is
        bound.

        :return hash of this InputItem instance
        """
        device_id = util.device_id(self.parent.parent)
        mode = self.parent.name

        return hash((device_id, mode, self.input_type, self.input_id))


class CodeBlock:

    def __init__(self, body_code="", static_code=""):
        self._body = body_code
        self._static = static_code

    @property
    def body(self):
        return self._body

    @property
    def static(self):
        return self._static

    def append(self, other):
        self._body += other.body
        self._static += other.static


class ProfileData(metaclass=ABCMeta):

    """Base class for all items holding profile data.

    This is primarily used for containers and actions to represent their
    configuration and to easily load, store, and generate code from them.
    """

    # Monotonically increasing counter for unique ids
    next_code_id = 0

    def __init__(self, parent):
        """Creates a new instance.

        :param parent the parent item of this instance in the profile tree
        """
        self.parent = parent

    def from_xml(self, node):
        """Initializes this node's values based on the provided XML node.

        :param node the XML node to use to populate this instance
        """
        self._parse_xml(node)

    def to_xml(self):
        """Returns the XML representation of this instance.

        :return XML representation of this instance
        """
        return self._generate_xml()

    def to_code(self):
        """Generates the code to execute the behaviour of this instance.

        :return code representing this instance's behaviour
        """
        code = self._generate_code()
        assert isinstance(code, CodeBlock)
        ProfileData.next_code_id += 1
        return code

    def is_valid(self):
        return self._is_valid()

    def get_input_type(self):
        item = self.parent
        while not isinstance(item, InputItem):
            item = item.parent
        return item.input_type

    @abstractmethod
    def _parse_xml(self, node):
        """Implementation of the XML parsing.

        :param node the XML node to use to populate this instance
        """
        pass

    @abstractmethod
    def _generate_xml(self):
        """Implementation of the XML generation.

        :return XML representation of this instance
        """
        pass

    @abstractmethod
    def _generate_code(self):
        """Implementation of the code generation.

        :return code representing this instance's behaviour
        """
        pass

    @abstractmethod
    def _is_valid(self):
        pass
