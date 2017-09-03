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


from abc import abstractmethod, ABCMeta
import logging
from mako.template import Template
from mako.lookup import TemplateLookup
from xml.etree import ElementTree

import gremlin
from . import common, error, plugin_manager, profile


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

    def from_xml(self, node):
        """Populates the virtual button based on the node's data.

        :param node the node containing data for this instance
        """
        self.lower_limit = profile.parse_float(node.get("lower-limit"))
        self.upper_limit = profile.parse_float(node.get("upper-limit"))

    def to_xml(self):
        """Returns an XML node representing the data of this instance.

        :return XML node containing the instance's data
        """
        node = ElementTree.Element("virtual-button")
        node.set("lower-limit", str(self.lower_limit))
        node.set("upper-limit", str(self.upper_limit))
        return node


class VirtualHatButton(AbstractVirtualButton):

    """Virtual button which combines hat directions into a button."""

    # Mapping from event directions to names
    direction_to_name = {
        ( 0,  0): "center",
        ( 0,  1): "north",
        ( 1,  1): "north-east",
        ( 1,  0): "east",
        ( 1, -1): "south-east",
        ( 0, -1): "south",
        (-1, -1): "south-west",
        (-1,  0): "west",
        (-1,  1): "north-west"
    }

    # Mapping from names to event directions
    name_to_direction = {
        "center": (0, 0),
        "north": (0, 1),
        "north-east": (1, 1),
        "east": (1, 0),
        "south-east": (1, -1),
        "south": (0, -1),
        "south-west": (-1, -1),
        "west": (-1, 0),
        "north-west": (-1, 1)
    }

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
        for key, value in node.items():
            if key in VirtualHatButton.name_to_direction and \
                            profile.parse_bool(value):
                self.directions.append(key)

    def to_xml(self):
        """Returns an XML node representing the data of this instance.

        :return XML node containing the instance's data
        """
        node = ElementTree.Element("virtual-button")
        for direction in self.directions:
            if direction in VirtualHatButton.name_to_direction:
                node.set(direction, "1")
        return node


class AbstractAction(profile.ProfileData):

    """Base class for all actions that can be encoded via the XML and
    UI system."""

    def __init__(self, parent):
        """Creates a new instance.

        :parent the container which is the parent to this action
        """
        assert isinstance(parent, AbstractContainer)
        super().__init__(parent)

    def from_xml(self, node):
        """Populates the instance with data from the given XML node.

        :param node the XML node to populate fields with
        """
        super().from_xml(node)

    def to_xml(self):
        """Returns a XML node representing the instance's contents.

        :return XML node representing the state of this instance
        """
        node = super().to_xml()
        return node

    def icon(self):
        """Returns the icon to use when representing the action.

        :return icon to use
        """
        raise error.MissingImplementationError(
            "AbstractAction.icon not implemented in subclass"
        )

    def requires_virtual_button(self):
        """Returns whether or not the action requires the use of a
        virtual button.

        :return True if a virtual button has to be used, False otherwise
        """
        raise error.MissingImplementationError(
            "AbstractAction.requires_virtual_button not implemented"
        )

    def _code_generation(self, template_name, params):
        """Generates the code using the provided data.

        :param template_name base name of the templates
        :param params the parameters to pass to the template
        :return CodeBlock object containing the generated code
        """
        # Insert additional common parameters
        params["InputType"] = common.InputType
        params["input_type"] = params["entry"].get_input_type()
        params["id"] = profile.ProfileData.next_code_id
        params["gremlin"] = gremlin
        tpl_lookup = TemplateLookup(directories=["."])

        code_block = profile.CodeBlock()
        code_block.store("container_action", Template(
            filename="action_plugins/{}/container_action.tpl".format(
                template_name
            ),
            lookup=tpl_lookup
        ).render(
            **params
        ))
        code_block.store("setup", Template(
            filename="action_plugins/{}/setup.tpl".format(template_name),
            lookup=tpl_lookup
        ).render(
            **params
        ))

        return code_block


class AbstractContainer(profile.ProfileData):

    """Base class for action container related information storage."""

    virtual_button_lut = {
        common.InputType.JoystickAxis: VirtualAxisButton,
        common.InputType.JoystickButton: None,
        common.InputType.JoystickHat: VirtualHatButton
    }

    def __init__(self, parent):
        """Creates a new instance.

        :parent the InputItem which is the parent to this action
        """
        super().__init__(parent)
        self.actions = []
        self.virtual_button = None

    def add_action(self, action):
        """Adds an action to this container.

        :param action the action to add
        """
        assert isinstance(action, AbstractAction)
        self.actions.append(action)

        # Create activation condition data if needed
        self.create_or_delete_virtual_button()

    def create_or_delete_virtual_button(self):
        """Creates activation condition data as required."""
        need_virtual_button = False
        for actions in self.action_sets:
            need_virtual_button = need_virtual_button or \
                any([a.requires_virtual_button() for a in actions if a is not None])

        if need_virtual_button:
            if self.virtual_button is None:
                self.virtual_button = \
                    AbstractContainer.virtual_button_lut[self.parent.input_type]()
            elif not isinstance(
                    self.virtual_button,
                    AbstractContainer.virtual_button_lut[self.parent.input_type]
            ):
                self.virtual_button = \
                    AbstractContainer.virtual_button_lut[self.parent.input_type]()
        else:
            self.virtual_button = None

    def from_xml(self, node):
        """Populates the instance with data from the given XML node.

        :param node the XML node to populate fields with
        """
        super().from_xml(node)
        self._parse_action_xml(node)
        self._parse_activation_condition_xml(node)
        self._parse_virtual_button_xml(node)

    def to_xml(self):
        """Returns a XML node representing the instance's contents.

        :return XML node representing the state of this instance
        """
        node = super().to_xml()
        # Add activation condition if needed
        if self.activation_condition:
            node.append(self.activation_condition.to_xml())
        return node

    def _parse_action_xml(self, node):
        """Parses the XML content related to actions.

        :param node the XML node to process
        """
        action_name_map = plugin_manager.ActionPlugins().tag_map
        for child in node:
            if child.tag == "activation-condition":
                continue
            if child.tag not in action_name_map:
                logging.getLogger("system").warning(
                    "Unknown node present: {}".format(child.tag)
                )
                continue
            entry = action_name_map[child.tag](self)
            entry.from_xml(child)
            self.actions.append(entry)

    def _parse_virtual_button_xml(self, node):
        """Parses the virtual button part of the XML data.

        :param node the XML node to process
        """
        vb_node = node.find("virtual-button")

        self.virtual_button = None
        if vb_node is not None:
            self.virtual_button = AbstractContainer.virtual_button_lut[
                self.get_input_type()
            ]()
            self.virtual_button.from_xml(vb_node)

    def _generate_code(self):
        """Generates Python code for this container."""
        # Generate code for each of the actions so they are cached and have a
        # unique code_id
        for action in self.actions:
            action.to_code()
            gremlin.profile.ProfileData.next_code_id += 1

    def _is_valid(self):
        """Returns whether or not this container is configured properly.

        :return True if configured properly, False otherwise
        """
        # Check state of the container
        state = self._is_container_valid()
        # Check state of all linked actions
        for action in self.actions:
            if action is None:
                state = False
            else:
                state = state & action.is_valid()
        return state

    @abstractmethod
    def _is_container_valid(self):
        """Returns whether or not the container itself is valid.

        :return True container data is valid, False otherwise
        """
        pass
