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


from xml.etree import ElementTree

import action_plugins.common
from action_plugins.common import AbstractAction, AbstractActionWidget,\
    VJoySelector
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
        input_types = {
            UiInputType.Keyboard: [UiInputType.JoystickButton],
            UiInputType.JoystickAxis:
                [UiInputType.JoystickAxis, UiInputType.JoystickButton],
            UiInputType.JoystickButton: [UiInputType.JoystickButton],
            UiInputType.JoystickHat: [UiInputType.JoystickHat]
        }
        self.vjoy_selector = VJoySelector(
            self.vjoy_devices,
            self.change_cb,
            input_types[self.action_data.parent.input_type]
        )
        self.main_layout.addWidget(self.vjoy_selector)

    def _update_device(self, index):
        """Handles changing the vJoy device in a remap configuration.

        :param index vjoy device index
        """
        self.change_cb()

    def to_profile(self):
        vjoy_data = self.vjoy_selector.get_selection()
        self.action_data.vjoy_device_id = vjoy_data["device_id"]
        self.action_data.vjoy_input_id = vjoy_data["input_id"]
        self.action_data.input_type = vjoy_data["input_type"]
        self.action_data.is_valid = True

    def initialize_from_profile(self, action_data):
        # Store new profile data
        self.action_data = action_data

        # Get the appropriate vjoy device identifier
        vjoy_dev_id = 0
        if action_data.vjoy_device_id not in [0, None]:
            vjoy_dev_id = action_data.vjoy_device_id

        # If no valid input item is selected get the next unused one
        if action_data.vjoy_input_id in [0, None]:
            main_profile = self.action_data.parent.parent.parent.parent
            free_inputs = \
                main_profile.list_unused_vjoy_inputs(self.vjoy_devices)
            input_type = self.type_to_name_map[action_data.input_type].lower()
            if vjoy_dev_id == 0:
                vjoy_dev_id = sorted(free_inputs.keys())[0]
            input_list = free_inputs[vjoy_dev_id][input_type]
            # If we have an unused item use it, otherwise use the first one
            if len(input_list) > 0:
                vjoy_input_id = input_list[0]
            else:
                vjoy_input_id = 1
        # If a valid input item is present use it
        else:
            vjoy_input_id = action_data.vjoy_input_id

        self.vjoy_selector.set_selection(
            self.action_data.input_type,
            vjoy_dev_id,
            vjoy_input_id
        )


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
    callback_params = ["vjoy"]

    def __init__(self, parent):
        AbstractAction.__init__(self, parent)

        self.vjoy_device_id = None
        self.vjoy_input_id = None
        self.input_type = self.parent.input_type

    def icon(self):
        input_string = "axis"
        if self.input_type == UiInputType.JoystickButton:
            input_string = "button"
        elif self.input_type == UiInputType.JoystickHat:
            input_string = "hat"
        return "action_plugins/remap/icon_{}_{:03d}.png".format(
                input_string,
                self.vjoy_input_id
            )

    def _create_default_condition(self):
        if self.parent.input_type in [UiInputType.JoystickButton, UiInputType.Keyboard]:
            self.condition = action_plugins.common.ButtonCondition(True, True)
        elif self.parent.input_type == UiInputType.JoystickAxis:
            self.condition = None
        elif self.parent.input_type == UiInputType.JoystickHat:
            self.condition = action_plugins.common.HatCondition(
                False, False, False, False, False, False, False, False
            )

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
