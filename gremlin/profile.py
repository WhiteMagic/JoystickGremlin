# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2018 Lionel Ott
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

import codecs
import collections
import copy
import logging
import shutil
from abc import abstractmethod, ABCMeta
import os
from xml.dom import minidom
from xml.etree import ElementTree

import action_plugins
from gremlin.common import DeviceType, InputType, VariableType
from . import base_classes, common, error, joystick_handling, \
    plugin_manager, util


# Data struct representing profile information of a device
ProfileDeviceInformation = collections.namedtuple(
    "ProfileDeviceInformation",
    ["device_id", "name", "containers", "conditions", "merge_axis"]
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


def safe_read(node, key, type_cast=None, default_value=None):
    """Safely reads an attribute from an XML node.

    If the attempt at reading the attribute fails, due to the attribute not
    being present, an exception will be thrown.

    :param node the XML node from which to read an attribute
    :param key the attribute to read
    :param type_cast the type to which to cast the read value, if specified
    :param default_value value to return in case the key is not present
    :return the value stored in the node with the given key
    """
    # Attempt to read the value and if present use the provided default value
    # in case reading fails
    value = default_value
    if key not in node.keys():
        if default_value is None:
            msg = "Attempted to read attribute '{}' which does not exist.".format(key)
            logging.getLogger("system").error(msg)
            raise error.ProfileError(msg)
    else:
        value = node.get(key)

    if type_cast is not None:
        try:
            value = type_cast(value)
        except ValueError:
            msg = "Failed casting '{}' to type '{}'".format(
                value, str(type_cast)
            )
            logging.getLogger("system").error(msg)
            raise error.ProfileError(msg)
    return value


def safe_format(value, data_type, formatter=str):
    """Returns a formatted value ensuring type correctness.

    This function ensures that the value being formated is of correct type
    before attempting formatting. Raises an exception on non-matching data
    types.

    :param value the value to format
    :param data_type expected data type of the value
    :param formatter function to format value with
    :return value formatted according to formatter
    """
    if isinstance(value, data_type):
        return formatter(value)
    else:
        raise error.ProfileError("Value \"{}\" has type {} when {} is expected".format(
            value,
            type(value),
            data_type
        ))


def extract_remap_actions(action_sets):
    """Returns a list of remap actions from a list of actions.

    :param action_sets set of actions from which to extract Remap actions
    :return list of Remap actions contained in the provided list of actions
    """
    remap_actions = []
    for actions in [a for a in action_sets if a is not None]:
        for action in actions:
            if isinstance(action, action_plugins.remap.Remap):
                remap_actions.append(action)
    return remap_actions


class ProfileConverter:

    """Handle converting and checking profiles."""

    # Current profile version number
    current_version = 7

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
            new_root = self._convert_from_v3(new_root)
            new_root = self._convert_from_v4(new_root)
            new_root = self._convert_from_v5(new_root)
            new_root = self._convert_from_v6(new_root, fname)
        if old_version == 2:
            new_root = self._convert_from_v2(root)
            new_root = self._convert_from_v3(new_root)
            new_root = self._convert_from_v4(new_root)
            new_root = self._convert_from_v5(new_root)
            new_root = self._convert_from_v6(new_root, fname)
        if old_version == 3:
            new_root = self._convert_from_v3(root)
            new_root = self._convert_from_v4(new_root)
            new_root = self._convert_from_v5(new_root)
            new_root = self._convert_from_v6(new_root, fname)
        if old_version == 4:
            new_root = self._convert_from_v4(root)
            new_root = self._convert_from_v5(new_root)
            new_root = self._convert_from_v6(new_root, fname)
        if old_version == 5:
            new_root = self._convert_from_v5(root)
            new_root = self._convert_from_v6(new_root, fname)
        if old_version == 6:
            new_root = self._convert_from_v6(root, fname)

        if new_root is not None:
            # Save converted version
            ugly_xml = ElementTree.tostring(new_root, encoding="unicode")
            ugly_xml = "".join([line.strip() for line in ugly_xml.split("\n")])
            dom_xml = minidom.parseString(ugly_xml)
            with open(fname, "w") as out:
                out.write(dom_xml.toprettyxml(indent="    ", newl="\n"))
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
        elif root.tag == "profile" and int(root.get("version")) == 4:
            return 4
        elif root.tag == "profile" and int(root.get("version")) == 5:
            return 5
        elif root.tag == "profile" and int(root.get("version")) == 6:
            return 6
        elif root.tag == "profile" and int(root.get("version")) == 7:
            return 7
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

    def _convert_from_v3(self, root):
        """Converts v3 profiles to v4 profiles.
        
        The following operations are performed in this conversion:
        - embed all actions in individual BasicContainer containers
        - remove button and keyboard conditions
        - move hat and axis condition from actions to containers
        - replace double macros for keyboard remaps with the new map to
          keyboard action
        
        :param root the v3 profile
        :return v4 representation of the profile
        """
        new_root = copy.deepcopy(root)
        new_root.set("version", "4")
        for mode in new_root.iter("mode"):
            for input_item in mode:

                # Check if macros are used to create what is now a
                # "map to keyboard" action
                press_and_release = [False, False]
                count = sum([1 for _ in input_item])
                for action in input_item:
                    if input_item.tag == "button":
                        if action.tag == "macro":
                            if "on-press" in action.keys():
                                press_and_release[0] = press_and_release[0] or \
                                    parse_bool(action.get("on-press"))
                            if "on-release" in action.keys():
                                press_and_release[1] = press_and_release[1] or \
                                    parse_bool(action.get("on-release"))

                # If this widget is purely a map to keyboard action then
                # replace the two macro widgets with a single one
                if count == 2 and all(press_and_release):
                    container = ElementTree.Element("container")
                    container.set("type", "basic")

                    container.append(
                        self._p3_extract_map_to_keyboard(input_item)
                    )
                    for action in input_item[:]:
                        input_item.remove(action)
                    input_item.append(container)

                # The item contains a variety of actions simply convert one
                # after the other
                else:
                    # Wrap each existing action into a basic container
                    containers = []
                    items_to_remove = []
                    for action in input_item:
                        container = ElementTree.Element("container")
                        container.set("type", "basic")

                        # Move conditions to the container and remove them from
                        # the action
                        if input_item.tag == "axis":
                            copy_condition = False
                            if action.tag == "remap":
                                if "button" in action.keys() or \
                                        "hat" in action.keys():
                                    copy_condition = True
                            elif action.tag == "response-curve":
                                pass
                            else:
                                copy_condition = True
                            if copy_condition:
                                cond = ElementTree.Element("activation-condition")
                                cond.set("lower-limit", action.get("lower-limit"))
                                cond.set("upper-limit", action.get("upper-limit"))
                                container.append(cond)
                            if "lower-limit" in action.keys():
                                del action.attrib["lower-limit"]
                            if "upper-limit" in action.keys():
                                del action.attrib["upper-limit"]
                            if "is-active" in action.keys():
                                del action.attrib["is-active"]
                        elif input_item.tag == "button":
                            if "on-press" in action.keys():
                                del action.attrib["on-press"]
                            if "on-release" in action.keys():
                                del action.attrib["on-release"]
                        elif input_item.tag == "hat":
                            if "on-n" in action.keys():
                                cond = ElementTree.Element("activation-condition")
                                keys = [
                                    ("on-n", "north"),
                                    ("on-ne", "north-east"),
                                    ("on-e", "east"),
                                    ("on-se", "south-east"),
                                    ("on-s", "south"),
                                    ("on-sw", "south-west"),
                                    ("on-w", "west"),
                                    ("on-nw", "north-west")
                                ]
                                for names in keys:
                                    if action.get(names[0]) == "True":
                                        cond.set(names[1], "True")
                                    if names[0] in action.keys():
                                        del action.attrib[names[0]]
                                container.append(cond)

                        # Macro actions have changed, update their layout
                        if action.tag == "macro":
                            actions_node = ElementTree.Element("actions")
                            remove_key_nodes = []
                            for key_node in action:
                                actions_node.append(key_node)
                                remove_key_nodes.append(key_node)

                            for key_node in remove_key_nodes:
                                action.remove(key_node)

                            action.append(actions_node)
                            action.append(ElementTree.Element("properties"))

                        container.append(action)
                        containers.append(container)
                        items_to_remove.append(action)

                    for action in items_to_remove:
                        input_item.remove(action)

                    for container in containers:
                        input_item.append(container)

        return new_root

    def _convert_from_v4(self, root):
        """Converts v4 profiles to v5 profiles.

        The following operations are performed in this conversion:
        - Place individual actions inside action_sets

        :param root the v4 profile
        :return v5 representation of the profile
        """
        new_root = copy.deepcopy(root)
        new_root.set("version", "5")
        for container in new_root.iter("container"):
            actions_to_remove = []
            action_sets = []
            for action in container:
                # Handle virtual button setups
                if action.tag == "activation-condition":
                    action.tag = "virtual-button"
                    action_sets.append(action)
                    actions_to_remove.append(action)
                # Handle actions
                else:
                    action_set = ElementTree.Element("action-set")
                    action_set.append(action)
                    action_sets.append(action_set)
                    actions_to_remove.append(action)

            for action in actions_to_remove:
                container.remove(action)
            for action_set in action_sets:
                container.append(action_set)

        return new_root

    def _convert_from_v5(self, root):
        """Converts v5 profiles to v6 profiles.

        The following operations are performed in this conversion:
        - Combine axis remaps and response curves into a single basic container

        :param root the v5 profile
        :return v6 representation of the profile
        """
        new_root = copy.deepcopy(root)
        new_root.set("version", "6")
        for axis in new_root.iter("axis"):
            has_remap = False
            has_curve = False
            for container in axis:
                has_remap |= container.find(".[@type='basic']//remap[@axis]") is not None
                has_curve |= container.find(".[@type='basic']//response-curve") is not None

            # If we have both axis remap and response curve actions place them
            # all in a single basic container
            if has_remap and has_curve:
                new_container = ElementTree.Element("container")
                new_container.set("type", "basic")
                new_actionset = ElementTree.Element("action-set")

                # Copy all axis remaps and response curves into the new
                # action set
                containers_to_delete = []
                for container in axis:
                    remove_container = False
                    for node in container.findall(".[@type='basic']//remap[@axis]"):
                        new_actionset.append(node)
                        remove_container = True
                    for node in container.findall(".[@type='basic']//response-curve"):
                        new_actionset.append(node)
                        remove_container = True

                    if remove_container:
                        containers_to_delete.append(container)

                new_container.append(new_actionset)
                axis.append(new_container)

                # Delete containers of
                for container in containers_to_delete:
                    axis.remove(container)

        return new_root

    def _convert_from_v6(self, root, fname):
        """Convert from a V6 profile to V7.

        This conversion only requires to modify the custom module loading bit
        which requires turning the module name into the full path. This
        requires the path to the initial profile as the module has to be in
        the same subfolder.
        """
        base_path = os.path.normcase(os.path.dirname(os.path.abspath(fname)))

        root.attrib["version"] = "7"
        for module in root.findall("import/module"):
            module.attrib["name"] = os.path.normpath("{}\{}.py".format(
                base_path,
                module.attrib["name"]
            ))

        return root

    def _p3_extract_map_to_keyboard(self, input_item):
        """Converts an old macro setup to a map to keyboard action.

        Previously a certain pattern was used to achieve a keyboard press
        forwarding. With the introduction of a dedicated action for this,
        actions following this pattern are being converted.

        :param input_item the InputItem containing the old macro definitions
        :return map to keyboard node representing the old macros
        """
        node = ElementTree.Element("map-to-keyboard")

        for action in input_item:
            assert action.tag == "macro"

            for key in action:
                if key.tag == "key":
                    key_node = ElementTree.Element("key")
                    key_node.set("scan_code", key.get("scan_code"))
                    key_node.set("extended", key.get("extended"))
                    node.append(key_node)
            break

        return node


class ProfileModifier:

    """Modifies profile contents and provides overview information."""

    def __init__(self, profile):
        """Creates a modifier for a specifc profile.

        :param profile the profile to be modified
        """
        self.profile = profile

    def device_information_list(self):
        """Returns the list of device information present in the profile.

        :return list of devices used in the profile and information about them
        """
        device_ids = []
        for device_id in self.profile.devices:
            device_ids.append((device_id.hardware_id, device_id.windows_id))
        for cond in self.all_conditions():
            if isinstance(cond, base_classes.JoystickCondition):
                device_ids.append((cond.device_id, cond.windows_id))
        for entry in self.profile.merge_axes:
            for key in ["lower", "upper"]:
                device_ids.append((
                    entry[key]["hardware_id"], entry[key]["windows_id"]
                ))

        device_names = self.device_names()
        device_info = []
        for devid in set(device_ids):
            device_info.append(ProfileDeviceInformation(
                common.DeviceIdentifier(devid[0], devid[1]),
                device_names[devid[0]],
                self.container_count(devid),
                self.condition_count(devid),
                self.merge_axis_count(devid)
            ))

        return device_info

    def container_count(self, hid_wid_tuple):
        """Returns the number of containers associated with a device.

        :param hid_wid_tuple tuple of hardware and windows id
        :return number of containers associated with the given device
        """
        count = 0
        for device_id, device in self.profile.devices.items():
            if self._equal_ids(device_id, hid_wid_tuple):
                for mode in device.modes.values():
                    for input_items in mode.config.values():
                        for input_item in input_items.values():
                            count += len(input_item.containers)
        return count

    def condition_count(self, hid_wid_tuple):
        """Returns the number of conditions associated with a device.

        :param hid_wid_tuple tuple of hardware and windows id
        :return number of conditions associated with the given device
        """
        count = 0
        for cond in self.all_conditions():
            if (cond.device_id, cond.windows_id) == hid_wid_tuple:
                count += 1
        return count

    def merge_axis_count(self, hid_wid_tuple):
        """Returns the number of merge axes associated with a device.

        :param hid_wid_tuple tuple of hardware and windows id
        :return number of merge axes associated with the given device
        """
        count = 0
        for entry in self.profile.merge_axes:
            for key in ["lower", "upper"]:
                cur_hw_id = (
                    entry[key]["hardware_id"], entry[key]["windows_id"]
                )
                if cur_hw_id == hid_wid_tuple:
                    count += 1
        return count

    def change_device_id(self, source_id, target_id):
        """Performs actions neccessary to move all data from source to target.

        Moves all profile content from a given source device to the desired
        target device.

        :param source_id identifier of the source device
        :param target_id identifier of the target device
        """

        if source_id.hardware_id == target_id.hardware_id and \
                source_id.windows_id == target_id.windows_id:
            logging.getLogger("system").warning(
                "Source and target device are identical"
            )
            return

        self.change_device_actions(source_id, target_id)
        self.change_conditions(source_id, target_id)
        self.change_merge_axis(source_id, target_id)


    def change_device_actions(self, source_id, target_id):
        """Moves actions from the source device to the target device.

        :param source_id identifier of the source device
        :param target_id identifier of the target device
        """
        source_dev = self._get_device(source_id)
        target_dev = self._get_device(target_id)

        # Can't move anything from a non-existent source device
        if source_dev is None:
            logging.getLogger("system").warning(
                "Specified a source device that doesn't exist"
            )
            return

        # Retrieve target device information structure to get its name and
        # properly initialize modes if needed
        target_hardware_device = None
        for dev in joystick_handling.joystick_devices():
            if util.get_device_identifier(dev) == target_id:
                target_hardware_device = dev

        # If there is no target device we can turn the source device into the
        # target device
        if target_dev is None:
            if target_hardware_device is None:
                logging.getLogger("system").warning(
                    "Target device which is not present specified"
                )
                return
            source_dev.hardware_id = target_id.hardware_id
            source_dev.windows_id = target_id.windows_id
            source_dev.name = target_hardware_device.name
            return

        # Ensure modes present in the source device exist in the target device
        for mode_name in source_dev.modes:
            target_dev.ensure_mode_exists(mode_name, target_hardware_device)

        # Move container entries from source to target as long as there is a
        # matching input item available
        for mode in source_dev.modes.values():
            target_mode = target_dev.modes[mode.name]
            for input_items in mode.config.values():
                for input_item in input_items.values():
                    input_type = input_item.input_type
                    input_id = input_item.input_id

                    if input_id not in target_mode.config[input_type]:
                        logging.getLogger("system").warn(
                            "Source input id not present in target device"
                        )
                        continue

                    # Move containers from source to target input item
                    target_input_item = target_mode.config[input_type][input_id]

                    for container in input_item.containers:
                        container.parent = target_input_item
                        target_mode.config[input_type] \
                            [input_id].containers.append(container)

                    # Remove all containers from the source device
                    input_item.containers = []

    def change_conditions(self, source_id, target_id):
        """Modifies conditions to use the target device instead of the
        source device.

        :param source_id identifier of the source device
        :param target_id identifier of the target device
        """
        # TODO: Does not ensure conditions are valid, i.e. missing inputs
        target_hardware_device = None
        for dev in joystick_handling.joystick_devices():
            if util.get_device_identifier(dev) == target_id:
                target_hardware_device = dev

        for condition in self.all_conditions():
            if isinstance(condition, base_classes.JoystickCondition):
                if condition.device_id == source_id.hardware_id and \
                        condition.windows_id == source_id.windows_id:
                    condition.device_id = target_id.hardware_id
                    condition.windows_id = target_id.windows_id
                    condition.device_name = target_hardware_device.name

    def change_merge_axis(self, source_id, target_id):
        """Modifies merge axis entries to use the target device instead of the
        source device.

        :param source_id identifier of the source device
        :param target_id identifier of the target device
        """
        # TODO: Does not ensure assignemts are valid, i.e. missing axis
        for entry in self.profile.merge_axes:
            for key in ["lower", "upper"]:
                if entry[key]["hardware_id"] == source_id.hardware_id and \
                        entry[key]["windows_id"] == source_id.windows_id:
                    entry[key]["hardware_id"] = target_id.hardware_id
                    entry[key]["windows_id"] = target_id.windows_id

    def device_names(self):
        """Returns a mapping from hardware ids to device names.

        :return mapping of hardware ids to device names
        """
        name_map = {}
        for device in self.profile.devices.values():
            name_map[device.hardware_id] = device.name
        for cond in self.all_conditions():
            if isinstance(cond, base_classes.JoystickCondition):
                name_map[cond.device_id] = cond.device_name
        return name_map

    def all_conditions(self):
        """Returns a list of all conditions.

        :return list of all conditions
        """
        all_conditions = []
        for device in self.profile.devices.values():
            for mode in device.modes.values():
                for input_items in mode.config.values():
                    for input_item in input_items.values():
                        for container in input_item.containers:
                            if container.activation_condition is not None:
                                all_conditions.extend(
                                    container.activation_condition.conditions
                                )
        return all_conditions

    def _get_device(self, device_id):
        """Returns the device corresponding to a given identifier.

        :return device matching the identifier if present
        """
        for devid, device in self.profile.devices.items():
            if devid.hardware_id == device_id.hardware_id and \
                    devid.windows_id == device_id.windows_id:
                return device
        return None

    def _equal_ids(self, device_id, hid_wid_tuple):
        """Returns whether two device identifications are identical.

        This requires the first parameter to be a DeviceIdentifier intance and
        the second one a tuple of hardware and windows id. This is needed as
        DeviceIdentifier equality copmarison takes device duplition into
        account while we want to always differentiate based on windows id.

        :param device_id DeviceIdentifier instance
        :param hid_wid_tuple tuple of hardware id and windows id
        :return True if hardware and windows id both match, False otherwise
        """
        assert isinstance(device_id, common.DeviceIdentifier),\
            "Requires DeviceIdentifier instance"
        assert isinstance(hid_wid_tuple, tuple) and len(hid_wid_tuple) == 2, \
            "Tuple of length 2 needed"

        return device_id.hardware_id == hid_wid_tuple[0] and \
            device_id.windows_id == hid_wid_tuple[1]


class Settings:

    """Stores general profile specific settings."""

    def __init__(self, parent):
        """Creates a new instance.

        :param parent the parent profile
        """
        self.parent = parent
        self.vjoy_as_input = {}
        self.vjoy_initial_values = {}
        self.startup_mode = None

    def to_xml(self):
        """Returns an XML node containing the settings.

        :return XML node containing the settings
        """
        node = ElementTree.Element("settings")

        # Startup mode
        if self.startup_mode is not None:
            mode_node = ElementTree.Element("startup-mode")
            mode_node.text = safe_format(self.startup_mode, str)
            node.append(mode_node)

        # Process vJoy as input settings
        for vid, value in self.vjoy_as_input.items():
            if value == True:
                vjoy_node = ElementTree.Element("vjoy-input")
                vjoy_node.set("id", safe_format(vid, int))
                node.append(vjoy_node)

        # Process vJoy axis initial values
        for vid, data in self.vjoy_initial_values.items():
            vjoy_node = ElementTree.Element("vjoy")
            vjoy_node.set("id", safe_format(vid, int))
            for aid, value in data.items():
                axis_node = ElementTree.Element("axis")
                axis_node.set("id", safe_format(aid, int))
                axis_node.set("value", safe_format(value, float))
                vjoy_node.append(axis_node)
            node.append(vjoy_node)

        return node

    def from_xml(self, node):
        """Populates the data storage with the XML node's contents.

        :param node the node containing the settings data
        """
        if not node:
            return

        # Startup mode
        self.startup_mode = None
        if node.find("startup-mode") is not None:
            self.startup_mode = node.find("startup-mode").text

        # vJoy as input settings
        self.vjoy_as_input = {}
        for vjoy_node in node.findall("vjoy-input"):
            vid = safe_read(vjoy_node, "id", int)
            self.vjoy_as_input[vid] = True

        # vjoy initialization values
        self.vjoy_initial_values = {}
        for vjoy_node in node.findall("vjoy"):
            vid = safe_read(vjoy_node, "id", int)
            self.vjoy_initial_values[vid] = {}
            for axis_node in vjoy_node.findall("axis"):
                aid = safe_read(axis_node, "id", int)
                value = safe_read(axis_node, "value", float, 0.0)
                self.vjoy_initial_values[vid][aid] = value

    def get_initial_vjoy_axis_value(self, vid, aid):
        """Returns the initial value a vJoy axis should use.

        :param vid the id of the virtual joystick
        :param aid the id of the axis
        :return default value for the specified axis
        """
        value = 0.0
        if vid in self.vjoy_initial_values:
            if aid in self.vjoy_initial_values[vid]:
                value = self.vjoy_initial_values[vid][aid]
        return value

    def set_initial_vjoy_axis_value(self, vid, aid, value):
        """Sets the default value for a particular vJoy axis.

        :param vid the id of the virtual joystick
        :param aid the id of the axis
        :param value the default value to use with the specified axis
        """
        if vid not in self.vjoy_initial_values:
            self.vjoy_initial_values[vid] = {}
        self.vjoy_initial_values[vid][aid] = value


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
        self.settings = Settings(self)
        self.parent = None

    def initialize_joystick_device(self, device, modes):
        """Ensures a joystick is properly initialized in the profile.

        :param device the device to initialize
        :param modes the list of modes to be present
        """
        new_device = Device(self)
        new_device.name = device.name
        new_device.hardware_id = device.hardware_id
        new_device.windows_id = device.windows_id
        new_device.type = DeviceType.Joystick
        self.devices[device.device_id] = new_device

        for mode in modes:
            new_device.ensure_mode_exists(mode)
            new_mode = new_device.modes[mode]
            for i in range(device.axis_count):
                new_mode.get_data(InputType.JoystickAxis, device.axis(i)[1])
            for i in range(1, device.buttons+1):
                new_mode.get_data(InputType.JoystickButton, i)
            for i in range(1, device.hats+1):
                new_mode.get_data(InputType.JoystickHat, i)

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

    def list_unused_vjoy_inputs(self):
        """Returns a list of unused vjoy inputs for the given profile.

        :return dictionary of unused inputs for each input type
        """
        vjoy_devices = joystick_handling.vjoy_devices()

        # Create list of all inputs provided by the vjoy devices
        vjoy = {}
        for entry in vjoy_devices:
            vjoy[entry.vjoy_id] = {"axis": [], "button": [], "hat": []}
            for i in range(entry.axis_count):
                vjoy[entry.vjoy_id]["axis"].append(
                    entry.axis(i)[1]
                )
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
                        for container in item.containers:
                            remap_actions.extend(
                                extract_remap_actions(container.action_sets)
                            )

        # Remove all remap actions from the list of available inputs
        for act in remap_actions:
            type_name = InputType.to_string(act.input_type)
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
        self.update_windows_ids(root)

        # Parse each device into separate DeviceConfiguration objects
        for child in root.iter("device"):
            device = Device(self)
            device.from_xml(child)
            self.devices[util.get_device_identifier(device)] = device

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
                    util.get_device_identifier(dev) not in self.devices:
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
                    self.devices[util.get_device_identifier(new_device)] = new_device

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

        # Parse settings entries
        self.settings.from_xml(root.find("settings"))

    def to_xml(self, fname):
        """Generates XML code corresponding to this profile.

        :param fname name of the file to save the XML to
        """
        # Generate XML document
        root = ElementTree.Element("profile")
        root.set("version", "7")

        # Device settings
        devices = ElementTree.Element("devices")
        device_list = sorted(
            self.devices.values(),
            key=lambda x: (x.hardware_id, x.windows_id)
        )
        for device in device_list:
            devices.append(device.to_xml())
        root.append(devices)

        # VJoy settings
        vjoy_devices = ElementTree.Element("vjoy-devices")
        for device in self.vjoy_devices.values():
            vjoy_devices.append(device.to_xml())
        root.append(vjoy_devices)

        # Module imports
        import_node = ElementTree.Element("import")
        for entry in sorted(self.imports):
            node = ElementTree.Element("module")
            node.set("name", entry)
            import_node.append(node)
        root.append(import_node)

        # Merge axis data
        for entry in self.merge_axes:
            node = ElementTree.Element("merge-axis")
            node.set("mode", safe_format(entry["mode"], str))
            for tag in ["vjoy"]:
                sub_node = ElementTree.Element(tag)
                sub_node.set(
                    "device",
                    safe_format(entry[tag]["device_id"], int)
                )
                sub_node.set("axis", safe_format(entry[tag]["axis_id"], int))
                node.append(sub_node)
            for tag in ["lower", "upper"]:
                sub_node = ElementTree.Element(tag)
                sub_node.set("id", safe_format(entry[tag]["hardware_id"], int))
                sub_node.set(
                    "windows_id",
                    safe_format(entry[tag]["windows_id"], int)
                )
                sub_node.set("axis", safe_format(entry[tag]["axis_id"], int))
                node.append(sub_node)
            root.append(node)

        # Settings data
        root.append(self.settings.to_xml())

        # Serialize XML document
        ugly_xml = ElementTree.tostring(root, encoding="utf-8")
        dom_xml = minidom.parseString(ugly_xml)
        with codecs.open(fname, "w", "utf-8-sig") as out:
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
                device = Device(self)
                device.name = device_name
                device.hardware_id = device_id.hardware_id
                device.windows_id = device_id.windows_id

                # Set the correct device type
                device.type = DeviceType.Joystick
                if device_name == "keyboard":
                    device.type = DeviceType.Keyboard
                self.devices[device_id] = device
            return self.devices[device_id]

    def empty(self):
        """Returns whether or not a profile is empty.

        :return True if the profile is empty, False otherwise
        """
        is_empty = True
        is_empty &= len(self.imports) == 0
        is_empty &= len(self.merge_axes) == 0

        # Enumerate all input devices
        all_input_types = [
            InputType.JoystickAxis,
            InputType.JoystickButton,
            InputType.JoystickHat,
            InputType.Keyboard
        ]

        # Process all devices
        for dev in self.devices.values():
            for mode in dev.modes.values():
                for input_type in all_input_types:
                    for item in mode.config[input_type].values():
                        is_empty &= len(item.containers) == 0

        # Process all vJoy devices
        for dev in self.vjoy_devices.values():
            for mode in dev.modes.values():
                for input_type in all_input_types:
                    for item in mode.config[input_type].values():
                        is_empty &= len(item.containers) == 0

        return is_empty

    def update_windows_ids(self, root):
        dev_reg = common.DeviceRegistry()
        device_map = {}

        # Fix device nodes
        for node in root.findall("./devices/device"):
            hid = safe_read(node, "id", int, -1)
            wid = safe_read(node, "windows_id", int, -1)

            windows_ids = dev_reg.by_hardware_id(hid)
            if len(windows_ids) == 1:
                device_map[hid] = wid
                if wid not in windows_ids:
                    node.set("windows_id", windows_ids[0])

        # Fix condition nodes
        for node in root.findall(".//condition"):
            hid = safe_read(node, "device_id", int, -1)
            wid = safe_read(node, "windows_id", int, -1)

            if hid in device_map and wid != device_map[hid]:
                node.set("windows_id", device_map[hid])

        # Fix axis merging
        for node in root.findall(".//merge-axis"):
            for child in [n for n in node if n.tag in ["lower", "upper"]]:
                hid = safe_read(child, "id", int, -1)
                wid = safe_read(child, "windows_id", int, -1)
                if hid in device_map and wid != device_map[hid]:
                    child.set("windows_id", device_map[hid])

        # Fix macros
        # TODO: Leave these broken until we get rid of windows and hardware id
        #       alltogether

    def _parse_merge_axis(self, node):
        """Parses merge axis entries.

        :param node the node to process
        :return merge axis data structure parsed from the XML node
        """
        entry = {
            "mode": node.get("mode", None)
        }
        # TODO: apply safe reading to these
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
        # if util.g_duplicate_devices:
        #     device_counts = {}
        #     windows_ids = {}
        #     for dev in joystick_handling.joystick_devices():
        #         device_counts[dev.hardware_id] = \
        #             device_counts.get(dev.hardware_id, 0) + 1
        #         windows_ids[dev.hardware_id] = dev.windows_id
        #
        #     for tag in ["lower", "upper"]:
        #         # Only one device exists, override system id
        #         if device_counts.get(entry[tag]["hardware_id"], 0) == 1:
        #             entry[tag]["windows_id"] = \
        #                 windows_ids[entry[tag]["hardware_id"]]

        return entry


class Device:

    """Stores the information about a single device including it's modes."""

    def __init__(self, parent):
        """Creates a new instance.

        :param parent the parent profile of this device
        """
        self.parent = parent
        self.name = None
        self.label = ""
        self.hardware_id = None
        self.windows_id = None
        self.modes = {}
        self.type = None

    def ensure_mode_exists(self, mode_name, device=None):
        """Ensures that a specified mode exists, creating it if needed.

        :param mode_name the name of the mode being checked
        :param device a device to initialize for this mode if specified
        """
        if mode_name in self.modes:
            mode = self.modes[mode_name]
        else:
            mode = Mode(self)
            mode.name = mode_name
            self.modes[mode.name] = mode

        if device is not None:
            for i in range(device.axis_count):
                mode.get_data(InputType.JoystickAxis, device.axis(i)[1])
            for id in range(1, device.buttons + 1):
                mode.get_data(InputType.JoystickButton, id)
            for id in range(1, device.hats + 1):
                mode.get_data(InputType.JoystickHat, id)

    def from_xml(self, node):
        """Populates this device based on the xml data.

        :param node the xml node to parse to populate this device
        """
        self.name = node.get("name")
        self.label = safe_read(node, "label", default_value=self.name)
        self.hardware_id = safe_read(node, "id", int)
        self.windows_id = safe_read(node, "windows_id", int)
        self.type = DeviceType.to_enum(safe_read(node, "type", str))

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
        node.set("name", safe_format(self.name, str))
        node.set("label", safe_format(self.label, str))
        node.set("id", safe_format(self.hardware_id, int))
        node.set("windows_id", safe_format(self.windows_id, int))
        node.set("type", DeviceType.to_string(self.type))
        for mode in sorted(self.modes.values(), key=lambda x: x.name):
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
        vjoy_device = None
        if self.parent.name == "vJoy Device":
            vjoy_proxy = joystick_handling.VJoyProxy()
            try:
                vjoy_device = vjoy_proxy[self.parent.hardware_id]
            except error.VJoyError:
                joystick_handling.VJoyProxy().reset()

        self.name = safe_read(node, "name", str)
        self.inherit = node.get("inherit", None)
        for child in node:
            item = InputItem(self)
            item.from_xml(child)

            store_item = True
            if vjoy_device is not None and \
                    item.input_type == InputType.JoystickAxis:
                store_item = vjoy_device.is_axis_valid(axis_id=item.input_id)

            if store_item:
                self.config[item.input_type][item.input_id] = item

        joystick_handling.VJoyProxy().reset()

    def to_xml(self):
        """Generates XML code for this DeviceConfiguration.

        :return XML node representing this object's data
        """
        node = ElementTree.Element("mode")
        node.set("name", safe_format(self.name, str))
        if self.inherit is not None:
            node.set("inherit", safe_format(self.inherit, str))
        input_types = [
            InputType.JoystickAxis,
            InputType.JoystickButton,
            InputType.JoystickHat,
            InputType.Keyboard
        ]
        for input_type in input_types:
            item_list = sorted(
                self.config[input_type].values(),
                key=lambda x: x.input_id
            )
            for item in item_list:
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
        if input_id == 1 and input_type == InputType.JoystickAxis:
            pass
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

    def all_input_items(self):
        for input_type in self.config.values():
            for input_item in input_type.values():
                yield input_item


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
        self.containers = []

    def from_xml(self, node):
        """Parses an InputItem node.

        :param node XML node to parse
        """
        container_name_map = plugin_manager.ContainerPlugins().tag_map
        self.input_type = InputType.to_enum(node.tag)
        self.input_id = safe_read(node, "id", int)
        self.description = safe_read(node, "description", str)
        self.always_execute = read_bool(node, "always-execute", False)
        if self.input_type == InputType.Keyboard:
            self.input_id = (self.input_id, read_bool(node, "extended"))
        for child in node:
            container_type = child.attrib["type"]
            if container_type not in container_name_map:
                logging.getLogger("system").warning(
                    "Unknown container type used: {}".format(container_type)
                )
                continue
            entry = container_name_map[container_type](self)
            entry.from_xml(child)
            self.containers.append(entry)

    def to_xml(self):
        """Generates a XML node representing this object's data.

        :return XML node representing this object
        """
        node = ElementTree.Element(InputType.to_string(self.input_type))
        if self.input_type == InputType.Keyboard:
            node.set("id", safe_format(self.input_id[0], int))
            node.set("extended", safe_format(self.input_id[1], bool))
        else:
            node.set("id", safe_format(self.input_id, int))

        if self.always_execute:
            node.set("always-execute", "True")

        if self.description:
            node.set("description", safe_format(self.description, str))
        else:
            node.set("description", "")

        for entry in self.containers:
            if entry.is_valid():
                node.append(entry.to_xml())

        return node

    def get_device_type(self):
        """Returns the DeviceType of this input item.

        :return DeviceType of this entry
        """
        item = self.parent
        while not isinstance(item, Device):
            item = item.parent
        return item.type

    def __eq__(self, other):
        """Checks whether or not two InputItem instances are identical.

        :return True if they are identical, False otherwise
        """
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        """Returns the hash of this input item.

        The hash takes into account to which device and mode the input item is
        bound.

        :return hash of this InputItem instance
        """
        device_id = util.get_device_identifier(self.parent.parent)
        mode = self.parent.name

        return hash((device_id, mode, self.input_type, self.input_id))


class ProfileData(metaclass=ABCMeta):

    """Base class for all items holding profile data.

    This is primarily used for containers and actions to represent their
    configuration and to easily load and store them.
    """

    def __init__(self, parent):
        """Creates a new instance.

        :param parent the parent item of this instance in the profile tree
        """
        self.parent = parent
        self.code = None

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

    def is_valid(self):
        """Returns whether or not an instance is fully specified.
        
        :return True if all required variables are set, False otherwise
        """
        return self._is_valid()

    def get_input_type(self):
        """Returns the InputType of this data entry.
        
        :return InputType of this entry
        """
        item = self.parent
        while not isinstance(item, InputItem):
            item = item.parent
        return item.input_type

    def get_mode(self):
        """Returns the Mode this data entry belongs to.

        :return Mode instance this object belongs to
        """
        item = self.parent
        while not isinstance(item, Mode):
            item = item.parent
        return item

    def get_device_type(self):
        """Returns the DeviceType of this data entry.
        
        :return DeviceType of this entry
        """
        item = self.parent
        while not isinstance(item, Device):
            item = item.parent
        return item.type

    def get_settings(self):
        """Returns the Settings data of the profile.

        :return Setttings object of this profile
        """
        item = self.parent
        while not isinstance(item, Profile):
            item = item.parent
        return item.settings

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
    def _is_valid(self):
        """Returns whether or not an instance is fully specified.
        
        :return True if all required variables are set, False otherwise
        """
        pass
