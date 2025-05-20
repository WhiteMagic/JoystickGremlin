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

from __future__ import annotations

from abc import abstractmethod, ABCMeta
import codecs
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING, Callable
import uuid
from xml.dom import minidom
from xml.etree import ElementTree

import PySide6.QtCore

import dill

import action_plugins
from gremlin.types import AxisButtonDirection, InputType, HatDirection, \
    ScriptVariableType, PropertyType
from gremlin import error, plugin_manager, util
from gremlin.intermediate_output import IntermediateOutput
from gremlin.tree import TreeNode
from gremlin.user_script import Script
from gremlin.util import safe_read, safe_format, read_action_ids, read_bool, \
    read_subelement, create_subelement_node


if TYPE_CHECKING:
    from gremlin.base_classes import AbstractActionData


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


class AbstractVirtualButton(metaclass=ABCMeta):

    """Base class of all virtual buttons."""

    def __init__(self):
        """Creates a new instance."""
        pass

    @abstractmethod
    def from_xml(self, node: ElementTree) -> None:
        """Populates the virtual button based on the node's data.

        Args:
            node: the XML node containing data for this instance
        """
        pass

    @abstractmethod
    def to_xml(self) -> ElementTree:
        """Returns an XML node representing the data of this instance.

        Returns:
            XML node containing the instance's data
        """
        pass


class VirtualAxisButton(AbstractVirtualButton):

    """Virtual button which turns an axis range into a button."""

    def __init__(self, lower_limit: float=0.0, upper_limit: float=0.0):
        """Creates a new instance.

        Args:
            lower_limit: the lower limit of the virtual button
            upper_limit: the upper limit of the virtual button
        """
        super().__init__()

        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.direction = AxisButtonDirection.Anywhere

    def from_xml(self, node: ElementTree) -> None:
        """Populates the virtual button based on the node's data.

        Args:
            node: the node containing data for this instance
        """
        self.lower_limit = read_subelement(node, "lower-limit")
        self.upper_limit = read_subelement(node, "upper-limit")
        self.direction = read_subelement(node, "axis-button-direction")

    def to_xml(self) -> ElementTree:
        """Returns an XML node representing the data of this instance.

        Returns:
            XML node containing the instance's data
        """
        node = ElementTree.Element("virtual-button")
        node.append(create_subelement_node("lower-limit", self.lower_limit))
        node.append(create_subelement_node("upper-limit", self.upper_limit))
        node.append(
            create_subelement_node("axis-button-direction", self.direction)
        )
        return node


class VirtualHatButton(AbstractVirtualButton):

    """Virtual button which combines hat directions into a button."""

    def __init__(self, directions: Set=()):
        """Creates a instance.

        Args:
            directions: list of direction that form the virtual button
        """
        super().__init__()

        self.directions = list(set(directions))

    def from_xml(self, node: ElementTree) -> None:
        """Populates the activation condition based on the node's data.

        Args:
            node: the node containing data for this instance
        """
        self.directions = []
        for hd_node in node.findall("hat-direction"):
            self.directions.append(HatDirection.to_enum(hd_node.text))

    def to_xml(self) -> ElementTree:
        """Returns an XML node representing the data of this instance.

        Returns:
            XML node containing the instance's data
        """
        node = ElementTree.Element("virtual-button")
        for direction in self.directions:
            hd_node = ElementTree.Element("hat-direction")
            hd_node.text = HatDirection.to_string(direction)
            node.append(hd_node)
        return node


class Settings:

    """Stores general profile specific settings."""

    def __init__(self, parent: Profile):
        """Creates a new instance.

        Args:
            parent the parent profile
        """
        self.parent = parent
        self.vjoy_as_input = {}
        self.vjoy_initial_values = {}
        self.startup_mode = None
        self.default_delay = 0.05

    def from_xml(self, node: ElementTree) -> None:
        """Populates the data storage with the XML node's contents.

        Args:
            node the node containing the settings data
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

    def to_xml(self) -> ElementTree:
        """Returns an XML node containing the settings.

        Returns:
            XML node containing the settings
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

    def get_initial_vjoy_axis_value(self, vid: int, aid: int) -> float:
        """Returns the initial value a vJoy axis should use.

        Args:
            vid the id of the virtual joystick
            aid the id of the axis

        Returns:
            default value for the specified axis
        """
        value = 0.0
        if vid in self.vjoy_initial_values:
            if aid in self.vjoy_initial_values[vid]:
                value = self.vjoy_initial_values[vid][aid]
        return value

    def set_initial_vjoy_axis_value(
        self,
        vid: int,
        aid: int,
        value: float
    ) -> None:
        """Sets the default value for a particular vJoy axis.

        Args:
            vid the id of the virtual joystick
            aid the id of the axis
            value the default value to use with the specified axis
        """
        if vid not in self.vjoy_initial_values:
            self.vjoy_initial_values[vid] = {}
        self.vjoy_initial_values[vid][aid] = value


class Library:

    """Stores actions in order to be reference by input binding instances.

    Each item is a self-contained entry with a UUID assigned to it which
    is used by the input items to reference the actual content.
    """

    def __init__(self):
        """Creates a new library instance.

        The library contains both the individual action configurations as well
        as the items composed of them.
        """
        self._actions: Dict[uuid.UUID, AbstractActionData] = {}

    def add_action(self, action: AbstractActionData) -> None:
        if action.id in self._actions:
            logging.getLogger("system").warning(
                f"Action with id {action.id} already exists, skipping."
            )
        self._actions[action.id] = action

    def delete_action(self, key: uuid.UUID) -> None:
        """Deletes the action with the given key from the library.

        Args:
            key: the key of the action to delete
        """
        if key not in self._actions:
            logging.getLogger("system").warning(
                f"Attempting to remove non-existant action with id {key}."
            )
        if key in self._actions:
            del self._actions[key]

    def remove_unused(
        self,
        action: AbstractActionData,
        recursive: bool=True
    ) -> None:
        """Removes the provided action and all its children if unsued.

        Args:
            action: the action to remove
            recursive: if true all children of the action will be subjected
                to the same removal check
        """
        # If the action occurs in another action we can abort any further
        # processing
        for entry in self._actions.values():
            if action in entry.get_actions():
                return

        # Build a list of all actions linked to the provided action and then
        # attempt to remove them one after the other
        if recursive:
            all_actions = [action]
            index = 0
            while index < len(all_actions):
                all_actions.extend(all_actions[index].get_actions())
                index += 1
            all_actions.pop(0)

            for entry in reversed(all_actions):
                self.remove_unused(entry, True)

        del self._actions[action.id]

    def actions_by_type(
            self,
            action_type: type[AbstractActionData]
    ) -> List[AbstractActionData]:
        """Returns all actions in the library matching the given type.

        Args:
            action_type: type of the action to return

        Returns:
            All actions of the given type
        """
        return [a for a in self._actions.values() if isinstance(a, action_type)]

    def actions_by_predicate(
            self,
            predicate: Callable[[AbstractActionData], bool]
    ) -> List[AbstractActionData]:
        """Returns the list of actions fulfilling the given predicate.

        Args:
            predicate: the predicate to evaluate on each action

        Returns:
            List of all actions fulfilling the given predicate
        """
        actions = []
        for action in self._actions.values():
            if predicate(action):
                actions.append(action)
        return actions


    def get_action(self, key: uuid.UUID) -> AbstractActionData:
        """Returns the action specified by the key.

        If there is no action with the specified key an exception is throw.

        Args:
            key: the key to return an action for

        Returns:
            The  instance stored at the given key
        """
        if key not in self._actions:
            raise error.GremlinError(f"Invalid key for library action: {key}")
        return self._actions[key]

    def has_action(self, key: uuid.UUID) -> bool:
        """Checks if an action exists with the given key.

        Args:
            key: the key to check for

        Returns:
            True if an action exists for the specific key, False otherwise
        """
        return key in self._actions

    def from_xml(self, node: ElementTree.Element) -> None:
        """Parses a library node to populate this instance.

        Args:
            node: XML node containing the library information
        """
        parse_later = []
        can_parse = lambda entry: all([
            aid in self._actions for aid in read_action_ids(entry)
        ])

        # Parse all actions
        for entry in node.findall("./library/action"):
            # Ensure all required attributes are present
            if not set(["id", "type"]).issubset(entry.keys()):
                raise error.ProfileError(
                    "Incomplete library action specification"
                )

            # Ensure the action type is known
            type_key = entry.get("type")
            if type_key not in plugin_manager.PluginManager().tag_map:
                action_id = safe_read(entry, "id", uuid.UUID)
                raise error.ProfileError(
                    f"Unknown type '{type_key}' in action with id '{action_id}'"
                )

            # Check if all actions referenced by this action have already
            # been parsed, if yes parse it otherwise attempt to process it
            # again at a later stage.
            if can_parse(entry):
                self._parse_xml_action(entry)
            else:
                parse_later.append(entry)


        # Parse all actions that have missing child actions and repeat this
        # until no action with missing child actions remains.
        iterations = 0
        action_set = None
        while len(parse_later) > 0:
            entry = parse_later.pop(0)
            if can_parse(entry):
                self._parse_xml_action(entry)
                iterations = 0
            else:
                parse_later.append(entry)

            # Compute a hash from all the actions to parse
            new_action_set = set(parse_later)
            if new_action_set != action_set:
                new_action_set = action_set
            else:
                iterations += 1
                if iterations > 5:
                    logging.getLogger("system").error(
                        f"Loading profile failed due to action resolution chain"
                    )
                    break


    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the content of this library.

        Returns:
            XML node holding the instance's content
        """
        # Process the entire library, removing links to invalid actions
        invalid_aids = [n.id for n in self._actions.values() if not n.is_valid()]
        for action in self._actions.values():
            for selector in action._valid_selectors():
                to_remove = []
                for i, child in enumerate(action.get_actions(selector)[0]):
                    if child.id in invalid_aids:
                        to_remove.append(i)
                for i in to_remove:
                    action.remove_action(i, selector)

        # Generate library subtree
        node = ElementTree.Element("library")
        for action in [n for n in self._actions.values() if n.is_valid()]:
            node.append(action.to_xml())
        return node

    def _parse_xml_action(self, action: ElementTree.Element) -> None:
        """Parses an action XML node and stores it within the library.

        Args:
            action: XML node to parse
        """
        type_key = action.get("type")
        action_obj = plugin_manager.PluginManager().tag_map[type_key]()
        action_obj.from_xml(action, self)
        if action_obj.id in self._actions:
            raise error.ProfileError(
                f"Duplicate library action entry with id '{action_obj.id}'"
            )
        self._actions[action_obj.id] = action_obj


class Profile:

    """Stores the contents and an entire configuration profile."""

    current_version = 14

    def __init__(self):
        self.inputs = {}
        self.library = Library()
        self.settings = Settings(self)
        self.modes = ModeHierarchy(self)
        self.scripts = ScriptManager(self)
        self.fpath = None

    def from_xml(self, fpath: str) -> None:
        """Reads the content of an XML file and initializes the profile.

        Args:
            fpath: path to the XML file to parse
        """
        # Parse file into an XML document
        self.fpath = fpath
        tree = ElementTree.parse(fpath)
        root = tree.getroot()

        # Process all intermediate output system inputs
        for node in root.findall(
            f"./inputs/input[device-id='{str(dill.UUID_IntermediateOutput)}']"
        ):
            self._create_io_input(node)

        # Create library entries and modes
        # self.settings.from_xml(root)
        self.library.from_xml(root)
        self.modes.from_xml(root)
        self.scripts.from_xml(root)

        # Parse individual inputs
        for node in root.findall("./inputs/input"):
            self._process_input(node)

    def to_xml(self, fpath: str) -> None:
        """Writes the profile's content to an XML file.

        Args:
            fpath: path to the XML file in which to write the content
        """
        root = ElementTree.Element("profile")
        root.set("version", str(Profile.current_version))

        # Inputs
        inputs = ElementTree.Element("inputs")
        for device_data in self.inputs.values():
            for input_data in device_data:
                if len(input_data.action_sequences) > 0:
                    inputs.append(input_data.to_xml())
        root.append(inputs)

        # Managed content
        # root.append(self.settings.to_xml())
        root.append(self.library.to_xml())
        root.append(self.modes.to_xml())
        root.append(self.scripts.to_xml())

        # Serialize XML document
        ugly_xml = ElementTree.tostring(root, encoding="utf-8")
        dom_xml = minidom.parseString(ugly_xml)
        with codecs.open(fpath, "w", "utf-8-sig") as out:
            out.write(dom_xml.toprettyxml(indent="    "))

    def get_input_count(
            self,
            device_guid: uuid.UUID,
            input_type: InputType,
            input_id: int,
            mode: str
    ) -> int:
        """Returns the number of InputItem instances corresponding to the
        provided information.

        Args:
            device_guid: GUID of the device
            input_type: type of the input
            input_id: id of the input
            mode: name of the mode

        Returns:
            Number of InputItem instances linked with the given information
        """
        if device_guid not in self.inputs:
            return 0

        for item in self.inputs[device_guid]:
            if item.input_type == input_type and item.input_id == input_id \
                    and item.mode == mode:
                return len(item.action_sequences)

        return 0

    def get_input_item(
            self,
            device_guid: uuid.UUID,
            input_type: InputType,
            input_id: int | uuid.UUID,
            mode: str,
            create_if_missing: bool=False
    ) -> InputItem | None:
        """Returns the InputItem corresponding to the provided information.

        Args:
            device_guid: GUID of the device
            input_type: type of the input
            input_id: id of the input
            mode: name of the mode of the input item
            create_if_missing: If True will create an empty InputItem if none
                exists

        Returns:
            InputItem corresponding to the given information
        """
        # Verify provided information has correct type information
        if not (
                isinstance(device_guid, uuid.UUID) and
                isinstance(input_type, InputType) and
                type(input_id) in [int, uuid.UUID] and
                isinstance(mode, str)
        ):
            raise error.ProfileError("Invalid input specification provided.")

        if device_guid not in self.inputs:
            if create_if_missing:
                self.inputs[device_guid] = []
            else:
                return None

        for item in self.inputs[device_guid]:
            if item.input_type == input_type and \
                    item.input_id == input_id and \
                    item.mode == mode:
                return item

        if create_if_missing:
            item = InputItem(self.library)
            item.device_id = device_guid
            item.input_type = input_type
            item.input_id = input_id
            item.mode = mode
            self.inputs[device_guid].append(item)
            return item
        else:
            return None

    def remove_action(
        self,
        action: AbstractActionData,
        binding: InputItemBinding
    ) -> None:
        """Removes an action from the specified InputBinding instance.

        Args:
            action: the action instance to remove
            binding: the InputBinding instance from which to remove the action
        """
        # Remove action from its parent
        all_actions = [
            (binding.root_action, child) for child in binding.root_action.get_actions()
        ]
        while len(all_actions) > 0:
            entry = all_actions.pop(0)
            all_actions.extend([
                (entry[1], child) for child in entry[1].get_actions()
            ])

            if entry[1] == action:
                entry[0].remove_action(action)
                break

        # Remove the action and its children from the library if they are
        # unused
        self.library.remove_unused(action, recursive=True)

    def _process_input(self, node: ElementTree) -> None:
        """Processes an InputItem XML node and stores it.

        Args:
            node: XML node containing InputItem data
        """
        item = InputItem(self.library)
        item.from_xml(node)

        if item.device_id not in self.inputs:
            self.inputs[item.device_id] = []
        self.inputs[item.device_id].append(item)

    def _create_io_input(self, node: ElementTree) -> None:
        """Creates an intermediate output input for the given node.

        Args:
            node: XML node corresponding to an IO input
        """
        io = IntermediateOutput()
        io.create(
            read_subelement(node, "input-type"),
            input_id=read_subelement(node, "input-id"),
            label=read_subelement(node, "label")
        )


class InputItem:

    """Represents the configuration of a single input in a particular mode."""

    def __init__(self, library: Library):
        """Creates a new instance.

        Args:
            library: library instance that contains all action definitions
        """
        self.device_id = None
        self.input_type = None
        self.input_id = None
        self.mode = None
        self.library = library
        self.action_sequences = []
        self.is_active = True

    def from_xml(self, node: ElementTree.Element) -> None:
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
            action = InputItemBinding(self)
            action.from_xml(entry)
            self.action_sequences.append(action)

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

        # Write label if an intermediate output item is serialized
        if self.device_id == dill.UUID_IntermediateOutput:
            io = IntermediateOutput()
            node.append(create_subelement_node(
                "label",
                io[self.input_id].label
            ))

        # Action configurations
        for entry in self.action_sequences:
            node.append(entry.to_xml())

        return node

    def descriptor(self) -> str:
        """Returns a string representation describing the input item.

        Returns:
            String identifying this input item in a textual manner
        """
        return f"{self.device_id}: {InputType.to_string(self.input_type)} " \
               f"{self.input_id}"

    def remove_item_binding(self, binding: InputItemBinding) -> None:
        """Removes the given binding instance if present.

        Args:
            binding: InputItemBinding instance to remove from the item
        """
        if binding in self.action_sequences:
            del self.action_sequences[self.action_sequences.index(binding)]


class InputItemBinding:

    """Links together a LibraryItem and it's activation behavior."""

    def __init__(self, input_item: InputItem):
        self.input_item = input_item
        self.root_action = None
        self.behavior = None
        self.virtual_button = None

    def from_xml(self, node: ElementTree.Element) -> None:
        root_id = read_subelement(node, "root-action")
        if not self.input_item.library.has_action(root_id):
            raise error.ProfileError(
                f"{self.input_item.descriptor()} links to an invalid library "
                f"item {root_id}"
            )
        self.root_action = self.input_item.library.get_action(root_id)
        self.behavior = read_subelement(node, "behavior")
        self.virtual_button = self._parse_virtual_button(node)

    def to_xml(self) -> ElementTree.Element:
        node = ElementTree.Element("action-configuration")
        node.append(
            create_subelement_node("root-action", self.root_action.id)
        )
        node.append(create_subelement_node("behavior", self.behavior))
        vb_node = self._write_virtual_button()
        if vb_node is not None:
            node.append(vb_node)

        return node

    @property
    def library(self) -> Library:
        """Returns the profile's library instance.

        Returns:
            Library instance of the profile
        """
        return self.input_item.library

    def _parse_virtual_button(
        self,
        node: ElementTree.Element
    ) -> AbstractVirtualButton:
        # Ensure the configuration requires a virtual button
        virtual_button = None
        if self.input_item.input_type == InputType.JoystickAxis and \
                self.behavior == InputType.JoystickButton:
            virtual_button = VirtualAxisButton()
        elif self.input_item.input_type == InputType.JoystickHat and \
                self.behavior == InputType.JoystickButton:
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
                self.behavior == InputType.JoystickButton:
            needs_virtual_button = True
        elif self.input_item.input_type == InputType.JoystickHat and \
                self.behavior == InputType.JoystickButton:
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

    """Contains all the modes and their hierarchical information."""

    def __init__(self, parent_profile: Profile):
        """Creates a new mode hierarchy.

        Args:
            parent_profile: the profile this mode hierarchy is associated with
        """
        self._profile = parent_profile
        self._hierarchy = TreeNode("")
        self._hierarchy.add_child(TreeNode("Default"))

    @property
    def first_mode(self) -> str:
        """Returns the name of the first mode.

        Returns:
            Name of the first mode
        """
        return self._hierarchy.children[0].value

    def mode_names(self) -> List[str]:
        """Returns a list containing the names of all modes.

        Returns:
            List of all mode names
        """
        return sorted([node.value for node in self.mode_list()])

    def mode_list(self) -> List[TreeNode]:
        """Returns a list of all mode nodes.

        Returns:
            List containing TreeNodes of all modes
        """
        modes = self._hierarchy.nodes_matching(lambda x: True)
        modes.remove(self._hierarchy)
        return modes

    def valid_parents(self, mode_name: str) -> List[str]:
        """Returns the list of parents that are valid for the given mode.

        Args:
            mode_name: name of the mode for which to return valid parents

        Returns:
            List of valid parents for the specified mode
        """
        parent_candidates = []
        mode_node = self.find_mode(mode_name)
        for node in self.mode_list():
            if not mode_node.is_descendant(node) and node != mode_node:
                parent_candidates.append(node.value)
        return sorted(parent_candidates)

    def find_mode(self, mode_name: str) -> TreeNode:
        """Returns the node corresponding to the name with the given name.

        Args:
            mode_name: name of the mode to find and return

        Returns:
            Node corresponding to the node with the provided name
        """
        nodes = self._hierarchy.nodes_matching(lambda x: mode_name == x.value)
        if len(nodes) > 1:
            raise error.GremlinError(
                f"More than one mode named '{mode_name}' exists"
            )
        elif len(nodes) == 0:
            raise error.GremlinError(
                f"No node with the name '{mode_name}' exists"
            )
        return nodes[0]

    def add_mode(self, mode_name: str) -> None:
        """Adds a new mode to the hierarchy.

        Args:
            mode_name: name of the new mode to add
        """
        if self.mode_exists(mode_name):
            raise error.GremlinError(
                f"Attempting to add an already existing mode '{mode_name}'."
            )
        self._hierarchy.add_child(TreeNode(mode_name))

    def delete_mode(self, mode_name: str) -> None:
        """Deletes the mode with the given name from the hierarchy.

        Args:
            mode_name: name of the mode to delete
        """
        if not self.mode_exists(mode_name):
            raise error.GremlinError(
                f"Attempting to delete a non-existant mode '{mode_name}'."
            )

        # Find node and remove it from the hierarchy tree but reconnect its
        # children to their grandparent.
        node = self.find_mode(mode_name)
        parent_node = node.parent
        node.detach()
        for child in node.children:
            child.set_parent(parent_node)

        # Find all InputItem actions using the mode being deleted and remove
        # them as well.
        for device_id, input_items in self._profile.inputs.items():
            self._profile.inputs[device_id] = [
                x for x in input_items if x.mode != mode_name
            ]

    def rename_mode(self, old_name: str, new_name: str) -> None:
        """Changes the name of an existing mode.

        Args:
            old_name: name of the mode to rename
            new_name: new name for the mode
        """
        # Don't do anything if the names are the same
        if old_name == new_name:
            return

        # Handle missing mode to rename
        if not self.mode_exists(old_name):
            raise error.GremlinError(
                f"Attempting to rename non-existant mode '{old_name}'"
            )
        # Raise an error if renaming to an existing name
        elif self.mode_exists(new_name):
            raise error.GremlinError(
                f"Unable to rename '{old_name}' to '{new_name}' as a mode "
                f"with that name already exists"
            )

        # Perform renaming of the mode
        node = self.find_mode(old_name)
        node.value = new_name

        # Find all actions associated to the old mode name
        for action in self._actions_with_mode(old_name):
            action.mode = new_name

    def set_parent(self, mode_name: str, parent_name: str | None) -> None:
        """Sets the parent of the specified mode.

        Args:
            mode_name: name of the mode to set the parent of
            parent_name: name of the new parent mode
        """
        mode_node = self.find_mode(mode_name)
        parent_node = self.find_mode(parent_name)
        # Detach node before setting new parent to avoid cycle detection
        mode_node.detach()
        mode_node.set_parent(parent_node)

    def mode_exists(self, name: str) -> bool:
        """Checks if a mode with a given name already exists.

        Args:
            name: name of the mode to check for existence

        Returns:
            True if the mode exists, False otherwise
        """
        return len(self._hierarchy.nodes_matching(lambda x: name == x.value)) > 0

    def from_xml(self, root: ElementTree.Element) -> None:
        # Parse individual nodes
        nodes = {}
        node_parents = {}
        for node in root.findall("./modes/mode"):
            if "parent" in node.attrib:
                node_parents[node.text] = node.get("parent")
            nodes[node.text] = TreeNode(node.text)

        # Reconstruct tree structure
        for child, parent in node_parents.items():
            nodes[child].set_parent(nodes[parent])

        self._hierarchy = TreeNode("")
        for node in nodes.values():
            if node.parent is None:
                node.set_parent(self._hierarchy)

    def to_xml(self) -> ElementTree.Element:
        node = ElementTree.Element("modes")
        for mode in self._hierarchy.nodes_matching(lambda x: True):
            if mode.parent is None:
                continue

            n_mode = ElementTree.Element("mode")
            n_mode.text = mode.value
            if mode.parent != self._hierarchy:
                n_mode.set(
                    "parent",
                    safe_format(mode.parent.value, str)
                )
            node.append(n_mode)
        return node

    def _actions_with_mode(self, mode: str) -> List[AbstractActionData]:
        """Returns all actions belonging to the given mode.

        Args:
            mode: name of the mode for which to return all actions
        """
        actions = []
        for action_list in self._profile.inputs.values():
            actions.extend([x for x in action_list if x.mode == mode])
        return actions


class ScriptManager:

    def __init__(self, profile: Profile) -> None:
        """Creates a new instance.

        Each script is uniquely identified by the path to the script as well
        as its assigned name.

        Args:
            profile: the profile whose scripts to manage
        """
        self._profile = profile
        self._scripts : list[Script] = []

    @property
    def scripts(self) -> list[Script]:
        """Returns all managed scripts.

        Returns:
            List of all managed scripts
        """
        return self._scripts

    def add_script(self, path: Path) -> None:
        """Adds a new script to the manager.

        Args:
            path: path to the script's location
        """
        self._scripts.append(Script(path, self._default_name(path)))
        self._scripts.sort(key=lambda s: (s.path, s.name))

    def remove_script(self, path: Path, name: str) -> None:
        """Removes the specified script.

        Args:
            path: path to the script
            name: name of the script
        """
        script = self._find_instance(path, name)
        if script:
            self._scripts.remove(script)

    def rename_script(self, path: Path, old_name: str, new_name: str) -> None:
        """Renames the specified script.

        Args:
            path: path to the script
            old_name: current name of the script
            new_name: new name to use for the script
        """
        names = [s.name for s in self.scripts if s.path == path]
        if new_name not in names:
            script = self._find_instance(path, old_name)
            script.name = new_name
            self._scripts.sort(key=lambda s: (s.path, s.name))

    def index_of(self, path: Path, name: str) -> int:
        """Returns the index of the specified script.

        Args:
            path: path to the script
            name: name of the script

        Returns:
            Index of the script in the list of scripts
        """
        instance = self._find_instance(path, name)
        if not instance:
            raise error.GremlinError(
                f"Unable to find script {path} with name '{name}'"
            )
        return self._scripts.index(instance)

    def _default_name(self, path: Path) -> str:
        """Generates a valid default name for the given script path.

        Args:
            path: path to the script

        Returns:
            Valid name to use for the script that doesn't clash with other
            existing scripts.
        """
        names = [s.name for s in self.scripts if s.path == path]
        for i in range(len(names) + 1):
            candidate = f"Instance {i+1}"
            if candidate not in names:
                return candidate
        raise error.GremlinError(
            f"Unablle to find a valid default name for {path}"
        )

    def from_xml(self, root: ElementTree.Element) -> None:
        for node in root.findall("./scripts/script"):
            self._scripts.append(Script())
            self._scripts[-1].from_xml(node)
        self._scripts.sort(key=lambda s: (s.path, s.name))

    def to_xml(self) -> ElementTree.Element:
        script_node = ElementTree.Element("scripts")
        for script in self._scripts:
            node = script.to_xml()
            if node:
                script_node.append(node)
        return script_node

    def _find_instance(self, path: Path, name: str) -> Script|None:
        """Attempts to find the specified script.

        Args:
            path: path to the script
            name: name of the script

        Returns:
            The script instance if one is found, else None
        """
        for script in self._scripts:
            if script.path == path and script.name == name:
                return script
        return None
