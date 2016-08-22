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


import os
from PyQt5 import QtWidgets
from xml.etree import ElementTree

from action_plugins.common import AbstractAction, AbstractActionWidget
from gremlin.common import UiInputType


class PauseActionWidget(AbstractActionWidget):

    """Widget for the pause action."""

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        AbstractActionWidget.__init__(
            self,
            action_data,
            vjoy_devices,
            change_cb,
            parent
        )
        assert(isinstance(action_data, PauseAction))

    def _setup_ui(self):
        self.label = QtWidgets.QLabel("Pauses callback execution")
        self.main_layout.addWidget(self.label)

    def to_profile(self):
        self.action_data.is_valid = True

    def initialize_from_profile(self, action_data):
        pass


class PauseAction(AbstractAction):

    """Action for pausing the execution of callbacks."""

    name = "Pause"
    tag = "pause"
    widget = PauseActionWidget
    input_types = [
        UiInputType.JoystickAxis,
        UiInputType.JoystickButton,
        UiInputType.JoystickHat,
        UiInputType.Keyboard
    ]

    def __init__(self, parent):
        AbstractAction.__init__(self, parent)

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def _parse_xml(self, node):
        pass

    def _generate_xml(self):
        return ElementTree.Element("pause-action")

    def _generate_code(self):
        return self._code_generation("pause", {"entry": self})


version = 1
name = "pause"
create = PauseAction
