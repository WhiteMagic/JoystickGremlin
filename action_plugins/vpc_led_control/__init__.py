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

"""
VPC Led Control is a modul to send Colour States from Joystick Gremlin to the Virpil Joystick LEDs.

"""

import os
from xml.etree import ElementTree

from PyQt5 import QtWidgets

import gremlin.profile
import gremlin.ui.input_item
import gremlin.vpc_led_controller
from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType


class VPC_LedModeWidget(gremlin.ui.input_item.AbstractActionWidget):
    """
    VPC Led Control is a modul to send Colour States from Joystick Gremlin to the Virpil Joystick LEDs.
    the VPC_Led_Control.exe is from the Virpil Software Suite.
    More Information about at
    https://forum.virpil.com/index.php?/topic/2326-vpc_led_control-new-small-tool-to-control-leds-on-your-vpc-device/

    Modul is written by Tholo
    """

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent=parent)
        assert isinstance(action_data, VPC_LEDMode)

    def _create_ui(self):
        self.device_list = QtWidgets.QComboBox()
        self.devices = gremlin.joystick_handling.joystick_devices()
        for dev in self.devices:
            self.device_list.addItem(dev.name)
        self.device_list.activated.connect(self._device_list_changed_cb)

        self.command_list = QtWidgets.QComboBox()
        for command in gremlin.vpc_led_controller.COMMAND_LIST:
            self.command_list.addItem(command)
        self.command_list.activated.connect(self._command_list_changed_cb)

        self.group_box = QtWidgets.QGroupBox("Color")
        self.groupbox_layout = QtWidgets.QVBoxLayout(self.group_box)
        self.last_color = QtWidgets.QLabel()
        self.groupbox_layout.addWidget(self.last_color)
        self.color_button = QtWidgets.QPushButton("change Color")
        self.color_button.clicked.connect(self._color_button_cb)

        #self.groupbox_layout.addWidget(self.color_button)
        self.groupbox_layout.addWidget(self.color_button)
        self.main_layout.addWidget(self.device_list)
        self.main_layout.addWidget(self.command_list)
        self.main_layout.addWidget(self.group_box)

    def _command_list_changed_cb(self):
        self.action_data.command = self.command_list.currentText()
        self.action_modified.emit()

    def _color_button_cb(self):
        self.button_press_dialog = QtWidgets.QColorDialog.getColor()
        color_hex = str(self.button_press_dialog.name())
        self.action_data.color = color_hex[1:]
        self.action_modified.emit()

    def _device_list_changed_cb(self):
        self.action_data.device_name = self.device_list.currentText()
        self._get_vid_pid()
        self.action_modified.emit()

    def _get_vid_pid(self):
        """
        read device vid and pid
        """
        for dev in self.devices:
            if dev.name == self.action_data.device_name:
                if len(format(int(dev.vendor_id), "x")) == 4:
                    vendor_id = str(format(int(dev.vendor_id), "x"))
                    self.action_data.device_vid = vendor_id
                elif len(format(int(dev.vendor_id), "#x")) >= 5:
                    vendor_id_format = str(format(int(dev.vendor_id), "#x")).replace("0x", "0")
                    self.action_data.device_vid = vendor_id_format

                if len(format(int(dev.product_id), "#x")) == 4:
                    p_id = str(format(int(dev.product_id), "#x"))
                    self.action_data.device_pid = p_id
                elif len(format(int(dev.product_id), "#x")) >= 5:
                    p_id_format = str(format(int(dev.product_id), "x")).replace("0x", "0")
                    if len(p_id_format) == 3:
                        p_id_format = f"0{p_id_format}"
                    self.action_data.device_pid = p_id_format

    def _populate_ui(self):
        command_id = self.command_list.findText(self.action_data.command)
        device_id = self.device_list.findText(self.action_data.device_name)
        self.command_list.setCurrentIndex(command_id)
        self.device_list.setCurrentIndex(device_id)
        self.last_color.setText(f"Current Color is: #{self.action_data.color}\n "
                                f"'rgb': {self.hex2rgb(self.action_data.color)}")
        self.last_color.setStyleSheet(f'color: #{self.action_data.color}')

    def hex2rgb(self, color):
        if len(color) == 0:
            color = "000000"
        rgb = list(int(color[i:i + 2], 16) for i in (0, 2, 4))
        return rgb

class VPC_LedModeFunctor(AbstractFunctor):
    def __init__(self, action):
        super().__init__(action)
        self.mode_name = action.mode_name
        self.color = action.color
        self.device_name = action.device_name
        self.command = action.command
        self.device_vid = action.device_vid
        self.device_pid = action.device_pid

    def process_event(self, event, value):  # todo add vpc uid from gui
        if len(self.color) == 0:
            self.color = "000000"
        send_color = gremlin.vpc_led_controller.set_color(self.device_vid, self.device_pid, self.command, self.color)
        if send_color:
            return True
        else:
            return False


class VPC_LEDMode(AbstractAction):
    """An action that can change the colors of the Virpil Devices."""
    name = "VPC Led Control"
    tag = "vpc_led"

    default_button_activation = (True, False)
    input_types = [
            InputType.JoystickAxis,
            InputType.JoystickButton,
            InputType.JoystickHat,
            InputType.Keyboard
            ]

    functor = VPC_LedModeFunctor
    widget = VPC_LedModeWidget

    def __init__(self, parent):
        super().__init__(parent)
        self.mode_name = self.get_mode().name
        self.color = ""
        self.device_name = ""
        self.command = ""
        self.device_vid = ""
        self.device_pid = ""

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        return self.get_input_type() in [
                InputType.JoystickAxis,
                InputType.JoystickHat
                ]

    def _parse_xml(self, node):
        self.color = gremlin.profile.safe_read(
                node, "color-hex", str, ""
                )
        for child in node:
            if child.tag == "led-command":
                self.command = child.get("command")
            if child.tag == "mode":
                self.mode_name = child.get("mode-name")
            if child.tag == "virpil-device":
                self.device_name = child.get("vpc-name")
            if child.tag == "virtual-usb-id":
                self.device_vid = child.get("vid")
                self.device_pid = child.get("pid")

    def _generate_xml(self):
        node = ElementTree.Element("vpc_led")
        node.set("color-hex", str(self.color))
        command_child = ElementTree.Element("led-command")
        command_child.set("command", self.command)
        mode_child = ElementTree.Element("mode")
        mode_child.set("mode-name", self.mode_name)
        entity_child = ElementTree.Element("virpil-device")
        entity_child.set("vpc-name", str(self.device_name))
        vid_child = ElementTree.Element("virtual-usb-id")
        vid_child.set("vid", self.device_vid)
        #pid_child = ElementTree.Element("p-usb-id")
        vid_child.set("pid", self.device_pid)
        node.append(command_child)
        node.append(mode_child)
        node.append(entity_child)
        node.append(vid_child)
        return node

    def _is_valid(self):
        return len(self.device_name) > 0


version = 1
name = "vpc_led"
create = VPC_LEDMode



