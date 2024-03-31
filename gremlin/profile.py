# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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
from typing import List, Optional, Set, Tuple, TYPE_CHECKING, Callable
import uuid
from xml.dom import minidom
from xml.etree import ElementTree

import dill

import action_plugins
from gremlin.types import AxisButtonDirection, InputType, HatDirection, \
    PluginVariableType
from gremlin import error, plugin_manager
from gremlin.intermediate_output import IntermediateOutput
from gremlin.tree import TreeNode
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
            # been parsed, if not process this action later
            if not all([aid in self._actions for aid in read_action_ids(entry)]):
                parse_later.append(entry)

            # Create action object and store it in the library
            if entry not in parse_later:
                self._parse_xml_action(entry)

        # Parse all actions that have missing child actions and repeat this
        # until no action with missing child actions remains.
        # FIXME: Detect when this gets stuck because a child simply doesn't exist
        while len(parse_later) > 0:
            entry = parse_later.pop(0)
            if not all([aid in self._actions for aid in read_action_ids(entry)]):
                parse_later.append(entry)
            else:
                self._parse_xml_action(entry)

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the content of this library.

        Returns:
            XML node holding the instance's content
        """
        node = ElementTree.Element("library")
        for item in [n for n in self._actions.values() if n.is_valid()]:
            node.append(item.to_xml())
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
                f"Duplicate library action id: {action_obj.id}"
            )
        self._actions[action_obj.id] = action_obj


class Profile:

    """Stores the contents and an entire configuration profile."""

    current_version = 14

    def __init__(self):
        self.inputs = {}
        self.library = Library()
        self.settings = Settings(self)
        self.modes = ModeHierarchy()
        self.plugins = []
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
        for node in root.findall("./inputs/input[device-id='F0AF472F-8E17-493B-A1EB-7333EE8543F2']"):
            self._create_io_input(node)

        # Create library entries and modes
        self.library.from_xml(root)
        self.modes.from_xml(root)

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

    def get_input_count(
            self,
            device_guid: uuid.UUID,
            input_type: InputType,
            input_id: int
    ) -> int:
        """Returns the number of InputItem instances corresponding to the
        provided information.

        Args:
            device_guid: GUID of the device
            input_type: type of the input
            input_id: id of the input

        Returns:
            Number of InputItem instances linked with the given information
        """
        if device_guid not in self.inputs:
            return 0

        for item in self.inputs[device_guid]:
            if item.input_type == input_type and item.input_id == input_id:
                return len(item.action_sequences)

        return 0

    def get_input_item(
            self,
            device_guid: uuid.UUID,
            input_type: InputType,
            input_id: int | uuid.UUID,
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
        # Verify provided information has correct type information
        if not (
                isinstance(device_guid, uuid.UUID) and
                isinstance(input_type, InputType) and
                type(input_id) in [int, uuid.UUID]
        ):
            raise error.ProfileError(f"Invalid input specification provided.")

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
            item.mode = self.modes.first_mode
            self.inputs[device_guid].append(item)
            return item
        else:
            raise error.ProfileError(
                f"No data for input {InputType.to_string(input_type)} "
                f"{input_id} of device {device_guid}"
            )

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
        """Creates an intermediate output input for the givern node.

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
        self.always_execute = False
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

    def __init__(self):
        self.hierarchy = []

    @property
    def first_mode(self) -> str:
        """Returns the name of the first mode.

        Returns:
            Name of the first mode
        """
        if len(self.hierarchy) == 0:
            return "Default"
        else:
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
            nodes[node.text] = TreeNode(node.text)

        # Reconstruct tree structure
        for child, parent in node_parents.items():
            nodes[child].set_parent(nodes[parent])

        self.hierarchy = []
        for node in nodes.values():
            if node.parent is None:
                self.hierarchy.append(node)

    def to_xml(self) -> ElementTree.Element:
        node = ElementTree.Element("modes")

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
                "device_id": safe_read(
                    node,
                    "device-guid",
                    uuid.UUID,
                    dill.UUID_Invalid
                ),
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
            node.set("device-guid", str(self.value["device_id"]))
            node.set("device-name", safe_format(self.value["device_name"], str))
            node.set("input-id", safe_format(self.value["input_id"], int))
            node.set("input-type", InputType.to_string(self.value["input_type"]))
        elif self.type == PluginVariableType.VirtualInput:
            node.set("vjoy-id", safe_format(self.value["device_id"], int))
            node.set("input-id", safe_format(self.value["input_id"], int))
            node.set("input-type", InputType.to_string(self.value["input_type"]))

        return node
