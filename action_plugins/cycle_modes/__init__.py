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
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree

from action_plugins.common import AbstractAction, AbstractActionWidget
from gremlin.common import UiInputType
import gremlin.util


class CycleModesWidget(AbstractActionWidget):

    """Widget allowing the configuration of a list of modes to cycle."""

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        AbstractActionWidget.__init__(
            self,
            action_data,
            vjoy_devices,
            change_cb,
            parent
        )
        assert(isinstance(action_data, CycleModes))

    def _setup_ui(self):
        self.model = QtCore.QStringListModel()
        self.view = QtWidgets.QListView()
        self.view.setModel(self.model)
        self.view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Add widgets which allow modifying the mode list
        self.mode_list = QtWidgets.QComboBox()
        for entry in gremlin.util.mode_list(self.action_data):
            self.mode_list.addItem(entry)
        self.add = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/macro_add.svg"), "Add"
        )
        self.add.clicked.connect(self._add_cb)
        self.delete = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/macro_delete.svg"), "Delete"
        )
        self.delete.clicked.connect(self._remove_cb)
        self.up = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/macro_up.svg"), "Up"
        )
        self.up.clicked.connect(self._up_cb)
        self.down = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/macro_down.svg"), "Down"
        )
        self.down.clicked.connect(self._down_cb)

        self.actions_layout = QtWidgets.QHBoxLayout()
        self.actions_layout.addWidget(self.mode_list)
        self.actions_layout.addWidget(self.add)
        self.actions_layout.addWidget(self.delete)
        self.actions_layout.addWidget(self.up)
        self.actions_layout.addWidget(self.down)

        self.main_layout.addWidget(self.view)
        self.main_layout.addLayout(self.actions_layout)

    def to_profile(self):
        mode_list = self.model.stringList()
        self.action_data.mode_list = mode_list
        self.action_data.is_valid = len(mode_list) > 0

    def initialize_from_profile(self, action_data):
        self.action_data = action_data
        self.model.setStringList(self.action_data.mode_list)

    def _add_cb(self):
        """Adds the currently selected mode to the list of modes."""
        mode_list = self.model.stringList()
        mode_list.append(self.mode_list.currentText())
        self.model.setStringList(mode_list)
        self.change_cb()

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
            self.change_cb()

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
            self.change_cb()

    def _remove_cb(self):
        """Removes the currently selected mode from the list of modes."""
        mode_list = self.model.stringList()
        index = self.view.currentIndex().row()
        if 0 <= index < len(mode_list):
            del mode_list[index]
            self.model.setStringList(mode_list)
            self.view.setCurrentIndex(self.model.index(0, 0))
            self.change_cb()


class CycleModes(AbstractAction):

    """Action allowing the switching through a list of modes."""

    icon = "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))
    name = "Cycle Modes"
    tag = "cycle-modes"
    widget = CycleModesWidget
    input_types = [
        UiInputType.JoystickAxis,
        UiInputType.JoystickButton,
        UiInputType.JoystickHat,
        UiInputType.Keyboard
    ]

    def __init__(self, parent):
        AbstractAction.__init__(self, parent)
        self.mode_list = []

    def _parse_xml(self, node):
        for child in node:
            self.mode_list.append(child.get("name"))

    def _generate_xml(self):
        node = ElementTree.Element("cycle-modes")
        for name in self.mode_list:
            child = ElementTree.Element("mode")
            child.set("name", name)
            node.append(child)
        return node

    def _generate_code(self):
        return self._code_generation(
            "cycle_modes",
            {
                "entry": self,
                "mode_list_name":
                    "mode_list_{:04d}".format(CycleModes.next_code_id),
                "gremlin": gremlin
            }
        )

version = 1
name = "cycle-modes"
create = CycleModes
