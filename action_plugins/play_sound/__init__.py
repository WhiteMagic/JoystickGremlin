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


import os
from PyQt5 import QtCore, QtGui, QtMultimedia, QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.types import InputType
import gremlin.ui.input_item


class PlaySoundWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget for the resume action."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent=parent)
        assert isinstance(action_data, PlaySound)

    def _create_ui(self):
        self.layout = QtWidgets.QHBoxLayout()
        self.file_path = QtWidgets.QLineEdit()
        self.edit_path = QtWidgets.QPushButton()
        self.edit_path.setIcon(QtGui.QIcon("gfx/button_edit.png"))
        self.edit_path.clicked.connect(self._new_executable)
        self.volume = QtWidgets.QSpinBox()
        self.volume.setRange(0, 100)
        self.volume.valueChanged.connect(self._volume_changed)

        self.layout.addWidget(self.file_path)
        self.layout.addWidget(self.edit_path)
        self.layout.addWidget(QtWidgets.QLabel("Volume"))
        self.layout.addWidget(self.volume)
        self.main_layout.addLayout(self.layout)

    def _populate_ui(self):
        self.file_path.setText(self.action_data.sound_file)
        self.volume.setValue(self.action_data.volume)

    def _volume_changed(self, value):
        self.action_data.volume = value

    def _new_executable(self):
        """Prompts the user to select a new executable to add to the
        profile.
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Path to sound file",
            "C:\\",
            "All Files (*)"
        )
        if fname != "":
            self.action_data.sound_file = fname
            self._populate_ui()


class PlaySoundFunctor(AbstractFunctor):

    player = QtMultimedia.QMediaPlayer()

    def __init__(self, action):
        super().__init__(action)
        self.sound_file = action.sound_file
        self.volume = action.volume

    def process_event(self, event, value):
        PlaySoundFunctor.player.setMedia(
            QtMultimedia.QMediaContent(
                QtCore.QUrl.fromLocalFile(self.sound_file)
            ))
        PlaySoundFunctor.player.setVolume(self.volume)
        PlaySoundFunctor.player.play()
        return True


class PlaySound(AbstractAction):

    """Action to resume callback execution."""

    name = "Play Sound"
    tag = "play-sound"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = PlaySoundFunctor
    widget = PlaySoundWidget

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def __init__(self, parent):
        super().__init__(parent)
        self.sound_file = None
        self.volume = 50

    def requires_virtual_button(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        self.sound_file = node.get("file")
        self.volume = int(node.get("volume", 50))

    def _generate_xml(self):
        node = ElementTree.Element("play-sound")
        node.set("file", self.sound_file)
        node.set("volume", str(self.volume))
        return node

    def _is_valid(self):
        return self.sound_file is not None and len(self.sound_file) > 0


version = 1
name = "play-sound"
create = PlaySound
