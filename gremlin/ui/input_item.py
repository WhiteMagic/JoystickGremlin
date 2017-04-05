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

import enum
from PyQt5 import QtWidgets, QtCore, QtGui

import gremlin
from gremlin.common import DeviceType, InputType
from . import common, conditions


class InputIdentifier(object):

    """Represents the identifier of a single input item."""

    def __init__(self, input_type, input_id, device_type):
        """Creates a new instance.

        :param input_type the type of input
        :param input_id the identifier of the input
        :param device_type the type of device this input belongs to
        """
        self._input_type = input_type
        self._input_id = input_id
        self._device_type = device_type

    @property
    def device_type(self):
        return self._device_type

    @property
    def input_type(self):
        return self._input_type

    @property
    def input_id(self):
        return self._input_id


class InputItemListModel(common.AbstractModel):

    def __init__(self, device_data, mode):
        super().__init__()
        self._device_data = device_data
        self._mode = mode

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode
        self.data_changed.emit()

    def rows(self):
        input_items = self._device_data.modes[self._mode]
        return len(input_items.config[InputType.JoystickAxis]) + \
            len(input_items.config[InputType.JoystickButton]) + \
            len(input_items.config[InputType.JoystickHat]) + \
            len(input_items.config[InputType.Keyboard])

    def data(self, index):
        input_items = self._device_data.modes[self._mode]
        axis_count = len(input_items.config[InputType.JoystickAxis])
        button_count = len(input_items.config[InputType.JoystickButton])
        hat_count = len(input_items.config[InputType.JoystickHat])
        key_count = len(input_items.config[InputType.Keyboard])

        if key_count > 0:
            return input_items.config[InputType.Keyboard][index]
        else:
            if index < axis_count:
                return input_items.config[InputType.JoystickAxis][index + 1]
            elif index < axis_count + button_count:
                return input_items.config[InputType.JoystickButton][index - axis_count + 1]
            elif index < axis_count + button_count + hat_count:
                return input_items.config[InputType.JoystickHat][index - axis_count - button_count + 1]


class InputItemListView(common.AbstractView):

    type_to_string = {
        InputType.JoystickAxis: "Axis",
        InputType.JoystickButton: "Button",
        InputType.JoystickHat: "Hat",
        InputType.Keyboard: ""
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create required UI items
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout()

        # Configure the widget holding the layout with all the buttons
        self.scroll_widget.setMaximumWidth(350)
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        # Configure the scroll area
        self.scroll_area.setMinimumWidth(300)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

    def redraw(self):
        common.clear_layout(self.scroll_layout)

        for index in range(self.model.rows()):
            data = self.model.data(index)
            label = str(data.input_id)
            identifier = InputIdentifier(
                data.input_type,
                data.input_id,
                data.parent.parent.type
            )
            widget = InputItemButton(label, identifier)
            widget.create_action_icons(data)
            widget.selected.connect(self._create_selection_callback(index))
            self.scroll_layout.addWidget(widget)
        self.scroll_layout.addStretch()

    def _create_selection_callback(self, index):
        return lambda x: self.select_item(index)

    def select_item(self, index):
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().setAutoFillBackground(False)
            if i == index:
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)
                item.widget().setAutoFillBackground(True)
                item.widget().setPalette(palette)

        self.item_selected.emit(index)


class InputItemButton(QtWidgets.QFrame):

    """Creates a button like widget which emits an event when pressed.

    This event can be used to display input item specific customization
    widgets. This button also shows icons of the associated actions.
    """

    # Signal emitted whenever this button is pressed
    selected = QtCore.pyqtSignal(InputIdentifier)

    def __init__(self, label, identifier, parent=None):
        """Creates a new instance.

        :param label the label / number of the input item
        :param identifier identifying information about the button
        :param parent the parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)
        self.identifier = identifier
        self.label = str(label)
        self._icons = []

        self.setFrameShape(QtWidgets.QFrame.Box)
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(
            QtWidgets.QLabel(self._create_button_label())
        )
        self.main_layout.addStretch(0)
        self.setMinimumSize(100, 40)

    def create_action_icons(self, profile_data):
        """Creates the label of this instance.

        Renders the text representing the instance's name as well as
        icons of actions associated with it.

        :param profile_data the profile.InputItem object associated
            with this instance
        """
        # Clear any potentially existing labels before adding labels
        while self.main_layout.count() > 2:
            item = self.main_layout.takeAt(2)
            item.widget().deleteLater()
            self.main_layout.removeItem(item)

        # Create the actual icons
        # FIXME: this currently ignores the containers themselves
        for entry in profile_data.actions:
            for action in entry.actions:
                if action is not None:
                    self.main_layout.addWidget(ActionLabel(action))

    def mousePressEvent(self, event):
        """Emits the input_item_changed event when this instance is
        clicked on by the mouse.

        :param event the mouse event
        """
        self.selected.emit(self.identifier)

    def _create_button_label(self):
        """Creates the label to display on this button.

        :return label to use for this button
        """
        return "{} {}".format(
            common.input_type_to_name[self.identifier.input_type],
            self.label
        )


class InputItemList(QtWidgets.QWidget):

    """Widget responsible for displaying a list of inputs with their
    currently configured action types.
    """

    # Signal emitted when a button has been selected, contains button
    # identifier as well as the mode
    input_item_selected = QtCore.pyqtSignal(InputIdentifier, str)

    # Button background palettes
    cur_palette = QtGui.QPalette()
    cur_palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)

    def __init__(
            self,
            device,
            device_profile,
            current_mode,
            parent=None
    ):
        """Creates a new instance.

        :param device the physical device the list represents
        :param device_profile the profile used to describe the device
        :param current_mode the currently active mode
        :param parent the parent of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        # Input item button storage
        self.input_items = {
            InputType.JoystickAxis: {},
            InputType.JoystickButton: {},
            InputType.JoystickHat: {},
            InputType.Keyboard: {}
        }

        # Store parameters
        self.device = device
        self.device_profile = device_profile
        if self.device is not None and self.device.is_virtual:
            self.device_profile.type = DeviceType.VJoy
        self.current_mode = current_mode
        self.current_identifier = None

        # Create required UI items
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout()

        # Configure the widget holding the layout with all the buttons
        self.scroll_widget.setMaximumWidth(350)
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        # Configure the scroll area
        self.scroll_area.setMinimumWidth(300)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

        # If this is the keyboard tab add the button needed to add
        # new keys.
        if self.device_profile.type == DeviceType.Keyboard:
            self.key_add_button = common.NoKeyboardPushButton("Add Key")
            self.key_add_button.clicked.connect(self._add_new_key)
            self.main_layout.addWidget(self.key_add_button)

        self._populate_item_list()

    def mode_changed_cb(self, new_mode):
        """Executed when the mode changes.

        :param new_mode the name of the new mode
        """
        self.current_mode = new_mode

        self._populate_item_list()
        if self.current_identifier:
            self._input_item_selection(self.current_identifier)

    def input_item_changed_cb(self, identifier):
        """Executed when the actions associated with an item change.

        :param identifier identification for the item that changed
        """
        input_type = identifier.input_type
        input_id = identifier.input_id

        # If this is a keyboard check if we need to remove the key
        if self.device_profile.type == DeviceType.Keyboard:
            assert(input_type == InputType.Keyboard)

            self._populate_item_list()
            if self.current_identifier and self.current_identifier.input_id in \
                    self.input_items[InputType.Keyboard]:
                item = self.input_items[InputType.Keyboard][
                    self.current_identifier.input_id
                ]
                item.setAutoFillBackground(True)
                item.setPalette(self.cur_palette)

            if input_id in self.input_items[input_type]:
                self.input_items[input_type][input_id].create_action_icons(
                    self.device_profile.modes[self.current_mode].get_data(
                        input_type,
                        input_id
                    )
                )

        # Joystick input item entries are never removed
        else:
            self.input_items[input_type][input_id].create_action_icons(
                self.device_profile.modes[self.current_mode].get_data(
                    identifier.input_type,
                    identifier.input_id
                )
            )

    def _populate_item_list(self):
        """Populates the widget with all required items."""
        # Remove existing content
        common.clear_layout(self.scroll_layout)
        self.input_items = {
            InputType.JoystickAxis: {},
            InputType.JoystickButton: {},
            InputType.JoystickHat: {},
            InputType.Keyboard: {}
        }

        # Bail if the current mode is invalid
        if self.current_mode is None:
            return

        if self.device_profile.type == DeviceType.Keyboard:
            self._populate_keyboard()
        elif self.device_profile.type == DeviceType.VJoy:
            self._populate_vjoy()
        elif self.device_profile.type == DeviceType.Joystick:
            self._populate_joystick()

        self.scroll_layout.addStretch()

    def _populate_joystick(self):
        """Handles generating the items for a joystick device."""
        input_counts = [
            (InputType.JoystickAxis, self.device.axes),
            (InputType.JoystickButton, self.device.buttons),
            (InputType.JoystickHat, self.device.hats)
        ]

        # Ensure the current mode exists for the device even if it
        # was added at runtime
        self.device_profile.ensure_mode_exists(self.current_mode)

        # Create items for each of the inputs on the device
        for input_type, count in input_counts:
            for i in range(1, count + 1):
                item = InputItemButton(
                    i,
                    InputIdentifier(
                        input_type,
                        i,
                        self.device_profile.type
                    ),
                    self
                )

                item.create_action_icons(
                    self.device_profile.modes[self.current_mode].get_data(
                        input_type,
                        i
                    )
                )
                item.input_item_clicked.connect(
                    self._input_item_selection
                )
                self.input_items[input_type][i] = item
                self.scroll_layout.addWidget(item)

    def _populate_keyboard(self):
        """Handles generating the items for the keyboard."""
        # Add existing keys to the scroll
        mode = self.device_profile.modes[self.current_mode]
        key_dict = {}
        for key, entry in mode.config[InputType.Keyboard].items():
            key_dict[gremlin.macro.key_from_code(key[0], key[1]).name] = entry

        for key_string in sorted(key_dict.keys()):
            # Create the input item
            entry = key_dict[key_string]
            key_code = (entry.input_id[0], entry.input_id[1])
            key = gremlin.macro.key_from_code(key_code[0], key_code[1])
            item = InputItemButton(
                key.name,
                InputIdentifier(
                    InputType.Keyboard,
                    key_code,
                    self.device_profile.type
                ),
                self
            )
            item.create_action_icons(entry)
            item.input_item_clicked.connect(self._input_item_selection)
            # Add the new item to the panel
            self.input_items[InputType.Keyboard][key_code] = item
            self.scroll_layout.addWidget(item)

    def _populate_vjoy(self):
        """Handles generating the items for a vjoy device."""
        # Ensure the current mode exists for the device even if it
        # was added at runtime
        self.device_profile.ensure_mode_exists(self.current_mode)

        # Create items for each axis
        for i in range(1, self.device.axes+1):
            item = InputItemButton(
                i,
                InputIdentifier(
                    InputType.JoystickAxis,
                    i,
                    self.device_profile.type
                ),
                self
            )
            item.create_action_icons(
                self.device_profile.modes[self.current_mode].get_data(
                    InputType.JoystickAxis,
                    i
                )
            )
            item.input_item_clicked.connect(
                self._input_item_selection
            )
            self.input_items[InputType.JoystickAxis][i] = item
            self.scroll_layout.addWidget(item)

    def _input_item_selection(self, identifier):
        """Selects the item specified by the input type and label..

        This is a callback called when the user clicks on a different
        input item in the ui. Delegates the loading of the
        configuration dialog for the selected input item.

        :param identifier the input item identifier
        """
        # If the current mode is not specified don't do anything
        if self.current_mode is None:
            return

        # Store the newly selected input item
        self.current_identifier = identifier

        # Deselect all input item entries
        for axis_id, axis in self.input_items[InputType.JoystickAxis].items():
            axis.setPalette(self.palette())
        for btn_id, button in self.input_items[InputType.JoystickButton].items():
            button.setPalette(self.palette())
        for hat_id, hat in self.input_items[InputType.JoystickHat].items():
            hat.setPalette(self.palette())
        for key_id, key in self.input_items[InputType.Keyboard].items():
            key.setPalette(self.palette())

        # Highlight selected button
        if identifier.input_id in self.input_items[identifier.input_type]:
            item = self.input_items[identifier.input_type][identifier.input_id]
            item.setAutoFillBackground(True)
            item.setPalette(self.cur_palette)
        else:
            self.current_identifier = None

        # Load the correct detail content for the newly selected
        # input item
        if identifier.input_id in self.input_items[identifier.input_type]:
            self.input_item_selected.emit(identifier, self.current_mode)
        else:
            self.current_identifier = None
            self.current_configuration_dialog = None

    def _add_new_key(self):
        """Displays the screen overlay prompting the user to press a
        key which will then be added.
        """
        self.keyboard_press_dialog = common.InputListenerWidget(
            self._add_key_to_scroll_list_cb,
            [gremlin.common.InputType.Keyboard]
        )

        # Display the dialog centered in the middle of the UI
        geom = self.geometry()
        point = self.mapToGlobal(QtCore.QPoint(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
        ))
        self.keyboard_press_dialog.setGeometry(
            point.x(),
            point.y(),
            300,
            150
        )
        self.keyboard_press_dialog.show()

    def _add_key_to_scroll_list_cb(self, key):
        """Adds the key pressed by the user to the list of keyboard
        keys."""
        # Add the new key to the profile if it is valid
        if key is None:
            return

        key_pair = (key.scan_code, key.is_extended)
        # Special handling of the right shift key due to Qt and windows
        # discrepancies in key code representation
        if key == gremlin.macro.Keys.RShift2:
            key_pair = (key.scan_code, False)

        # Grab the profile entry which creates one if it doesn't exist
        # yet
        self.device_profile.modes[self.current_mode].get_data(
            InputType.Keyboard,
            key_pair
        )

        # Recreate the entire UI to have the button show up
        self._populate_item_list()
        self._input_item_selection(InputIdentifier(
            InputType.Keyboard,
            key_pair,
            DeviceType.Keyboard
        ))


class ActionLabel(QtWidgets.QLabel):

    """Handles showing the correct icon for the given action."""

    def __init__(self, action_entry, parent=None):
        """Creates a new label for the given entry.

        :param action_entry the entry to create the label for
        :param parent the parent
        """
        QtWidgets.QLabel.__init__(self, parent)
        self.setPixmap(QtGui.QPixmap(action_entry.icon()))


# class ContainerDock(QtWidgets.QDockWidget):
#
#     # Signal which is emitted whenever the widget is closed
#     closed = QtCore.pyqtSignal(QtWidgets.QWidget)
#
#     # Palette used to render widgets
#     palette = QtGui.QPalette()
#     palette.setColor(QtGui.QPalette.Background, QtCore.Qt.lightGray)
#
#     def __init__(self, container_widget, parent=None):
#         """Creates a new instance.
#
#         :param container_widget the container widget this dock holds
#         :param parent the parent widget of this widget
#         """
#         super().__init__(parent)
#         assert(isinstance(
#             container_widget,
#             gremlin.base_classes.AbstractContainerWidget
#         ))
#
#         # Lookup table from input type to available actions
#         self.container_widget = container_widget
#
#         self.setWindowTitle(self.container_widget.data.name)
#         self.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
#
#         # Create root widget of the dock element
#         self.main_widget = QtWidgets.QWidget()
#         self.main_widget.setAutoFillBackground(True)
#         self.main_widget.setPalette(self.palette)
#
#         self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
#         # TODO: need to handle those differently now
#         # self._add_condition()
#         self.main_layout.addWidget(self.container_widget)
#         self.setWidget(self.main_widget)
#
#     def to_profile(self):
#         """Updates the profile data associated with the container's content."""
#         self.container_widget.save_changes()
#         # TODO: This is condition stuff and needs to be handled differently
#         # if self._is_button_like() and self._has_condition():
#         #     # Extract activation condition data
#         #     self.action_widget.action_data.condition =\
#         #         action_plugins.common.ButtonCondition(
#         #             self.condition.press.isChecked(),
#         #             self.condition.release.isChecked(),
#         #             self.condition.shift_data
#         #         )
#         # elif self._is_hat() and self._has_condition():
#         #     self.action_widget.action_data.condition = \
#         #         action_plugins.common.HatCondition(
#         #             self.condition.widgets["N"].isChecked(),
#         #             self.condition.widgets["NE"].isChecked(),
#         #             self.condition.widgets["E"].isChecked(),
#         #             self.condition.widgets["SE"].isChecked(),
#         #             self.condition.widgets["S"].isChecked(),
#         #             self.condition.widgets["SW"].isChecked(),
#         #             self.condition.widgets["W"].isChecked(),
#         #             self.condition.widgets["NW"].isChecked()
#         #         )
#         # elif self._is_axis() and self._has_condition():
#         #     self.action_widget.action_data.condition = \
#         #         action_plugins.common.AxisCondition(
#         #             self.condition.checkbox.isChecked(),
#         #             self.condition.lower_limit.value(),
#         #             self.condition.upper_limit.value()
#         #         )
#
#     # TODO: Handle condition stuff saner
#     # def _populate_condition(self):
#     #     """Populate widget items with data if present."""
#     #     # Only run if we need a condition
#     #     if not self._has_condition():
#     #         return
#     #
#     #     # Get condition data and return if there is nothing
#     #     condition = self.container_widget.action_data.condition
#     #     if condition is None:
#     #         return
#     #
#     #     if self._is_button_like():
#     #         self.condition.disconnect_signals()
#     #
#     #         self.condition.press.setChecked(condition.on_press)
#     #         self.condition.release.setChecked(condition.on_release)
#     #
#     #         # Shift action label
#     #         if condition.shift_button is not None:
#     #             self.condition.shift_data = condition.shift_button
#     #             if condition.shift_button["hardware_id"] == 0:
#     #                 key = macro.key_from_code(
#     #                     condition.shift_button["id"][0],
#     #                     condition.shift_button["id"][1]
#     #                 )
#     #                 self.condition.shift_button.setText(key.name)
#     #             else:
#     #                 devices = util.joystick_devices()
#     #                 dummy_event = Event(
#     #                     InputType.JoystickButton,
#     #                     condition.shift_button["id"],
#     #                     condition.shift_button["hardware_id"],
#     #                     condition.shift_button["windows_id"]
#     #                 )
#     #                 for dev in devices:
#     #                     if util.device_id(dummy_event) == util.device_id(dev):
#     #                         self.condition.shift_button.setText(
#     #                             "{} - Button {:d}".format(
#     #                                 dev.name,
#     #                                 condition.shift_button["id"]
#     #                             ))
#     #         self.condition.connect_signals()
#     #
#     #     elif self._is_hat():
#     #         self.condition.disconnect_signals()
#     #         self.condition.widgets["N"].setChecked(condition.on_n)
#     #         self.condition.widgets["NE"].setChecked(condition.on_ne)
#     #         self.condition.widgets["E"].setChecked(condition.on_e)
#     #         self.condition.widgets["SE"].setChecked(condition.on_se)
#     #         self.condition.widgets["S"].setChecked(condition.on_s)
#     #         self.condition.widgets["SW"].setChecked(condition.on_sw)
#     #         self.condition.widgets["W"].setChecked(condition.on_w)
#     #         self.condition.widgets["NW"].setChecked(condition.on_nw)
#     #         self.condition.connect_signals()
#     #     elif self._is_axis():
#     #         self.condition.disconnect_signals()
#     #         self.condition.checkbox.setChecked(condition.is_active)
#     #         self.condition.lower_limit.setValue(condition.lower_limit)
#     #         self.condition.upper_limit.setValue(condition.upper_limit)
#     #         self.condition.connect_signals()
#
#     def closeEvent(self, event):
#         """Emits the closed event when this widget is being closed.
#
#         :param event the close event details
#         """
#         QtWidgets.QDockWidget.closeEvent(self, event)
#         self.closed.emit(self)
#
#     # def _has_condition(self):
#     #     """Returns whether or not the widget has a condition.
#     #
#     #     :return True if a condition is present, False otherwise
#     #     """
#     #     has_condition = False
#     #     type_action_map = plugin_manager.ActionPlugins().type_action_map
#     #     input_type = self.container_widget.action_data.parent.input_type
#     #     action_type = type(self.container_widget.action_data)
#     #
#     #     if self._is_button_like() and action_type in type_action_map[input_type]:
#     #         has_condition = True
#     #     elif self._is_hat() and action_type in type_action_map[input_type]:
#     #         has_condition = True
#     #     elif self._is_axis() and action_type in type_action_map[input_type]:
#     #         has_condition = True
#     #
#     #     return has_condition
#
#     # def _add_condition(self):
#     #     """Adds a condition widget to the UI if necessary."""
#     #     type_action_map = plugin_manager.ActionPlugins().type_action_map
#     #     input_type = self.container_widget.action_data.parent.input_type
#     #     action_type = type(self.container_widget.action_data)
#     #     condition = None
#     #
#     #     if self._is_button_like() and action_type in type_action_map[input_type]:
#     #         condition = ButtonConditionWidget(self.to_profile)
#     #     elif self._is_hat() and action_type in type_action_map[input_type]:
#     #         condition = HatConditionWidget(self.to_profile)
#     #     elif self._is_axis() and action_type in type_action_map[input_type]:
#     #         condition = AxisConditionWidget(self.to_profile)
#     #
#     #     if condition is not None:
#     #         self.condition = condition
#     #         self._populate_condition()
#     #         self.main_layout.addWidget(self.condition)
#
#     # def _is_button_like(self):
#     #     """Returns True if the action_widget is button like, i.e. a
#     #     joystick button or a keyboard key.
#     #
#     #     :return True if the action_widget is associated with a button
#     #         like input type, False otherwise
#     #     """
#     #     input_type = self.container_widget.action_data.parent.input_type
#     #     return input_type in [
#     #         UiInputType.JoystickButton,
#     #         UiInputType.Keyboard
#     #     ]
#     #
#     # def _is_hat(self):
#     #     """Returns True if the action_widget is associated with a hat.
#     #
#     #     :return True if the action_widget is associated with a hat,
#     #         False otherwise
#     #     """
#     #     is_hat = self.container_widget.action_data.parent.input_type == \
#     #              UiInputType.JoystickHat
#     #     is_remap = isinstance(
#     #         self.container_widget.action_data, action_plugins.remap.Remap
#     #     )
#     #     return is_hat and not is_remap
#     #
#     # def _is_axis(self):
#     #     """Returns True if the action_widget is associated with an axis.
#     #
#     #     :return True if the action_widget is associated with an axis,
#     #         False otherwise
#     #     """
#     #     is_axis = self.container_widget.action_data.parent.input_type == \
#     #               UiInputType.JoystickAxis
#     #     return is_axis


class ContainerSelector(QtWidgets.QWidget):

    container_added = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QtWidgets.QHBoxLayout(self)

        self.container_dropdown = QtWidgets.QComboBox()
        for name in self._valid_container_list():
            self.container_dropdown.addItem(name)
        self.add_button = QtWidgets.QPushButton("Add")
        self.add_button.clicked.connect(self._add_container)

        self.main_layout.addWidget(self.container_dropdown)
        self.main_layout.addWidget(self.add_button)

    def _valid_container_list(self):
        """Returns a list of valid actions for this InputItemWidget.

        :return list of valid action names
        """
        container_list = []
        for entry in gremlin.plugin_manager.ContainerPlugins().repository.values():
            container_list.append(entry.name)
        return sorted(container_list)

    def _add_container(self, clicked=False):
        self.container_added.emit(self.container_dropdown.currentText())


class AbstractContainerWidget(QtWidgets.QDockWidget):

    # Signal which is emitted whenever the widget is closed
    closed = QtCore.pyqtSignal(QtWidgets.QWidget)

    # Signal which is emitted whenever the widget's contents change
    modified = QtCore.pyqtSignal()

    # Palette used to render widgets
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Background, QtCore.Qt.lightGray)

    def __init__(self, profile_data, parent=None):
        assert isinstance(profile_data, gremlin.base_classes.AbstractContainer)
        super().__init__(parent)
        self.profile_data = profile_data
        self.action_widgets = []

        # Basic widget configuration
        self.setWindowTitle(self._get_window_title())
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)

        # Create root widget of the dock element
        self.dock_widget = QtWidgets.QWidget()
        self.dock_widget.setAutoFillBackground(True)
        self.dock_widget.setPalette(self.palette)
        self.setWidget(self.dock_widget)

        # Create layout and place it inside the dock widget
        self.main_layout = QtWidgets.QVBoxLayout(self.dock_widget)

        # Create the actual UI
        self._create_ui()

    def _get_widget_index(self, widget):
        index = -1
        for i, entry in enumerate(self.action_widgets):
            if entry.action_widget == widget:
                index = i
        return index

    def _add_action_widget(self, widget):
        wrapped_widget = ActionWrapper(
            widget,
            self.profile_data.interaction_types
        )
        self.action_widgets.append(wrapped_widget)
        widget.modified.connect(lambda: self.modified.emit())
        wrapped_widget.interacted.connect(
            lambda x: self._handle_interaction(widget, x)
        )
        return wrapped_widget

    def _add_separator(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.main_layout.addWidget(line)

    def closeEvent(self, event):
        """Emits the closed event when this widget is being closed.

        :param event the close event details
        """
        QtWidgets.QDockWidget.closeEvent(self, event)
        self.closed.emit(self)

    def _handle_interaction(self, widget, action):
        raise gremlin.error.MissingImplementationError(
            "AbstractContainerWidget._handle_interaction not "
            "implemented in subclass"
        )

    def _create_ui(self):
        raise gremlin.error.MissingImplementationError(
            "AbstractContainerWidget._setup_ui not "
            "implemented in subclass"
        )

    def _get_window_title(self):
        return self.profile_data.name


class AbstractActionWidget(QtWidgets.QFrame):

    """Base class for all widgets representing actions from the profile
    module."""

    # Signal which is emitted whenever the widget's contents change
    modified = QtCore.pyqtSignal()

    def __init__(self, action_data, parent=None):
        """Creates a new instance.

        :param action_data the sub-classed AbstractAction instance
            associated with this specific action.
        :param parent parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)

        self.action_data = action_data

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self._create_ui()
        self._populate_ui()

    def _create_ui(self):
        """Creates all the elements necessary for the widget."""
        raise gremlin.error.MissingImplementationError(
            "AbstractActionWidget._create_ui not implemented in subclass"
        )

    def _populate_ui(self):
        """Updates this widget's representation based on the provided
        AbstractAction instance.
        """
        raise gremlin.error.MissingImplementationError(
            "ActionWidget._populate_ui not implemented in subclass"
        )

    def _get_input_type(self):
        """Returns the input type this widget's action is associated with.
        
        :return InputType corresponding to this action
        """
        return self.action_data.parent.parent.input_type

    def _get_profile_root(self):
        """Returns the root of the entire profile.
        
        :return root Profile instance
        """
        root = self.action_data
        while not isinstance(root, gremlin.profile.Profile):
            root = root.parent
        return root


class ActionWrapper(QtWidgets.QWidget):

    class Interactions(enum.Enum):
        """Enumeration of possible interactions."""
        Up = 1
        Down = 2
        Delete = 3
        Edit = 4
        Count = 5

    condition_map = {
        InputType.JoystickAxis: conditions.AxisConditionWidget,
        InputType.JoystickButton: conditions.ButtonConditionWidget,
        InputType.JoystickHat: conditions.HatConditionWidget,
        InputType.Keyboard: conditions.ButtonConditionWidget
    }

    interacted = QtCore.pyqtSignal(Interactions)

    def __init__(self, action_widget, allowed_interactions, parent=None):
        super().__init__(parent)
        self.action_widget = action_widget
        self.condition_widget = self._create_condition()
        self.condition_widget.modified.connect(
            lambda: self.action_widget.modified.emit()
        )
        self._create_edit_controls(allowed_interactions)

        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.addWidget(self.action_widget, 0, 0)
        self.main_layout.addWidget(self.condition_widget, 0, 1)
        self.main_layout.addLayout(self.controls_layout, 0, 2)
        self.main_layout.setColumnStretch(0, 2)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def _create_condition(self):
        # Determine type of input we're dealing with
        input_type = self.action_widget.action_data.parent.parent.input_type
        return ActionWrapper.condition_map[input_type](
            self.action_widget.action_data
        )

    def _create_edit_controls(self, allowed_interactions):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.red)

        self.controls_layout = QtWidgets.QVBoxLayout()
        if ActionWrapper.Interactions.Up in allowed_interactions:
            self.control_move_up = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_up"), ""
            )
            self.control_move_up.clicked.connect(
                lambda: self.interacted.emit(ActionWrapper.Interactions.Up)
            )
            self.controls_layout.addWidget(self.control_move_up)
        if ActionWrapper.Interactions.Down in allowed_interactions:
            self.control_move_down = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_down"), ""
            )
            self.control_move_down.clicked.connect(
                lambda: self.interacted.emit(ActionWrapper.Interactions.Down)
            )
            self.controls_layout.addWidget(self.control_move_down)
        if ActionWrapper.Interactions.Delete in allowed_interactions:
            self.control_delete = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_delete"), ""
            )
            self.control_delete.clicked.connect(
                lambda: self.interacted.emit(ActionWrapper.Interactions.Delete)
            )
            self.controls_layout.addWidget(self.control_delete)
        if ActionWrapper.Interactions.Edit in allowed_interactions:
            self.control_edit = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_edit"), ""
            )
            self.control_edit.clicked.connect(
                lambda: self.interacted.emit(ActionWrapper.Interactions.Edit)
            )
            self.controls_layout.addWidget(self.control_edit)

        self.controls_layout.addStretch()
