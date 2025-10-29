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

"""Profile management for Joystick Gremlin.

This module provides the Profile class and related components for managing
input device configurations.

REFACTORED: Split large monolithic module into focused profile_modules package.
This file now serves as a re-export wrapper for backward compatibility.

New organization:
- profile_modules.virtual_buttons: Virtual button abstractions
- profile_modules.settings: Profile settings
- profile_modules.mode_hierarchy: Mode hierarchy management
- profile_modules.script_manager: Script management
- profile_modules.library: Action library
- profile_modules.input_items: Input item configuration
"""

from __future__ import annotations

import codecs
import uuid
from typing import TYPE_CHECKING
from xml.dom import minidom
from xml.etree import ElementTree

import dill_compat as dill

from gremlin.types import InputType
from gremlin import error
from gremlin.intermediate_output import IntermediateOutput
from gremlin.util import read_subelement

# Re-export all classes from profile_modules for backward compatibility
from gremlin.profile_modules import (
    AbstractVirtualButton,
    VirtualAxisButton,
    VirtualHatButton,
    Settings,
    ModeHierarchy,
    Script,
    ScriptManager,
    Library,
    InputItem,
    InputItemBinding
)

if TYPE_CHECKING:
    from gremlin.base_classes import AbstractActionData


def mode_list(profile: Profile):
    """Returns a list of all modes from the given profile.

    Args:
        profile: Profile instance to extract modes from

    Returns:
        Sorted list of unique mode names
    """
    return profile.modes.get_all_mode_names()


class Profile:
    """Stores the contents and an entire configuration profile."""

    current_version = 14

    def __init__(self):
        """Initialize a new profile."""
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

    def _validate_input_specification(self, device_guid, input_type, input_id, mode):
        """Validate input specification types.
        
        Args:
            device_guid: Device GUID
            input_type: Input type
            input_id: Input ID
            mode: Mode name
            
        Raises:
            ProfileError: If specification is invalid
        """
        if not (
                isinstance(device_guid, uuid.UUID) and
                isinstance(input_type, InputType) and
                type(input_id) in [int, uuid.UUID] and
                isinstance(mode, str)
        ):
            raise error.ProfileError("Invalid input specification provided.")

    def _find_existing_item(self, device_guid, input_type, input_id, mode):
        """Find existing input item.
        
        Args:
            device_guid: Device GUID
            input_type: Input type
            input_id: Input ID
            mode: Mode name
            
        Returns:
            InputItem if found, None otherwise
        """
        if device_guid not in self.inputs:
            return None
        
        for item in self.inputs[device_guid]:
            if item.input_type == input_type and \
                    item.input_id == input_id and \
                    item.mode == mode:
                return item
        
        return None

    def _create_new_item(self, device_guid, input_type, input_id, mode):
        """Create new input item.
        
        Args:
            device_guid: Device GUID
            input_type: Input type
            input_id: Input ID
            mode: Mode name
            
        Returns:
            Newly created InputItem
        """
        if device_guid not in self.inputs:
            self.inputs[device_guid] = []
        
        item = InputItem(self.library)
        item.device_id = device_guid
        item.input_type = input_type
        item.input_id = input_id
        item.mode = mode
        self.inputs[device_guid].append(item)
        return item

    def get_input_item(
            self,
            device_guid: uuid.UUID,
            input_type: InputType,
            input_id: int | uuid.UUID,
            mode: str,
            create_if_missing: bool = False
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
        self._validate_input_specification(device_guid, input_type, input_id, mode)
        
        existing_item = self._find_existing_item(device_guid, input_type, input_id, mode)
        if existing_item:
            return existing_item
        
        if create_if_missing:
            return self._create_new_item(device_guid, input_type, input_id, mode)
        
        return None

    def remove_action(
        self,
        action: "AbstractActionData",
        binding: InputItemBinding
    ) -> None:
        """Removes an action from the specified InputBinding instance.

        Args:
            action: the action instance to remove
            binding: the InputBinding instance from which to remove the action
        """
        # Remove action from its parent
        root_children, _ = binding.root_action.get_actions()
        all_actions = [
            (binding.root_action, child) for child in root_children
        ]
        while len(all_actions) > 0:
            entry = all_actions.pop(0)
            child_actions, _ = entry[1].get_actions()
            all_actions.extend([
                (entry[1], child) for child in child_actions
            ])

            if entry[1] == action:
                entry[0].remove_action(action)
                break

        # Remove the action and its children from the library if they are
        # unused
        self.library.remove_unused(action, recursive=True)

    def _process_input(self, node: ElementTree.Element) -> None:
        """Processes an InputItem XML node and stores it.

        Args:
            node: XML node containing InputItem data
        """
        item = InputItem(self.library)
        item.from_xml(node)

        if item.device_id not in self.inputs:
            self.inputs[item.device_id] = []
        self.inputs[item.device_id].append(item)

    def _create_io_input(self, node: ElementTree.Element) -> None:
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


# Export all for backward compatibility
__all__ = [
    # Virtual buttons
    'AbstractVirtualButton',
    'VirtualAxisButton',
    'VirtualHatButton',
    
    # Settings
    'Settings',
    
    # Mode management
    'ModeHierarchy',
    
    # Scripts
    'Script',
    'ScriptManager',
    
    # Library
    'Library',
    
    # Input items
    'InputItem',
    'InputItemBinding',
    
    # Main profile class
    'Profile',
    
    # Utility functions
    'mode_list',
]
