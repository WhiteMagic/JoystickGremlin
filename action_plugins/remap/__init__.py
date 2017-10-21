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

from .. import common
from gremlin.common import InputType
from gremlin import input_devices, joystick_handling
import gremlin.ui.common
import gremlin.ui.input_item


class RemapWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Dialog which allows the selection of a vJoy output to use as
    as the remapping for the currently selected input.
    """

    # Mapping from types to display names
    type_to_name_map = {
        InputType.JoystickAxis: "Axis",
        InputType.JoystickButton: "Button",
        InputType.JoystickHat: "Hat",
        InputType.Keyboard: "Button",
    }
    name_to_type_map = {
        "Axis": InputType.JoystickAxis,
        "Button": InputType.JoystickButton,
        "Hat": InputType.JoystickHat
    }

    def __init__(self, action_data, parent=None):
        """Creates a new RemapWidget.

        :param action_data profile data managed by this widget
        :param parent the parent of this widget
        """
        devices = gremlin.joystick_handling.joystick_devices()
        self.vjoy_devices = [dev for dev in devices if dev.is_virtual]
        super().__init__(action_data, parent)
        assert(isinstance(action_data, Remap))

    def _create_ui(self):
        """Creates the UI components."""
        input_types = {
            InputType.Keyboard: [
                InputType.JoystickButton
            ],
            InputType.JoystickAxis: [
                InputType.JoystickAxis,
                InputType.JoystickButton
            ],
            InputType.JoystickButton: [
                InputType.JoystickButton
            ],
            InputType.JoystickHat: [
                InputType.JoystickButton,
                InputType.JoystickHat
            ]
        }
        self.vjoy_selector = gremlin.ui.common.VJoySelector(
            self.vjoy_devices,
            self.save_changes,
            input_types[self._get_input_type()]
        )
        self.main_layout.addWidget(self.vjoy_selector)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def _populate_ui(self):
        """Populates the UI components."""
        # Get the appropriate vjoy device identifier
        vjoy_dev_id = 0
        if self.action_data.vjoy_device_id not in [0, None]:
            vjoy_dev_id = self.action_data.vjoy_device_id

        # If no valid input item is selected get the next unused one
        if self.action_data.vjoy_input_id in [0, None]:
            free_inputs = self._get_profile_root().list_unused_vjoy_inputs(
                self.vjoy_devices
            )
            input_type = \
                self.type_to_name_map[self.action_data.input_type].lower()
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
            vjoy_input_id = self.action_data.vjoy_input_id

        self.vjoy_selector.set_selection(
            self.action_data.input_type,
            vjoy_dev_id,
            vjoy_input_id
        )

        # Save changes so the UI updates properly
        self.save_changes()

    def save_changes(self):
        """Saves UI contents to the profile data storage."""
        # Store remap data
        vjoy_data = self.vjoy_selector.get_selection()
        self.action_data.vjoy_device_id = vjoy_data["device_id"]
        self.action_data.vjoy_input_id = vjoy_data["input_id"]
        self.action_data.input_type = vjoy_data["input_type"]

        # Check if this requires an activation condition
        self.action_data.parent.create_or_delete_virtual_button()

        # Signal changes
        self.action_modified.emit()


class RemapFunctor(gremlin.base_classes.AbstractFunctor):

    def __init__(self, action):
        self.vjoy_device_id = action.vjoy_device_id
        self.vjoy_input_id = action.vjoy_input_id
        self.input_type = action.input_type
        self.needs_auto_release = self._check_for_auto_release(action)

    def process_event(self, event, value):
        if self.input_type == InputType.JoystickAxis:
            joystick_handling.VJoyProxy()[self.vjoy_device_id] \
                .axis(self.vjoy_input_id).value = value.current

        elif self.input_type == InputType.JoystickButton:
            if event.event_type == InputType.JoystickButton \
                    and event.is_pressed \
                    and self.needs_auto_release:
                input_devices.ButtonReleaseActions().register_button_release(
                    (self.vjoy_device_id, self.vjoy_input_id),
                    event
                )

            joystick_handling.VJoyProxy()[self.vjoy_device_id] \
                .button(self.vjoy_input_id).is_pressed = value.current
        elif self.input_type == InputType.JoystickHat:
            joystick_handling.VJoyProxy()[self.vjoy_device_id] \
                .hat(self.vjoy_input_id).direction = value.current

        return True

    def _check_for_auto_release(self, action):
        activation_condition = None
        if action.parent.activation_condition:
            activation_condition = action.parent.activation_condition
        elif action.activation_condition:
            activation_condition = action.activation_condition

        # If an input action activation condition is present the auto release
        # may have to be disabled
        needs_auto_release = True
        if activation_condition:
            for condition in activation_condition.conditions:
                if isinstance(condition, gremlin.base_classes.InputActionCondition):
                    if condition.comparison != "always":
                        needs_auto_release = False

        return needs_auto_release


class Remap(gremlin.base_classes.AbstractAction):

    """Action remapping physical joystick inputs to vJoy inputs."""

    name = "Remap"
    tag = "remap"

    default_button_activation = (True, True)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = RemapFunctor
    widget = RemapWidget


    def __init__(self, parent):
        """Creates a new instance.

        :param parent the container to which this action belongs
        """
        super().__init__(parent)

        # Set vjoy ids to None so we know to pick the next best one
        # automatically
        self.vjoy_device_id = None
        self.vjoy_input_id = None
        self.input_type = self.parent.parent.input_type

    def icon(self):
        """Returns the icon corresponding to the remapped input.

        :return icon representing the remap action
        """
        # Do not return a valid icon if the input id itself is invalid
        if self.vjoy_input_id is None:
            return None

        input_string = "axis"
        if self.input_type == InputType.JoystickButton:
            input_string = "button"
        elif self.input_type == InputType.JoystickHat:
            input_string = "hat"
        return "action_plugins/remap/gfx/icon_{}_{:03d}.png".format(
                input_string,
                self.vjoy_input_id
            )

    def requires_virtual_button(self):
        """Returns whether or not the action requires an activation condition.

        :return True if an activation condition is required, False otherwise
        """
        input_type = self.get_input_type()

        if input_type in [InputType.JoystickButton, InputType.Keyboard]:
            return False
        elif input_type == InputType.JoystickAxis:
            if self.input_type == InputType.JoystickAxis:
                return False
            else:
                return True
        elif input_type == InputType.JoystickHat:
            if self.input_type == InputType.JoystickHat:
                return False
            else:
                return True

    def _parse_xml(self, node):
        """Populates the data storage with data from the XML node.

        :param node XML node with which to populate the storage
        """
        if "axis" in node.attrib:
            self.input_type = InputType.JoystickAxis
            self.vjoy_input_id = int(node.get("axis"))
        elif "button" in node.attrib:
            self.input_type = InputType.JoystickButton
            self.vjoy_input_id = int(node.get("button"))
        elif "hat" in node.attrib:
            self.input_type = InputType.JoystickHat
            self.vjoy_input_id = int(node.get("hat"))
        elif "keyboard" in node.attrib:
            self.input_type = InputType.Keyboard
            self.vjoy_input_id = int(node.get("button"))
        else:
            raise gremlin.error.GremlinError(
                "Invalid remap type provided: {}".format(node.attrib)
            )

        self.vjoy_device_id = int(node.get("vjoy"))

    def _generate_xml(self):
        """Returns an XML node encoding this action's data.

        :return XML node containing the action's data
        """
        node = ElementTree.Element("remap")
        node.set("vjoy", str(self.vjoy_device_id))
        if self.input_type == InputType.Keyboard:
            node.set(
                common.input_type_to_tag(InputType.JoystickButton),
                str(self.vjoy_input_id)
            )
        else:
            node.set(
                common.input_type_to_tag(self.input_type),
                str(self.vjoy_input_id)
            )
        return node

    def _generate_code(self):
        """Returns Python code for this action.

        :return Python code related to this action
        """
        return self._code_generation(
            "remap",
            {
                "entry": self
            }
        )

    def _is_valid(self):
        """Returns whether or not the action is configured properly.

        :return True if the action is configured correctly, False otherwise
        """
        return True

version = 1
name = "remap"
create = Remap
