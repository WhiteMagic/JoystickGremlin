# -*- coding: utf-8; -*-

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
from PyQt5 import QtCore, QtGui, QtMultimedia, QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
import gremlin.ui.input_item


class LoadProfileWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget for loading the profile."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent=parent)
        assert isinstance(action_data, LoadProfile)

    def _create_ui(self):
        self.layout = QtWidgets.QHBoxLayout()
        self.file_path = QtWidgets.QLineEdit()
        self.edit_path = QtWidgets.QPushButton()
        self.edit_path.setIcon(QtGui.QIcon("gfx/button_edit.png"))
        self.edit_path.clicked.connect(self._new_executable)

        self.layout.addWidget(self.file_path)
        self.layout.addWidget(self.edit_path)
        self.main_layout.addLayout(self.layout)

    def _populate_ui(self):
        self.file_path.setText(self.action_data.profile_file)

    def _new_executable(self):
        """Prompts the user to select a profile which is to be loaded.
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Path to profile file",
            "C:\\",
            "All Files (*)"
        )
        if fname != "":
            self.action_data.profile_file = fname
            self._populate_ui()


class LoadProfileFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)
        self.profile_file = action.profile_file

    def process_event(self, event, value):
        gremlin.gremlin_ui._do_load_profile(self.profile_file)
        gremlin.gremlin_ui.ui.actionActivate.setChecked(True)
        gremlin.gremlin_ui.activate(True)
        return True


class LoadProfile(AbstractAction):

    """Action to resume callback execution."""

    name = "Load Profile"
    tag = "load-profile"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = LoadProfileFunctor
    widget = LoadProfileWidget

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def __init__(self, parent):
        super().__init__(parent)
        self.profile_file = None

    def requires_virtual_button(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        self.profile_file = node.get("file")

    def _generate_xml(self):
        node = ElementTree.Element("load-profile")
        node.set("file", self.profile_file)
        return node

    def _is_valid(self):
        return self.profile_file is not None and len(self.profile_file) > 0


version = 1
name = "load-profile"
create = LoadProfile
