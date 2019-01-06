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
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
import gremlin.ui.input_item


class CycleModesWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget allowing the configuration of a list of modes to cycle."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent=parent)
        assert(isinstance(action_data, CycleModes))

    def _create_ui(self):
        self.model = QtCore.QStringListModel()
        self.view = QtWidgets.QListView()
        self.view.setModel(self.model)
        self.view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Add widgets which allow modifying the mode list
        self.mode_list = QtWidgets.QComboBox()
        for entry in gremlin.profile.mode_list(self.action_data):
            self.mode_list.addItem(entry)
        self.add = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_add.svg"), "Add"
        )
        self.add.clicked.connect(self._add_cb)
        self.delete = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_delete.svg"), "Delete"
        )
        self.delete.clicked.connect(self._remove_cb)
        self.up = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_up.svg"), "Up"
        )
        self.up.clicked.connect(self._up_cb)
        self.down = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_down.svg"), "Down"
        )
        self.down.clicked.connect(self._down_cb)

        self.actions_layout = QtWidgets.QGridLayout()
        self.actions_layout.addWidget(self.mode_list, 0, 0)
        self.actions_layout.addWidget(self.add, 0, 1)
        self.actions_layout.addWidget(self.delete, 0, 2)
        self.actions_layout.addWidget(self.up, 1, 1)
        self.actions_layout.addWidget(self.down, 1, 2)

        self.main_layout.addWidget(self.view)
        self.main_layout.addLayout(self.actions_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def _populate_ui(self):
        self.model.setStringList(self.action_data.mode_list)

    def save_changes(self):
        """Saves UI state to the profile."""
        mode_list = self.model.stringList()
        self.action_data.mode_list = mode_list
        self.action_modified.emit()

    def _add_cb(self):
        """Adds the currently selected mode to the list of modes."""
        mode_list = self.model.stringList()
        mode_list.append(self.mode_list.currentText())
        self.model.setStringList(mode_list)
        self.save_changes()

    def _up_cb(self):
        """Moves the currently selected mode upwards."""
        mode_list = self.model.stringList()
        index = self.view.currentIndex().row()
        new_index = index - 1
        if new_index >= 0:
            mode_list[index], mode_list[new_index] =\
                mode_list[new_index], mode_list[index]
            self.model.setStringList(mode_list)
            self.view.setCurrentIndex(self.model.index(new_index, 0))
            self.save_changes()

    def _down_cb(self):
        """Moves the currently selected mode downwards."""
        mode_list = self.model.stringList()
        index = self.view.currentIndex().row()
        new_index = index + 1
        if new_index < len(mode_list):
            mode_list[index], mode_list[new_index] =\
                mode_list[new_index], mode_list[index]
            self.model.setStringList(mode_list)
            self.view.setCurrentIndex(self.model.index(new_index, 0))
            self.save_changes()

    def _remove_cb(self):
        """Removes the currently selected mode from the list of modes."""
        mode_list = self.model.stringList()
        index = self.view.currentIndex().row()
        if 0 <= index < len(mode_list):
            del mode_list[index]
            self.model.setStringList(mode_list)
            self.view.setCurrentIndex(self.model.index(0, 0))
            self.save_changes()


class CycleModesFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)
        self.mode_list = gremlin.control_action.ModeList(action.mode_list)

    def process_event(self, event, value):
        gremlin.control_action.cycle_modes(self.mode_list)
        return True


class CycleModes(AbstractAction):

    """Action allowing the switching through a list of modes."""

    name = "Cycle Modes"
    tag = "cycle-modes"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = CycleModesFunctor
    widget = CycleModesWidget

    def __init__(self, parent):
        super().__init__(parent)
        self.mode_list = []

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        for child in node:
            self.mode_list.append(child.get("name"))

    def _is_valid(self):
        return len(self.mode_list) > 0

    def _generate_xml(self):
        node = ElementTree.Element("cycle-modes")
        for mode_name in self.mode_list:
            child = ElementTree.Element("mode")
            child.set("name", mode_name)
            node.append(child)
        return node


version = 1
name = "cycle-modes"
create = CycleModes
