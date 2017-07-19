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


import os
from PyQt5 import QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction
from gremlin.common import InputType
import gremlin.profile
import gremlin.ui.input_item


class TemporaryModeSwitchWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget which allows the configuration of a mode to switch to."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent)
        assert isinstance(action_data, TemporaryModeSwitch)

    def _create_ui(self):
        self.mode_list = QtWidgets.QComboBox()
        for entry in gremlin.profile.mode_list(self.action_data):
            self.mode_list.addItem(entry)
        self.mode_list.activated.connect(self._mode_list_changed_cb)
        self.main_layout.addWidget(self.mode_list)

    def _mode_list_changed_cb(self):
        self.action_data.mode_name = self.mode_list.currentText()
        self.modified.emit()

    def _populate_ui(self):
        mode_id = self.mode_list.findText(self.action_data.mode_name)
        self.mode_list.setCurrentIndex(mode_id)


class TemporaryModeSwitch(AbstractAction):

    """Action representing the change of mode."""

    name = "Temporary Mode Switch"
    tag = "temporary-mode-switch"
    widget = TemporaryModeSwitchWidget
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]
    callback_params = []

    def __init__(self, parent):
        super().__init__(parent)
        self.mode_name = self.get_mode().name

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_activation_condition(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        self.mode_name = node.get("name")

    def _generate_xml(self):
        node = ElementTree.Element("temporary-mode-switch")
        node.set("name", self.mode_name)
        return node

    def _generate_code(self):
        return self._code_generation(
            "temporary_mode_switch",
            {"entry": self}
        )

    def _is_valid(self):
        return len(self.mode_name) > 0


version = 1
name = "temporary-mode-switch"
create = TemporaryModeSwitch
