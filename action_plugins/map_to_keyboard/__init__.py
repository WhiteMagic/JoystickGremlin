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
from xml.etree import ElementTree

from PyQt5 import QtCore, QtGui, QtWidgets

from .. import common
from gremlin.common import InputType
import gremlin.ui.common
import gremlin.ui.input_item


class MapToKeyboardWidget(gremlin.ui.input_item.AbstractActionWidget):

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent)

    def _create_ui(self):
        self.key_combination = QtWidgets.QLabel()
        self.record_button = QtWidgets.QPushButton("Record keys")

        self.record_button.clicked.connect(self._record_keys_cb)

        self.main_layout.addWidget(self.key_combination)
        self.main_layout.addWidget(self.record_button)
        self.main_layout.addStretch(1)

    def _populate_ui(self):
        text = "<b>Current key combination:</b> "
        names = []
        for key in self.action_data.keys:
            names.append(gremlin.macro.key_from_code(*key).name)
        text += " + ".join(names)

        self.key_combination.setText(text)

    def _update_keys(self, keys):
        self.action_data.keys = [(key.scan_code, key.is_extended) for key in keys]
        self.modified.emit()

    def _record_keys_cb(self):
        self.button_press_dialog = gremlin.ui.common.InputListenerWidget(
            self._update_keys,
            [common.InputType.Keyboard],
            return_kb_event=False,
            multi_keys=True
        )

        # Display the dialog centered in the middle of the UI
        root = self
        while root.parent():
            root = root.parent()
        geom = root.geometry()

        self.button_press_dialog.setGeometry(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
            300,
            150
        )
        self.button_press_dialog.show()


class MapToKeyboard(gremlin.base_classes.AbstractAction):

    icon = None
    name = "Map to Keyboard"
    tag = "map-to-keyboard"
    widget = MapToKeyboardWidget
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat
    ]
    callback_params = []

    def __init__(self, parent):
        super().__init__(parent)
        self.keys = []

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_activation_condition(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        self.keys = []

        for child in node.findall("key"):
            self.keys.append((
                int(child.get("scan_code")),
                gremlin.profile.parse_bool(child.get("extended"))
            ))

    def _generate_xml(self):
        node = ElementTree.Element("map-to-keyboard")
        for key in self.keys:
            key_node = ElementTree.Element("key")
            key_node.set("scan_code", str(key[0]))
            key_node.set("extended", str(key[1]))
            node.append(key_node)
        return node

    def _generate_code(self):
        return self._code_generation("map_to_keyboard", {"entry": self})

    def _is_valid(self):
        return len(self.keys) > 0


version = 1
name = "map-to-keyboard"
create = MapToKeyboard
