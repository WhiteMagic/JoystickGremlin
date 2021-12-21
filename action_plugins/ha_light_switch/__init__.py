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
HA Light Switch is a modul to send commands from Joystick Gremlin to Home Assisten over the HA RESTful API.

"""

import os
from PyQt5 import QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
import gremlin.profile
import gremlin.ui.input_item
from gremlin.ha_request import set_ha_entity_states, get_entity, post_service_to_ha
from config_ha_jg import light_entities
from PyQt5.QtCore import Qt

class HALightSwitchWidget(gremlin.ui.input_item.AbstractActionWidget):
    """
    HA Switch Mode is a modul to send States from Joystick Gremlin to Home Assistant over the HA RESTful API.
    Written by Tholo
    """

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent=parent)
        assert isinstance(action_data, HALightSwitch)

    def _create_ui(self):
        self.inner_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel("<b>Home Assistant Light Extra Arguments</b>")
        self.ha_request_text = QtWidgets.QLineEdit()
        self.ha_request_text.textChanged.connect(self._update_sensor_msg)
        self.inner_layout.addWidget(self.label)
        self.inner_layout.addWidget(self.ha_request_text)


        self.entity_list = QtWidgets.QComboBox()
        for entity, friendly_name in light_entities.items():
            self.entity_list.addItem(entity)
        self.entity_list.activated.connect(self._entity_list_changed_cb)

        self.command_list = QtWidgets.QComboBox()
        for command in ["turn_on", "turn_off", "toggle"]:
            self.command_list.addItem(command)
        self.command_list.activated.connect(self._command_list_changed_cb)

        self.group_box = QtWidgets.QGroupBox("Color")
        self.groupbox_layout = QtWidgets.QVBoxLayout(self.group_box)

        self.last_color = QtWidgets.QLabel()
        self.groupbox_layout.addWidget(self.last_color)

        self.color_button = QtWidgets.QPushButton("change Color")
        self.color_button.clicked.connect(self._color_button_cb)
        self.brightness_label = QtWidgets.QLabel("Brightness ")
        self.brightness_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.brightness_slider.setTickInterval(10)
        self.brightness_slider.valueChanged[int].connect(self._brightness_change_cb)


        self.effect_button = QtWidgets.QPushButton("Set Effect")
        self.effect_button.clicked.connect(self._effect_button_change_cb)


        self.groupbox_layout.addWidget(self.color_button)
        self.groupbox_layout.addWidget(self.brightness_label)
        self.groupbox_layout.addWidget(self.brightness_slider)
        self.groupbox_layout.addWidget(self.effect_button)


        self.main_layout.addWidget(self.entity_list)
        self.main_layout.addWidget(self.command_list)
        self.main_layout.addWidget(self.group_box)
        self.main_layout.addLayout(self.inner_layout)

    def _effect_button_change_cb(self):
        self.effect_dialog = QtWidgets.QDialog()


        self.effect_dialog.exec()

    def _brightness_change_cb(self):
        self.action_data.brightness = self.brightness_slider.value()

    def _command_list_changed_cb(self):
        self.action_data.command = self.command_list.currentText()
        self.action_modified.emit()

    def _entity_list_changed_cb(self):
        self.action_data.entity_name = self.entity_list.currentText()
        self.action_modified.emit()

    def _color_button_cb(self):
        self.button_press_dialog = QtWidgets.QColorDialog.getColor().getRgb()
        rgb_color_hex = str(self.button_press_dialog)
        print(rgb_color_hex)
        self.action_data.color = self.button_press_dialog
        self.action_modified.emit()

    def _update_sensor_msg(self, value):
        self.action_data.text = value

    def _populate_ui(self):
        self.ha_request_text.setText(self.action_data.text)
        entity_id = self.entity_list.findText(self.action_data.entity_name)
        command_id = self.command_list.findText(self.action_data.command)
        self.entity_list.setCurrentIndex(entity_id)
        self.command_list.setCurrentIndex(command_id)
        self.last_color.setText(f"Current Color is: {self.action_data.color}")
        self.last_color.setStyleSheet(f'color: rgb{self.action_data.color}')
        self.brightness_label.setText(f"Brightness {self.action_data.brightness}")
        if isinstance(self.action_data.brightness, int):
            self.brightness_slider.setSliderPosition(self.action_data.brightness)

class EffectDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Effects")
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


class HALightSwitchFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)
        self.entity_name = action.entity_name
        self.command = action.command
        self.color = action.color
        self.text = action.text
        self.brightness = action.brightness


    def process_event(self, event, value):
        # todo attr zusammenbauen
        if "light" in self.entity_name:
            domain = "light"
        else:
            domain = "homeassistent"
            print("Error Domain not set")
        #post_service_to_ha(domain, self.entity_name, self.command, attributes=self.text)
        print(f"do {domain}, Ent {self.entity_name}, cmd {self.command}\n atrr {self.text} "
              f"bright {self.brightness}")
        return True


class HALightSwitch(AbstractAction):
    """Action representing the change of Sensor or Light in Home Assistent."""

    name = "HA Light Switch"
    tag = "ha-light-switch"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = HALightSwitchFunctor
    widget = HALightSwitchWidget

    def __init__(self, parent):
        super().__init__(parent)
        self.entity_name = ""
        self.command = ""

        self.color = ""
        self.brightness = ""
        self.text = ""

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        self.text = gremlin.profile.safe_read(
            node, "text", str, ""
        )
        for child in node:
            if child.tag == "mode":
                self.mode_name = child.get("mode-name")
            if child.tag == "entity":
                self.entity_name = child.get("entity-name")

    def _generate_xml(self):
        node = ElementTree.Element("ha-light-switch")
        node.set("text", str(self.text))
        mode_child = ElementTree.Element("mode")
        mode_child.set("mode-name", self.mode_name)
        entity_child = ElementTree.Element("entity")
        entity_child.set("entity-name", str(self.entity_name))
        node.append(mode_child)
        node.append(entity_child)
        return node

    def _is_valid(self):
        return len(self.entity_name) > 0


version = 1
name = "ha-light-switch"
create = HALightSwitch
