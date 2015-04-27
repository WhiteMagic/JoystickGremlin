# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
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

from mako.template import Template
from PyQt5 import QtWidgets
from xml.etree import ElementTree

import action
from action.common import AbstractAction, AbstractActionWidget
from gremlin.event_handler import InputType
import gremlin.error


class RemapWidget(AbstractActionWidget):

    """Dialog which allows the selection of a vJoy output to use as
    as the remapping for the currently selected input.
    """

    # Mapping from types to display names
    name_map = {
        InputType.JoystickAxis: "Axis",
        InputType.JoystickButton: "Button",
        InputType.JoystickHat: "Hat",
        InputType.Keyboard: "Button",
    }

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        """Creates a new RemapWidget.

        :param action_data profile.InputItem data for this widget
        :param vjoy_devices the list of available vjoy devices
        :param change_cb callback to execute when the widget changes
        :param parent of this widget
        """
        AbstractActionWidget.__init__(self, action_data, vjoy_devices, change_cb, parent)
        assert(isinstance(action_data, Remap))

    def _setup_ui(self):
        self.device_dropdown = None
        self.input_item_dropdowns = []

        self._create_device_dropdown()
        self._create_input_item_dropdown()

    def _create_device_dropdown(self):
        """Creates the vJoy device selection drop downs."""
        self.device_dropdown = QtWidgets.QComboBox(self)
        self.device_dropdown.addItem("None")
        for i in range(1, len(self.vjoy_devices)+1):
            self.device_dropdown.addItem("vJoy Device {:d}".format(i))
        self.main_layout.addWidget(self.device_dropdown)
        self.device_dropdown.activated.connect(self._update_device)

    def _create_input_item_dropdown(self):
        """Creates the vJoy input item selection drop downs."""
        count_map = {
            InputType.JoystickAxis: lambda x: x.axes,
            InputType.JoystickButton: lambda x: x.buttons,
            InputType.JoystickHat: lambda x: x.hats
        }
        input_type = self.action_data.input_type
        if input_type == InputType.Keyboard:
            input_type = InputType.JoystickButton

        self.input_item_dropdowns = []

        # Create "None" selection
        selection = QtWidgets.QComboBox(self)
        selection.addItem("None")
        selection.setVisible(False)
        self.main_layout.addWidget(selection)
        selection.activated.connect(self.change_cb)
        self.input_item_dropdowns.append(selection)

        # Create input item selections
        for dev in self.vjoy_devices:
            selection = QtWidgets.QComboBox(self)
            selection.addItem("None")
            for i in range(1, count_map[input_type](dev)+1):
                selection.addItem("{} {:d}".format(
                    self.name_map[input_type],
                    i
                ))
            selection.setVisible(False)
            selection.activated.connect(self.change_cb)
            self.main_layout.addWidget(selection)
            self.input_item_dropdowns.append(selection)
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
        vjoy_item_id = self.input_item_dropdowns[vjoy_device_id].currentIndex()

        self.action_data.vjoy_device_id = vjoy_device_id
        self.action_data.vjoy_input_id = vjoy_item_id
        self.action_data.is_valid = (vjoy_item_id != 0 and vjoy_item_id != 0)

    def initialize_from_profile(self, action_data):
        # Store new profile data
        self.action_data = action_data

        # Select correct drop down menu entries
        device_name = "None"
        if action_data.vjoy_device_id not in [0, None]:
            device_name = "vJoy Device {:d}".format(action_data.vjoy_device_id)
        input_name = "None"
        if action_data.vjoy_input_id not in [0, None]:
            input_name = "{} {:d}".format(
                self.name_map[action_data.input_type],
                action_data.vjoy_input_id
            )

        dev_id = self.device_dropdown.findText(device_name)
        btn_id = self.input_item_dropdowns[dev_id].findText(input_name)
        self.device_dropdown.setCurrentIndex(dev_id)
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)
        self.input_item_dropdowns[dev_id].setVisible(True)
        self.input_item_dropdowns[dev_id].setCurrentIndex(btn_id)


class Remap(AbstractAction):

    """Action remapping physical joystick inputs to vJoy inputs."""

    icon = "gfx/icon_remap.svg"
    name = "Remap"
    widget = RemapWidget
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    def __init__(self, parent):
        AbstractAction.__init__(self, parent)

        self.vjoy_device_id = None
        self.input_type = None
        self.vjoy_input_id = None

    def _parse_xml(self, node):
        if "axis" in node.attrib:
            self.input_type = InputType.JoystickAxis
            self.vjoy_input_id = int(node.get("axis"))
            self.condition = action.common.parse_axis_condition(node)
        elif "button" in node.attrib:
            self.input_type = InputType.JoystickButton
            self.vjoy_input_id = int(node.get("button"))
            self.condition = action.common.parse_button_condition(node)
        elif "hat" in node.attrib:
            self.input_type = InputType.JoystickHat
            self.vjoy_input_id = int(node.get("hat"))
            self.condition = action.common.parse_hat_condition(node)
        elif "keyboard" in node.attrib:
            self.input_type = InputType.Keyboard
            self.vjoy_input_id = int(node.get("button"))
            self.condition = action.common.parse_button_condition(node)
        else:
            raise gremlin.error.GremlinError(
                "Invalid remap type provided: {}".format(node.attrib)
            )

        self.vjoy_device_id = int(node.get("vjoy"))

    def _generate_xml(self):
        node = ElementTree.Element("remap")
        node.set("vjoy", str(self.vjoy_device_id))
        if self.input_type == InputType.Keyboard:
            node.set(
                action.common.input_type_to_tag(InputType.JoystickButton),
                str(self.vjoy_input_id)
            )
        else:
            node.set(
                action.common.input_type_to_tag(self.input_type),
                str(self.vjoy_input_id)
            )
        return node

    def _generate_code(self):
        tpl = Template(filename="templates/remap_body.tpl")
        return {
            "body": tpl.render(
                entry=self,
                InputType=InputType,
                helpers=action.common.template_helpers
            )
        }