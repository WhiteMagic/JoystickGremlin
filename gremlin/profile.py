# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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

from __future__ import annotations

from abc import abstractmethod, ABCMeta
import codecs
import collections
import copy
import logging
import os
import shutil
from typing import Any, List, Optional
import uuid
from xml.dom import minidom
from xml.etree import ElementTree

import dill

import action_plugins
import gremlin.types
from .types import InputType, DeviceType, HatDirection, PluginVariableType, \
    MergeAxisOperation
from . import base_classes, common, error, input_devices, joystick_handling, \
    plugin_manager, profile_library, tree
from .util import parse_guid, safe_read, safe_format, read_bool, \
    read_subelement, create_subelement_node
#from gremlin.profile_library import  *


# Data struct representing profile information of a device
ProfileDeviceInformation = collections.namedtuple(
    "ProfileDeviceInformation",
    ["device_guid", "name", "containers", "conditions", "merge_axis"]
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
    current_version = 9

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

        conversion_map = {
            1: self._convert_from_v1,
            2: self._convert_from_v2,
            3: self._convert_from_v3,
            4: self._convert_from_v4,
            5: self._convert_from_v5,
            6: self._convert_from_v6,
            7: self._convert_from_v7,
            8: self._convert_from_v8,
        }

        # Create a backup of the outdated profile
        old_version = self._determine_version(root)
        shutil.copyfile(fname, "{}.v{:d}".format(fname, old_version))

        # Convert the profile
        new_root = None
        while old_version < ProfileConverter.current_version:
            if new_root is None:
                new_root = conversion_map[old_version](root, fname=fname)
            else:
                new_root = conversion_map[old_version](new_root, fname=fname)
            old_version += 1

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
        elif root.tag == "profile":
            return int(root.get("version"))
        else:
            raise error.ProfileError(
                "Invalid profile version encountered"
            )

    def _convert_from_v1(self, root, fname=None):
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

    def _convert_from_v2(self, root, fname=None):
        """Converts v2 profiles to v3 profiles.

        :param root the v2 profile
        :return v3 representation of the profile
        """
        # Get hardware ids of the connected devices
        device_name_map = {}
        for device in joystick_handling.joystick_devices():
            device_name_map[device.name] = device.device_guid

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

    def _convert_from_v3(self, root, fname=None):
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

    def _convert_from_v4(self, root, fname=None):
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

    def _convert_from_v5(self, root, fname=None):
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
            module.attrib["name"] = os.path.normpath(
                f"{base_path}\\{module.attrib['name']}.py"
            )

        return root

    def _convert_from_v7(self, root, fname=None):
        """Convert from a V7 profile to V8.

        This updates map to mouse actions to the new format.

        Parameters
        ----------
        root : ElementTree
            Root of the XML tree being modified

        Returns
        -------
        ElementTree
            Modified XML root element
        """
        root.attrib["version"] = "8"

        for node in root.findall(".//map-to-mouse"):
            node.set("time-to-max-speed", node.get("acceleration", "1.0"))

            axis = node.get("axis")
            direction = node.get("direction", 0)
            if axis == "x":
                direction = 90
            elif axis == "y":
                direction = 0
            node.set("direction", str(direction))
            node.set("button_id", "1")
            node.set("motion_input", "True")

        return root

    def _convert_from_v8(self, root, fname=None):
        """Convert from a V8 profile to V9.

        Performs the following changes:
        - Merge axis attribut'es reworked
          - vjoy.device => vjoy.vjoy-id
          - vjoy.axis => vjoy.axis-id
          - lower/upper.id => lower/upper.device-guid
          - lower/upper.axis => lower/upper.axis-id
        - Macro attribute changes
          - macro.actions.joystick
            - device_id => device-guid
            - input_type => input-type
            - input_id => input-id
          - macro.actions.key
            - scan_code => scan-code
          - macro.actions.vjoy
            - vjoy_id => vjoy-id
            - input_type => input-type
            - input_id => input-id
        - Map to keyboard
          - map-to-keyboard.key
            - scan_code => scan-code
        - Map to mouse
          - map-to-mouse
              - motion_input => motion-input
              - button_id => button-id
        - Split axis
          - split-axis
            - device1 => device-low-vjoy-id
            - axis1 => device-low-axis
            - device2 => device-high-vjoy-id
            - axis2 => device-high-axis
        - Conditions
          - condition
            - scan_code => scan-code
            - range_low => range-low
            - range_high => range-high
            - device_name => device-name
            - device_id => removed
            - windows_id => removed
            - device-guid => added

        Parameters
        ----------
        root : ElementTree
            Root of the XML tree being modified

        Returns
        -------
        ElementTree
            Modified XML root element
        """
        root.attrib["version"] = "9"
        syslog = logging.getLogger("system")

        class GUIDConverter:

            """Simplifies conversion from old device identifiers to the new
            GUID ones."""

            def __init__(self):
                """Initializes the converter by caching needed values."""
                # Map for old hardware id to new guid value
                self.hwid_to_guid = {}
                self.dev_info = {}
                for dev in joystick_handling.joystick_devices():
                    hwid = (dev.vendor_id << 16) + dev.product_id
                    self.hwid_to_guid[hwid] = str(dev.device_guid)
                    self.dev_info[str(dev.device_guid)] = dev
                self.vjoy_to_guid = {}
                for dev in joystick_handling.vjoy_devices():
                    self.vjoy_to_guid[dev.vjoy_id] = str(dev.device_guid)

            def axis_lookup(self, device_guid, linear_id):
                """Returns the axis id for the given linear index.

                :param device_guid GUID of the device of interest
                :param linear_id linear axis index to convert into axis index
                :return axis index corresponding to the linear index
                """
                if device_guid not in self.dev_info:
                    return linear_id

                device = self.dev_info[device_guid]
                if linear_id > device.axis_count or linear_id >= len(device.axis_map):
                    logging.getLogger("system").error(
                        "Invalid linear axis id received, {} id = {}".format(
                            device.name,
                            linear_id
                        )
                    )
                    return linear_id

                return device.axis_map[linear_id].axis_index

            def lookup(self, hardware_id, name=None):
                """Returns the GUID for the provided hardware id.

                This will create a random GUID if the device is not currently
                connected.

                :param hardware_id old style hardware id
                :param name name of the device if available
                :return GUID corresponding to the provided hardware id
                """
                try:
                    hardware_id = int(hardware_id)
                except (ValueError, TypeError):
                    syslog.warn(
                        "Cannot convert {} into a valid hardware id".format(
                            hardware_id
                        )
                    )
                    return "{{{}}}".format(uuid.uuid4())

                if hardware_id not in self.hwid_to_guid:
                    syslog.warn(
                        "GUID for device {} with hardware_id {} is "
                        "unknown.".format(
                            "" if name is None else name,
                            hardware_id
                        )
                    )
                    self.hwid_to_guid[hardware_id] = "{{{}}}".format(uuid.uuid4())

                return self.hwid_to_guid[hardware_id]

            def vjoy_lookup(self, vjoy_id):
                """Returns the GUID corresponding to a specific vjoy device.

                This will create a random GUID if the device is not currently
                connected.

                :param vjoy_id vjoy id of the device
                :return GUID corresponding to the vjoy device
                """
                try:
                    vjoy_id = int(vjoy_id)
                except (ValueError, TypeError):
                    syslog.warn(
                        "Cannot convert {} into a valid vjoy id".format(vjoy_id)
                    )
                    return "{{{}}}".format(uuid.uuid4())

                if vjoy_id not in self.vjoy_to_guid:
                    syslog.warn(
                        "GUID for vjoy {} is unknown".format(vjoy_id)
                    )
                    self.vjoy_to_guid[vjoy_id] = "{{{}}}".format(uuid.uuid4())

                return self.vjoy_to_guid[vjoy_id]

        # Initialize the GUID converter
        uuid_converter = GUIDConverter()

        for entry in root.findall("devices/device"):
            if entry.attrib.get("type", None) == "keyboard":
                entry.set("device-guid", str(dill.GUID_Keyboard))
            else:
                entry.set(
                    "device-guid",
                    uuid_converter.lookup(
                        entry.attrib.get("id", None),
                        entry.attrib.get("name", "")
                    )
                )

            # Remove the now obsolete id and windows id attributes
            del entry.attrib["id"]
            del entry.attrib["windows_id"]

            for child in entry.findall("mode/axis"):
                child.set(
                    "id",
                    str(uuid_converter.axis_lookup(
                        entry.attrib["device-guid"],
                        int(child.attrib["id"])-1
                    ))
                )

        for entry in root.findall("vjoy-devices/vjoy-device"):
            entry.set("vjoy-id", entry.attrib["id"])
            entry.set(
                "device-guid",
                uuid_converter.vjoy_lookup(int(entry.attrib["id"]))
            )
            del entry.attrib["id"]
            del entry.attrib["windows_id"]

        for entry in root.findall(".//condition"):
            replacements = [
                ("scan_code", "scan-code"),
                ("range_low", "range-low"),
                ("range_high", "range-high"),
                ("device_name", "device-name")
            ]
            for rep in replacements:
                if rep[0] in entry.keys():
                    entry.set(rep[1], entry.attrib[rep[0]])
                    del entry.attrib[rep[0]]
            if "device_id" in entry.keys():
                entry.set(
                    "device-guid",
                    uuid_converter.lookup(entry.attrib.get("device_id", None))
                )
                del entry.attrib["device_id"]
                del entry.attrib["windows_id"]
            if entry.attrib["input"] == "action":
                entry.set("condition-type", "action")
            elif entry.attrib["input"] == "keyboard":
                entry.set("condition-type", "keyboard")
            elif entry.attrib["input"] in ["axis", "button", "hat"]:
                entry.set("condition-type", "joystick")

        for entry in root.findall(".//macro/actions/joystick"):
            entry.set(
                "device-guid",
                uuid_converter.lookup(entry.attrib.get("device_id", None))
            )
            entry.set("input-type", entry.attrib["input_type"])
            entry.set("input-id", entry.attrib["input_id"])
            del entry.attrib["device_id"]
            del entry.attrib["input_type"]
            del entry.attrib["input_id"]

        for entry in root.findall(".//macro/actions/key"):
            entry.set("scan-code", entry.attrib["scan_code"])
            del entry.attrib["scan_code"]

        for entry in root.findall(".//macro/actions/vjoy"):
            entry.set("vjoy-id", entry.attrib["vjoy_id"])
            entry.set("input-type", entry.attrib["input_type"])
            entry.set("input-id", entry.attrib["input_id"])
            del entry.attrib["vjoy_id"]
            del entry.attrib["input_type"]
            del entry.attrib["input_id"]

        for entry in root.findall(".//merge-axis/vjoy"):
            entry.set("vjoy-id", entry.attrib["device"])
            entry.set("axis-id", entry.attrib["axis"])
            del entry.attrib["device"]
            del entry.attrib["axis"]

        for entry in root.findall(".//merge-axis/lower"):
            entry.set(
                "device-guid",
                uuid_converter.lookup(entry.attrib.get("id", None))
            )
            entry.set("axis-id", entry.attrib["axis"])
            del entry.attrib["id"]
            del entry.attrib["axis"]
            del entry.attrib["windows_id"]

        for entry in root.findall(".//merge-axis/upper"):
            entry.set(
                "device-guid",
                uuid_converter.lookup(entry.attrib.get("id", None))
            )
            entry.set("axis-id", entry.attrib["axis"])
            del entry.attrib["id"]
            del entry.attrib["axis"]
            del entry.attrib["windows_id"]

        for entry in root.findall(".//map-to-keyboard/key"):
            entry.set("scan-code", entry.attrib["scan_code"])
            del entry.attrib["scan_code"]

        for entry in root.findall(".//map-to-mouse"):
            entry.set("motion-input", entry.attrib["motion_input"])
            entry.set("button-id", entry.attrib["button_id"])
            del entry.attrib["motion_input"]
            del entry.attrib["button_id"]

        for entry in root.findall(".//split-axis"):
            entry.set("device-low-vjoy-id", entry.attrib["device1"])
            entry.set("device-low-axis", entry.attrib["axis1"])
            entry.set("device-high-vjoy-id", entry.attrib["device2"])
            entry.set("device-high-axis", entry.attrib["axis2"])
            del entry.attrib["device1"]
            del entry.attrib["axis1"]
            del entry.attrib["device2"]
            del entry.attrib["axis2"]

        plugins_node = ElementTree.Element("plugins")
        for entry in root.findall(".//import/module"):
            p_node = ElementTree.Element("plugin")
            p_node.set("file-name", entry.attrib["name"])

            i_node = ElementTree.Element("instance")
            i_node.set("name", "Default")

            p_node.append(i_node)
            plugins_node.append(p_node)
        root.append(plugins_node)

        for entry in root.findall("import"):
            root.remove(entry)

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
        """Creates a modifier for a specific profile.

        :param profile the profile to be modified
        """
        self.profile = profile

    def device_information_list(self):
        """Returns the list of device information present in the profile.

        :return list of devices used in the profile and information about them
        """
        device_guids = []
        device_names = {}
        for guid, dev in self.profile.devices.items():
            device_guids.append(guid)
            device_names[guid] = dev.name
        for cond in self.all_conditions():
            if isinstance(cond, base_classes.JoystickCondition):
                device_guids.append(cond.device_guid)
                device_names[cond.device_guid] = cond.device_name
        for entry in self.profile.merge_axes:
            for key in ["lower", "upper"]:
                device_guids.append(entry[key]["device_guid"])

        device_info = []
        for device_guid in set(device_guids):
            device_info.append(ProfileDeviceInformation(
                device_guid,
                device_names.get(device_guid, "Unknown"),
                self.container_count(device_guid),
                self.condition_count(device_guid),
                self.merge_axis_count(device_guid)
            ))

        return device_info

    def container_count(self, device_guid):
        """Returns the number of containers associated with a device.

        :param device_guid GUID of the target device
        :return number of containers associated with the given device
        """
        count = 0
        for dev_guid, device in self.profile.devices.items():
            if dev_guid == device_guid:
                for mode in device.modes.values():
                    for input_items in mode.config.values():
                        for input_item in input_items.values():
                            count += len(input_item.containers)
        return count

    def condition_count(self, device_guid):
        """Returns the number of conditions associated with a device.

        :param device_guid GUID of the target device
        :return number of conditions associated with the given device
        """
        count = 0
        for cond in self.all_conditions():
            if isinstance(cond, base_classes.JoystickCondition) and \
                    cond.device_guid == device_guid:
                count += 1
        return count

    def merge_axis_count(self, device_guid):
        """Returns the number of merge axes associated with a device.

        :param device_guid GUID of the target device
        :return number of merge axes associated with the given device
        """
        count = 0
        for entry in self.profile.merge_axes:
            for key in ["lower", "upper"]:
                if entry[key]["device_guid"] == device_guid:
                    count += 1
        return count

    def change_device_guid(self, source_guid, target_guid):
        """Performs actions necessary to move all data from source to target.

        Moves all profile content from a given source device to the desired
        target device.

        :param source_guid identifier of the source device
        :param target_guid identifier of the target device
        """

        if source_guid == target_guid:
            logging.getLogger("system").warning(
                "Swap devices: Source and target device are identical"
            )
            return

        self.change_device_actions(source_guid, target_guid)
        self.change_conditions(source_guid, target_guid)
        self.change_merge_axis(source_guid, target_guid)

    def change_device_actions(self, source_guid, target_guid):
        """Moves actions from the source device to the target device.

        :param source_guid identifier of the source device
        :param target_guid identifier of the target device
        """
        source_dev = self._get_device(source_guid)
        target_dev = self._get_device(target_guid)

        # Can't move anything from a non-existent source device
        if source_dev is None:
            logging.getLogger("system").warning(
                "Swap devices: Specified a source device that doesn't exist"
            )
            return

        # Retrieve target device information structure to get its name and
        # properly initialize modes if needed
        target_hardware_device = None
        for dev in joystick_handling.joystick_devices():
            if dev.device_guid == target_guid:
                target_hardware_device = dev

        # If there is no target device configuration present we can rename
        # the source device configuration into the target device and avoid
        # copying and deleting things.
        if target_dev is None:
            if target_hardware_device is None:
                logging.getLogger("system").warning(
                    "Swap devices: Empty target device configuration found"
                )
                return
            source_dev.device_guid = target_guid
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
                        logging.getLogger("system").warning(
                            "Swap devices: Source input id not present in "
                            "target device"
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

        # Remove the device entry completely
        del self.profile.devices[source_guid]


    def change_conditions(self, source_guid, target_guid):
        """Modifies conditions to use the target device instead of the
        source device.

        :param source_guid identifier of the source device
        :param target_guid identifier of the target device
        """
        # TODO: Does not ensure conditions are valid, i.e. missing inputs
        target_hardware_device = None
        for dev in joystick_handling.joystick_devices():
            if dev.device_guid == target_guid:
                target_hardware_device = dev

        for condition in self.all_conditions():
            if isinstance(condition, base_classes.JoystickCondition):
                if condition.device_guid == source_guid:
                    condition.device_guid = target_guid
                    condition.device_name = target_hardware_device.name

    def change_merge_axis(self, source_guid, target_guid):
        """Modifies merge axis entries to use the target device instead of the
        source device.

        :param source_id identifier of the source device
        :param target_id identifier of the target device
        """
        # TODO: Does not ensure assignments are valid, i.e. missing axis
        for entry in self.profile.merge_axes:
            for key in ["lower", "upper"]:
                if entry[key]["device_guid"] == source_guid:
                    entry[key]["device_guid"] = target_guid

    def device_names(self):
        """Returns a mapping from hardware ids to device names.

        :return mapping of hardware ids to device names
        """
        name_map = {}
        for device in self.profile.devices.values():
            name_map[device.device_guid] = device.name
        for cond in self.all_conditions():
            if isinstance(cond, base_classes.JoystickCondition):
                name_map[cond.device_guid] = cond.device_name
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

    def _get_device(self, device_guid):
        """Returns the device corresponding to a given identifier.

        :return device_guid matching the identifier if present
        """
        for dev_guid, device in self.profile.devices.items():
            if dev_guid == device_guid:
                return device
        return None


class AbstractVirtualButton(metaclass=ABCMeta):

    """Base class of all virtual buttons."""

    def __init__(self):
        """Creates a new instance."""
        pass

    @abstractmethod
    def from_xml(self, node):
        """Populates the virtual button based on the node's data.

        :param node the node containing data for this instance
        """
        pass

    @abstractmethod
    def to_xml(self):
        """Returns an XML node representing the data of this instance.

        :return XML node containing the instance's data
        """
        pass


class VirtualAxisButton(AbstractVirtualButton):

    """Virtual button which turns an axis range into a button."""

    def __init__(self, lower_limit=0.0, upper_limit=0.0):
        """Creates a new instance.

        :param lower_limit the lower limit of the virtual button
        :param upper_limit the upper limit of the virtual button
        """
        super().__init__()
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.direction = gremlin.types.AxisButtonDirection.Anywhere

    def from_xml(self, node):
        """Populates the virtual button based on the node's data.

        :param node the node containing data for this instance
        """
        self.lower_limit = read_subelement(node, "lower-limit")
        self.upper_limit = read_subelement(node, "upper-limit")
        self.direction = read_subelement(node, "direction")

    def to_xml(self):
        """Returns an XML node representing the data of this instance.

        :return XML node containing the instance's data
        """
        node = ElementTree.Element("virtual-button")
        node.append(create_subelement_node("lower-limit", self.lower_limit))
        node.append(create_subelement_node("upper-limit", self.upper_limit))
        node.append(create_subelement_node("direction", self.direction))
        return node


class VirtualHatButton(AbstractVirtualButton):

    """Virtual button which combines hat directions into a button."""

    def __init__(self, directions=()):
        """Creates a instance.

        :param directions list of direction that form the virtual button
        """
        super().__init__()
        self.directions = list(set(directions))

    def from_xml(self, node):
        """Populates the activation condition based on the node's data.

        :param node the node containing data for this instance
        """
        self.directions = []
        for hd_node in node.findall("hat-direction"):
            self.directions.append(HatDirection.to_enum(hd_node.text))

    def to_xml(self):
        """Returns an XML node representing the data of this instance.

        :return XML node containing the instance's data
        """
        node = ElementTree.Element("virtual-button")
        for direction in self.directions:
            hd_node = ElementTree.Element("hat-direction")
            hd_node.text = HatDirection.to_string(direction)
            node.append(hd_node)
        return node


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
        self.default_delay = 0.05

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

        # Default delay
        delay_node = ElementTree.Element("default-delay")
        delay_node.text = safe_format(self.default_delay, float)
        node.append(delay_node)

        # Process vJoy as input settings
        for vid, value in self.vjoy_as_input.items():
            if value is True:
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

        # Default delay
        self.default_delay = 0.05
        if node.find("default-delay") is not None:
            self.default_delay = float(node.find("default-delay").text)

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

    """Stores the contents and an entire configuration profile."""

    def __init__(self):
        self.inputs = {}
        self.library = profile_library.Library()
        self.settings = Settings(self)
        self.modes = ModeHierarchy()
        self.plugins = []
        self.fpath = None

    def from_xml(self, fpath: str) -> None:
        # Parse file into an XML document
        self.fpath = fpath
        tree = ElementTree.parse(fpath)
        root = tree.getroot()

        self.library.from_xml(root)
        self.modes.from_xml(root)

        # Parse individual inputs
        for node in root.findall("./inputs/input"):
            item = InputItem(self.library)
            item.from_xml(node)

            if item.device_id not in self.inputs:
                self.inputs[item.device_id] = []
            self.inputs[item.device_id].append(item)

    def to_xml(self, fpath: str) -> None:
        root = ElementTree.Element("profile")
        root.set("version", str(ProfileConverter.current_version))

        inputs = ElementTree.Element("inputs")
        for device_data in self.inputs.values():
            for input_data in device_data:
                inputs.append(input_data.to_xml())
        root.append(inputs)
        root.append(self.settings.to_xml())
        root.append(self.library.to_xml())
        root.append(self.modes.to_xml())

        # User plugins
        plugins = ElementTree.Element("plugins")
        for plugin in self.plugins:
            plugins.append(plugin.to_xml())
        root.append(plugins)

        # Serialize XML document
        ugly_xml = ElementTree.tostring(root, encoding="utf-8")
        dom_xml = minidom.parseString(ugly_xml)
        with codecs.open(fpath, "w", "utf-8-sig") as out:
            out.write(dom_xml.toprettyxml(indent="    "))

    def get_input_item(
            self,
            device_guid: dill.GUID,
            input_type: InputType,
            input_id: int,
            create_if_missing: bool=False
    ) -> InputItem:
        """Returns the InputItem corresponding to the provided information.

        Args:
            device_guid: GUID of the device
            input_type: type of the input
            input_id: id of the input
            create_if_missing: If True will create an empty InputItem if none
                exists

        Returns:
            InputItem corresponding to the given information
        """
        if device_guid not in self.inputs:
            if create_if_missing:
                self.inputs[device_guid] = []
            else:
                raise error.ProfileError(
                    f"Device with GUID {device_guid} does not exist"
                )

        for item in self.inputs[device_guid]:
            if item.input_type == input_type and item.input_id == input_id:
                return item

        if create_if_missing:
            item = InputItem(self.library)
            item.device_id = device_guid
            item.input_type = input_type
            item.input_id = input_id
            self.inputs[device_guid].append(item)
            return item
        else:
            raise error.ProfileError(
                f"No data for input {InputType.to_string(input_type)} "
                f"{input_id} of device {device_guid}"
            )

    def _parse_actions(self, node: ElementTree.Element) -> List[Any]:
        pass


class InputItem:

    """Represents the configuration of a single input in a particular mode."""

    def __init__(self, library: profile_library.Library):
        """Creates a new instance."""
        self.device_id = None
        self.input_type = None
        self.input_id = None
        self.mode = None
        self.library = library
        self.action_configurations = []
        self.always_execute = False
        self.is_active = True

    def from_xml(self, node: ElementTree.Element):
        self.device_id = read_subelement(node, "device-id")
        self.input_type = read_subelement(node, "input-type")
        self.input_id = read_subelement(node, "input-id")
        self.mode = read_subelement(node, "mode")

        # If the input is from a keyboard convert the input id into
        # the scan code and extended input flag
        if self.input_type == InputType.Keyboard:
            self.input_id = (self.input_id & 0xFF, self.input_id >> 8)

        # Parse every action configuration entry
        for entry in node.findall("action-configuration"):
            action = ActionConfiguration(self)
            action.from_xml(entry)
            self.action_configurations.append(action)

    def to_xml(self) -> ElementTree.Element:
        node = ElementTree.Element("input")

        # Input item specification
        node.append(create_subelement_node("device-id", self.device_id))
        node.append(create_subelement_node("input-type", self.input_type))
        node.append(create_subelement_node("mode", self.mode))
        input_id = self.input_id
        # To convert keyboard input tuples (scan_code, extended_bit) to integer:
        # input_id = extended_bit << 8 | scan_code
        if self.input_type == InputType.Keyboard:
            input_id = self.input_id[1] << 8 | self.input_id[0]
        node.append(create_subelement_node("input-id", input_id))

        # Action configurations
        for entry in self.action_configurations:
            node.append(entry.to_xml())

        return node

    def descriptor(self) -> str:
        """Returns a string representation describing the input item.

        Returns:
            String identifying this input item in a textual manner
        """
        return f"{self.device_id}: {InputType.to_string(self.input_type)} " \
               f"{self.input_id}"


class ActionConfiguration:

    """Links together a LibraryItem and it's activation behaviour."""

    def __init__(self, input_item: InputItem):
        self.input_item = input_item
        self.description = ""
        self.library_reference = None
        self.behaviour = None
        self.virtual_button = None

    def from_xml(self, node: ElementTree.Element) -> None:
        self.description = read_subelement(node, "description")
        reference_id = read_subelement(node, "library-reference")
        if reference_id not in self.input_item.library:
            raise error.ProfileError(
                f"{self.input_item.descriptor()} links to an invalid library "
                f"item {reference_id}"
            )
        self.library_reference = self.input_item.library[reference_id]
        self.behaviour = read_subelement(node, "behaviour")
        self.virtual_button = self._parse_virtual_button(node)

    def to_xml(self) -> ElementTree.Element:
        node = ElementTree.Element("action-configuration")
        node.append(create_subelement_node("description", self.description))
        node.append(
            create_subelement_node("library-reference", self.library_reference.id)
        )
        node.append(create_subelement_node("behaviour", self.behaviour))
        vb_node = self._write_virtual_button()
        if vb_node is not None:
            node.append(vb_node)

        return node

    def _parse_virtual_button(self, node: ElementTree.Element) -> AbstractVirtualButton:
        # Ensure the configuration requires a virtual button
        virtual_button = None
        if self.input_item.input_type == InputType.JoystickAxis and \
                self.behaviour == InputType.JoystickButton:
            virtual_button = VirtualAxisButton()
        elif self.input_item.input_type == InputType.JoystickHat and \
                self.behaviour == InputType.JoystickButton:
            virtual_button = VirtualHatButton()

        # Ensure we have a virtual button entry to parse
        if virtual_button is not None:
            vb_node = node.find("virtual-button")
            if vb_node is None:
                raise error.ProfileError(
                    f"Missing virtual-button entry library item "
                    f"{self.library_reference.id}"
                )
            virtual_button.from_xml(vb_node)

        return virtual_button

    def _write_virtual_button(self) -> Optional[ElementTree.Element]:
        # Ascertain whether or not a virtual button node needs to be created
        needs_virtual_button = False
        if self.input_item.input_type == InputType.JoystickAxis and \
                self.behaviour == InputType.JoystickButton:
            needs_virtual_button = True
        elif self.input_item.input_type == InputType.JoystickHat and \
                self.behaviour == InputType.JoystickButton:
            needs_virtual_button = True

        # Ensure there is no virtual button information present
        # if it is not needed
        if not needs_virtual_button:
            self.virtual_button = None
            return None

        # Check we have virtual button data
        if self.virtual_button is None:
            raise error.ProfileError(
                f"Virtual button specification not present for action "
                f"configuration part of input {self.input_item.descriptor()}."
            )
        return self.virtual_button.to_xml()


class ModeHierarchy:

    def __init__(self):
        self.hierarchy = []

    @property
    def first_mode(self) -> str:
        """Returns the name of the first mode.

        Returns:
            Name of the first mode
        """
        return self.hierarchy[0].value

    def mode_list(self) -> List[str]:
        """Returns the list of all modes in the hierarchy.

        Returns:
            List of all mode names
        """
        mode_names = []
        stack = self.hierarchy[:]
        while len(stack) > 0:
            node = stack.pop()
            stack.extend(node.children[:])
            mode_names.append(node.value)
        return sorted(mode_names)

    def from_xml(self, root: ElementTree.Element) -> None:
        nodes = {}
        node_parents = {}
        # Parse individual nodes
        for node in root.findall("./modes/mode"):
            if "parent" in node.attrib:
                node_parents[node.text] = node.get("parent")
            nodes[node.text] = tree.TreeNode(node.text)

        # Reconstruct tree structure
        for child, parent in node_parents.items():
            nodes[child].set_parent(nodes[parent])

        self.hierarchy = []
        for node in nodes.values():
            if node.parent is None:
                self.hierarchy.append(node)

    def to_xml(self) -> ElementTree.Element:
        node = ElementTree.Element("nodes")

        for tree in self.hierarchy:
            for i in range(tree.node_count):
                tree_node = tree.node_at_index(i)
                n_mode = ElementTree.Element("mode")
                n_mode.text = tree_node.value
                if tree_node.depth > 0:
                    n_mode.set(
                        "parent",
                        safe_format(tree_node.parent.value, str)
                    )
                node.append(n_mode)

        return node


# class ProfileOld:
#
#     """Stores the contents of an entire configuration profile.
#
#     This includes configurations for each device's modes.
#     """
#
#     def __init__(self):
#         """Constructor creating a new instance."""
#         self.devices = {}
#         self.vjoy_devices = {}
#         self.merge_axes = []
#         self.plugins = []
#         self.settings = Settings(self)
#         self.library = Library()
#         self.parent = None
#
#     def initialize_joystick_device(self, device, modes):
#         """Ensures a joystick is properly initialized in the profile.
#
#         :param device the device to initialize
#         :param modes the list of modes to be present
#         """
#         new_device = Device(self)
#         new_device.name = device.name
#         new_device.device_guid = device.device_guid
#         new_device.type = DeviceType.Joystick
#         self.devices[device.device_guid] = new_device
#
#         for mode in modes:
#             new_device.ensure_mode_exists(mode)
#             new_mode = new_device.modes[mode]
#             # Touch every input to ensure it gets default initialized
#             for i in range(device.axis_count):
#                 if i >= len(device.axis_map):
#                     logging.getLogger("system").error(
#                         "{} invalid axis request {} < {}".format(
#                             device.name,
#                             device.axis_count,
#                             i
#                         )
#                     )
#                 else:
#                     new_mode.get_data(
#                         InputType.JoystickAxis,
#                         device.axis_map[i].axis_index
#                     )
#             for i in range(1, device.button_count+1):
#                 new_mode.get_data(InputType.JoystickButton, i)
#             for i in range(1, device.hat_count+1):
#                 new_mode.get_data(InputType.JoystickHat, i)
#
#     def build_inheritance_tree(self):
#         """Returns a tree structure encoding the inheritance between the
#         various modes.
#
#         :return tree encoding mode inheritance
#         """
#         tree = {}
#         for dev_id, device in self.devices.items():
#             for mode_name, mode in device.modes.items():
#                 if mode.inherit is None and mode_name not in tree:
#                     tree[mode_name] = {}
#                 elif mode.inherit:
#                     stack = [mode_name, ]
#                     parent = device.modes[mode.inherit]
#                     stack.append(parent.name)
#                     while parent.inherit is not None:
#                         parent = device.modes[parent.inherit]
#                         stack.append(parent.name)
#
#                     stack = list(reversed(stack))
#                     branch = tree
#                     for entry in stack:
#                         if entry not in branch:
#                             branch[entry] = {}
#                         branch = branch[entry]
#         return tree
#
#     def get_root_modes(self):
#         """Returns a list of root modes.
#
#         :return list of root modes
#         """
#         root_modes = []
#         for device in self.devices.values():
#             if device.type != DeviceType.Keyboard:
#                 continue
#             for mode_name, mode in device.modes.items():
#                 if mode.inherit is None:
#                     root_modes.append(mode_name)
#         return list(set(root_modes))
#
#     def list_unused_vjoy_inputs(self):
#         """Returns a list of unused vjoy inputs for the given profile.
#
#         :return dictionary of unused inputs for each input type
#         """
#         vjoy_devices = joystick_handling.vjoy_devices()
#
#         # Create list of all inputs provided by the vjoy devices
#         vjoy = {}
#         for entry in vjoy_devices:
#             vjoy[entry.vjoy_id] = {"axis": [], "button": [], "hat": []}
#             for i in range(entry.axis_count):
#                 vjoy[entry.vjoy_id]["axis"].append(
#                     entry.axis_map[i].axis_index
#                 )
#             for i in range(entry.button_count):
#                 vjoy[entry.vjoy_id]["button"].append(i+1)
#             for i in range(entry.hat_count):
#                 vjoy[entry.vjoy_id]["hat"].append(i+1)
#
#         # List all input types
#         all_input_types = [
#             InputType.JoystickAxis,
#             InputType.JoystickButton,
#             InputType.JoystickHat,
#             InputType.Keyboard
#         ]
#
#         # Create a list of all used remap actions
#         remap_actions = []
#         for dev in self.devices.values():
#             for mode in dev.modes.values():
#                 for input_type in all_input_types:
#                     for item in mode.config[input_type].values():
#                         for container in item.containers:
#                             remap_actions.extend(
#                                 extract_remap_actions(container.action_sets)
#                             )
#
#         # Remove all remap actions from the list of available inputs
#         for act in remap_actions:
#             # Skip remap actions that have invalid configuration
#             if act.input_type is None:
#                 continue
#
#             type_name = InputType.to_string(act.input_type)
#             if act.vjoy_input_id in [0, None] \
#                     or act.vjoy_device_id in [0, None] \
#                     or act.vjoy_input_id not in vjoy[act.vjoy_device_id][type_name]:
#                 continue
#
#             idx = vjoy[act.vjoy_device_id][type_name].index(act.vjoy_input_id)
#             del vjoy[act.vjoy_device_id][type_name][idx]
#
#         return vjoy
#
#     def from_xml(self, fname):
#         """Parses the global XML document into the profile data structure.
#
#         :param fname the path to the XML file to parse
#         """
#         # Check for outdated profile structure and warn user / convert
#         profile_converter = ProfileConverter()
#         profile_was_updated = False
#         if not profile_converter.is_current(fname):
#             logging.getLogger("system").warning("Outdated profile, converting")
#             profile_converter.convert_profile(fname)
#             profile_was_updated = True
#
#         tree = ElementTree.parse(fname)
#         root = tree.getroot()
#
#         # Parse library entries first so input items can link against them
#         # later on
#         self.library.from_xml(root.find("library"))
#
#         # Parse each device into separate DeviceConfiguration objects
#         for child in root.iter("device"):
#             device = Device(self)
#             device.from_xml(child)
#             self.devices[device.device_guid] = device
#
#         # Parse each vjoy device into separate DeviceConfiguration objects
#         for child in root.iter("vjoy-device"):
#             device = Device(self)
#             device.from_xml(child)
#             self.vjoy_devices[device.device_guid] = device
#
#         # Ensure that the profile contains an entry for every existing
#         # device even if it was not part of the loaded XML and
#         # replicate the modes present in the profile. This adds both entries
#         # for physical and virtual joysticks.
#         devices = joystick_handling.joystick_devices()
#         for dev in devices:
#             add_device = False
#             if dev.is_virtual and dev.device_guid not in self.vjoy_devices:
#                 add_device = True
#             elif not dev.is_virtual and dev.device_guid not in self.devices:
#                 add_device = True
#
#             if add_device:
#                 new_device = Device(self)
#                 new_device.name = dev.name
#                 if dev.is_virtual:
#                     new_device.type = DeviceType.VJoy
#                     new_device.device_guid = dev.device_guid
#                     self.vjoy_devices[dev.device_guid] = new_device
#                 else:
#                     new_device.type = DeviceType.Joystick
#                     new_device.device_guid = dev.device_guid
#                     self.devices[dev.device_guid] = new_device
#
#                 # Create required modes
#                 for mode in mode_list(new_device):
#                     if mode not in new_device.modes:
#                         new_device.modes[mode] = Mode(new_device)
#                         new_device.modes[mode].name = mode
#
#         # Parse merge axis entries
#         for child in root.iter("merge-axis"):
#             self.merge_axes.append(self._parse_merge_axis(child))
#
#         # Parse settings entries
#         self.settings.from_xml(root.find("settings"))
#
#         # Parse plugin entries
#         for child in root.findall("plugins/plugin"):
#             plugin = Plugin(self)
#             plugin.from_xml(child)
#             self.plugins.append(plugin)
#
#         return profile_was_updated
#
#     def to_xml(self, fname):
#         """Generates XML code corresponding to this profile.
#
#         :param fname name of the file to save the XML to
#         """
#         # Generate XML document
#         root = ElementTree.Element("profile")
#         root.set("version", str(ProfileConverter.current_version))
#
#         # Device settings
#         devices = ElementTree.Element("devices")
#         device_list = sorted(
#             self.devices.values(),
#             key=lambda x: str(x.device_guid)
#         )
#         for device in device_list:
#             devices.append(device.to_xml())
#         root.append(devices)
#
#         # VJoy settings
#         vjoy_devices = ElementTree.Element("vjoy-devices")
#         for device in self.vjoy_devices.values():
#             vjoy_devices.append(device.to_xml())
#         root.append(vjoy_devices)
#
#         # Merge axis data
#         for entry in self.merge_axes:
#             node = ElementTree.Element("merge-axis")
#             node.set("mode", safe_format(entry["mode"], str))
#             node.set("operation", safe_format(
#                 MergeAxisOperation.to_string(entry["operation"]),
#                 str
#             ))
#             for tag in ["vjoy"]:
#                 sub_node = ElementTree.Element(tag)
#                 sub_node.set(
#                     "vjoy-id",
#                     safe_format(entry[tag]["vjoy_id"], int)
#                 )
#                 sub_node.set("axis-id", safe_format(entry[tag]["axis_id"], int))
#                 node.append(sub_node)
#             for tag in ["lower", "upper"]:
#                 sub_node = ElementTree.Element(tag)
#                 sub_node.set("device-guid", write_guid(entry[tag]["device_guid"]))
#                 sub_node.set("axis-id", safe_format(entry[tag]["axis_id"], int))
#                 node.append(sub_node)
#             root.append(node)
#
#         # Settings data
#         root.append(self.settings.to_xml())
#
#         # Library entries
#         root.append(self.library.to_xml())
#
#         # User plugins
#         plugins = ElementTree.Element("plugins")
#         for plugin in self.plugins:
#             plugins.append(plugin.to_xml())
#         root.append(plugins)
#
#         # Serialize XML document
#         ugly_xml = ElementTree.tostring(root, encoding="utf-8")
#         dom_xml = minidom.parseString(ugly_xml)
#         with codecs.open(fname, "w", "utf-8-sig") as out:
#             out.write(dom_xml.toprettyxml(indent="    "))
#
#     def get_device_modes(self, device_guid, device_type, device_name=None):
#         """Returns the modes associated with the given device.
#
#         :param device_guid the device's GUID
#         :param device_type the type of the device being queried
#         :param device_name the name of the device
#         :return all modes for the specified device
#         """
#         if device_type == DeviceType.VJoy:
#             if device_guid not in self.vjoy_devices:
#                 # Create the device
#                 device = Device(self)
#                 device.name = device_name
#                 device.device_guid = device_guid
#                 device.type = DeviceType.VJoy
#                 self.vjoy_devices[device_guid] = device
#             return self.vjoy_devices[device_guid]
#
#         else:
#             if device_guid not in self.devices:
#                 # Create the device
#                 device = Device(self)
#                 device.name = device_name
#                 device.device_guid = device_guid
#
#                 # Set the correct device type
#                 device.type = DeviceType.Joystick
#                 if device_name == "keyboard":
#                     device.type = DeviceType.Keyboard
#                 self.devices[device_guid] = device
#             return self.devices[device_guid]
#
#     def empty(self):
#         """Returns whether or not a profile is empty.
#
#         :return True if the profile is empty, False otherwise
#         """
#         is_empty = True
#         is_empty &= len(self.merge_axes) == 0
#
#         # Enumerate all input devices
#         all_input_types = [
#             InputType.JoystickAxis,
#             InputType.JoystickButton,
#             InputType.JoystickHat,
#             InputType.Keyboard
#         ]
#
#         # Process all devices
#         for dev in self.devices.values():
#             for mode in dev.modes.values():
#                 for input_type in all_input_types:
#                     for item in mode.config[input_type].values():
#                         is_empty &= len(item.library_references) == 0
#
#         # Process all vJoy devices
#         for dev in self.vjoy_devices.values():
#             for mode in dev.modes.values():
#                 for input_type in all_input_types:
#                     for item in mode.config[input_type].values():
#                         is_empty &= len(item.library_references) == 0
#
#         return is_empty
#
#     def _parse_merge_axis(self, node):
#         """Parses merge axis entries.
#
#         :param node the node to process
#         :return merge axis data structure parsed from the XML node
#         """
#         entry = {
#             "mode": node.get("mode", None),
#             "operation": MergeAxisOperation.to_enum(
#                 safe_read(node, "operation", str, "average")
#             )
#         }
#         for tag in ["vjoy"]:
#             entry[tag] = {
#                 "vjoy_id": safe_read(node.find(tag), "vjoy-id", int),
#                 "axis_id": safe_read(node.find(tag), "axis-id", int),
#             }
#         for tag in ["lower", "upper"]:
#             entry[tag] = {
#                 "device_guid": util.parse_guid(node.find(tag).get("device-guid")),
#                 "axis_id": safe_read(node.find(tag), "axis-id", int)
#             }
#
#         return entry
#
#
# class Device:
#
#     """Stores the information about a single device including it's modes."""
#
#     def __init__(self, parent):
#         """Creates a new instance.
#
#         :param parent the parent profile of this device
#         """
#         self.parent = parent
#         self.name = None
#         self.label = ""
#         self.device_guid = None
#         self.modes = {}
#         self.type = None
#
#     def ensure_mode_exists(self, mode_name, device=None):
#         """Ensures that a specified mode exists, creating it if needed.
#
#         :param mode_name the name of the mode being checked
#         :param device a device to initialize for this mode if specified
#         """
#         if mode_name in self.modes:
#             mode = self.modes[mode_name]
#         else:
#             mode = Mode(self)
#             mode.name = mode_name
#             self.modes[mode.name] = mode
#
#         if device is not None:
#             for i in range(device.axis_count):
#                 if i >= len(device.axis_map):
#                     logging.getLogger("system").error(
#                         "{} invalid axis request {} < {}".format(
#                             device.name,
#                             device.axis_count,
#                             i
#                         )
#                     )
#                 else:
#                     mode.get_data(
#                         InputType.JoystickAxis,
#                         device.axis_map[i].axis_index
#                     )
#             for idx in range(1, device.button_count + 1):
#                 mode.get_data(InputType.JoystickButton, idx)
#             for idx in range(1, device.hat_count + 1):
#                 mode.get_data(InputType.JoystickHat, idx)
#
#     def from_xml(self, node):
#         """Populates this device based on the xml data.
#
#         :param node the xml node to parse to populate this device
#         """
#         self.name = node.get("name")
#         self.label = safe_read(node, "label", default_value=self.name)
#         self.type = DeviceType.to_enum(safe_read(node, "type", str))
#         self.device_guid = util.parse_guid(node.get("device-guid"))
#
#         for child in node:
#             mode = Mode(self)
#             mode.from_xml(child)
#             self.modes[mode.name] = mode
#
#     def to_xml(self):
#         """Returns a XML node representing this device's contents.
#
#         :return xml node of this device's contents
#         """
#         node_tag = "device" if self.type != DeviceType.VJoy else "vjoy-device"
#         node = ElementTree.Element(node_tag)
#         node.set("name", safe_format(self.name, str))
#         node.set("label", safe_format(self.label, str))
#         node.set("device-guid", write_guid(self.device_guid))
#         node.set("type", DeviceType.to_string(self.type))
#         for mode in sorted(self.modes.values(), key=lambda x: x.name):
#             node.append(mode.to_xml())
#         return node
#
#
# class Mode:
#
#     """Represents the configuration of the mode of a single device."""
#
#     def __init__(self, parent):
#         """Creates a new DeviceConfiguration instance.
#
#         :param parent the parent device of this mode
#         """
#         self.parent = parent
#         self.inherit = None
#         self.name = None
#
#         self.config = {
#             InputType.JoystickAxis: {},
#             InputType.JoystickButton: {},
#             InputType.JoystickHat: {},
#             InputType.Keyboard: {}
#         }
#
#     def from_xml(self, node):
#         """Parses the XML mode data.
#
#         :param node XML node to parse
#         """
#         self.name = safe_read(node, "name", str)
#         self.inherit = node.get("inherit", None)
#         for child in node:
#             item = InputItem(self)
#             item.from_xml(child)
#
#             store_item = True
#             # This can fail if the device in question is not connected, in
#             # which case we'll simply save the action item without
#             # verification.
#             if item.input_type == InputType.JoystickAxis \
#                     and dill.DILL.device_exists(self.parent.device_guid):
#                 joy = input_devices.JoystickProxy()[self.parent.device_guid]
#                 store_item = joy.is_axis_valid(item.input_id)
#
#             if store_item:
#                 self.config[item.input_type][item.input_id] = item
#
#     def to_xml(self):
#         """Generates XML code for this DeviceConfiguration.
#
#         :return XML node representing this object's data
#         """
#         node = ElementTree.Element("mode")
#         node.set("name", safe_format(self.name, str))
#         if self.inherit is not None:
#             node.set("inherit", safe_format(self.inherit, str))
#         input_types = [
#             InputType.JoystickAxis,
#             InputType.JoystickButton,
#             InputType.JoystickHat,
#             InputType.Keyboard
#         ]
#         for input_type in input_types:
#             item_list = sorted(
#                 self.config[input_type].values(),
#                 key=lambda x: x.input_id
#             )
#             for item in item_list:
#                 node.append(item.to_xml())
#         return node
#
#     def delete_data(self, input_type, input_id):
#         """Deletes the data associated with the provided
#         input item entry.
#
#         :param input_type the type of the input
#         :param input_id the index of the input
#         """
#         if input_id in self.config[input_type]:
#             del self.config[input_type][input_id]
#
#     def get_data(self, input_type, input_id):
#         """Returns the configuration data associated with the provided
#         InputItem entry.
#
#         :param input_type the type of input
#         :param input_id the id of the given input type
#         :return InputItem corresponding to the provided combination of
#             type and id
#         """
#         assert(input_type in self.config)
#         if input_id == 1 and input_type == InputType.JoystickAxis:
#             pass
#         if input_id not in self.config[input_type]:
#             entry = InputItem(self)
#             entry.input_type = input_type
#             entry.input_id = input_id
#             self.config[input_type][input_id] = entry
#         return self.config[input_type][input_id]
#
#     def set_data(self, input_type, input_id, data):
#         """Sets the data of an InputItem.
#
#         :param input_type the type of the InputItem
#         :param input_id the id of the InputItem
#         :param data the data of the InputItem
#         """
#         assert(input_type in self.config)
#         self.config[input_type][input_id] = data
#
#     def has_data(self, input_type, input_id):
#         """Returns True if data for the given input exists, False otherwise.
#
#         :param input_type the type of the InputItem
#         :param input_id the id of the InputItem
#         :return True if data exists, False otherwise
#         """
#         return input_id in self.config[input_type]
#
#     def all_input_items(self):
#         for input_type in self.config.values():
#             for input_item in input_type.values():
#                 yield input_item
#
#
# class InputItemOld:
#
#     """Represents a single input item such as a button or axis.
#
#     Each input item holds information about the type of input it is and
#     what mode and device it is connected to. The configuration about what
#     happens when the particular input is activated is stored as a list
#     of references to library entries.
#     """
#
#     def __init__(self, parent):
#         """Creates a new InputItem instance.
#
#         Parameters
#         ==========
#         parent : profile.Mode
#             Mode which contains this instance
#         """
#         assert(isinstance(parent, Mode))
#         self.parent = parent
#         self.input_type = None
#         self.input_id = None
#         self.always_execute = False
#         self.description = ""
#         self.library=_references = []
#
#     def from_xml(self, node):
#         """Parses an InputItem node to populate this instance.
#
#         Parameters
#         ==========
#         node : ElementTree.Element
#             XML node containing the information
#         """
#         self.input_type = InputType.to_enum(node.tag)
#         self.input_id = safe_read(node, "id", int)
#         self.description = safe_read(node, "description", str)
#         self.always_execute = read_bool(node, "always-execute", False)
#         if self.input_type == InputType.Keyboard:
#             self.input_id = (self.input_id, read_bool(node, "extended"))
#         for entry in node.findall("library-reference"):
#             reference = LibraryReference(self)
#             reference.from_xml(entry)
#             self.library_references.append(reference)
#
#     def to_xml(self):
#         """Returns an XML node encoding the content of this InputItem.
#
#         Returns
#         =======
#         ElementTree.Element
#             XML node holding the instance's content
#         """
#         node = ElementTree.Element(InputType.to_string(self.input_type))
#         if self.input_type == InputType.Keyboard:
#             node.set("id", safe_format(self.input_id[0], int))
#             node.set("extended", safe_format(self.input_id[1], bool))
#         else:
#             node.set("id", safe_format(self.input_id, int))
#
#         if self.always_execute:
#             node.set("always-execute", "True")
#
#         if self.description:
#             node.set("description", safe_format(self.description, str))
#         else:
#             node.set("description", "")
#
#         for entry in self.library_references:
#             node.append(entry.to_xml())
#
#         return node
#
#     def get_device_type(self):
#         """Returns the DeviceType of this input item.
#
#         Returns
#         =======
#         gremlin.types.DeviceType
#             DeviceType of this instance
#         """
#         item = self.parent
#         while not isinstance(item, Device):
#             item = item.parent
#         return item.type
#
#     def get_input_type(self):
#         """Returns the InputType of this input.
#
#         Returns
#         =======
#         gremlin.types.InputType
#             InputType of this instance
#         """
#         return self.input_type
#
#     def __eq__(self, other):
#         """Checks whether or not two InputItem instances are identical.
#
#         Parameters
#         ==========
#         other : profile.InputItem
#             InputItem to compare with for identity
#
#         Returns
#         =======
#         bool
#             True if both instances are identical, False otherwise
#         """
#         assert(isinstance(other, InputItem))
#         return self.__hash__() == other.__hash__()
#
#     def __hash__(self):
#         """Returns the hash of this InputItem instance.
#
#         The hash takes into account to which device and mode the input item is
#         associated with.
#
#         Returns
#         =======
#         int
#             Hash value for this InputItem
#         """
#         return hash((
#             self.parent.parent.device_guid,
#             self.input_type,
#             self.input_id
#         ))


class Plugin:

    """Represents an unconfigured plugin."""

    def __init__(self, parent):
        """Creates a new instance.

        Parameters
        ==========
        parent : object
            The parent object of this plugin
        """
        self.parent = parent
        self.file_name = None
        self.instances = []

    def from_xml(self, node):
        """Initializes the values of this instance based on the node's contents.

        Parameters
        ==========
        node : ElementTree.Element
            XML node containing this instance's configuration
        """
        self.file_name = safe_read(node, "file-name", str, None)
        for child in node.iter("instance"):
            instance = PluginInstance(self)
            instance.from_xml(child)
            self.instances.append(instance)

    def to_xml(self):
        """Returns an XML node representing this instance.

        Returns
        =======
        ElementTree.Element
            XML node representing this instance
        """
        node = ElementTree.Element("plugin")
        node.set("file-name", safe_format(self.file_name, str))
        for instance in self.instances:
            if instance.is_configured():
                node.append(instance.to_xml())
        return node


class PluginInstance:

    """Instantiation of a usrer plugin with its own set of parameters."""

    def __init__(self, parent):
        """Creates a new instance.

        Parameters
        ==========
        parent : object
            The parent object of this plugin
        """
        self.parent = parent
        self.name = None
        self.variables = {}

    def is_configured(self):
        """Returns whether or not the instance is properly configured.

        Returns
        =======
        bool
            True if the instance is fully configured, False otherwise
        """
        is_configured = True
        for var in [var for var in self.variables.values() if not var.is_optional]:
            is_configured &= var.value is not None
        return is_configured

    def has_variable(self, name):
        """Returns whether or not this instance has a particular variable.

        Parameters
        ==========
        name : str
            Name of the variable to check the existence of

        Returns
        =======
        bool
            True if a variable with the given name exists, False otherwise
        """
        return name in self.variables

    def set_variable(self, name, variable):
        """Sets a named variable.

        Parameters
        ==========
        name : str
            Name of the variable object to be set
        variable : PluginVariable
            Variable to store
        """
        self.variables[name] = variable

    def get_variable(self, name):
        """Returns the variable stored under the specified name.

        If no variable with the specified name exists, a new empty variable
        will be created and returned.

        Parameters
        ==========
        name : str
            Name of the variable to return

        Returns
        =======
        PluginVariable
            Variable corresponding to the specified name
        """
        if name not in self.variables:
            var = PluginVariable(self)
            var.name = name
            self.variables[name] = var

        return self.variables[name]

    def from_xml(self, node):
        """Initializes the contents of this instance.

        Parameters
        ==========
        node : ElementTree.Element
            XML node containing this instance's configuration
        """
        self.name = safe_read(node, "name", str, "")
        for child in node.iter("variable"):
            variable = PluginVariable(self)
            variable.from_xml(child)
            self.variables[variable.name] = variable

    def to_xml(self):
        """Returns an XML node representing this instance.

        Returns
        =======
        ElementTree.Element
            XML node representing this instance
        """
        node = ElementTree.Element("instance")
        node.set("name", safe_format(self.name, str))
        for variable in self.variables.values():
            variable_node = variable.to_xml()
            if variable_node is not None:
                node.append(variable_node)
        return node


class PluginVariable:

    """A single variable of a user plugin instance."""

    def __init__(self, parent):
        """Creates a new instance.

        Parameters
        ==========
        parent : object
            The parent object of this plugin
        """
        self.parent = parent
        self.name = None
        self.type = None
        self.value = None
        self.is_optional = False

    def from_xml(self, node):
        """Initializes the contents of this instance.

        Parameters
        ==========
        node : ElementTree.Element
            XML node containing this instance's configuration
        """
        self.name = safe_read(node, "name", str, "")
        self.type = PluginVariableType.to_enum(
            safe_read(node, "type", str, "String")
        )
        self.is_optional = read_bool(node, "is-optional")

        # Read variable content based on type information
        if self.type == PluginVariableType.Int:
            self.value = safe_read(node, "value", int, 0)
        elif self.type == PluginVariableType.Float:
            self.value = safe_read(node, "value", float, 0.0)
        elif self.type == PluginVariableType.Selection:
            self.value = safe_read(node, "value", str, "")
        elif self.type == PluginVariableType.String:
            self.value = safe_read(node, "value", str, "")
        elif self.type == PluginVariableType.Bool:
            self.value = read_bool(node, "value", False)
        elif self.type == PluginVariableType.Mode:
            self.value = safe_read(node, "value", str, "")
        elif self.type == PluginVariableType.PhysicalInput:
            self.value = {
                "device_id": util.parse_guid(node.attrib["device-guid"]),
                "device_name": safe_read(node, "device-name", str, ""),
                "input_id": safe_read(node, "input-id", int, None),
                "input_type": InputType.to_enum(
                    safe_read(node, "input-type", str, None)
                )
            }
        elif self.type == PluginVariableType.VirtualInput:
            self.value = {
                "device_id": safe_read(node, "vjoy-id", int, None),
                "input_id": safe_read(node, "input-id", int, None),
                "input_type": InputType.to_enum(
                    safe_read(node, "input-type", str, None)
                )
            }

    def to_xml(self):
        """Returns an XML node representing this instance.

        Returns
        =======
        ElementTree.Element
            XML node representing this instance
        """
        if self.value is None:
            return None

        node = ElementTree.Element("variable")
        node.set("name", safe_format(self.name, str))
        node.set("type", PluginVariableType.to_string(self.type))
        node.set("is-optional", safe_format(self.is_optional, bool, str))

        # Write out content based on the type
        if self.type in [
            PluginVariableType.Int, PluginVariableType.Float,
            PluginVariableType.Mode, PluginVariableType.Selection,
            PluginVariableType.String,
        ]:
            node.set("value", str(self.value))
        elif self.type == PluginVariableType.Bool:
            node.set("value", "1" if self.value else "0")
        elif self.type == PluginVariableType.PhysicalInput:
            node.set("device-guid", write_guid(self.value["device_id"]))
            node.set("device-name", safe_format(self.value["device_name"], str))
            node.set("input-id", safe_format(self.value["input_id"], int))
            node.set("input-type", InputType.to_string(self.value["input_type"]))
        elif self.type == PluginVariableType.VirtualInput:
            node.set("vjoy-id", safe_format(self.value["device_id"], int))
            node.set("input-id", safe_format(self.value["input_id"], int))
            node.set("input-type", InputType.to_string(self.value["input_type"]))

        return node
