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
import gremlin.ui.input_item


class PauseActionWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget for the pause action."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent)
        assert(isinstance(action_data, PauseAction))

    def _create_ui(self):
        self.label = QtWidgets.QLabel("Pauses callback execution")
        self.main_layout.addWidget(self.label)

    def _populate_ui(self):
        pass


class PauseAction(AbstractAction):

    """Action for pausing the execution of callbacks."""

    name = "Pause"
    tag = "pause"
    widget = PauseActionWidget
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]
    callback_params = []

    def __init__(self, parent):
        super().__init__(parent)

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_activation_condition(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        pass

    def _generate_xml(self):
        return ElementTree.Element("pause")

    def _generate_code(self):
        return self._code_generation("pause", {"entry": self})

    def _is_valid(self):
        return True


version = 1
name = "pause"
create = PauseAction
