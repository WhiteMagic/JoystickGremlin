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


class DoubleTapContainerWidget(gremlin.ui.input_item.AbstractContainerWidget):

    """DoubleTap container for actions for double or single taps."""

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
            QtWidgets.QLabel("<b>Double-tap delay: </b>")
        )
        self.delay_input = gremlin.ui.common.DynamicDoubleSpinBox()
        self.delay_input.setRange(0.1, 2.0)
        self.delay_input.setSingleStep(0.1)
        self.delay_input.setValue(0.5)
        self.delay_input.setValue(self.profile_data.delay)
        self.delay_input.valueChanged.connect(self._delay_changed_cb)
        self.options_layout.addWidget(self.delay_input)
        self.options_layout.addStretch()

        # Activation moment
        self.options_layout.addWidget(QtWidgets.QLabel("<b>Single/Double Tap: </b>"))
        self.activate_exclusive = QtWidgets.QRadioButton("exclusive")
        self.activate_combined = QtWidgets.QRadioButton("combined")
        if self.profile_data.activate_on == "combined":
            self.activate_combined.setChecked(True)
        else:
            self.activate_exclusive.setChecked(True)
        self.activate_combined.toggled.connect(self._activation_changed_cb)
        self.activate_exclusive.toggled.connect(self._activation_changed_cb)
        self.options_layout.addWidget(self.activate_exclusive)
        self.options_layout.addWidget(self.activate_combined)

        self.action_layout.addLayout(self.options_layout)

        if self.profile_data.action_sets[0] is None:
            self._add_action_selector(
                lambda x: self._add_action(0, x),
                "Single Tap"
            )
        else:
            self._create_action_widget(
                0,
                "Single Tap",
                self.action_layout,
                gremlin.ui.common.ContainerViewTypes.Action
            )

        if self.profile_data.action_sets[1] is None:
            self._add_action_selector(
                lambda x: self._add_action(1, x),
                "Double Tap"
            )
        else:
            self._create_action_widget(
                1,
                "Double Tap",
                self.action_layout,
                gremlin.ui.common.ContainerViewTypes.Action
            )

    def _create_condition_ui(self):
        if self.profile_data.activation_condition_type == "action":
            if self.profile_data.action_sets[0] is not None:
                self._create_action_widget(
                    0,
                    "Single Tap",
                    self.activation_condition_layout,
                    gremlin.ui.common.ContainerViewTypes.Condition
                )

            if self.profile_data.action_sets[1] is not None:
                self._create_action_widget(
                    1,
                    "Double Tap",
                    self.activation_condition_layout,
                    gremlin.ui.common.ContainerViewTypes.Condition
                )

    def _add_action_selector(self, add_action_cb, label):
        """Adds an action selection UI widget.

        :param add_action_cb function to call when an action is added
        :param label the description of the action selector
        """
        action_selector = gremlin.ui.common.ActionSelector(
            self.profile_data.get_input_type()
        )
        action_selector.action_added.connect(add_action_cb)

        group_layout = QtWidgets.QVBoxLayout()
        group_layout.addWidget(action_selector)
        group_layout.addStretch(1)
        group_box = QtWidgets.QGroupBox(label)
        group_box.setLayout(group_layout)

        self.action_layout.addWidget(group_box)

    def _create_action_widget(self, index, label, layout, view_type):
        """Creates a new action widget.

        :param index the index at which to store the created action
        :param label the name of the action to create
        """
        widget = self._create_action_set_widget(
            self.profile_data.action_sets[index],
            label,
            view_type
        )
        layout.addWidget(widget)
        widget.redraw()
        widget.model.data_changed.connect(self.container_modified.emit)

    def _add_action(self, index, action_name):
        """Adds a new action to the container.

        :param action_name the name of the action to add
        """
        plugin_manager = gremlin.plugin_manager.ActionPlugins()
        action_item = plugin_manager.get_class(action_name)(self.profile_data)
        if self.profile_data.action_sets[index] is None:
            self.profile_data.action_sets[index] = []
        self.profile_data.action_sets[index].append(action_item)
        self.profile_data.create_or_delete_virtual_button()
        self.container_modified.emit()

    def _delay_changed_cb(self, value):
        """Updates the activation delay value.

        :param value the value after which the double-tap action activates
        """
        self.profile_data.delay = value

    def _activation_changed_cb(self, value):
        """Updates the activation condition state.

        :param value whether or not the selection was toggled - ignored
        """
        if self.activate_combined.isChecked():
            self.profile_data.activate_on = "combined"
        else:
            self.profile_data.activate_on = "exclusive"

    def _handle_interaction(self, widget, action):
        """Handles interaction icons being pressed on the individual actions.

        :param widget the action widget on which an action was invoked
        :param action the type of action being invoked
        """
        index = self._get_widget_index(widget)
        if index != -1:
            if index == 0 and self.profile_data.action_sets[0] is None:
                index = 1
            self.profile_data.action_sets[index] = None
            self.container_modified.emit()

    def _get_window_title(self):
        """Returns the title to use for this container.

        :return title to use for the container
        """
        if self.profile_data.is_valid():
            return "Double Tap: ({}) / ({})".format(
                ", ".join([a.name for a in self.profile_data.action_sets[0]]),
                ", ".join([a.name for a in self.profile_data.action_sets[1]])
            )
        else:
            return "DoubleTap"


class DoubleTapContainerFunctor(gremlin.base_classes.AbstractFunctor):

    """Executes the contents of the associated DoubleTap container."""

    def __init__(self, container):
        super().__init__(container)
        self.single_tap = gremlin.execution_graph.ActionSetExecutionGraph(
            container.action_sets[0]
        )
        self.double_tap = gremlin.execution_graph.ActionSetExecutionGraph(
            container.action_sets[1]
        )
        self.delay = container.delay
        self.activate_on = container.activate_on

        self.start_time = 0
        self.timer = None
        self.tap_type = None
        self.value_press = None
        self.event_press = None
        self.value_release = None
        self.event_release = None

    def process_event(self, event, value):
        # TODO: Currently this does not handle hat or axis events, however
        #       virtual buttons created on those inputs is supported
        if not isinstance(value.current, bool):
            logging.getLogger("system").warning(
                "Invalid data type received in DoubleTap container: {}".format(
                    type(event.value)
                )
            )
            return False

        # Copy state when input is pressed
        if value.current:
            self.value_press = copy.deepcopy(value)
            self.event_press = event.clone()
            self.value_release = None
            self.event_release = None
        # also copy state on release for delayed single taps
        elif self.activate_on == "exclusive":
            self.value_release = copy.deepcopy(value)
            self.event_release = event.clone()

        # Execute double tap logic
        if value.current:
            # double tap
            if (self.start_time + self.delay) > time.time():
                # avoid triple tapping doing several double taps
                self.start_time = 0
                self.tap_type = "double"
                if self.activate_on == "exclusive":
                    self.timer.cancel()
            else:
                self.start_time = time.time()
                self.tap_type = "single"
                if self.activate_on == "exclusive":
                    self.timer = threading.Timer(self.delay, self._single_tap)
                    self.timer.start()

        if self.tap_type == "double":
            self.double_tap.process_event(event, value)
        elif self.activate_on != "exclusive":
            self.single_tap.process_event(event, value)

    def _single_tap(self):
        """Callback executed, when the delay expires."""
        self.single_tap.process_event(self.event_press, self.value_press)
        if self.event_release:
            time.sleep(0.05)
            self.single_tap.process_event(self.event_release, self.value_release)


class DoubleTapContainer(gremlin.base_classes.AbstractContainer):

    """A container with two actions which are triggered based on the delay
    between the taps.

    A single tap will run the first action while a double tap will run the
    second action.
    """

    name = "Double Tap"
    tag = "double_tap"
    functor = DoubleTapContainerFunctor
    widget = DoubleTapContainerWidget
    input_types = [
        gremlin.common.InputType.JoystickAxis,
        gremlin.common.InputType.JoystickButton,
        gremlin.common.InputType.JoystickHat,
        gremlin.common.InputType.Keyboard
    ]
    interaction_types = [
        gremlin.ui.input_item.ActionSetView.Interactions.Edit,
    ]

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the InputItem this container is linked to
        """
        super().__init__(parent)
        self.action_sets = [[], []]
        self.delay = 0.5
        self.activate_on = "exclusive"

    def _parse_xml(self, node):
        """Populates the container with the XML node's contents.

        :param node the XML node with which to populate the container
        """
        super()._parse_xml(node)
        self.delay = float(node.get("delay", 0.5))
        self.activate_on = node.get("activate-on", "combined")

    def _generate_xml(self):
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
        node = ElementTree.Element("container")
        node.set("type", DoubleTapContainer.tag)
        node.set("delay", str(self.delay))
        node.set("activate-on", self.activate_on)
        for actions in self.action_sets:
            as_node = ElementTree.Element("action-set")
            for action in actions:
                as_node.append(action.to_xml())
            node.append(as_node)
        return node

    def _is_container_valid(self):
        """Returns whether or not this container is configured properly.

        :return True if the container is configured properly, False otherwise
        """
        return any(len(action_set) for action_set in self.action_sets)


# Plugin definitions
version = 1
name = "double_tap"
create = DoubleTapContainer
