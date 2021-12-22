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
from PyQt5 import QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
import gremlin.ui.input_item


class TextToSpeechWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget which allows the configuration of TTS actions."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent=parent)
        assert isinstance(action_data, TextToSpeech)

    def _create_ui(self):
        self.text_field = QtWidgets.QPlainTextEdit()
        self.text_field.textChanged.connect(self._content_changed_cb)
        self.main_layout.addWidget(self.text_field)

    def _content_changed_cb(self):
        self.action_data.text = self.text_field.toPlainText()

    def _populate_ui(self):
        self.text_field.setPlainText(self.action_data.text)


class TextToSpeechFunctor(AbstractFunctor):

    tts = gremlin.tts.TextToSpeech()

    def __init__(self, action):
        super().__init__(action)
        self.text = action.text

    def process_event(self, event, value):
        TextToSpeechFunctor.tts.speak(gremlin.tts.text_substitution(self.text))
        return True


class TextToSpeech(AbstractAction):

    """Action representing a single TTS entry."""

    name = "Text to Speech"
    tag = "text-to-speech"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = TextToSpeechFunctor
    widget = TextToSpeechWidget

    def __init__(self, parent):
        super().__init__(parent)
        self.text = ""

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        self.text = node.get("text")

    def _generate_xml(self):
        node = ElementTree.Element("text-to-speech")
        node.set("text", self.text)
        return node

    def _is_valid(self):
        return len(self.text) > 0


version = 1
name = "text-to-speech"
create = TextToSpeech
