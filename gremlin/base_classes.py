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

import logging
from mako.template import Template
from mako.lookup import TemplateLookup

import gremlin
from . import common, error, plugin_manager, profile


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

    def __init__(self, parent):
        super().__init__(parent)
        self.actions = []

    def add_action(self, action):
        assert isinstance(action, AbstractAction)
        self.actions.append(action)

    def is_valid(self):
        state = self._is_valid()
        for action in self.actions:
            if action is None:
                state = False
            else:
                state = state & action.is_valid()
        return state

    def from_xml(self, node):
        super().from_xml(node)
        self._parse_action_xml(node)

    def _parse_action_xml(self, node):
        action_name_map = plugin_manager.ActionPlugins().tag_map
        for child in node:
            if child.tag not in action_name_map:
                logging.getLogger("system").warning(
                    "Unknown node present: {}".format(child.tag)
                )
                continue
            entry = action_name_map[child.tag](self)
            entry.from_xml(child)
            self.actions.append(entry)

    def _generate_code(self):
        # Generate code for each of the actions so they are cached and have a
        # unique code_id
        for action in self.actions:
            action.to_code()
            gremlin.profile.ProfileData.next_code_id += 1
