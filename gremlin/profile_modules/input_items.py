# -*- coding: utf-8; -*-

"""Input item configuration classes for profiles.

This module contains classes for managing input configurations
and their bindings to actions in the library.

Extracted from gremlin.profile for better organization.
"""

from typing import List, Optional
from xml.etree import ElementTree
import uuid

import dill

from gremlin import error
from gremlin.intermediate_output import IntermediateOutput
from gremlin.types import InputType
from gremlin.util import read_subelement, create_subelement_node


class InputItem:
    """Represents the configuration of a single input in a particular mode.
    
    An InputItem links a physical input (button, axis, hat) to one or more
    action configurations that should be executed when the input is triggered.
    """

    def __init__(self, library):
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
        """Loads input item from XML.

        Args:
            node: XML element containing input item data
        """
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
        """Converts input item to XML.

        Returns:
            XML element containing input item data
        """
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

    def remove_item_binding(self, binding) -> None:
        """Removes the given binding instance if present.

        Args:
            binding: InputItemBinding instance to remove from the item
        """
        if binding in self.action_sequences:
            del self.action_sequences[self.action_sequences.index(binding)]


class InputItemBinding:
    """Links together a Library action and its activation behavior.
    
    This class manages the connection between a physical input and
    the action(s) it should trigger, including behavior configuration
    and virtual button settings.
    """

    def __init__(self, input_item: InputItem):
        """Creates a new binding.

        Args:
            input_item: parent InputItem this binding belongs to
        """
        self.input_item = input_item
        self.root_action = None
        self.behavior = None
        self.virtual_button = None

    def from_xml(self, node: ElementTree.Element) -> None:
        """Loads binding from XML.

        Args:
            node: XML element containing binding data
        """
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
        """Converts binding to XML.

        Returns:
            XML element containing binding data
        """
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
    def library(self):
        """Returns the profile's library instance.

        Returns:
            Library instance of the profile
        """
        return self.input_item.library

    def _parse_virtual_button(self, node: ElementTree.Element):
        """Parses virtual button configuration from XML.

        Args:
            node: XML element to parse

        Returns:
            Virtual button instance or None
        """
        from gremlin.profile_modules.virtual_buttons import (
            VirtualAxisButton, VirtualHatButton
        )
        
        # Ensure the configuration requires a virtual button
        virtual_button = None
        if self.input_item.input_type == InputType.JoystickAxis and \
                self.behavior == InputType.JoystickButton:
            virtual_button = VirtualAxisButton(0.0, 0.0, None)
        elif self.input_item.input_type == InputType.JoystickHat and \
                self.behavior == InputType.JoystickButton:
            virtual_button = VirtualHatButton(None)

        # Ensure we have a virtual button entry to parse
        if virtual_button is not None:
            vb_node = node.find("virtual-button")
            if vb_node is None:
                raise error.ProfileError(
                    f"Missing virtual-button entry for binding"
                )
            # Note: Assumes virtual button classes have from_xml method
            if hasattr(virtual_button, 'from_xml'):
                virtual_button.from_xml(vb_node)

        return virtual_button

    def _write_virtual_button(self) -> Optional[ElementTree.Element]:
        """Writes virtual button configuration to XML.

        Returns:
            XML element or None if no virtual button needed
        """
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
        
        # Note: Assumes virtual button classes have to_xml method
        if hasattr(self.virtual_button, 'to_xml'):
            return self.virtual_button.to_xml()
        return None
