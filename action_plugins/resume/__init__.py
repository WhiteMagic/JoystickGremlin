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


class ResumeActionWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget for the resume action."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent)
        assert isinstance(action_data, ResumeAction)

    def _create_ui(self):
        self.label = QtWidgets.QLabel("Resumes callback execution")
        self.main_layout.addWidget(self.label)

    def _populate_ui(self):
        pass


class ResumeAction(AbstractAction):

    """Action to resume callback execution."""

    name = "Resume"
    tag = "resume"
    widget = ResumeActionWidget
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]
    activation_conditions = [
        InputType.JoystickAxis,
        InputType.JoystickHat
    ]
    activation_conditions = [
        InputType.JoystickAxis,
        InputType.JoystickHat
    ]
    callback_params = []

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def __init__(self, parent):
        super().__init__(parent)

    def _parse_xml(self, node):
        pass

    def _generate_xml(self):
        return ElementTree.Element("resume")

    def _generate_code(self):
        return self._code_generation("resume", {"entry": self})

    def _is_valid(self):
        return True


version = 1
name = "resume"
create = ResumeAction
