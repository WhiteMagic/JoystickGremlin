# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
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


from PyQt5 import QtWidgets
from xml.etree import ElementTree

import action_plugins.common
from action_plugins.common import AbstractAction, AbstractActionWidget
from gremlin.common import UiInputType
import gremlin.error


class RemapWidget(AbstractActionWidget):

    """Dialog which allows the selection of a vJoy output to use as
    as the remapping for the currently selected input.
    """

    # Mapping from types to display names
    type_to_name_map = {
        UiInputType.JoystickAxis: "Axis",
        UiInputType.JoystickButton: "Button",
        UiInputType.JoystickHat: "Hat",
        UiInputType.Keyboard: "Button",
    }
    name_to_type_map = {
        "Axis": UiInputType.JoystickAxis,
        "Button": UiInputType.JoystickButton,
        "Hat": UiInputType.JoystickHat
    }

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        """Creates a new RemapWidget.

        :param action_data profile.InputItem data for this widget
        :param vjoy_devices the list of available vjoy devices
        :param change_cb callback to execute when the widget changes
        :param parent of this widget
        """
        AbstractActionWidget.__init__(
            self,
            action_data,
            vjoy_devices,
            change_cb,
            parent
        )
        assert(isinstance(action_data, Remap))

    def _setup_ui(self):
        self.device_dropdown = None
        self.input_item_dropdowns = []

        self._create_device_dropdown()
        self._create_input_item_dropdown()

    def _create_device_dropdown(self):
        """Creates the vJoy device selection drop downs."""
        self.device_dropdown = QtWidgets.QComboBox(self)
        for i in range(1, len(self.vjoy_devices)+1):
            self.device_dropdown.addItem("vJoy Device {:d}".format(i))
        self.main_layout.addWidget(self.device_dropdown)
        self.device_dropdown.activated.connect(self._update_device)

    def _create_input_item_dropdown(self):
        """Creates the vJoy input item selection drop downs."""
        count_map = {
            UiInputType.JoystickAxis: lambda x: x.axes,
            UiInputType.JoystickButton: lambda x: x.buttons,
            UiInputType.JoystickHat: lambda x: x.hats
        }
        input_type = self.action_data.parent.input_type
        if input_type == UiInputType.Keyboard:
            input_type = UiInputType.JoystickButton

        self.input_item_dropdowns = []

        # Create input item selections for the vjoy devices, each
        # selection will be invisible unless it is selected as the
        # active device
        for dev in self.vjoy_devices:
            selection = QtWidgets.QComboBox(self)
            selection.setMaxVisibleItems(20)

            # Add items based on the input type
            for i in range(1, count_map[input_type](dev)+1):
                selection.addItem("{} {:d}".format(
                    self.type_to_name_map[input_type],
                    i
                ))
            # If we are dealing with an axis add buttons as valid
            # remap targets as well for usage with axis conditions
            if input_type == UiInputType.JoystickAxis:
                for i in range(1, count_map[UiInputType.JoystickButton](dev)+1):
                    selection.addItem("{} {:d}".format(
                        self.type_to_name_map[UiInputType.JoystickButton],
                        i
                    ))

            # Add the selection and hide it
            selection.setVisible(False)
            selection.activated.connect(self.change_cb)
            self.main_layout.addWidget(selection)
            self.input_item_dropdowns.append(selection)

        # Show the "None" selection entry
        self.input_item_dropdowns[0].setVisible(True)

    def _update_device(self, index):
        """Handles changing the vJoy device in a remap configuration.

        :param index vjoy device index
        """
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)
        self.input_item_dropdowns[index].setVisible(True)
        self.input_item_dropdowns[index].setCurrentIndex(0)
        self.change_cb()

    def to_profile(self):
        vjoy_device_id = self.device_dropdown.currentIndex()
        input_selection = \
            self.input_item_dropdowns[vjoy_device_id].currentText()
        # Count devices starting at 1 rather then 0
        vjoy_device_id += 1

        arr = input_selection.split()
        vjoy_input_type = self.name_to_type_map[arr[0]]
        vjoy_item_id = int(arr[1])

        self.action_data.vjoy_device_id = vjoy_device_id
        self.action_data.vjoy_input_id = vjoy_item_id
        self.action_data.input_type = vjoy_input_type
        self.action_data.is_valid = True

    def initialize_from_profile(self, action_data):
        # Store new profile data
        self.action_data = action_data

        # Get the appropriate vjoy device identifier
        dev_id = 0
        if action_data.vjoy_device_id not in [0, None]:
            dev_id = self.device_dropdown.findText(
                "vJoy Device {:d}".format(action_data.vjoy_device_id)
            )

        # If no valid input item is selected get the next unused one
        if action_data.vjoy_input_id in [0, None]:
            main_profile = self.action_data.parent.parent.parent.parent
            free_inputs = main_profile.list_unused_vjoy_inputs(
                    self.vjoy_devices
            )
            type_name = self.type_to_name_map[action_data.input_type].lower()
            input_list = free_inputs[dev_id+1][type_name]
            # If we have an unused item use it, otherwise use the first one
            if len(input_list) > 0:
                input_id = input_list[0]
            else:
                input_id = 1
        # If a valid input item is present use it
        else:
            input_id = action_data.vjoy_input_id

        # Retrieve the index of the correct entry in the combobox
        input_name = "{} {:d}".format(
            self.type_to_name_map[action_data.input_type],
            input_id
        )
        btn_id = self.input_item_dropdowns[dev_id].findText(input_name)

        # Select and display correct combo boxes and entries within
        self.device_dropdown.setCurrentIndex(dev_id)
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)
        self.input_item_dropdowns[dev_id].setVisible(True)
        self.input_item_dropdowns[dev_id].setCurrentIndex(btn_id)


class Remap(AbstractAction):

    """Action remapping physical joystick inputs to vJoy inputs."""

    icon = None
    name = "Remap"
    tag = "remap"
    widget = RemapWidget
    input_types = [
        UiInputType.JoystickAxis,
        UiInputType.JoystickButton,
        UiInputType.JoystickHat,
        UiInputType.Keyboard
    ]

    def __init__(self, parent):
        AbstractAction.__init__(self, parent)

        self.vjoy_device_id = None
        self.vjoy_input_id = None
        self.input_type = None

    def _parse_xml(self, node):
        if "axis" in node.attrib:
            self.input_type = UiInputType.JoystickAxis
            self.vjoy_input_id = int(node.get("axis"))
            self.condition = action_plugins.common.parse_axis_condition(node)
        elif "button" in node.attrib:
            self.input_type = UiInputType.JoystickButton
            self.vjoy_input_id = int(node.get("button"))
            self.condition = action_plugins.common.parse_button_condition(node)
        elif "hat" in node.attrib:
            self.input_type = UiInputType.JoystickHat
            self.vjoy_input_id = int(node.get("hat"))
            self.condition = action_plugins.common.parse_hat_condition(node)
        elif "keyboard" in node.attrib:
            self.input_type = UiInputType.Keyboard
            self.vjoy_input_id = int(node.get("button"))
            self.condition = action_plugins.common.parse_button_condition(node)
        else:
            raise gremlin.error.GremlinError(
                "Invalid remap type provided: {}".format(node.attrib)
            )

        self.vjoy_device_id = int(node.get("vjoy"))

    def _generate_xml(self):
        node = ElementTree.Element("remap")
        node.set("vjoy", str(self.vjoy_device_id))
        if self.input_type == UiInputType.Keyboard:
            node.set(
                action_plugins.common.input_type_to_tag(UiInputType.JoystickButton),
                str(self.vjoy_input_id)
            )
        else:
            node.set(
                action_plugins.common.input_type_to_tag(self.input_type),
                str(self.vjoy_input_id)
            )
        return node

    def _generate_code(self):
        return self._code_generation(
            "remap",
            {
                "entry": self,
                "gremlin": gremlin
            }
        )

version = 1
name = "remap"
create = Remap
