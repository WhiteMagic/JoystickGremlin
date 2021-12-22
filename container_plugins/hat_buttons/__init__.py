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

from PyQt5 import QtWidgets

import dill

import gremlin
import gremlin.ui.common
import gremlin.ui.input_item
from container_plugins.basic import BasicContainer


# Lookup for direction to index with 4 way hat usage
_four_lookup = {
    (0, 1): 0,
    (1, 0): 1,
    (0, -1): 2,
    (-1, 0): 3
}

# Lookup for direction to indices with 8 way hat usage
_eight_lookup = {
    (0, 1): 0,
    (1, 1): 1,
    (1, 0): 2,
    (1, -1): 3,
    (0, -1): 4,
    (-1, -1): 5,
    (-1, 0): 6,
    (-1, 1): 7
}

# Names for the indices in a 4 way hat case
_four_names = ["North", "East", "South", "West"]

# Names for the indices in a 8 way hat case
_eight_names = [
    "North", "North East", "East", "South East", "South",
    "South West", "West", "North West"
]


class HatButtonsContainerWidget(gremlin.ui.input_item.AbstractContainerWidget):

    """Basic container which holds a single action."""

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the profile data represented by this widget
        :param parent the parent of this widget
        """
        super().__init__(profile_data, parent)

    def _create_action_ui(self):
        """Creates the UI components."""
        gremlin.ui.common.clear_layout(self.action_layout)

        self.options_layout = QtWidgets.QHBoxLayout()
        self.four_way = QtWidgets.QRadioButton("4 Way")
        self.eight_way = QtWidgets.QRadioButton("8 Way")
        if self.profile_data.button_count == 4:
            self.four_way.setChecked(True)
            self.eight_way.setChecked(False)
        else:
            self.four_way.setChecked(False)
            self.eight_way.setChecked(True)
        self.four_way.clicked.connect(self._change_button_type)
        self.eight_way.clicked.connect(self._change_button_type)
        self.options_layout.addWidget(QtWidgets.QLabel("<b>Button mode</b>"))
        self.options_layout.addWidget(self.four_way)
        self.options_layout.addWidget(self.eight_way)
        self.options_layout.addStretch()

        self.action_layout.addLayout(self.options_layout)

        # Create hat direction action sets
        if self.profile_data.button_count == 4:
            for i, direction in enumerate(_four_names):
                if self.profile_data.action_sets[i] is None:
                    self._add_action_selector(
                        lambda x: self._add_action(i, x),
                        direction
                    )
                else:
                    self._create_action_widget(
                        i,
                        direction,
                        self.action_layout,
                        gremlin.ui.common.ContainerViewTypes.Action
                    )
        elif self.profile_data.button_count == 8:
            for i, direction in enumerate(_eight_names):
                if self.profile_data.action_sets[i] is None:
                    self._add_action_selector(
                        lambda x: self._add_action(i, x),
                        direction
                    )
                else:
                    self._create_action_widget(
                        i,
                        direction,
                        self.action_layout,
                        gremlin.ui.common.ContainerViewTypes.Action
                    )
        else:
            pass

        self.action_layout.addStretch()

    def _create_condition_ui(self):
        if self.profile_data.activation_condition_type != "action":
            return

        lookup = _four_lookup
        if self.profile_data.button_count == 8:
            lookup = _eight_lookup
        id_to_direction = {}
        for k, v in lookup.items():
            id_to_direction[v] = k

        names = _four_names
        if self.profile_data.button_count == 8:
            names = _eight_names
        for i, action_set in enumerate(self.profile_data.action_sets):
            widget = self._create_action_set_widget(
                action_set,
                names[i],
                gremlin.ui.common.ContainerViewTypes.Condition
            )
            self.activation_condition_layout.addWidget(widget)
            widget.redraw()
            widget.model.data_changed.connect(self.container_modified.emit)

    def _create_action_widget(self, index, label, layout, view_type):
        """Creates a new action widget.

        :param index the index at which to store the created action
        :param label the name of the action to create
        :param layout the layout widget to populate
        :param view_type the visualization type being used
        """
        widget = self._create_action_set_widget(
            self.profile_data.action_sets[index],
            label,
            view_type
        )
        layout.addWidget(widget)
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
            return "Hat Buttons"

    def _change_button_type(self, state):
        """Handles changing the number of buttons being used.

        :param state radio button state - not used
        """
        button_count = 4 if self.four_way.isChecked() else 8
        if button_count != self.profile_data.button_count:
            self.profile_data.button_count = button_count
            if button_count == 4 and len(self.profile_data.action_sets) == 8:
                del self.profile_data.action_sets[7]
                del self.profile_data.action_sets[5]
                del self.profile_data.action_sets[3]
                del self.profile_data.action_sets[1]
            elif button_count == 8 and len(self.profile_data.action_sets) == 4:
                self.profile_data.action_sets.insert(1, [])
                self.profile_data.action_sets.insert(3, [])
                self.profile_data.action_sets.insert(5, [])
                self.profile_data.action_sets.insert(7, [])
            self._create_action_ui()


class HatButtonsContainerFunctor(gremlin.base_classes.AbstractFunctor):

    """Executes the contents of the associated basic container.

    This functor does nothing when called (should never happen) as the
    callbacks generated by this container are several basic containers.
    """

    def __init__(self, container):
        super().__init__(container)

    def process_event(self, event, value):
        """Executes the content with the provided data.

        :param event the event to process
        :param value the value received with the event
        :return True if execution was successful, False otherwise
        """
        pass


class HatButtonsContainer(gremlin.base_classes.AbstractContainer):

    """Represents a container which holds exactly one action."""

    name = "Hat Buttons"
    tag = "hat_buttons"
    functor = HatButtonsContainerFunctor
    widget = HatButtonsContainerWidget
    input_types = [gremlin.common.InputType.JoystickHat]
    interaction_types = []

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the InputItem this container is linked to
        """
        super().__init__(parent)
        self.button_count = 4
        self.action_sets = [[], [], [], []]

    def generate_callbacks(self):
        """Returns a list of callback data entries.

        :return list of container callback entries
        """
        lookup = _four_lookup
        if self.button_count == 8:
            lookup = _eight_lookup
        id_to_direction = {}
        for k, v in lookup.items():
            id_to_direction[v] = k

        callbacks = []

        # For a virtual button create a callback that sends VirtualButton
        # events and another callback that triggers of these events
        # like a button would.
        for i, action_set in enumerate(self.action_sets):
            # Ignore directions with no associated actions
            if len(action_set) == 0:
                continue

            # Callback generating virtual button events
            callbacks.append(gremlin.execution_graph.CallbackData(
                gremlin.execution_graph.VirtualButtonProcess(
                    gremlin.base_classes.VirtualHatButton([
                        gremlin.util.hat_tuple_to_direction(id_to_direction[i])
                    ])
                ),
                None
            ))
            # Create fake BasicContainer for each action set
            basic_container = BasicContainer()
            basic_container.action_sets = [action_set]
            basic_container.activation_condition = self.activation_condition
            basic_container.activation_condition_type = \
                self.activation_condition_type

            # Callback reacting to virtual button events
            callbacks.append(gremlin.execution_graph.CallbackData(
                gremlin.execution_graph.VirtualButtonCallback(basic_container),
                gremlin.event_handler.Event(
                    gremlin.common.InputType.VirtualButton,
                    callbacks[-1].callback.virtual_button.identifier,
                    device_guid=dill.GUID_Virtual,
                    is_pressed=True,
                    raw_value=True
                )
            ))

        return callbacks

    def _parse_xml(self, node):
        """Populates the container with the XML node's contents.

        :param node the XML node with which to populate the container
        """
        self.button_count = gremlin.profile.safe_read(
            node, "button-count", int, 4
        )

    def _generate_xml(self):
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
        node = ElementTree.Element("container")
        node.set("type", HatButtonsContainer.tag)
        node.set("button-count", str(self.button_count))
        for action_set in self.action_sets:
            as_node = ElementTree.Element("action-set")
            for action in action_set:
                as_node.append(action.to_xml())
            node.append(as_node)
        return node

    def _is_container_valid(self):
        """Returns whether or not this container is configured properly.

        :return True if the container is configured properly, False otherwise
        """
        count = 0
        for action_set in self.action_sets:
            count += len(action_set)
        return count > 0


# Plugin definitions
version = 1
name = "hat_buttons"
create = HatButtonsContainer
