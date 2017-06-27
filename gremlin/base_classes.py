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


class AbstractActivationCondition(metaclass=ABCMeta):

    def __init__(self):
        pass

    @abstractmethod
    def from_xml(self, node):
        pass

    @abstractmethod
    def to_xml(self):
        pass


class AxisActivationCondition(AbstractActivationCondition):

    def __init__(self, lower_limit=0.0, upper_limit=0.0):
        super().__init__()
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def from_xml(self, node):
        self.lower_limit = profile.parse_float(node.get("lower-limit"))
        self.upper_limit = profile.parse_float(node.get("upper-limit"))

    def to_xml(self):
        node = ElementTree.Element("activation-condition")
        node.set("lower-limit", str(self.lower_limit))
        node.set("upper-limit", str(self.upper_limit))
        return node


class HatActivationCondition(AbstractActivationCondition):

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

    def __init__(self, directions=[]):
        super().__init__()
        self.directions = list(set(directions))

    def from_xml(self, node):
        for key, value in node.items():
            if key in HatActivationCondition.name_to_direction and \
                            profile.parse_bool(value):
                self.directions.append(key)

    def to_xml(self):
        node = ElementTree.Element("activation-condition")
        for dir in self.directions:
            if dir in HatActivationCondition.name_to_direction:
                node.set(dir, "1")
        return node


class AbstractAction(profile.ProfileData):

    """Base class for all actions that can be encoded via the XML and
    UI system."""

    def __init__(self, parent):
        """Creates a new instance.

        :parent the InputItem which is the parent to this action
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

    def requires_activation_condition(self):
        """Returns whether or not the action requires the use of an
        activation condition.

        :return True if an activation condition is to be used, False otherwise
        """
        raise error.MissingImplementationError(
            "AbstractAction.requires_activation_condition not implemented"
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
            filename="action_plugins/{}/container_action.tpl".format(template_name),
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

    condition_data = {
        common.InputType.JoystickAxis: AxisActivationCondition,
        common.InputType.JoystickButton: None,
        common.InputType.JoystickHat: HatActivationCondition
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.actions = []
        self.activation_condition = None

    def add_action(self, action):
        assert isinstance(action, AbstractAction)
        self.actions.append(action)

        # Create activation condition data if needed
        self.create_or_delete_activation_condition()

    def create_or_delete_activation_condition(self):
        """Creates activation condition data as required."""
        need_activation_condition = any(
            [a.requires_activation_condition() for a in self.actions if a is not None]
        )

        if need_activation_condition:
            if self.activation_condition is None:
                self.activation_condition = \
                    AbstractContainer.condition_data[self.parent.input_type]()
            elif not isinstance(
                    self.activation_condition,
                    AbstractContainer.condition_data[self.parent.input_type]
            ):
                self.activation_condition = \
                    AbstractContainer.condition_data[self.parent.input_type]()
        else:
            self.activation_condition = None

    def from_xml(self, node):
        super().from_xml(node)
        self._parse_action_xml(node)
        self._parse_activation_condition_xml(node)

    def to_xml(self):
        node = super().to_xml()
        # Add activation condition if needed
        if self.activation_condition:
            node.append(self.activation_condition.to_xml())
        return node

    def _parse_action_xml(self, node):
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

    def _parse_activation_condition_xml(self, node):
        ac_node = node.find("activation-condition")

        if ac_node is not None:
            self.activation_condition = AbstractContainer.condition_data[
                self.get_input_type()
            ]()
            self.activation_condition.from_xml(ac_node)

    def _generate_code(self):
        # Generate code for each of the actions so they are cached and have a
        # unique code_id
        for action in self.actions:
            action.to_code()
            gremlin.profile.ProfileData.next_code_id += 1

    def _is_valid(self):
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
