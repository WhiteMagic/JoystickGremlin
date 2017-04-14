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

#from gremlin.code_generator import template_helpers
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
        self.condition = self._create_condition()

    def from_xml(self, node):
        """Populates the instance with data from the given XML node.

        :param node the XML node to populate fields with
        """
        super().from_xml(node)
        self.condition.from_xml(node)

    def to_xml(self):
        """Returns a XML node representing the instance's contents.

        :return XML node representing the state of this instance
        """
        node = super().to_xml()
        self.condition.to_xml(node)
        return node

    def icon(self):
        """Returns the icon to use when representing the action.

        :return icon to use
        """
        raise error.MissingImplementationError(
            "AbstractAction.icon not implemented in subclass"
        )

    def _create_condition(self):
        input_type = self.get_input_type()
        if input_type in [
                common.InputType.JoystickButton,
                common.InputType.Keyboard
        ]:
            return ButtonCondition()
        elif input_type == common.InputType.JoystickAxis:
            return AxisCondition()
        elif input_type == common.InputType.JoystickHat:
            return HatCondition()

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


class AxisCondition:

    """Indicates when an action associated with an axis is to be run."""

    def __init__(self, is_active=False, lower_limit=0.0, upper_limit=0.0):
        """Creates a new instance.

        :param lower_limit lower axis limit of the activation range
        :param upper_limit upper axis limit of the activation range
        """
        self.is_active = is_active
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def from_xml(self, node):
        self.is_active = profile.parse_bool(node.get("is-active"))
        self.lower_limit = profile.parse_float(node.get("lower-limit"))
        self.upper_limit = profile.parse_float(node.get("upper-limit"))

    def to_xml(self, node):
        node.set("is-active", str(self.is_active))
        node.set("lower-limit", str(self.lower_limit))
        node.set("upper-limit", str(self.upper_limit))

    def to_code(self, code):
        return code


class ButtonCondition:

    """Indicates when an action associated with a button is to be run"""

    def __init__(self, on_press=True, on_release=False):
        """Creates a new instance.

        :param on_press when True the action is executed when the button
            is pressed
        :param on_release when True the action is execute when the
            button is released
        """
        self.on_press = on_press
        self.on_release = on_release

    def from_xml(self, node):
        try:
            on_press = profile.parse_bool(node.get("on-press"))
        except error.ProfileError:
            on_press = None
        try:
            on_release = profile.parse_bool(node.get("on-release"))
        except error.ProfileError:
            on_release = None

        # No valid data at all, set default values
        if on_press is None and on_release is None:
            self.on_press = True
            self.on_release = False
        # Some valid data handle it
        else:
            self.on_press = False if on_press is None else on_press
            self.on_release = False if on_release is None else on_release

    def to_xml(self, node):
        node.set("on-press", str(self.on_press))
        node.set("on-release", str(self.on_release))

    def to_code(self, code):
        tpl_lookup = TemplateLookup(directories=["."])
        tpl = Template(
            filename="templates/button_condition.tpl",
            lookup=tpl_lookup
        )
        return tpl.render(
            code=code,
            on_press=self.on_press,
            on_release=self.on_release
        )


class HatCondition:

    """Indicates when an action associated with a hat is to be run."""

    def __init__(
            self,
            on_n=False,
            on_ne=False,
            on_e=False,
            on_se=False,
            on_s=False,
            on_sw=False,
            on_w=False,
            on_nw=False
    ):
        """Creates a new instance."""
        self.on_n = on_n
        self.on_ne = on_ne
        self.on_e = on_e
        self.on_se = on_se
        self.on_s = on_s
        self.on_sw = on_sw
        self.on_w = on_w
        self.on_nw = on_nw

    def from_xml(self, node):
        self.on_n = profile.read_bool(node, "on-n")
        self.on_ne = profile.read_bool(node, "on-ne")
        self.on_e = profile.read_bool(node, "on-e")
        self.on_se = profile.read_bool(node, "on-se")
        self.on_s = profile.read_bool(node, "on-s")
        self.on_sw = profile.read_bool(node, "on-sw")
        self.on_w = profile.read_bool(node, "on-w")
        self.on_nw = profile.read_bool(node, "on-nw")

    def to_xml(self, node):
        print(self.on_n)
        node.set("on-n", str(self.on_n))
        node.set("on-ne", str(self.on_ne))
        node.set("on-e", str(self.on_e))
        node.set("on-se", str(self.on_se))
        node.set("on-s", str(self.on_s))
        node.set("on-sw", str(self.on_sw))
        node.set("on-w", str(self.on_w))
        node.set("on-nw", str(self.on_nw))

    def to_code(self, code):
        return code
