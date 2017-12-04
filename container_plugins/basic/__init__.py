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

from xml.etree import ElementTree

from mako.template import Template

import gremlin
import gremlin.ui.common
import gremlin.ui.input_item


class BasicContainerWidget(gremlin.ui.input_item.AbstractContainerWidget):

    """Basic container which holds a single action."""

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the profile data represented by this widget
        :param parent the parent of this widget
        """
        super().__init__(profile_data, parent)

    def _create_action_ui(self):
        """Creates the UI components."""
        if len(self.profile_data.action_sets) > 0:
            assert len(self.profile_data.action_sets) == 1

            self.profile_data.create_or_delete_virtual_button()
            widget = self._create_action_set_widget(
                self.profile_data.action_sets[0],
                "Basic",
                gremlin.ui.common.ContainerViewTypes.Basic
            )
            self.action_layout.addWidget(widget)
            widget.redraw()
            widget.model.data_changed.connect(self.container_modified.emit)
        else:
            if self.profile_data.get_device_type() == gremlin.common.DeviceType.VJoy:
                action_selector = gremlin.ui.common.ActionSelector(
                    gremlin.common.DeviceType.VJoy
                )
            else:
                action_selector = gremlin.ui.common.ActionSelector(
                    self.profile_data.parent.input_type
                )
            action_selector.action_added.connect(self._add_action)
            self.action_layout.addWidget(action_selector)

    def _create_condition_ui(self):
        if len(self.profile_data.action_sets) > 0 and \
                self.profile_data.activation_condition_type == "action":
            assert len(self.profile_data.action_sets) == 1

            widget = self._create_action_set_widget(
                self.profile_data.action_sets[0],
                "Basic",
                gremlin.ui.common.ContainerViewTypes.Condition
            )
            self.activation_condition_layout.addWidget(widget)
            widget.redraw()
            widget.model.data_changed.connect(self.container_modified.emit)

    def _add_action(self, action_name):
        """Adds a new action to the container.

        :param action_name the name of the action to add
        """
        plugin_manager = gremlin.plugin_manager.ActionPlugins()
        action_item = plugin_manager.get_class(action_name)(self.profile_data)
        self.profile_data.add_action(action_item)
        self.container_modified.emit()

    def _handle_interaction(self, widget, action):
        """Handles interaction icons being pressed on the individual actions.

        :param widget the action widget on which an action was invoked
        :param action the type of action being invoked
        """
        pass

    def _get_window_title(self):
        """Returns the title to use for this container.

        :return title to use for the container
        """
        if len(self.profile_data.action_sets) > 0:
            return ", ".join(a.name for a in self.profile_data.action_sets[0])
        else:
            return "Basic"


class BasicContainerFunctor(gremlin.base_classes.AbstractFunctor):

    def __init__(self, container):
        super().__init__(container)
        self.action_set = gremlin.code_runner.ActionSetExecutionGraph(
            container.action_sets[0]
        )

    def process_event(self, event, value):
        return self.action_set.process_event(event, value)


class BasicContainer(gremlin.base_classes.AbstractContainer):

    """Represents a container which holds exactly one action."""

    name = "Basic"
    tag = "basic"
    functor = BasicContainerFunctor
    widget = BasicContainerWidget
    input_types = [
        gremlin.common.InputType.JoystickButton,
        gremlin.common.InputType.Keyboard
    ]
    interaction_types = []

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the InputItem this container is linked to
        """
        super().__init__(parent)

    def _parse_xml(self, node):
        """Populates the container with the XML node's contents.

        :param node the XML node with which to populate the container
        """
        pass

    def _generate_xml(self):
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
        node = ElementTree.Element("container")
        node.set("type", "basic")
        as_node = ElementTree.Element("action-set")
        for action in self.action_sets[0]:
            as_node.append(action.to_xml())
        node.append(as_node)
        return node

    def _generate_code(self):
        """Returns Python code for this container.

        :return Python code for this container
        """
        super()._generate_code()
        code_id = gremlin.profile.ProfileData.next_code_id
        gremlin.profile.ProfileData.next_code_id += 1
        tpl = Template(filename="container_plugins/basic/global.tpl")
        code = gremlin.profile.CodeBlock()
        code.store("container", tpl.render(
            entry=self,
            id=code_id,
            code=code
        ))
        tpl = Template(filename="container_plugins/basic/body.tpl")
        code.store("body", tpl.render(
            entry=self,
            id=code_id,
            code=code
        ))
        return code

    def _is_container_valid(self):
        """Returns whether or not this container is configured properly.

        :return True if the container is configured properly, False otherwise
        """
        return len(self.action_sets) == 1


# Plugin definitions
version = 1
name = "basic"
create = BasicContainer
