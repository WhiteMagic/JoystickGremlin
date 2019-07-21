# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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

import gremlin
import gremlin.ui.common
import gremlin.ui.input_item


class BasicContainerWidget(gremlin.ui.input_item.AbstractContainerWidget):

    """Basic container which holds a single action."""

    def __init__(self, library_reference, parent=None):
        """Creates a new instance.

        :param library_reference the profile data represented by this widget
        :param parent the parent of this widget
        """
        super().__init__(library_reference, parent)

    def _create_action_ui(self):
        """Creates the UI components."""
        if len(self.library_reference.get_action_sets()) > 0:
            assert len(self.library_reference.get_action_sets()) == 1

            self.library_reference.configure_virtual_button_data()
            widget = self._create_action_set_widget(
                self.library_reference.get_action_sets()[0],
                "Basic",
                gremlin.ui.common.ContainerViewTypes.Action
            )
            self.action_layout.addWidget(widget)
            widget.redraw()
            widget.model.data_changed.connect(self.container_modified.emit)
        else:
            if self.library_reference.get_device_type() == gremlin.common.DeviceType.VJoy:
                action_selector = gremlin.ui.common.ActionSelector(
                    gremlin.common.DeviceType.VJoy
                )
            else:
                action_selector = gremlin.ui.common.ActionSelector(
                    self.library_reference.get_input_type()
                )
            action_selector.action_added.connect(self._add_action)
            self.action_layout.addWidget(action_selector)

    def _create_condition_ui(self):
        container = self.library_reference.get_container()
        if len(container.action_sets) > 0 and \
                container.activation_condition_type == "action":
            assert len(container.action_sets) == 1

            widget = self._create_action_set_widget(
                container.action_sets[0],
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
        action_item = plugin_manager.get_class(action_name)(self.library_reference)
        self.library_reference.add_action(action_item)
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
        if len(self.library_reference.get_action_sets()) > 0:
            return ", ".join(a.name for a in self.library_reference.get_action_sets()[0])
        else:
            return "Basic"


class BasicContainerFunctor(gremlin.base_classes.AbstractFunctor):

    """Executes the contents of the associated basic container."""

    def __init__(self, container):
        super().__init__(container)
        self.action_set = gremlin.execution_graph.ActionSetExecutionGraph(
            container.action_sets[0]
        )

    def process_event(self, event, value):
        """Executes the content with the provided data.

        :param event the event to process
        :param value the value received with the event
        :return True if execution was successful, False otherwise
        """
        return self.action_set.process_event(event, value)


class BasicContainer(gremlin.base_classes.AbstractContainer):

    """Represents a container which holds exactly one action."""

    name = "Basic"
    tag = "basic"

    input_types = [
        gremlin.common.InputType.JoystickAxis,
        gremlin.common.InputType.JoystickButton,
        gremlin.common.InputType.JoystickHat,
        gremlin.common.InputType.Keyboard
    ]
    interaction_types = []

    functor = BasicContainerFunctor
    widget = BasicContainerWidget

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the InputItem this container is linked to
        """
        super().__init__(parent)

    def add_action(self, action, index=-1):
        assert isinstance(action, gremlin.base_classes.AbstractAction)

        # Make sure if we're dealing with axis with remap and response curve
        # actions that they are arranged sensibly
        if action.get_input_type() == gremlin.common.InputType.JoystickAxis:
            remap_sets = []
            curve_sets = []
            for container in self.parent.containers:
                for action_set in container.action_sets:
                    for t_action in action_set:
                        if t_action.tag == "response-curve":
                            curve_sets.append(action_set)
                        elif t_action.tag == "remap":
                            remap_sets.append(action_set)

            if action.tag == "remap" and len(curve_sets) == 1 and \
                    len(remap_sets) == 0:
                curve_sets[0].append(action)
            elif action.tag == "response-curve" and len(remap_sets) == 1 and \
                    len(curve_sets) == 0:
                remap_sets[0].append(action)
            else:
                if index == -1:
                    self.action_sets.append([])
                    index = len(self.action_sets) - 1
                self.action_sets[index].append(action)
        else:
            if index == -1:
                self.action_sets.append([])
                index = len(self.action_sets) - 1
            self.action_sets[index].append(action)

        self.create_or_delete_virtual_button()

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

    def _is_container_valid(self):
        """Returns whether or not this container is configured properly.

        :return True if the container is configured properly, False otherwise
        """
        return len(self.action_sets) == 1


# Plugin definitions
version = 1
name = "basic"
create = BasicContainer
