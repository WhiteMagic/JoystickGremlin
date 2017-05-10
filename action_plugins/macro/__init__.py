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


import logging
import os
import pickle
import threading
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction
from gremlin.common import InputType
import gremlin.macro
from gremlin.ui.common import NoKeyboardPushButton
import gremlin.ui.input_item


class MacroActionEditor(QtWidgets.QWidget):

    def __init__(self, model, index, parent=None):
        super().__init__(parent)
        self.model = model
        self.index = index

        self.action_types = {
            "Keyboard": self._keyboard_ui,
            "Pause": self._pause_ui,
            "Mouse": self._mouse_ui,
            "Joystick": self._joystick_ui
        }

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.ui_elements = {}
        self._create_ui()
        self._populate_ui()
        # self.main_layout.addWidget(QtWidgets.QLabel(str(self.index.row())))

    def _create_ui(self):
        self.action_selector = QtWidgets.QComboBox()
        for name in sorted(self.action_types):
            self.action_selector.addItem(name)
        self.action_selector.currentTextChanged.connect(self._change_action)

        self.main_layout.addWidget(self.action_selector)

        self.action_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(self.action_layout)
        self.main_layout.addStretch(1)

    def _populate_ui(self):
        entry = self.model.get_entry(self.index.row())
        self.action_selector.currentTextChanged.disconnect(self._change_action)
        if isinstance(entry, gremlin.macro.PauseAction):
            self.action_selector.setCurrentText("Pause")
            self._pause_ui()
        if isinstance(entry, gremlin.macro.KeyAction):
            self.action_selector.setCurrentText("Keyboard")
            self._keyboard_ui()

        self.action_selector.currentTextChanged.connect(self._change_action)

    def _change_action(self, value):
        gremlin.ui.common.clear_layout(self.action_layout)
        self.ui_elements = {}

        # Update the object stored in the model to match the new type
        if value == "Pause":
            self.model.set_entry(
                gremlin.macro.PauseAction(0.2),
                self.index.row()
            )

        self._update_model()

        # Display the editor widget for the particular action
        self.action_types[value]()

    def _pause_ui(self):
        self.ui_elements["duration_label"] = QtWidgets.QLabel("Duration")
        self.ui_elements["duration_spinbox"] = QtWidgets.QDoubleSpinBox()
        self.ui_elements["duration_spinbox"].setSingleStep(0.1)
        self.ui_elements["duration_spinbox"].setMaximum(3600)
        self.ui_elements["duration_spinbox"].setValue(
            self.model.get_entry(self.index.row()).duration
        )
        self.ui_elements["duration_spinbox"].valueChanged.connect(
            self._update_pause
        )

        self.action_layout.addWidget(self.ui_elements["duration_label"])
        self.action_layout.addWidget(self.ui_elements["duration_spinbox"])

    def _keyboard_ui(self):
        action = self.model.get_entry(self.index.row())
        self.ui_elements["key_label"] = QtWidgets.QLabel("Key")
        self.ui_elements["key_input"] = QtWidgets.QPushButton(action.key.name)
        self.ui_elements["key_press"] = QtWidgets.QRadioButton("Press")
        self.ui_elements["key_release"] = QtWidgets.QRadioButton("Release")
        if action.is_pressed:
            self.ui_elements["key_press"].setChecked(True)
        else:
            self.ui_elements["key_release"].setChecked(True)

        self.ui_elements["key_press"].toggled.connect(self._update_keyboard)
        self.ui_elements["key_release"].toggled.connect(self._update_keyboard)

        self.action_layout.addWidget(self.ui_elements["key_label"])
        self.action_layout.addWidget(self.ui_elements["key_input"])
        self.action_layout.addWidget(self.ui_elements["key_press"])
        self.action_layout.addWidget(self.ui_elements["key_release"])

    def _mouse_ui(self):
        pass

    def _joystick_ui(self):
        pass

    def _update_keyboard(self, state):
        action = self.model.get_entry(self.index.row())
        action.is_pressed = self.ui_elements["key_press"].isChecked()
        self._update_model()

    def _update_pause(self, value):
        self.model.get_entry(self.index.row()).duration = value
        self._update_model()

    def _update_model(self):
        self.model.update(self.index)


class MacroListModel(QtCore.QAbstractListModel):

    """Model representing a Macro.

    This model supports model modification.
    """

    gfx_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "gfx"
    )
    icon_lookup = {
        "press": QtGui.QIcon("{}/press".format(gfx_path)),
        "release": QtGui.QIcon("{}/release".format(gfx_path)),
        "pause": QtGui.QIcon("{}/pause".format(gfx_path))
    }

    def __init__(self, data_storage, parent=None):
        """Creates a new instance.

        :param parent parent widget
        """
        QtCore.QAbstractListModel.__init__(self, parent)

        self._data = data_storage

    def rowCount(self, parent=None):
        """Returns the number of rows in the model.

        :param parent the parent of the model
        :return number of rows in the model
        """
        return len(self._data)

    def data(self, index, role):
        """Return the data of the index for the specified role.

        :param index the index into the model which is queried
        :param role the role for which the data is to be formatted
        :return data formatted for the given role at the given index
        """
        idx = index.row()
        if idx >= len(self._data):
            return QtCore.QVariant()

        entry = self._data[idx]
        if role == QtCore.Qt.DisplayRole:
            if isinstance(entry, gremlin.macro.PauseAction):
                return "Pause for {:.4f} s".format(entry.duration)
            elif isinstance(entry, gremlin.macro.KeyAction):
                return "{} key {}".format(
                    "Press" if entry.is_pressed else "Release",
                    entry.key.name
                )
            else:
                raise gremlin.error.GremlinError("Unknown macro action")
        elif role == QtCore.Qt.DecorationRole:
            if isinstance(entry, gremlin.macro.PauseAction):
                return MacroListModel.icon_lookup["pause"]
            elif isinstance(entry, gremlin.macro.KeyAction):
                action = "press" if entry.is_pressed else "release"
                return MacroListModel.icon_lookup[action]
            else:
                return QtCore.QVariant()
        else:
            return QtCore.QVariant()

    def mimeTypes(self):
        """Returns the MIME types supported by this model for drag & drop.

        :return supported MIME types
        """
        return ["data/macro-action"]

    def mimeData(self, index_list):
        """Returns encoded data for the provided indices.

        :param index_list list of indices to encode
        :return encoded content
        """
        assert len(index_list) == 1
        data = QtCore.QMimeData()
        data.setData(
            "data/macro-action",
            pickle.dumps((self._data[index_list[0].row()], index_list[0].row()))
        )
        return data

    def dropMimeData(self, data, action, row, column, parent):
        """Handles the drop event using the provided MIME encoded data.

        :param data MIME encoded data being dropped
        :param action type of drop action being requested
        :param row the row in which to insert the data
        :param column the column in which to insert the data
        :param parent the parent in the model under which the data is inserted
        :return True if data was processed, False otherwise
        """
        if action != QtCore.Qt.MoveAction:
            print("!!! Incorrect action type")
            return False

        if row == -1:
            return False

        action, old_id = pickle.loads(data.data("data/macro-action"))
        self._data.insert(row, action)

        if old_id > row:
            old_id += 1
        del self._data[old_id]
        return True

    def flags(self, index):
        """Returns the flags of an item.

        :param index the index of the item for which to return the flags
        :return flags of an item
        """
        # Allow dragging of valid entries but disallow dropping on them while
        # invalid indices are valid drop locations, i.e. in between existing
        # entries.
        if index.isValid():
            return super().flags(index) | \
                    QtCore.Qt.ItemIsSelectable | \
                    QtCore.Qt.ItemIsDragEnabled | \
                    QtCore.Qt.ItemIsEnabled | \
                    QtCore.Qt.ItemNeverHasChildren
        else:
            return QtCore.Qt.ItemIsSelectable | \
                    QtCore.Qt.ItemIsDragEnabled | \
                    QtCore.Qt.ItemIsDropEnabled | \
                    QtCore.Qt.ItemIsEnabled | \
                    QtCore.Qt.ItemNeverHasChildren

    def supportedDropActions(self):
        """Return the drop actions supported by this model.

        :return Drop actions supported by this model
        """
        return QtCore.Qt.MoveAction

    def get_entry(self, index):
        """Returns the action entry at the given index.

        :param index the index of the entry to return
        :return entry stored at the given index
        """
        if not 0 <= index < len(self._data):
            logging.getLogger("system").error(
                "Attempted to retrieve entry at invalid index"
            )
            return None
        return self._data[index]

    def set_entry(self, entry, index):
        """Sets the entry at the given index to the given value.

        :param entry the new entry object to store
        :param index the index at which to store the entry
        """
        print("X")
        if not 0 <= index < len(self._data):
            logging.getLogger("system").error(
                "Attempted to set an entry with index greater then number of elements"
            )
            return

        self._data[index] = entry

    def remove_entry(self, index):
        """Removes the entry at the provided index.

        If the index is invalid nothing happens.

        :param index the index of the entry to remove
        """
        if 0 <= index < len(self._data):
            self.beginRemoveRows(self.index(0, 0), index, index)
            del self._data[index]
            self.endRemoveRows()

    def add_entry(self, index, entry):
        """Adds the given entry at the provided index.

        :param index the index at which to insert the new entry
        :param entry the entry to insert
        """
        self.beginInsertRows(QtCore.QModelIndex(), index, index)
        self._data.insert(index + 1, entry)
        self.endInsertRows()

    def swap(self, id1, id2):
        """Swaps the entries pointed to by the two indices.

        If either of the indices is invalid nothing happens.

        :param id1 first index
        :param id2 second index
        """
        if -1 < id1 < len(self._data) and -1 < id2 < len(self._data):
            self._data[id1], self._data[id2] = \
                self._data[id2], self._data[id1]
            self.dataChanged.emit(self.index(id1, 0), self.index(id2, 0))

    def update(self, index):
        self.dataChanged.emit(index, index)


class MacroListView(QtWidgets.QListView):

    """Implements a specialized list view.

    The purpose of this class is to properly emit a "clicked" event when
    the selected index is changed via keyboard interaction.

    The reason this is needed is that for some reason the correct way,
    i.e. using the QItemSelectionModel signals is not working.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, evt):
        """Process key events and emit a clicked signal if the selection
        changes."""
        old_index = self.currentIndex()
        super().keyPressEvent(evt)
        new_index = self.currentIndex()
        if old_index.row() != new_index.row():
            self.clicked.emit(new_index)


class MacroWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget which allows creating and editing of macros."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent)
        assert(isinstance(action_data, Macro))

    def _create_ui(self):
        self.model = MacroListModel(self.action_data.sequence)
        # self.model = MacroListModelV2()
        #self._connect_signals()

        self.list_view = MacroListView()
        self.list_view.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.list_view.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectItems
        )
        self.list_view.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.list_view.setMovement(QtWidgets.QListView.Snap)
        self.list_view.setDefaultDropAction(QtCore.Qt.MoveAction)

        self.list_view.setModel(self.model)
        self.list_view.setCurrentIndex(self.model.index(0, 0))

        self.list_view.clicked.connect(self._edit_action)

        self.editor_widget = QtWidgets.QTextEdit("Some text")

        gfx_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "gfx"
        )

        # Buttons
        self.button_layout = QtWidgets.QGridLayout()
        self.button_up = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_up"), "Up"
        )
        self.button_up.clicked.connect(self._up_cb)
        self.button_down = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_down"), "Down"
        )
        self.button_delete = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_delete"), "Delete"
        )
        self.button_delete.clicked.connect(self._delete_cb)
        self.button_down.clicked.connect(self._down_cb)
        record_icon = QtGui.QIcon()
        record_icon.addPixmap(
            QtGui.QPixmap("{}/macro_record".format(gfx_path)),
            QtGui.QIcon.Normal
        )
        record_icon.addPixmap(
            QtGui.QPixmap("{}/macro_record_on".format(gfx_path)),
            QtGui.QIcon.Active,
            QtGui.QIcon.On
        )

        self.button_record = NoKeyboardPushButton(record_icon, "Record")
        self.button_record.setCheckable(True)
        self.button_record.clicked.connect(self._record_cb)
        self.button_pause = QtWidgets.QPushButton(
            QtGui.QIcon("{}/macro_add_pause".format(gfx_path)), "Add Pause"
        )
        self.button_pause.clicked.connect(self._pause_cb)
        self.button_layout.addWidget(self.button_up, 0, 0)
        self.button_layout.addWidget(self.button_down, 0, 1)
        self.button_layout.addWidget(self.button_delete, 0, 2)
        self.button_layout.addWidget(self.button_record, 1, 0)
        self.button_layout.addWidget(self.button_pause, 1, 1)

        self.action_edit_layout = QtWidgets.QHBoxLayout()
        self.action_edit_layout.addWidget(self.list_view)
        self.action_edit_layout.addWidget(self.editor_widget)

        self.main_layout.addLayout(self.action_edit_layout)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def _edit_action(self, model_index):
        self.editor_widget = MacroActionEditor(self.model, model_index)
        old_item = self.action_edit_layout.takeAt(1)
        old_item.widget().hide()
        old_item.widget().deleteLater()
        self.action_edit_layout.addWidget(self.editor_widget)

    def _populate_ui(self):
        # Replace existing model with an empty one which is filled from
        # the profile data.
        # This needs to stay otherwise the code breaks.
        self.model = MacroListModel(self.action_data.sequence)
        # self.model.clear()
        # self.model.populate(self.action_data.sequence)
        self.list_view.setModel(self.model)

    def key_event_cb(self, event):
        action = gremlin.macro.Macro.KeyAction(
            gremlin.macro.key_from_code(
                event.identifier[0],
                event.identifier[1]
            ),
            event.is_pressed
        )
        self._append_entry(action)

    def _up_cb(self):
        """Moves the currently selected entry upwards."""
        idx = self.list_view.currentIndex().row()
        if idx > 0:
            self._swap_entries(idx, idx-1)

    def _down_cb(self):
        """Moves the currently selected entry downwards."""
        idx = self.list_view.currentIndex().row()
        if idx < len(self.model.entries)-1:
            self._swap_entries(idx, idx+1)

    def _record_cb(self):
        """Starts the recording of key presses."""
        if self.button_record.isChecked():
            # Record keystrokes
            self._recording = True
            el = gremlin.event_handler.EventListener()
            el.keyboard_event.connect(self.key_event_cb)
        else:
            # Stop recording keystrokes
            self._recording = False
            el = gremlin.event_handler.EventListener()
            el.keyboard_event.disconnect(self.key_event_cb)

    def _pause_cb(self):
        """Adds a pause macro action to the list."""
        self._append_entry(gremlin.macro.Macro.Pause(0.01))

    def _delete_cb(self):
        """Callback executed when the delete button is pressed."""
        idx = self.list_view.currentIndex().row()
        del self.action_data.sequence[idx]
        new_idx = min(len(self.action_data.sequence), max(0, idx - 1))
        self.model.populate(self.action_data.sequence)
        self.list_view.setCurrentIndex(
            self.model.index(new_idx, 0, QtCore.QModelIndex())
        )

    def _swap_entries(self, id1, id2):
        """Swaps the two model items with the given indices.

        :param id1 the first index
        :param id2 the second index
        """
        self.model.swap(id1, id2)
        self.list_view.setCurrentIndex(self.model.index(id2, 0))

    def _append_entry(self, entry):
        """Adds the given entry after current selection.

        :param entry the entry to add to the model
        """
        cur_index = self.list_view.currentIndex().row()
        self.model.add_entry(
            cur_index,
            entry
        )
        # self.action_data.sequence.insert(cur_index+1, entry)
        # self.model.populate(self.action_data.sequence)
        self.list_view.setCurrentIndex(
            self.model.index(cur_index+1, 0)
        )


class Macro(AbstractAction):

    """Represents a macro action."""

    name = "Macro"
    tag = "macro"
    widget = MacroWidget
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]
    callback_params = []

    def __init__(self, parent):
        """Creates a new Macro instance.

        :param parent the parent profile.ItemAction of this macro action
        """
        super().__init__(parent)
        self.sequence = []

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def _parse_xml(self, node):
        """Parses the XML node corresponding to a macro action.

        :param node the XML node to parse.
        """
        self.sequence = []
        for child in node:
            if child.tag == "key":
                key_action = gremlin.macro.KeyAction(
                    gremlin.macro.key_from_code(
                        int(child.get("scan_code")),
                        gremlin.profile.parse_bool(child.get("extended"))
                    ),
                    gremlin.profile.parse_bool(child.get("press"))
                )
                self.sequence.append(key_action)
            elif child.tag == "pause":
                self.sequence.append(
                    gremlin.macro.PauseAction(float(child.get("duration")))
                )

    def _generate_xml(self):
        """Generates a XML node corresponding to this object.

        :return XML node representing the object's data
        """
        node = ElementTree.Element("macro")
        for entry in self.sequence:
            if isinstance(entry, gremlin.macro.KeyAction):
                action_node = ElementTree.Element("key")
                action_node.set("scan_code", str(entry.key.scan_code))
                action_node.set("extended", str(entry.key.is_extended))
                action_node.set("press", str(entry.is_pressed))
                node.append(action_node)
            elif isinstance(entry, gremlin.macro.PauseAction):
                pause_node = ElementTree.Element("pause")
                pause_node.set("duration", str(entry.duration))
                node.append(pause_node)
        return node

    def _generate_code(self):
        """Generates the python code corresponding to this instance.

        :return python code executing this object's contents.
        """
        return self._code_generation(
            "macro",
            {
                "entry": self
            }
        )

    def _is_valid(self):
        return len(self.sequence) > 0

version = 1
name = "macro"
create = Macro
