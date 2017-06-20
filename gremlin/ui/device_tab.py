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

from PyQt5 import QtWidgets, QtGui, QtCore

import container_plugins.basic
import gremlin
from gremlin.common import InputType
from . import common, input_item


class InputItemConfiguration(QtWidgets.QFrame):

    """UI dialog responsible for the configuration of a single
    input item such as an axis, button, hat, or key.
    """

    # Signal emitted when the description changes
    description_changed = QtCore.pyqtSignal(str)

    def __init__(self, vjoy_devices, item_data, parent=None):
        """Creates a new object instance.

        :param vjoy_devices list of vJoy devices
        :param item_data profile data associated with the item
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.item_data = item_data
        self.vjoy_devices = vjoy_devices

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.button_layout = QtWidgets.QHBoxLayout()
        self.widget_layout = QtWidgets.QVBoxLayout()

        self._create_description()
        if self.item_data.parent.parent.type == gremlin.common.DeviceType.VJoy:
            self._create_vjoy_dropdowns()
        else:
            self._create_dropdowns()

        self.action_model = ActionContainerModel(self.item_data.containers)
        self.action_view = ActionContainerView()
        self.action_view.set_model(self.action_model)
        self.action_view.redraw()

        self.main_layout.addWidget(self.action_view)

    # def from_profile(self, data):
    #     """Sets the data of this widget.
    #
    #     :param data profile.InputItem object containing data for this
    #         widget
    #     """
    #     if not data:
    #         return
    #
    #     # Remove signal callbacks
    #     self.description_field.textChanged.disconnect(self.to_profile)
    #     self.always_execute.stateChanged.disconnect(self.to_profile)
    #
    #     # Create UI widgets and populate them based on the type of
    #     # action stored in the profile.
    #     self.item_profile = data
    #     for action in self.item_profile.actions:
    #         try:
    #             self._do_add(action, False)
    #         except gremlin.error.GremlinError as err:
    #             logging.getLogger("system").exception(str(err))
    #             raise err
    #     self.description_field.setText(self.item_profile.description)
    #     self.always_execute.setChecked(self.item_profile.always_execute)
    #
    #     # Reconnect all signals
    #     self.description_field.textChanged.connect(self.to_profile)
    #     self.always_execute.stateChanged.connect(self.to_profile)

    # def to_profile(self):
    #     """Updates all action items associated with this input item."""
    #     for widget in self.action_widgets:
    #         widget.to_profile()
    #     self.item_profile.always_execute = self.always_execute.isChecked()
    #     self.item_profile.description = self.description_field.text()

    # def _do_add(self, container, emit=True):
    #     """Adds an ActionWidget to the ui by placing it into a
    #     closable container.
    #
    #     :param emit whether or not to emit a changed signal
    #     """
    #     assert isinstance(container, gremlin.base_classes.AbstractContainer)
    #
    #     if container not in self.item_profile.actions:
    #         self.item_profile.actions.append(container)
    #
    #     container_widget = container.widget(container)
    #     container_widget.modified.connect(lambda: self.changed.emit())
    #     container_widget.closed.connect(self._do_remove)
    #
    #     self.action_widgets.append(container_widget)
    #     self.main_layout.addWidget(container_widget)
    #     if emit:
    #         self.changed.emit()
    #
    #     return container_widget

    # def _do_remove(self, widget, emit=True):
    #     """Removes a widget from the ui as well as the profile.
    #
    #     :param widget the widget and associated data to remove
    #     :param emit emits a changed signal if True, otherwise nothing
    #         is emitted
    #     """
    #     assert isinstance(
    #         widget,
    #         input_item.AbstractContainerWidget
    #     )
    #     # Remove profile data
    #     profile_data = widget.profile_data
    #     assert profile_data in self.item_profile.actions
    #     self.item_profile.actions.remove(profile_data)
    #     # Remove UI widgets
    #     self.main_layout.removeWidget(widget)
    #     self.action_widgets.remove(widget)
    #     # Signal change within the widget
    #     if emit:
    #         self.changed.emit()

    def _add_action(self, action_name):
        """Adds a new action to the input item."""
        plugin_manager = gremlin.plugin_manager.ActionPlugins()
        container = container_plugins.basic.BasicContainer(self.item_data)
        container.add_action(
            plugin_manager.get_class(action_name)(container)
        )
        # container.closed.connect(lambda: self._remove_container(container))
        self.action_model.add_container(container)

    def _add_container(self, container_name):
        plugin_manager = gremlin.plugin_manager.ContainerPlugins()
        self.action_model.add_container(
            plugin_manager.get_class(container_name)(self.item_data)
        )

    def _remove_container(self, container):
        self.action_model.remove_container(container)

    def _create_description(self):
        """Creates the description input for the input item."""
        self.description_layout = QtWidgets.QHBoxLayout()
        self.description_layout.addWidget(
            QtWidgets.QLabel("<b>Description</b>")
        )
        self.description_field = QtWidgets.QLineEdit()
        self.description_field.setText(self.item_data.description)
        self.description_field.textChanged.connect(self._edit_description_cb)
        self.description_layout.addWidget(self.description_field)

        self.main_layout.addLayout(self.description_layout)

    def _create_dropdowns(self):
        """Creates a drop down selection with actions that can be
        added to the current input item.
        """
        self.action_layout = QtWidgets.QHBoxLayout()

        self.action_selector = gremlin.ui.common.ActionSelector(
            self.item_data.input_type
        )
        self.action_selector.action_added.connect(self._add_action)
        self.container_selector = input_item.ContainerSelector()
        self.container_selector.container_added.connect(self._add_container)
        self.always_execute = QtWidgets.QCheckBox("Always execute")
        self.always_execute.setChecked(self.item_data.always_execute)
        self.always_execute.stateChanged.connect(self._always_execute_cb)

        self.action_layout.addWidget(self.action_selector)
        self.action_layout.addWidget(self.container_selector)
        self.action_layout.addWidget(self.always_execute)
        self.main_layout.addLayout(self.action_layout)

    def _create_vjoy_dropdowns(self):
        self.action_layout = QtWidgets.QHBoxLayout()

        self.action_selector = gremlin.ui.common.ActionSelector(
            gremlin.common.DeviceType.VJoy
        )
        self.action_selector.action_added.connect(self._add_action)
        self.action_layout.addWidget(self.action_selector)
        self.main_layout.addLayout(self.action_layout)

    def _edit_description_cb(self, text):
        self.item_data.description = text
        self.description_changed.emit(text)

    def _always_execute_cb(self, state):
        self.item_data.always_execute = self.always_execute.isChecked()

    def _valid_action_names(self):
        """Returns a list of valid actions for this InputItemWidget.

        :return list of valid action names
        """
        action_names = []
        if self.item_data.input_type == gremlin.common.DeviceType.VJoy:
            entry = gremlin.plugin_manager.ActionPlugins().repository.get(
                "response-curve",
                None
            )
            if entry is not None:
                action_names.append(entry.name)
            else:
                raise gremlin.error.GremlinError(
                    "Response curve plugin is missing"
                )
        else:
            for entry in gremlin.plugin_manager.ActionPlugins().repository.values():
                if self.item_data.input_type in entry.input_types:
                    action_names.append(entry.name)
        return sorted(action_names)


class ActionContainerModel(common.AbstractModel):

    """Stores action containers for display using the corresponding view."""

    def __init__(self, containers, parent=None):
        """Creates a new instance.

        :param containers the container instances of this model
        """
        super().__init__(parent)
        self._containers = containers

    def rows(self):
        return len(self._containers)

    def data(self, index):
        return self._containers[index]

    def add_container(self, container):
        self._containers.append(container)
        self.data_changed.emit()

    def remove_container(self, container):
        if container in self._containers:
            del self._containers[self._containers.index(container)]
        self.data_changed.emit()


class ActionContainerView(common.AbstractView):

    """View class used to display ActionContainerModel contents."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create required UI items
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout()

        # Configure the widget holding the layout with all the buttons
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        # Configure the scroll area
        self.scroll_area.setMinimumWidth(700)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

    def redraw(self):
        common.clear_layout(self.scroll_layout)
        for index in range(self.model.rows()):
            widget = self.model.data(index).widget(self.model.data(index))
            widget.closed.connect(self._create_closed_cb(widget))
            widget.modified.connect(self.model.data_changed.emit)
            self.scroll_layout.addWidget(widget)
        self.scroll_layout.addStretch(1)

    def _create_closed_cb(self, widget):
        return lambda: self.model.remove_container(widget.profile_data)


class DeviceTabWidget(QtWidgets.QWidget):

    """Widget used to configure a single device."""

    def __init__(
            self,
            vjoy_devices,
            device,
            device_profile,
            current_mode,
            parent=None
    ):
        """Creates a new object instance.

        :param vjoy_devices list of vJoy devices
        :param device device information about this widget's device
        :param device_profile profile data of the entire device
        :param current_mode currently active mode
        :param parent the parent of this widget
        """
        super().__init__(parent)

        # Store parameters
        self.device_profile = device_profile
        self.current_mode = current_mode

        self.vjoy_devices = vjoy_devices
        self.device = device

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.device_profile.ensure_mode_exists(self.current_mode, self.device)

        # List of inputs
        self.input_item_list_model = input_item.InputItemListModel(
            device_profile,
            current_mode
        )
        self.input_item_list_view = input_item.InputItemListView()
        # Only show axis values for vJoy devices
        if device is not None and device.hardware_id == 305446573:
            self.input_item_list_view.limit_input_types([InputType.JoystickAxis])
        self.input_item_list_view.set_model(self.input_item_list_model)
        # TODO: make this saner
        self.input_item_list_view.redraw()

        # Handle user interaction
        self.input_item_list_view.item_selected.connect(
            self.input_item_selected_cb
        )
        self.main_layout.addWidget(self.input_item_list_view)

    def input_item_selected_cb(self, index):
        item_data = input_item_index_lookup(
            index,
            self.device_profile.modes[self.current_mode]
        )

        # Remove the existing widget, if there is one
        item = self.main_layout.takeAt(1)
        if item is not None and item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        self.main_layout.removeItem(item)

        widget = InputItemConfiguration(
            self.vjoy_devices,
            item_data
        )
        change_cb = self._create_change_cb(index)
        widget.action_model.data_changed.connect(change_cb)
        widget.description_changed.connect(change_cb)

        self.main_layout.addWidget(widget)

    def _create_change_cb(self, index):
        return lambda: self.input_item_list_view.redraw_index(index)

    def mode_changed_cb(self, mode):
        self.current_mode = mode
        self.device_profile.ensure_mode_exists(self.current_mode, self.device)
        self.input_item_list_model.mode = mode

        # Remove the existing widget, if there is one
        item = self.main_layout.takeAt(1)
        if item is not None and item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        self.main_layout.removeItem(item)


def input_item_index_lookup(index, input_items):
    axis_count = len(input_items.config[InputType.JoystickAxis])
    button_count = len(input_items.config[InputType.JoystickButton])
    hat_count = len(input_items.config[InputType.JoystickHat])
    key_count = len(input_items.config[InputType.Keyboard])

    if key_count > 0:
        return input_items.get_data(InputType.Keyboard, index)
    else:
        if index < axis_count:
            return input_items.get_data(InputType.JoystickAxis, index + 1)
        elif index < axis_count + button_count:
            return input_items.get_data(
                InputType.JoystickButton,
                index - axis_count + 1
            )
        elif index < axis_count + button_count + hat_count:
            return input_items.get_data(
                InputType.JoystickHat,
                index - axis_count - button_count + 1
            )


# class ConfigurationPanel(QtWidgets.QWidget):
#
#     """Widget which allows configuration of actions for input items."""
#
#     # Signal emitted when the configuration has changed
#     input_item_changed = QtCore.pyqtSignal(input_item.InputIdentifier)
#
#     def __init__(
#             self,
#             vjoy_devices,
#             device,
#             device_profile,
#             current_mode,
#             parent=None
#     ):
#         """Creates a new instance.
#
#         :param vjoy_devices the vjoy devices present in the system
#         :param device the physical device being configured
#         :param device_profile the profile of the device
#         :param current_mode the currently active mode
#         :param parent the parent of this widget
#         """
#         QtWidgets.QWidget.__init__(self, parent)
#
#         # Store parameters
#         self.vjoy_devices = vjoy_devices
#         self.device = device
#         self.device_profile = device_profile
#         self.current_mode = current_mode
#
#         # Storage for the current configuration panel
#         self.current_configuration_dialog = None
#         self.current_identifier = None
#
#         # Create required UI items
#         self.main_layout = QtWidgets.QVBoxLayout(self)
#         self.configuration_scroll = QtWidgets.QScrollArea()
#         self.configuration_widget = QtWidgets.QWidget()
#         self.configuration_layout = QtWidgets.QVBoxLayout()
#
#         # Main widget within the scroll area which contains the
#         # layout with the actual content
#         self.configuration_widget.setMinimumWidth(500)
#         self.configuration_widget.setLayout(self.configuration_layout)
#
#         # Scroll area configuration
#         self.configuration_scroll.setSizePolicy(QtWidgets.QSizePolicy(
#             QtWidgets.QSizePolicy.Minimum,
#             QtWidgets.QSizePolicy.Minimum
#         ))
#         self.configuration_scroll.setMinimumWidth(525)
#         self.configuration_scroll.setWidget(self.configuration_widget)
#         self.configuration_scroll.setWidgetResizable(True)
#
#         # Add scroll area to the main layout
#         self.main_layout.addWidget(self.configuration_scroll)
#
#     def refresh(self, identifier, mode_name):
#         """Redraws the entire configuration dialog for the given item.
#
#         :param identifier the identifier of the item for which to
#                 redraw the widget
#         :param mode_name name of the currently active mode
#         """
#         self.current_mode = mode_name
#         self._remove_invalid_actions_and_inputs()
#
#         # Create InputItemConfigurationPanel object and hook
#         # it's signals up
#         self.current_configuration_dialog = InputItemConfigurationPanel(
#             self.vjoy_devices,
#             self.device_profile.modes[self.current_mode].get_data(
#                 identifier.input_type,
#                 identifier.input_id
#             )
#         )
#         self.current_configuration_dialog.changed.connect(
#             self._input_item_content_changed_cb
#         )
#         self.current_identifier = identifier
#
#         # Visualize the dialog
#         common.clear_layout(self.configuration_layout)
#         self.configuration_layout.addWidget(
#             self.current_configuration_dialog
#         )
#         self.configuration_layout.addStretch(0)
#
#     def mode_changed_cb(self, new_mode):
#         """Executed when the mode changes.
#
#         :param new_mode the name of the new mode
#         """
#         # Cleanup the content of the previous mode before we switch
#         self._remove_invalid_actions_and_inputs()
#
#         # Save new mode
#         self.current_mode = new_mode
#
#         # Select previous selection if it exists
#         if self.current_identifier is not None:
#             self.refresh(self.current_identifier, new_mode)
#
#     def _remove_invalid_actions_and_inputs(self):
#         """Perform maintenance on the previously selected item.
#
#         This removes invalid actions and deletes keys without any
#         associated actions.
#         """
#         if self.current_configuration_dialog is not None:
#             # Remove actions that have not been properly configured
#             item_profile = self.current_configuration_dialog.item_profile
#             items_to_delete = []
#             for entry in item_profile.actions:
#                 if not entry.is_valid():
#                     items_to_delete.append(entry)
#             for entry in items_to_delete:
#                 item_profile.actions.remove(entry)
#
#             if len(items_to_delete) > 0:
#                 self.input_item_changed.emit(self.current_identifier)
#
#             # Delete the previously selected item if it contains no
#             # action and we're on the keyboard tab. However, only do
#             # this if the mode of the configuration dialog and the mode
#             # match.
#             if self.device_profile.type == gremlin.common.DeviceType.Keyboard:
#                 if (item_profile.parent.name == self.current_mode) and \
#                         len(item_profile.actions) == 0:
#                     self.device_profile.modes[self.current_mode].delete_data(
#                         common.InputType.Keyboard,
#                         item_profile.input_id
#                     )
#                     self.input_item_changed.emit(self.current_identifier)
#
#     def _input_item_content_changed_cb(self):
#         """Updates the profile data of an input item when its contents
#         change."""
#         assert(self.current_identifier is not None)
#         assert(self.current_mode in self.device_profile.modes)
#
#         self.current_configuration_dialog.save_changes()
#         self.input_item_changed.emit(self.current_identifier)