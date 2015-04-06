# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
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

from mako.template import Template
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree

from action.common import AbstractAction, AbstractActionWidget
import gremlin.event_handler


class TextToSpeechWidget(AbstractActionWidget):

    """Widget which allows the configuration of TTS actions."""

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        AbstractActionWidget.__init__(self, action_data, vjoy_devices, change_cb, parent)
        assert(isinstance(action_data, TextToSpeech))

    def _setup_ui(self):
        self.text_field = QtWidgets.QPlainTextEdit()
        self.text_field.textChanged.connect(self.to_profile)
        self.main_layout.addWidget(self.text_field)

    def to_profile(self):
        self.action_data.text = self.text_field.toPlainText()
        self.action_data.is_valid = len(self.action_data.text) > 0

    def initialize_from_profile(self, action_data):
        self.action_data = action_data
        self.text_field.setPlainText(self.action_data.text)


class TextToSpeech(AbstractAction):

    """Action representing a single TTS entry."""

    icon = "gfx/icon_tts.svg"
    name = "Text to Speech"
    widget = TextToSpeechWidget
    input_types = [
        gremlin.event_handler.InputType.JoystickButton,
        gremlin.event_handler.InputType.Keyboard
    ]

    def __init__(self, parent):
        AbstractAction.__init__(self, parent)
        self.text = ""

    def _parse_xml(self, node):
        self.text = node.get("text")

    def _generate_xml(self):
        node = ElementTree.Element("text-to-speech")
        node.set("text", self.text)
        return node

    def _generate_code(self):
        tpl = Template(filename="templates/text_to_speech.tpl")
        return {
            "body": tpl.render(entry=self)
        }