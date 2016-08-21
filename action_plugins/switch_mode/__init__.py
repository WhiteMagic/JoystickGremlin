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

from action_plugins.common import AbstractAction, AbstractActionWidget
from gremlin.common import UiInputType
import gremlin.util


class SwitchModeWidget(AbstractActionWidget):

    """Widget which allows the configuration of a mode to switch to."""

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        AbstractActionWidget.__init__(
            self,
            action_data,
            vjoy_devices,
            change_cb,
            parent
        )
        assert(isinstance(action_data, SwitchMode))

    def _setup_ui(self):
        self.mode_list = QtWidgets.QComboBox()
        for entry in gremlin.util.mode_list(self.action_data):
            self.mode_list.addItem(entry)
        self.mode_list.activated.connect(self.change_cb)
        self.main_layout.addWidget(self.mode_list)

    def to_profile(self):
        self.action_data.mode_name = self.mode_list.currentText()
        self.action_data.is_valid = len(self.action_data.mode_name) > 0

    def initialize_from_profile(self, action_data):
        self.action_data = action_data
        mode_id = self.mode_list.findText(action_data.mode_name)
        self.mode_list.setCurrentIndex(mode_id)


class SwitchMode(AbstractAction):

    """Action representing the change of mode."""

    icon = "gfx/action/action_switch_mode.png"
    name = "Switch Mode"
    tag = "switch-mode"
    widget = SwitchModeWidget
    input_types = [
        UiInputType.JoystickAxis,
        UiInputType.JoystickButton,
        UiInputType.JoystickHat,
        UiInputType.Keyboard
    ]

    def __init__(self, parent):
        AbstractAction.__init__(self, parent)
        self.mode_name = None

    def _parse_xml(self, node):
        self.mode_name = node.get("name")

    def _generate_xml(self):
        node = ElementTree.Element("switch-mode")
        node.set("name", self.mode_name)
        return node

    def _generate_code(self):
        return self._code_generation(
            "switch_mode",
            {"entry": self}
        )

version = 1
name = "switch-mode"
create = SwitchMode
