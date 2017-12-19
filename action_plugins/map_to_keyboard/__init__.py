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

from PyQt5 import QtWidgets

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
from gremlin.input_devices import ButtonReleaseActions
import gremlin.ui.common
import gremlin.ui.input_item


class MapToKeyboardWidget(gremlin.ui.input_item.AbstractActionWidget):

    """UI widget for mapping inputs to keyboard key combinations."""

    def __init__(self, action_data, parent=None):
        """Creates a new instance.

        :param action_data the data managed by this widget
        :param parent the parent of this widget
        """
        super().__init__(action_data, parent)

    def _create_ui(self):
        """Creates the UI components."""
        self.key_combination = QtWidgets.QLabel()
        self.record_button = QtWidgets.QPushButton("Record keys")

        self.record_button.clicked.connect(self._record_keys_cb)

        self.main_layout.addWidget(self.key_combination)
        self.main_layout.addWidget(self.record_button)
        self.main_layout.addStretch(1)

    def _populate_ui(self):
        """Populates the UI components."""
        text = "<b>Current key combination:</b> "
        names = []
        for key in self.action_data.keys:
            names.append(gremlin.macro.key_from_code(*key).name)
        text += " + ".join(names)

        self.key_combination.setText(text)

    def _update_keys(self, keys):
        """Updates the storage with a new set of keys.

        :param keys the keys to use in the key combination
        """
        self.action_data.keys = [
            (key.scan_code, key.is_extended) for key in keys
        ]
        self.action_modified.emit()

    def _record_keys_cb(self):
        """Prompts the user to press the desired key combination."""
        self.button_press_dialog = gremlin.ui.common.InputListenerWidget(
            self._update_keys,
            [InputType.Keyboard],
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


class MapToKeyboardFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)
        self.press = gremlin.macro.Macro()
        for key in action.keys:
            self.press.press(gremlin.macro.key_from_code(key[0], key[1]))

        self.release = gremlin.macro.Macro()
        for key in action.keys:
            self.release.release(gremlin.macro.key_from_code(key[0], key[1]))

    def process_event(self, event, value):
        if value.current:
            gremlin.macro.MacroManager().queue_macro(self.press)
            ButtonReleaseActions().register_callback(
                lambda: gremlin.macro.MacroManager().queue_macro(self.release),
                event
            )
        else:
            gremlin.macro.MacroManager().queue_macro(self.release)
        return True


class MapToKeyboard(AbstractAction):

    """Action data for the map to keyboard action.

    Map to keyboard presses and releases a set of keys in sync with another
    physical input being pressed or released.
    """

    name = "Map to Keyboard"
    tag = "map-to-keyboard"

    default_button_activation = (True, True)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = MapToKeyboardFunctor
    widget = MapToKeyboardWidget

    def __init__(self, parent):
        """Creates a new instance.

        :param parent the container this action is part of
        """
        super().__init__(parent)
        self.keys = []

    def icon(self):
        """Returns the icon to use for this action.

        :return icon representing this action
        """
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        """Returns whether or not an activation condition is needed.

        :return True if an activation condition is required for this particular
            action instance, False otherwise
        """
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        """Reads the contents of an XML node to populate this instance.

        :param node the node whose content should be used to populate this
            instance
        """
        self.keys = []

        for child in node.findall("key"):
            self.keys.append((
                int(child.get("scan_code")),
                gremlin.profile.parse_bool(child.get("extended"))
            ))

    def _generate_xml(self):
        """Returns an XML node containing this instance's information.

        :return XML node containing the information of this  instance
        """
        node = ElementTree.Element("map-to-keyboard")
        for key in self.keys:
            key_node = ElementTree.Element("key")
            key_node.set("scan_code", str(key[0]))
            key_node.set("extended", str(key[1]))
            node.append(key_node)
        return node

    def _is_valid(self):
        """Returns whether or not this action is valid.

        :return True if the action is configured correctly, False otherwise
        """
        return len(self.keys) > 0


version = 1
name = "map-to-keyboard"
create = MapToKeyboard
