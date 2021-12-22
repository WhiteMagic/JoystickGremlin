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


import copy
import logging
import threading
import time
from xml.etree import ElementTree

from PyQt5 import QtWidgets

import gremlin
import gremlin.ui.common
import gremlin.ui.input_item


class SmartToggleContainerWidget(gremlin.ui.input_item.AbstractContainerWidget):

    """SmartToggle container which holds or toggles a single action."""

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the profile data represented by this widget
        :param parent the parent of this widget
        """
        super().__init__(profile_data, parent)

    def _create_action_ui(self):
        """Creates the UI components."""
        self.profile_data.create_or_delete_virtual_button()

        self.options_layout = QtWidgets.QHBoxLayout()

        # Activation delay
        self.options_layout.addWidget(
            QtWidgets.QLabel("<b>Toggle time: </b>")
        )
        self.delay_input = gremlin.ui.common.DynamicDoubleSpinBox()
        self.delay_input.setRange(0.1, 2.0)
        self.delay_input.setSingleStep(0.1)
        self.delay_input.setValue(0.5)
        self.delay_input.setValue(self.profile_data.delay)
        self.delay_input.valueChanged.connect(self._delay_changed_cb)
        self.options_layout.addWidget(self.delay_input)
        self.options_layout.addStretch()

        self.action_layout.addLayout(self.options_layout)

        if len(self.profile_data.action_sets) > 0:
            assert len(self.profile_data.action_sets) == 1

            widget = self._create_action_set_widget(
                self.profile_data.action_sets[0],
                "Smart Toggle",
                gremlin.ui.common.ContainerViewTypes.Action
            )
            self.action_layout.addWidget(widget)
            widget.redraw()
            widget.model.data_changed.connect(self.container_modified.emit)
        else:
            action_selector = gremlin.ui.common.ActionSelector(
                self.profile_data.get_input_type()
            )
            action_selector.action_added.connect(self._add_action)
            self.action_layout.addWidget(action_selector)

    def _create_condition_ui(self):
        if len(self.profile_data.action_sets) > 0 and \
                self.profile_data.activation_condition_type == "action":
            assert len(self.profile_data.action_sets) == 1

            widget = self._create_action_set_widget(
                self.profile_data.action_sets[0],
                "Smart Toggle",
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
        if self.profile_data.action_sets[0] is None:
            self.profile_data.action_sets[0] = []
        self.profile_data.action_sets[0].append(action_item)
        self.profile_data.create_or_delete_virtual_button()
        self.container_modified.emit()

    def _delay_changed_cb(self, value):
        """Updates the activation delay value.

        :param value the value after which the long press action activates
        """
        self.profile_data.delay = value

    def _activation_changed_cb(self, value):
        """Updates the activation condition state.

        :param value whether or not the selection was toggled - ignored
        """
        if self.activate_press.isChecked():
            self.profile_data.activate_on = "press"
        else:
            self.profile_data.activate_on = "release"

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
            return "Smart Toggle"


class SmartToggleContainerFunctor(gremlin.base_classes.AbstractFunctor):

    """Executes the contents of the associated SmartToggle container."""

    def __init__(self, container):
        """Creates a new functor instance.

        Parameters
        ==========
        container : SmartToggleContainer
            The instance containing the configuration of the container
        """
        super().__init__(container)
        self.action_set = gremlin.execution_graph.ActionSetExecutionGraph(
            container.action_sets[0]
        )
        self.delay = container.delay
        self.release_value = None
        self.release_event = None
        self.mode = None
        self.activation_time = 0.0

        # Disable the auto release feature which clashes with the toggle logic
        for functor in self.action_set.functors:
            if "needs_auto_release" in functor.__dict__:
                functor.needs_auto_release = False

    def process_event(self, event, value):
        # TODO: Currently this does not handle hat or axis events, however
        #       virtual buttons created on those inputs is supported
        if not isinstance(value.current, bool):
            logging.getLogger("system").warning(
                "Invalid data type received in Smart Toggle container: {}".format(
                    type(event.value)
                )
            )
            return False

        if value.current:
            # Currently not in either toggle or hold mode
            if self.mode is None:
                self.action_set.process_event(event, value)
                self.activation_time = time.time()

            # Run release logic when the second press happens in toggle mode
            elif self.mode == "toggle":
                self.action_set.process_event(
                    self.release_event,
                    self.release_value
                )
                self.activation_time = 0.0
                self.mode = None
        else:
            # If the input is release before the hold timeout occurs switch
            # to toggle mode and store the event for artificial release on
            # next input press
            if self.activation_time + self.delay > time.time():
                self.mode = "toggle"
                self.release_event = event.clone()
                self.release_value = value

            # Run release logic when the release event occurs in hold mode
            else:
                self.action_set.process_event(event, value)
                self.activation_time = 0.0
                self.mode = None

        return True


class SmartToggleContainer(gremlin.base_classes.AbstractContainer):

    """Represents a container which holds exactly one action."""

    name = "Smart Toggle"
    tag = "smart_toggle"

    input_types = [
        gremlin.common.InputType.JoystickAxis,
        gremlin.common.InputType.JoystickButton,
        gremlin.common.InputType.JoystickHat,
        gremlin.common.InputType.Keyboard
    ]
    interaction_types = []

    functor = SmartToggleContainerFunctor
    widget = SmartToggleContainerWidget

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the InputItem this container is linked to
        """
        super().__init__(parent)
        self.action_sets = [[]]
        self.delay = 0.5

    def _parse_xml(self, node):
        """Populates the container with the XML node's contents.

        :param node the XML node with which to populate the container
        """
        super()._parse_xml(node)
        self.delay = gremlin.profile.safe_read(node, "delay", float, 0.5)

    def _generate_xml(self):
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
        node = ElementTree.Element("container")
        node.set("type", SmartToggleContainer.tag)
        node.set("delay", gremlin.profile.safe_format(self.delay, float))
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
name = "smart_toggle"
create = SmartToggleContainer
