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
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
import gremlin.macro
from gremlin.ui.common import NoKeyboardPushButton
import gremlin.ui.input_item


class MacroActionEditor(QtWidgets.QWidget):

    """Widget displaying macro action settings and permitting their change."""

    def __init__(self, model, index, parent=None):
        """Creates a new editor widget.

        :param model the model storing the content
        :param index the index of the model entry being edited
        :param parent the parent of this widget
        """
        super().__init__(parent)
        self.model = model
        self.index = index

        self.action_types = {
            "Joystick": self._joystick_ui,
            "Keyboard": self._keyboard_ui,
            "Pause": self._pause_ui,
            # The following two devices are yet to be implemented
            # "Mouse": self._mouse_ui,
        }

        self.setMinimumWidth(200)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.group_box = QtWidgets.QGroupBox("Action Settings")
        self.group_layout = QtWidgets.QVBoxLayout(self.group_box)
        self.main_layout.addWidget(self.group_box)
        self.ui_elements = {}
        self._create_ui()
        self._populate_ui()

    def _create_ui(self):
        """Creates the editor UI."""
        self.action_selector = QtWidgets.QComboBox()
        for action_name in sorted(self.action_types):
            self.action_selector.addItem(action_name)
        self.action_selector.currentTextChanged.connect(self._change_action)

        self.group_layout.addWidget(self.action_selector)

        self.action_layout = QtWidgets.QVBoxLayout()
        self.group_layout.addLayout(self.action_layout)
        self.group_layout.addStretch(1)

    def _populate_ui(self):
        """Populate the UI elements with data from the model."""
        self.action_selector.currentTextChanged.disconnect(self._change_action)

        entry = self.model.get_entry(self.index.row())
        if isinstance(entry, gremlin.macro.KeyAction):
            self.action_selector.setCurrentText("Keyboard")
            self._keyboard_ui()
        elif isinstance(entry, gremlin.macro.JoystickAction):
            self.action_selector.setCurrentText("Joystick")
            self._joystick_ui()
        elif isinstance(entry, gremlin.macro.PauseAction):
            self.action_selector.setCurrentText("Pause")
            self._pause_ui()

        self.action_selector.currentTextChanged.connect(self._change_action)

    def _change_action(self, value):
        """Handle changing the action type.

        :param value the name of the new action type for the currently selected
            entry
        """
        # Clear the current editor widget ui components
        gremlin.ui.common.clear_layout(self.action_layout)
        self.ui_elements = {}

        # Update the model data to match the new type
        if value == "Keyboard":
            self.model.set_entry(
                gremlin.macro.KeyAction(
                    gremlin.macro.key_from_name("enter"),
                    True
                ),
                self.index.row()
            )
        elif value == "Joystick":
            self.model.set_entry(
                gremlin.macro.JoystickAction(
                    0,
                    gremlin.common.InputType.JoystickButton,
                    1,
                    True
                ),
                self.index.row()
            )
        elif value == "Pause":
            self.model.set_entry(
                gremlin.macro.PauseAction(0.2),
                self.index.row()
            )

        # Update the UI elements
        self._update_model()
        self.action_types[value]()

    def _pause_ui(self):
        """Creates and populates the PauseAction editor UI."""
        self.ui_elements["duration_label"] = QtWidgets.QLabel("Duration")
        self.ui_elements["duration_spinbox"] = \
            gremlin.ui.common.DynamicDoubleSpinBox()
        self.ui_elements["duration_spinbox"].setSingleStep(0.1)
        self.ui_elements["duration_spinbox"].setMaximum(3600)
        duration = 0.5
        if self.model.get_entry(self.index.row()) is not None:
            duration = self.model.get_entry(self.index.row()).duration
        self.ui_elements["duration_spinbox"].setValue(duration)
        self.ui_elements["duration_spinbox"].valueChanged.connect(
            self._update_pause
        )

        self.action_layout.addWidget(self.ui_elements["duration_label"])
        self.action_layout.addWidget(self.ui_elements["duration_spinbox"])

    def _keyboard_ui(self):
        """Creates and populates the KeyAction editor UI."""
        action = self.model.get_entry(self.index.row())
        if action is None:
            return
        self.ui_elements["key_label"] = QtWidgets.QLabel("Key")
        self.ui_elements["key_input"] = \
            gremlin.ui.common.NoKeyboardPushButton(action.key.name)
        self.ui_elements["key_input"].clicked.connect(
            lambda: self._request_user_input([gremlin.common.InputType.Keyboard])
        )
        self.ui_elements["key_press"] = QtWidgets.QRadioButton("Press")
        self.ui_elements["key_release"] = QtWidgets.QRadioButton("Release")
        if action.is_pressed:
            self.ui_elements["key_press"].setChecked(True)
        else:
            self.ui_elements["key_release"].setChecked(True)

        self.ui_elements["key_press"].toggled.connect(self._modify_key_state)
        self.ui_elements["key_release"].toggled.connect(self._modify_key_state)

        self.action_layout.addWidget(self.ui_elements["key_label"])
        self.action_layout.addWidget(self.ui_elements["key_input"])
        self.action_layout.addWidget(self.ui_elements["key_press"])
        self.action_layout.addWidget(self.ui_elements["key_release"])

    def _mouse_ui(self):
        """Creates and populates the MouseAction editor UI."""
        pass

    def _joystick_ui(self):
        """Creates and populates the JoystickAction editor UI."""
        action = self.model.get_entry(self.index.row())
        if action is None:
            return

        self.ui_elements["input_label"] = QtWidgets.QLabel("Input")
        self.ui_elements["input_button"] = \
            gremlin.ui.common.NoKeyboardPushButton("Press Me")
        self.ui_elements["input_button"].clicked.connect(
            lambda: self._request_user_input([
                gremlin.common.InputType.JoystickAxis,
                gremlin.common.InputType.JoystickButton,
                gremlin.common.InputType.JoystickHat
            ])
        )

        # Handle display of value based on the actual input type
        if action.input_type == gremlin.common.InputType.JoystickAxis:
            self.ui_elements["axis_value"] = \
                gremlin.ui.common.DynamicDoubleSpinBox()
            self.ui_elements["axis_value"].setRange(-1.0, 1.0)
            self.ui_elements["axis_value"].setSingleStep(0.1)
            self.ui_elements["axis_value"].setValue(action.value)
            self.ui_elements["axis_value"].valueChanged.connect(
                self._modify_axis_state
            )
            self.action_layout.addWidget(self.ui_elements["axis_value"])

        elif action.input_type == gremlin.common.InputType.JoystickButton:
            self.ui_elements["button_press"] = QtWidgets.QRadioButton("Press")
            self.ui_elements["button_release"] = QtWidgets.QRadioButton("Release")
            if action.value:
                self.ui_elements["button_press"].setChecked(True)
            else:
                self.ui_elements["button_release"].setChecked(True)

            self.ui_elements["button_press"].toggled.connect(
                self._modify_button_state
            )
            self.ui_elements["button_release"].toggled.connect(
                self._modify_button_state
            )
            self.action_layout.addWidget(self.ui_elements["button_press"])
            self.action_layout.addWidget(self.ui_elements["button_release"])
        elif action.input_type == gremlin.common.InputType.JoystickHat:
            self.ui_elements["hat_direction"] = QtWidgets.QComboBox()
            directions = [
                "Center", "North", "North East", "East", "South East",
                "South", "South West", "West", "North West"
            ]
            for val in directions:
                self.ui_elements["hat_direction"].addItem(val)
            self.ui_elements["hat_direction"].currentTextChanged.connect(
                self._modify_hat_state
            )
            self.ui_elements["hat_direction"].setCurrentText(
                gremlin.common.direction_tuple_lookup[action.value]
            )
            self.action_layout.addWidget(self.ui_elements["hat_direction"])

        self.action_layout.addWidget(self.ui_elements["input_label"])
        self.action_layout.addWidget(self.ui_elements["input_button"])

    def _modify_key_state(self, state):
        """Updates the key activation state, i.e. press or release of a key.

        :param state the radio button state
        """
        action = self.model.get_entry(self.index.row())
        action.is_pressed = self.ui_elements["key_press"].isChecked()
        self._update_model()

    def _modify_button_state(self, state):
        action = self.model.get_entry(self.index.row())
        action.value = self.ui_elements["button_press"].isChecked()
        self._update_model()

    def _modify_axis_state(self, state):
        action = self.model.get_entry(self.index.row())
        action.value = self.ui_elements["axis_value"].value()
        self._update_model()

    def _modify_hat_state(self, state):
        action = self.model.get_entry(self.index.row())
        action.value = gremlin.common.direction_tuple_lookup[state]
        self._update_model()

    def _update_pause(self, value):
        """Update the model data when editor changes occur.

        :param value the pause duration in seconds
        """
        self.model.get_entry(self.index.row()).duration = value
        self._update_model()

    def _update_model(self):
        """Forces an update of the model at the current intex."""
        self.model.update(self.index)

    def _request_user_input(self, input_types):
        """Prompts the user for the input to bind to this item."""
        if gremlin.common.InputType.Keyboard in input_types:
            callback = self._modify_key
        else:
            callback = self._modify_joystick

        self.button_press_dialog = gremlin.ui.common.InputListenerWidget(
            callback,
            input_types,
            return_kb_event=True
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

    def _modify_key(self, event):
        """Changes which key is mapped.

        :param event the event containing information about the key to use
        """
        self.model.get_entry(self.index.row()).key = \
            gremlin.macro.key_from_code(*event.identifier)
        self._update_model()
        gremlin.ui.common.clear_layout(self.action_layout)
        self.ui_elements = {}
        self._keyboard_ui()

    def _modify_joystick(self, event):
        self.model.set_entry(
            gremlin.macro.JoystickAction(
                event.windows_id,
                event.event_type,
                event.identifier,
                event.value
            ),
            self.index.row()
        )
        self._update_model()
        gremlin.ui.common.clear_layout(self.action_layout)
        self.ui_elements = {}
        self._joystick_ui()


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

    value_format = {
        gremlin.common.InputType.JoystickAxis:
            lambda entry: "{:.3f}".format(entry.value),
        gremlin.common.InputType.JoystickButton:
            lambda entry: "pressed" if entry.value else "released",
        gremlin.common.InputType.JoystickHat:
            lambda entry: gremlin.common.direction_tuple_lookup[entry.value]
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
            elif isinstance(entry, gremlin.macro.JoystickAction):
                cur_joystick = None
                for joy in gremlin.joystick_handling.joystick_devices():
                    if joy.windows_id == entry.device_id:
                        cur_joystick = joy

                return "{} {} {} - {}".format(
                    cur_joystick.name,
                    gremlin.common.input_type_to_name[entry.input_type],
                    entry.input_id,
                    MacroListModel.value_format[entry.input_type](entry)
                )
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
        if not 0 <= index < len(self._data):
            logging.getLogger("system").error(
                "Attempted to set an entry with index greater "
                "then number of elements"
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
        """Emits a signal indicating the given index was updated.

        :param index the index which has been updated
        """
        self.dataChanged.emit(index, index)


class MacroListView(QtWidgets.QListView):

    """Implements a specialized list view.

    The purpose of this class is to properly emit a "clicked" event when
    the selected index is changed via keyboard interaction. In addition to
    this the view also handles item deletion via the keyboard.

    The reason this is needed is that for some reason the correct way,
    i.e. using the QItemSelectionModel signals is not working.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, evt):
        """Process key events.

        :param evt the keyboard event
        """
        # Check if the active index changed, and if so emit the clicked signal
        old_index = self.currentIndex()
        super().keyPressEvent(evt)
        new_index = self.currentIndex()
        if old_index.row() != new_index.row():
            self.clicked.emit(new_index)

        # Handle deleting entries via the keyboard
        if evt.matches(QtGui.QKeySequence.Delete):
            self.model().remove_entry(new_index.row())
            if new_index.row() >= self.model().rowCount():
                new_index = self.model().index(
                    self.model().rowCount()-1,
                    0,
                    QtCore.QModelIndex()
                )
            self.setCurrentIndex(new_index)
            self.clicked.emit(new_index)


class AbstractRepeatMacroWidget(QtWidgets.QWidget):

    """Abstract base class for all repeat UI widgets."""

    def __init__(self, data, parent=None):
        """Creates a new instance.

        :param data the data shown and managed by the widget
        :param parent the parent of this widget
        """
        super().__init__(parent)
        self.data = data
        self.main_layout = QtWidgets.QGridLayout(self)

        self._create_ui()
        self._populate_ui()

    def _create_ui(self):
        """Creates the UI components."""
        raise gremlin.error.MissingImplementationError(
            "AbstractRepeatMacroWidget::_create_ui not implemented in subclass"
        )

    def _populate_ui(self):
        """Populates the UI components."""
        raise gremlin.error.MissingImplementationError(
            "AbstractRepeatMacroWidget::_populate_ui not "
            "implemented in subclass"
        )

    def _update_data(self):
        """Updates the managed data based on the UI contents."""
        raise gremlin.error.MissingImplementationError(
            "AbstractRepeatMacroWidget::_populate_ui not "
            "implemented in subclass"
        )


class CountRepeatMacroWidget(AbstractRepeatMacroWidget):

    """Repeat UI to specify a number of times to repeat a macro."""

    def __init__(self, data, parent=None):
        super().__init__(data, parent)

    def _create_ui(self):
        self.delay = gremlin.ui.common.DynamicDoubleSpinBox()
        self.delay.setMaximum(3600)
        self.delay.setSingleStep(0.1)
        self.delay.setValue(0.1)

        self.count = QtWidgets.QSpinBox()
        self.count.setMaximum(1e9)
        self.count.setSingleStep(1)
        self.count.setValue(1)

        self.main_layout.addWidget(QtWidgets.QLabel("Delay"), 0, 0)
        self.main_layout.addWidget(self.delay, 0, 1)
        self.main_layout.addWidget(QtWidgets.QLabel("Count"), 1, 0)
        self.main_layout.addWidget(self.count, 1, 1)

    def _populate_ui(self):
        self.delay.setValue(self.data.delay)
        self.count.setValue(self.data.count)

        self.delay.valueChanged.connect(self._update_data)
        self.count.valueChanged.connect(self._update_data)

    def _update_data(self):
        self.data.delay = self.delay.value()
        self.data.count = self.count.value()


class ToggleRepeatMacroWidget(AbstractRepeatMacroWidget):

    """Repeat UI for a toggle repetition."""

    def __init__(self, data, parent=None):
        super().__init__(data, parent)

    def _create_ui(self):
        self.delay = gremlin.ui.common.DynamicDoubleSpinBox()
        self.delay.setMaximum(3600)
        self.delay.setSingleStep(0.1)
        self.delay.setValue(0.1)

        self.main_layout.addWidget(QtWidgets.QLabel("Delay"), 0, 0)
        self.main_layout.addWidget(self.delay, 0, 1)

    def _populate_ui(self):
        self.delay.setValue(self.data.delay)
        self.delay.valueChanged.connect(self._update_data)

    def _update_data(self):
        self.data.delay = self.delay.value()


class HoldRepeatMacroWidget(AbstractRepeatMacroWidget):

    """Repeat UI for a hold repetition."""

    def __init__(self, data, parent=None):
        super().__init__(data, parent)

    def _create_ui(self):
        self.delay = gremlin.ui.common.DynamicDoubleSpinBox()
        self.delay.setMaximum(3600)
        self.delay.setSingleStep(0.1)
        self.delay.setValue(0.1)

        self.main_layout.addWidget(QtWidgets.QLabel("Delay"), 0, 0)
        self.main_layout.addWidget(self.delay, 0, 1)

    def _populate_ui(self):
        self.delay.setValue(self.data.delay)
        self.delay.valueChanged.connect(self._update_data)

    def _update_data(self):
        self.data.delay = self.delay.value()


class MacroSettingsWidget(QtWidgets.QWidget):

    """Widget presenting macro settings."""

    # Lookup tables mapping between display name and enum name
    name_to_widget = {
        "Count": CountRepeatMacroWidget,
        "Toggle": ToggleRepeatMacroWidget,
        "Hold": HoldRepeatMacroWidget
    }
    name_to_storage = {
        "Count": gremlin.macro.CountRepeat,
        "Toggle": gremlin.macro.ToggleRepeat,
        "Hold": gremlin.macro.HoldRepeat
    }
    storage_to_name = {
        gremlin.macro.CountRepeat: "Count",
        gremlin.macro.ToggleRepeat: "Toggle",
        gremlin.macro.HoldRepeat: "Hold"
    }

    def __init__(self, action_data, parent=None):
        """Creates a new UI widget instance.

        :param action_data the data presented by the UI
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.action_data = action_data
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.group_box = QtWidgets.QGroupBox("Macro Settings")
        self.group_layout = QtWidgets.QVBoxLayout()
        self.group_box.setLayout(self.group_layout)
        self.main_layout.addWidget(self.group_box)

        self._create_ui()

    def _create_ui(self):
        """Creates the UI elements"""
        # Create UI elements
        self.exclusive_checkbox = QtWidgets.QCheckBox("Exclusive")
        self.repeat_dropdown = QtWidgets.QComboBox()
        self.repeat_dropdown.addItems(["None", "Count", "Toggle", "Hold"])
        self.repeat_widget = None
        if type(self.action_data.repeat) in MacroSettingsWidget.storage_to_name:
            mode_name = MacroSettingsWidget.storage_to_name[
                type(self.action_data.repeat)
            ]
            self.repeat_widget = MacroSettingsWidget.name_to_widget[mode_name](
                self.action_data.repeat
            )

        # Populate UI elements
        self.exclusive_checkbox.setChecked(self.action_data.exclusive)
        if self.action_data.repeat is not None:
            mode_name = MacroSettingsWidget.storage_to_name[
                type(self.action_data.repeat)
            ]
            self.repeat_widget = MacroSettingsWidget.name_to_widget[mode_name](
                self.action_data.repeat
            )
            self.repeat_dropdown.setCurrentText(mode_name)

        # Connect signals
        self.exclusive_checkbox.clicked.connect(self._update_settings)
        self.repeat_dropdown.currentTextChanged.connect(self._update_settings)

        # Place UI elements
        self.group_layout.addWidget(self.exclusive_checkbox)
        self.group_layout.addWidget(self.repeat_dropdown)
        if self.repeat_widget is not None:
            self.group_layout.addWidget(self.repeat_widget)

    def _update_settings(self, value):
        """Updates the action data based on UI content.

        :param value the value of a change (ignored)
        """
        self.action_data.exclusive = self.exclusive_checkbox.isChecked()

        # Only create a new repeat widget if it changed
        widget_type = MacroSettingsWidget.name_to_widget.get(
            self.repeat_dropdown.currentText(),
            None
        )
        storage_type = MacroSettingsWidget.name_to_storage.get(
            self.repeat_dropdown.currentText(),
            None
        )
        if widget_type is None and self.repeat_widget is not None:
            self.action_data.repeat = None
            self.repeat_widget = None

            old_item = self.group_layout.takeAt(2)
            if old_item is not None:
                old_item.widget().hide()
                old_item.widget().deleteLater()
        elif widget_type is not None and \
                not isinstance(self.repeat_widget, widget_type):
            self.action_data.repeat = storage_type()
            self.repeat_widget = widget_type(self.action_data.repeat)

            old_item = self.group_layout.takeAt(2)
            if old_item is not None:
                old_item.widget().hide()
                old_item.widget().deleteLater()
            self.group_layout.addWidget(self.repeat_widget)


class MacroWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget which allows creating and editing of macros."""

    # Path to graphics
    gfx_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "gfx"
    )

    def __init__(self, action_data, parent=None):
        """Creates a new UI widget.

        :param action_data the data of the macro action
        :param parent the parent of the widget
        """
        super().__init__(action_data, parent)
        assert(isinstance(action_data, Macro))

        self._recording_times = {}

    def _create_ui(self):
        """Creates the UI of this widget."""
        self.model = MacroListModel(self.action_data.sequence)

        # Replace the default vertical with a horizontal layout
        QtWidgets.QWidget().setLayout(self.layout())
        self.main_layout = QtWidgets.QHBoxLayout(self)

        self.editor_settings_layout = QtWidgets.QVBoxLayout()
        self.buttons_layout = QtWidgets.QVBoxLayout()

        # Create list view for macro actions and setup drag & drop support
        self.list_view = MacroListView()
        self.list_view.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.list_view.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.list_view.setModel(self.model)
        self.list_view.setCurrentIndex(self.model.index(0, 0))
        self.list_view.clicked.connect(self._edit_action)

        # Create editor as well as settings place holder widgets
        self.editor_widget = QtWidgets.QWidget()
        self.settings_widget = MacroSettingsWidget(self.action_data)
        self.editor_settings_layout.addWidget(self.editor_widget)
        self.editor_settings_layout.addWidget(self.settings_widget)
        self.editor_settings_layout.addStretch()

        # Create buttons used to modify and interact with the macro actions
        self.button_new_entry = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_add"), ""
        )
        self.button_new_entry.setToolTip("Add a new action")
        self.button_new_entry.clicked.connect(self._pause_cb)
        self.button_delete = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_delete"), ""
        )
        self.button_delete.clicked.connect(self._delete_cb)
        self.button_delete.setToolTip("Delete currently selected entry")

        record_icon = QtGui.QIcon()
        record_icon.addPixmap(
            QtGui.QPixmap("{}/macro_record".format(MacroWidget.gfx_path)),
            QtGui.QIcon.Normal
        )
        record_icon.addPixmap(
            QtGui.QPixmap("{}/macro_record_on".format(MacroWidget.gfx_path)),
            QtGui.QIcon.Active,
            QtGui.QIcon.On
        )

        self.button_record = NoKeyboardPushButton(record_icon, "")
        self.button_record.setCheckable(True)
        self.button_record.clicked.connect(self._record_cb)
        self.button_record.setToolTip("Start / stop recording keyboard input")
        self.button_pause = QtWidgets.QPushButton(
            QtGui.QIcon("{}/macro_add_pause".format(MacroWidget.gfx_path)), ""
        )
        self.button_pause.clicked.connect(self._pause_cb)
        self.button_pause.setToolTip(
            "Add pause after the currently selected entry"
        )

        time_icon = QtGui.QIcon()
        time_icon.addPixmap(
            QtGui.QPixmap("{}/time".format(MacroWidget.gfx_path)),
            QtGui.QIcon.Normal
        )
        time_icon.addPixmap(
            QtGui.QPixmap("{}/time_on".format(MacroWidget.gfx_path)),
            QtGui.QIcon.Active,
            QtGui.QIcon.On
        )
        self.button_time = NoKeyboardPushButton(time_icon, "")
        self.button_time.setCheckable(True)
        self.button_time.setToolTip("Add pause between actions")

        self.buttons_layout.addWidget(self.button_new_entry)
        self.buttons_layout.addWidget(self.button_delete)
        self.buttons_layout.addWidget(self.button_pause)
        self.buttons_layout.addWidget(self.button_record)
        self.buttons_layout.addWidget(self.button_time)
        self.buttons_layout.addStretch()

        # Assemble the entire widget
        self.main_layout.addWidget(self.list_view)
        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addLayout(self.editor_settings_layout)

        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def _populate_ui(self):
        """Populate the UI with content from the data."""
        self.model = MacroListModel(self.action_data.sequence)
        self.list_view.setModel(self.model)
        self.list_view.setCurrentIndex(self.model.index(0, 0))
        self._edit_action(self.model.index(0, 0))

    def _edit_action(self, model_index):
        """Enable editing of the current action via a editor widget.

        :param model_index the index of the model entry to edit
        """
        self.editor_widget = MacroActionEditor(self.model, model_index)
        old_item = self.editor_settings_layout.takeAt(0)
        old_item.widget().hide()
        old_item.widget().deleteLater()
        self.editor_settings_layout.insertWidget(0, self.editor_widget)

    def _refresh_editor_ui(self):
        """Forcibly refresh the editor widget content."""
        self.list_view.clicked.emit(self.list_view.currentIndex())

    def _create_key_action(self, event):
        """Creates a new macro.KeyAction instance from the given event.

        :param event the event for which to create a KeyAction object
        """
        if self.button_time.isChecked():
            self._append_entry(gremlin.macro.PauseAction(
                time.time() - max(self._recording_times.values())
            ))
        action = gremlin.macro.KeyAction(
            gremlin.macro.key_from_code(
                event.identifier[0],
                event.identifier[1]
            ),
            event.is_pressed
        )
        self._recording_times["keyboard"] = time.time()
        self._append_entry(action)

    def _create_joystick_action(self, event):
        # If this is an axis motion do some checks such that we don't spam
        # the ui with entries
        add_new_entry = True
        if event.event_type == gremlin.common.InputType.JoystickAxis:
            cur_index = self.list_view.currentIndex().row()
            entry = self.model.get_entry(cur_index)

            if event not in self._recording_times:
                self._recording_times[event] = time.time()
            elif time.time() - self._recording_times[event] < 0.1:
                add_new_entry = False

        if add_new_entry:
            if self.button_time.isChecked():
                self._append_entry(gremlin.macro.PauseAction(
                    time.time() - max(self._recording_times.values())
                ))
            action = gremlin.macro.JoystickAction(
                event.windows_id,
                event.event_type,
                event.identifier,
                event.value
            )
            self._recording_times[event] = time.time()
            self._append_entry(action)

    def _record_cb(self):
        """Starts the recording of key presses."""
        if self.button_record.isChecked():
            # Record keystrokes
            self._recording = True
            el = gremlin.event_handler.EventListener()
            el.keyboard_event.connect(self._create_key_action)
            el.joystick_event.connect(self._create_joystick_action)
        else:
            # Stop recording keystrokes
            self._recording = False
            el = gremlin.event_handler.EventListener()
            el.keyboard_event.disconnect(self._create_key_action)

    def _pause_cb(self):
        """Adds a pause macro action to the list."""
        self._append_entry(gremlin.macro.PauseAction(0.01))
        self._refresh_editor_ui()

    def _delete_cb(self):
        """Callback executed when the delete button is pressed."""
        idx = self.list_view.currentIndex().row()
        if 0 <= idx < len(self.action_data.sequence):
            del self.action_data.sequence[idx]
            new_idx = min(len(self.action_data.sequence), max(0, idx - 1))
            self.list_view.setCurrentIndex(
                self.model.index(new_idx, 0, QtCore.QModelIndex())
            )
            self._refresh_editor_ui()

    def _append_entry(self, entry):
        """Adds the given entry after current selection.

        :param entry the entry to add to the model
        """
        cur_index = self.list_view.currentIndex().row()
        self.model.add_entry(cur_index, entry)
        self.list_view.setCurrentIndex(self.model.index(cur_index+1, 0))
        self._refresh_editor_ui()


class MacroFunctor(AbstractFunctor):

    manager = gremlin.macro.MacroManager()

    def __init__(self, action):
        super().__init__(action)
        self.macro = gremlin.macro.Macro()
        for seq in action.sequence:
            if isinstance(seq, gremlin.macro.PauseAction):
                self.macro.pause(seq.duration)
            elif isinstance(seq, gremlin.macro.KeyAction):
                self.macro.action(
                    gremlin.macro.key_from_code(
                        seq.key._scan_code,
                        seq.key._is_extended
                    ),
                    seq.is_pressed
                )
            else:
                raise gremlin.error.GremlinError("Invalid macro action")
        self.macro.exclusive = action.exclusive
        self.macro.repeat = action.repeat

    def process_event(self, event, value):
        MacroFunctor.manager.queue_macro(self.macro)
        if isinstance(self.macro.repeat, gremlin.macro.HoldRepeat):
            gremlin.input_devices.ButtonReleaseActions().register_callback(
                lambda: MacroFunctor.manager.terminate_macro(self.macro),
                event
            )
        return True


class Macro(AbstractAction):

    """Represents a macro action."""

    name = "Macro"
    tag = "macro"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = MacroFunctor
    widget = MacroWidget

    def __init__(self, parent):
        """Creates a new Macro instance.

        :param parent the parent profile.ItemAction of this macro action
        """
        super().__init__(parent)
        self.sequence = []
        self.exclusive = False
        self.repeat = None

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        return self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

    def _parse_xml(self, node):
        """Parses the XML node corresponding to a macro action.

        :param node the XML node to parse.
        """
        # Reset storage
        self.sequence = []
        self.exclusive = False
        self.repeat = None

        # Read properties
        for child in node.find("properties"):
            if child.tag == "exclusive":
                self.exclusive = True
            elif child.tag == "repeat":
                repeat_type = child.get("type")
                if repeat_type == "count":
                    self.repeat = gremlin.macro.CountRepeat()
                elif repeat_type == "toggle":
                    self.repeat = gremlin.macro.ToggleRepeat()
                elif repeat_type == "hold":
                    self.repeat = gremlin.macro.HoldRepeat()
                else:
                    logging.getLogger("system").warning(
                        "Invalid macro repeat type: {}".format(repeat_type)
                    )

                if self.repeat:
                    self.repeat.from_xml(child)

        # Read macro actions
        for child in node.find("actions"):
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
        properties = ElementTree.Element("properties")
        if self.exclusive:
            prop_node = ElementTree.Element("exclusive")
            properties.append(prop_node)
        if self.repeat:
            properties.append(self.repeat.to_xml())
        node.append(properties)

        action_list = ElementTree.Element("actions")
        for entry in self.sequence:
            if isinstance(entry, gremlin.macro.KeyAction):
                action_node = ElementTree.Element("key")
                action_node.set("scan_code", str(entry.key.scan_code))
                action_node.set("extended", str(entry.key.is_extended))
                action_node.set("press", str(entry.is_pressed))
                action_list.append(action_node)
            elif isinstance(entry, gremlin.macro.PauseAction):
                pause_node = ElementTree.Element("pause")
                pause_node.set("duration", str(entry.duration))
                action_list.append(pause_node)
        node.append(action_list)
        return node

    def _is_valid(self):
        return len(self.sequence) > 0


version = 1
name = "macro"
create = Macro
