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
HA Switch Mode is a modul to send States from Joystick Gremlin to Home Assisten over the HA RESTful API.

"""

import os
from PyQt5 import QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
import gremlin.profile
import gremlin.ui.input_item
from gremlin.ha_request import set_ha_entity_states
from config_ha_jg import ENTITIES


class HASwitchModeWidget(gremlin.ui.input_item.AbstractActionWidget):
    """
    HA Switch Mode is a modul to send States from Joystick Gremlin to Home Assistant over the HA RESTful API.
    Written by Tholo
    """

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent=parent)
        assert isinstance(action_data, HASwitchMode)

    def _create_ui(self):
        self.inner_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel("<b>Home Assistant Sensor Arguments</b>")
        self.ha_request_text = QtWidgets.QLineEdit()
        self.ha_request_text.textChanged.connect(self._update_sensor_msg)
        self.inner_layout.addWidget(self.label)
        self.inner_layout.addWidget(self.ha_request_text)

        self.mode_list = QtWidgets.QComboBox()
        for entry in gremlin.profile.mode_list(self.action_data):
            self.mode_list.addItem(entry)
        self.mode_list.activated.connect(self._mode_list_changed_cb)

        self.entity_list = QtWidgets.QComboBox()
        for entity, friendly_name in ENTITIES.items():
            self.entity_list.addItem(entity)

        # todo subinnerlayout for Descriptions
        self.entity_list.activated.connect(self._entity_list_changed_cb)
        self.main_layout.addWidget(self.entity_list)
        self.main_layout.addWidget(self.mode_list)
        self.main_layout.addLayout(self.inner_layout)



    def _mode_list_changed_cb(self):
        self.action_data.mode_name = self.mode_list.currentText()
        self.action_modified.emit()

    def _entity_list_changed_cb(self):
        self.action_data.entity_name = self.entity_list.currentText()
        print(f"Entity aus action {self.action_data.entity_name}")
        self.action_modified.emit()

    def _get_friendly_name_cb(self):
        # todo rewrite entity with friendly names
        pass

    def _populate_ui(self):
        self.ha_request_text.setText(self.action_data.text)
        mode_id = self.mode_list.findText(self.action_data.mode_name)
        entity_id = self.entity_list.findText(self.action_data.entity_name)
        self.entity_list.setCurrentIndex(entity_id)
        self.mode_list.setCurrentIndex(mode_id)

    def _update_sensor_msg(self, value):
        self.action_data.text = value


class HASwitchModeFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)
        self.mode_name = action.mode_name
        self.text = action.text
        self.entity_name = action.entity_name

    def process_event(self, event, value):
        set_ha_entity_states(self.entity_name, self.mode_name,
                             friendly_name=entities.get(self.entity_name, None),
                             attributes=self.text)
        return True


class HASwitchMode(AbstractAction):
    """Action representing the change of Sensor or Light in Home Assistent."""

    name = "HA Switch Mode"
    tag = "ha-switch-mode"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = HASwitchModeFunctor
    widget = HASwitchModeWidget

    def __init__(self, parent):
        super().__init__(parent)
        self.mode_name = self.get_mode().name
        self.text = ""
        self.entity_name = ""

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
        node = ElementTree.Element("ha-switch-mode")
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
name = "ha-switch-mode"
create = HASwitchMode
