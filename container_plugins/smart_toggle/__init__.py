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
            QtWidgets.QLabel("<b>Long press delay: </b>")
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
        self.activation_moment_box = QtWidgets.QGroupBox("Activate:")
        self.activation_moment_layout = QtWidgets.QVBoxLayout()
        self.activate_press = QtWidgets.QRadioButton("on press")
        self.activate_release = QtWidgets.QRadioButton("on release")
        if self.profile_data.activate_on == "press":
            self.activate_press.setChecked(True)
        else:
            self.activate_release.setChecked(True)
        self.activate_press.toggled.connect(self._activation_changed_cb)
        self.activate_release.toggled.connect(self._activation_changed_cb)
        self.activation_moment_layout.addWidget(self.activate_press)
        self.activation_moment_layout.addWidget(self.activate_release)
        self.activation_moment_box.setLayout(self.activation_moment_layout)
        self.options_layout.addWidget(self.activation_moment_box)

        # Toggle type (hold / momentary)
        self.toggle_type_box = QtWidgets.QGroupBox("Toggle type:")
        self.toggle_type_layout = QtWidgets.QVBoxLayout()
        self.toggle_hold = QtWidgets.QRadioButton("hold")
        self.toggle_momentary = QtWidgets.QRadioButton("momentary")
        if self.profile_data.toggle_type == "hold":
            self.toggle_hold.setChecked(True)
        else:
            self.toggle_momentary.setChecked(True)
        self.toggle_hold.toggled.connect(self._toggle_type_changed_cb)
        self.toggle_momentary.toggled.connect(self._toggle_type_changed_cb)
        self.toggle_type_layout.addWidget(self.toggle_hold)
        self.toggle_type_layout.addWidget(self.toggle_momentary)
        self.toggle_type_box.setLayout(self.toggle_type_layout)
        self.options_layout.addWidget(self.toggle_type_box)

        self.action_layout.addLayout(self.options_layout)

        if len(self.profile_data.action_sets) > 0:
            assert len(self.profile_data.action_sets) == 1

            widget = self._create_action_set_widget(
                self.profile_data.action_sets[0],
                "SmartToggle",
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
                "SmartToggle",
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

    def _toggle_type_changed_cb(self, value):
        """Updates the toggle type

        :param value whether or not the selection was toggled - ignored
        """
        if self.toggle_hold.isChecked():
            self.profile_data.toggle_type = "hold"
        else:
            self.profile_data.toggle_type = "momentary"

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
            return "SmartToggle"


class SmartToggleContainerFunctor(gremlin.base_classes.AbstractFunctor):

    """Executes the contents of the associated SmartToggle container."""

    def __init__(self, container):
        super().__init__(container)
        self.action_set = gremlin.execution_graph.ActionSetExecutionGraph(
            container.action_sets[0]
        )
        self.delay = container.delay
        self.activate_on = container.activate_on
        self.toggle_type = container.toggle_type
        self.toggle_status = False
        self.timer = None
        self.value_press = None
        self.event_press = None
        # TODO find proper way to do this
        self.action_set.functors[1].needs_auto_release = False

    def process_event(self, event, value):
        # TODO: Currently this does not handle hat or axis events, however
        #       virtual buttons created on those inputs is supported
        if not isinstance(value.current, bool):
            logging.getLogger("system").warning(
                "Invalid data type received in Tempo container: {}".format(
                    type(event.value)
                )
            )
            return False

        # Copy state when input is pressed
        if value.current:
            self.value_press = copy.deepcopy(value)
            self.event_press = event.clone()

        # Execute smart trigger logic
        if value.current:
            self.start_time = time.time()
            self.toggle_status = not self.toggle_status

            if self.activate_on == "press":
                if self.toggle_type == "hold":
                    self._process_hold_toggle(self.toggle_status, event, value)
                else:
                    self._process_momentary_toggle(event, value)
            elif self.delay > 0.0:
                # on release, we still want to send a toggle after delay seconds
                self.timer = threading.Timer(self.delay, self._long_press)
                self.timer.start()
        else:
            if self.timer:
                self.timer.cancel()
            # Short press
            if (self.start_time + self.delay) > time.time() or self.delay == 0.0:
                if self.activate_on == "release":
                    if self.toggle_type == "hold":
                        self._process_hold_toggle(self.toggle_status, self.event_press, self.value_press, event, value)
                    else:
                        self._process_momentary_toggle(self.event_press, self.value_press, event, value)
            # Long press
            else:
                if self.toggle_type == "hold":
                    self.toggle_status = not self.toggle_status
                    self._process_hold_toggle(self.toggle_status, self.event_press, self.value_press, event, value)
                else:
                    self._process_momentary_toggle(self.event_press, self.value_press, event, value)

            self.timer = None

        return True

    def _generate_events(self, event_p, value_p, event_r=None, value_r=None):
        """Callback executed for a short press action.

        :param event_p event to press the action
        :param value_p value to press the action
        :param event_r event to release the action
        :param value_r value to release the action
        """
        if event_r is None:
            event_r = event_p.clone()
        if value_r is None:
            value_r = copy.deepcopy(value_p)
            value_r.current = False
        return event_p, value_p, event_r, value_r

    def _process_hold_toggle(self, target_status, event_p, value_p, event_r=None, value_r=None):
        event_p, value_p, event_r, value_r = self._generate_events(
                event_p, value_p, event_r, value_r)
        if target_status:
            self.action_set.process_event(event_p, value_p)
        else:
            self.action_set.process_event(event_r, value_r)
        return True

    def _process_momentary_toggle(self, event_p, value_p, event_r=None, value_r=None):
        def _send_momentary_toggle_events(event_p, value_p, event_r, value_r):
            self.action_set.process_event(event_p, value_p)
            time.sleep(0.05)
            self.action_set.process_event(event_r, value_r)

        event_p, value_p, event_r, value_r = self._generate_events(
                event_p, value_p, event_r, value_r)

        threading.Thread(target=lambda: _send_momentary_toggle_events(
            event_p, value_p, event_r, value_r)).start()

        return True

    def _long_press(self):
        """Callback executed, when the delay expires."""
        if self.toggle_type == "hold":
            self._process_hold_toggle(self.toggle_status, self.event_press, self.value_press)
        else:
            self._process_momentary_toggle(self.event_press, self.value_press)


class SmartToggleContainer(gremlin.base_classes.AbstractContainer):

    """Represents a container which holds exactly one action."""

    name = "SmartToggle"
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
        self.toggle_type = "hold"
        self.activate_on = "release"

    def _parse_xml(self, node):
        """Populates the container with the XML node's contents.

        :param node the XML node with which to populate the container
        """
        super()._parse_xml(node)
        self.delay = float(node.get("delay", 0.5))
        self.activate_on = node.get("activate-on", "release")
        self.toggle_type = node.get("toggle-type", "hold")

    def _generate_xml(self):
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
        node = ElementTree.Element("container")
        node.set("type", SmartToggleContainer.tag)
        node.set("delay", str(self.delay))
        node.set("toggle-type", str(self.toggle_type))
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
