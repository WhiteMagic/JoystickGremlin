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

from PyQt5 import QtCore, QtGui, QtWidgets

import gremlin
from . import common, ui_about


class OptionsUi(common.BaseDialogUi):

    """UI allowing the configuration of a variety of options."""

    def __init__(self, parent=None):
        """Creates a new options UI instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        # Actual configuration object being managed
        self.config = gremlin.config.Configuration()
        self.setMinimumWidth(400)

        self.setWindowTitle("Options")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.tab_container = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tab_container)

        self._create_general_page()
        self._create_profile_page()

    def _create_general_page(self):
        """Creates the general options page."""
        self.general_page = QtWidgets.QWidget()
        self.general_layout = QtWidgets.QVBoxLayout(self.general_page)

        # Highlight input option
        self.highlight_input = QtWidgets.QCheckBox(
            "Highlight currently used input"
        )
        self.highlight_input.clicked.connect(self._highlight_input)
        self.highlight_input.setChecked(self.config.highlight_input)

        # Close to system tray option
        self.close_to_systray = QtWidgets.QCheckBox(
            "Closing minimizes to system tray"
        )
        self.close_to_systray.clicked.connect(self._close_to_systray)
        self.close_to_systray.setChecked(self.config.close_to_tray)

        # Start minimized option
        self.start_minimized = QtWidgets.QCheckBox(
            "Start Joystick Gremlin minimized"
        )
        self.start_minimized.clicked.connect(self._start_minimized)
        self.start_minimized.setChecked(self.config.start_minimized)

        # Show message on mode change
        self.show_mode_change_message = QtWidgets.QCheckBox(
            "Show message when changing mode"
        )
        self.show_mode_change_message.clicked.connect(
            self._show_mode_change_message
        )
        self.show_mode_change_message.setChecked(
            self.config.mode_change_message
        )

        # Default action selection
        self.default_action_layout = QtWidgets.QHBoxLayout()
        self.default_action_label = QtWidgets.QLabel("Default action")
        self.default_action_dropdown = QtWidgets.QComboBox()
        self.default_action_layout.addWidget(self.default_action_label)
        self.default_action_layout.addWidget(self.default_action_dropdown)
        self._init_action_dropdown()
        self.default_action_layout.addStretch()

        self.general_layout.addWidget(self.highlight_input)
        self.general_layout.addWidget(self.close_to_systray)
        self.general_layout.addWidget(self.start_minimized)
        self.general_layout.addWidget(self.show_mode_change_message)
        self.general_layout.addLayout(self.default_action_layout)
        self.general_layout.addStretch()
        self.tab_container.addTab(self.general_page, "General")

    def _create_profile_page(self):
        """Creates the profile options page."""
        self.profile_page = QtWidgets.QWidget()
        self.profile_page_layout = QtWidgets.QVBoxLayout(self.profile_page)

        # Autoload profile option
        self.autoload_checkbox = QtWidgets.QCheckBox(
            "Automatically load profile based on current application"
        )
        self.autoload_checkbox.clicked.connect(self._autoload_profiles)
        self.autoload_checkbox.setChecked(self.config.autoload_profiles)

        # Executable dropdown list
        self.executable_layout = QtWidgets.QHBoxLayout()
        self.executable_label = QtWidgets.QLabel("Executable")
        self.executable_selection = QtWidgets.QComboBox()
        self.executable_selection.setMinimumWidth(300)
        self.executable_selection.currentTextChanged.connect(
            self._show_executable
        )
        self.executable_add = QtWidgets.QPushButton()
        self.executable_add.setIcon(QtGui.QIcon("gfx/button_add.png"))
        self.executable_add.clicked.connect(self._new_executable)
        self.executable_remove = QtWidgets.QPushButton()
        self.executable_remove.setIcon(QtGui.QIcon("gfx/button_delete.png"))
        self.executable_remove.clicked.connect(self._remove_executable)
        self.executable_list = QtWidgets.QPushButton()
        self.executable_list.setIcon(QtGui.QIcon("gfx/list_show.png"))
        self.executable_list.clicked.connect(self._list_executables)

        self.executable_layout.addWidget(self.executable_label)
        self.executable_layout.addWidget(self.executable_selection)
        self.executable_layout.addWidget(self.executable_add)
        self.executable_layout.addWidget(self.executable_remove)
        self.executable_layout.addWidget(self.executable_list)
        self.executable_layout.addStretch()

        self.profile_layout = QtWidgets.QHBoxLayout()
        self.profile_field = QtWidgets.QLineEdit()
        self.profile_field.textChanged.connect(self._update_profile)
        self.profile_field.editingFinished.connect(self._update_profile)
        self.profile_select = QtWidgets.QPushButton()
        self.profile_select.setIcon(QtGui.QIcon("gfx/button_edit.png"))
        self.profile_select.clicked.connect(self._select_profile)

        self.profile_layout.addWidget(self.profile_field)
        self.profile_layout.addWidget(self.profile_select)

        self.profile_page_layout.addWidget(self.autoload_checkbox)
        self.profile_page_layout.addLayout(self.executable_layout)
        self.profile_page_layout.addLayout(self.profile_layout)
        self.profile_page_layout.addStretch()

        self.tab_container.addTab(self.profile_page, "Profiles")

        self.populate_executables()

    def closeEvent(self, event):
        """Closes the calibration window.

        :param event the close event
        """
        self.config.save()
        super().closeEvent(event)

    def populate_executables(self, executable_name=None):
        """Populates the profile drop down menu.

        :param executable_name name of the executable to pre select
        """
        self.profile_field.textChanged.disconnect(self._update_profile)
        self.executable_selection.clear()
        executable_list = sorted(self.config.get_executable_list())
        for path in executable_list:
            self.executable_selection.addItem(path)
        self.profile_field.textChanged.connect(self._update_profile)

        # Select the provided executable if it exists, otherwise the first one
        # in the list
        index = 0
        if executable_name is not None and executable_name in executable_list:
            index = self.executable_selection.findText(executable_name)
        self.executable_selection.setCurrentIndex(index)

    def _autoload_profiles(self, clicked):
        """Stores profile autoloading preference.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.autoload_profiles = clicked
        self.config.save()

    def _close_to_systray(self, clicked):
        """Stores closing to system tray preference.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.close_to_tray = clicked
        self.config.save()

    def _start_minimized(self, clicked):
        """Stores start minimized preference.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.start_minimized = clicked
        self.config.save()

    def _highlight_input(self, clicked):
        """Stores preference for input highlighting.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.highlight_input = clicked
        self.config.save()

    def _list_executables(self):
        """Shows a list of executables for the user to pick."""
        self.executable_list_view = ProcessWindow()
        self.executable_list_view.process_selected.connect(self._add_executable)
        self.executable_list_view.show()

    def _add_executable(self, fname):
        """Adds the provided executable to the list of configurations.

        :param fname the executable for which to add a mapping
        """
        if fname not in self.config.get_executable_list():
            self.config.set_profile(fname, "")
            self.populate_executables(fname)

    def _new_executable(self):
        """Prompts the user to select a new executable to add to the
        profile.
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Path to executable",
            "C:\\",
            "Executable (*.exe)"
        )
        if fname != "":
            self._add_executable(fname)

    def _remove_executable(self):
        """Removes the current executable from the configuration."""
        self.config.remove_profile(self.executable_selection.currentText())
        self.populate_executables()

    def _select_profile(self):
        """Displays a file selection dialog for a profile.

        If a valid file is selected the mapping from executable to
        profile is updated.
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Path to executable",
            gremlin.util.userprofile_path(),
            "Profile (*.xml)"
        )
        if fname != "":
            self.profile_field.setText(fname)
            self.config.set_profile(
                self.executable_selection.currentText(),
                self.profile_field.text()
            )

    def _show_executable(self, exec_path):
        """Displays the profile associated with the given executable.

        :param exec_path path to the executable to shop
        """
        self.profile_field.setText(self.config.get_profile(exec_path))

    def _show_mode_change_message(self, clicked):
        """Stores the user's preference for mode change notifications.

        :param clicked whether or not the checkbox is ticked"""
        self.config.mode_change_message = clicked
        self.config.save()

    def _update_profile(self):
        """Updates the profile associated with the current executable."""
        self.config.set_profile(
            self.executable_selection.currentText(),
            self.profile_field.text()
        )

    def _init_action_dropdown(self):
        """Initializes the action selection dropdown menu."""
        plugins = gremlin.plugin_manager.ActionPlugins()

        for act in sorted(plugins.repository.values(), key=lambda x: x.name):
            self.default_action_dropdown.addItem(act.name)
        self.default_action_dropdown.setCurrentText(self.config.default_action)
        self.default_action_dropdown.currentTextChanged.connect(
            self._update_default_action
        )

    def _update_default_action(self, value):
        """Updates the config with the newly selected action name.

        :param value the name of the newly selected action
        """
        self.config.default_action = value
        self.config.save()


class ProcessWindow(common.BaseDialogUi):

    """Displays active processes in a window for the user to select."""

    # Signal emitted when the user selects a process
    process_selected = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent of the widget
        """
        super().__init__(parent)

        self.setWindowTitle("Process List")
        self.setMinimumWidth(400)
        self.setMinimumHeight(600)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.list_model = QtCore.QStringListModel()
        self.list_model.setStringList(
            gremlin.process_monitor.list_current_processes()
        )
        self.list_view = QtWidgets.QListView()
        self.list_view.setModel(self.list_model)
        self.list_view.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.main_layout.addWidget(self.list_view)

        self.select_button = QtWidgets.QPushButton("Select")
        self.select_button.clicked.connect(self._select)
        self.main_layout.addWidget(self.select_button)

    def _select(self):
        """Emits the process_signal when the select button is pressed."""
        self.process_selected.emit(self.list_view.currentIndex().data())
        self.close()


class LogWindowUi(common.BaseDialogUi):

    """Window displaying log file content."""

    def __init__(self,  parent=None):
        """Creates a new instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.setWindowTitle("Log Viewer")
        self.setMinimumWidth(600)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.tab_container = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tab_container)

        self._ui_elements = {}
        self._create_log_display(
            os.path.join(gremlin.util.userprofile_path(), "system.log"),
            "System"
        )
        self._create_log_display(
            os.path.join(gremlin.util.userprofile_path(), "user.log"),
            "User"
        )
        self.watcher = gremlin.util.FileWatcher([
            os.path.join(gremlin.util.userprofile_path(), "system.log"),
            os.path.join(gremlin.util.userprofile_path(), "user.log")
        ])
        self.watcher.file_changed.connect(self._reload)

    def closeEvent(self, event):
        """Handles closing of the window.

        :param event the closing event
        """
        self.watcher.stop()
        super().closeEvent(event)

    def _create_log_display(self, fname, title):
        """Creates a new tab displaying log file contents.

        :param fname path to the file whose content to display
        :param title the title of the tab
        """
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        log_display = QtWidgets.QTextEdit()
        log_display.setText(open(fname).read())
        button = QtWidgets.QPushButton("Clear log")
        button.clicked.connect(lambda: self._clear_log(fname))
        layout.addWidget(log_display)
        layout.addWidget(button)

        self._ui_elements[fname] = {
            "page": page,
            "layout": layout,
            "button": button,
            "log_display": log_display
        }

        self.tab_container.addTab(
            self._ui_elements[fname]["page"],
            title
        )

    def _clear_log(self, fname):
        """Clears the specified log file.

        :param fname path to the file to clear
        """
        open(fname, "w").close()

    def _reload(self, fname):
        """Reloads the content of tab displaying the given file.

        :param fname name of the file whose content to update
        """
        widget = self._ui_elements[fname]["log_display"]
        widget.setText(open(fname).read())
        widget.verticalScrollBar().setValue(
            widget.verticalScrollBar().maximum()
        )


class AboutUi(common.BaseDialogUi):

    """Widget which displays information about the application."""

    def __init__(self, parent=None):
        """Creates a new about widget.

        This creates a simple widget which shows version information
        and various software licenses.

        :param parent parent of this widget
        """
        super().__init__(parent)
        self.ui = ui_about.Ui_About()
        self.ui.setupUi(self)

        self.ui.about.setHtml(open("about/about.html").read())

        self.ui.jg_license.setHtml(
            open("about/joystick_gremlin.html").read()
        )

        license_list = [
            "about/third_party_licenses.html",
            "about/modernuiicons.html",
            "about/pyqt.html",
            "about/pysdl2.html",
            "about/pywin32.html",
            "about/qt5.html",
            "about/sdl2.html",
            "about/vjoy.html",
            "about/mako.html",
        ]
        third_party_licenses = ""
        for fname in license_list:
            third_party_licenses += open(fname).read()
        self.ui.third_party_licenses.setHtml(third_party_licenses)


class ModeManagerUi(common.BaseDialogUi):

    """Enables the creation of modes and configuring their inheritance."""

    # Signal emitted when mode configuration changes
    modes_changed = QtCore.pyqtSignal()

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the data being profile whose modes are being
            configured
        :param parent the parent of this widget
        """
        super().__init__(parent)
        self._profile = profile_data
        self.setWindowTitle("Mode Manager")

        self.mode_dropdowns = {}
        self.mode_rename = {}
        self.mode_delete = {}
        self.mode_callbacks = {}

        self._create_ui()

        # Disable keyboard event handler
        el = gremlin.event_handler.EventListener()
        el.keyboard_hook.stop()

    def closeEvent(self, event):
        """Emits the closed event when this widget is being closed.

        :param event the close event details
        """
        # Re-enable keyboard event handler
        el = gremlin.event_handler.EventListener()
        el.keyboard_hook.start()
        super().closeEvent(event)

    def _create_ui(self):
        """Creates the required UII elements."""
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.mode_layout = QtWidgets.QGridLayout()

        self.main_layout.addLayout(self.mode_layout)
        self.add_button = QtWidgets.QPushButton("Add Mode")
        self.add_button.clicked.connect(self._add_mode_cb)
        self.main_layout.addWidget(self.add_button)

        self._populate_mode_layout()

    def _populate_mode_layout(self):
        """Generates the mode layout UI displaying the different modes."""
        # Clear potentially existing content
        common.clear_layout(self.mode_layout)
        self.mode_dropdowns = {}
        self.mode_rename = {}
        self.mode_delete = {}
        self.mode_callbacks = {}

        # Obtain mode names and the mode they inherit from
        mode_list = {}
        for device in self._profile.devices.values():
            for mode in device.modes.values():
                if mode.name not in mode_list:
                    # FIXME: somewhere a mode's name is not set
                    if mode.name is None:
                        continue
                    mode_list[mode.name] = mode.inherit

        # Create UI element for each mode
        row = 0
        for mode, inherit in sorted(mode_list.items()):
            self.mode_layout.addWidget(QtWidgets.QLabel(mode), row, 0)
            self.mode_dropdowns[mode] = QtWidgets.QComboBox()
            self.mode_dropdowns[mode].addItem("None")
            self.mode_dropdowns[mode].setMinimumContentsLength(20)
            for name in sorted(mode_list.keys()):
                if name != mode:
                    self.mode_dropdowns[mode].addItem(name)

            self.mode_callbacks[mode] = self._create_inheritance_change_cb(mode)
            self.mode_dropdowns[mode].currentTextChanged.connect(
                self.mode_callbacks[mode]
            )
            self.mode_dropdowns[mode].setCurrentText(inherit)

            # Rename mode button
            self.mode_rename[mode] = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_edit.png"), ""
            )
            self.mode_layout.addWidget(self.mode_rename[mode], row, 2)
            self.mode_rename[mode].clicked.connect(
                self._create_rename_mode_cb(mode)
            )
            # Delete mode button
            self.mode_delete[mode] = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/mode_delete"), ""
            )
            self.mode_layout.addWidget(self.mode_delete[mode], row, 3)
            self.mode_delete[mode].clicked.connect(
                self._create_delete_mode_cb(mode)
            )

            self.mode_layout.addWidget(self.mode_dropdowns[mode], row, 1)
            row += 1

    def _create_inheritance_change_cb(self, mode):
        """Returns a lambda function callback to change the inheritance of
        a mode.

        This is required as otherwise lambda functions created within a
        function do not behave as desired.

        :param mode the mode for which the callback is being created
        :return customized lambda function
        """
        return lambda x: self._change_mode_inheritance(mode, x)

    def _create_rename_mode_cb(self, mode):
        """Returns a lambda function callback to rename a mode.

        This is required as otherwise lambda functions created within a
        function do not behave as desired.

        :param mode the mode for which the callback is being created
        :return customized lambda function
        """
        return lambda: self._rename_mode(mode)

    def _create_delete_mode_cb(self, mode):
        """Returns a lambda function callback to delete the given mode.

        This is required as otherwise lambda functions created within a
        function do not behave as desired.

        :param mode the mode to remove
        :return lambda function to perform the removal
        """
        return lambda: self._delete_mode(mode)

    def _change_mode_inheritance(self, mode, inherit):
        """Updates the inheritance information of a given mode.

        :param mode the mode to update
        :param inherit the name of the mode this mode inherits from
        """
        # Check if this inheritance would cause a cycle, turning the
        # tree structure into a graph
        has_inheritance_cycle = False
        if inherit != "None":
            all_modes = list(self._profile.devices.values())[0].modes
            cur_mode = inherit
            while all_modes[cur_mode].inherit is not None:
                if all_modes[cur_mode].inherit == mode:
                    has_inheritance_cycle = True
                    break
                cur_mode = all_modes[cur_mode].inherit

        # Update the inheritance information in the profile
        if not has_inheritance_cycle:
            for name, device in self._profile.devices.items():
                if inherit == "None":
                    inherit = None
                device.modes[mode].inherit = inherit
            self.modes_changed.emit()

    def _rename_mode(self, mode_name):
        """Asks the user for the new name for the given mode.

        If the user provided name for the mode is invalid the
        renaming is aborted and no change made.

        :param mode_name new name for the mode
        """
        # Retrieve new name from the user
        name, user_input = QtWidgets.QInputDialog.getText(
                self,
                "Mode name",
                "",
                QtWidgets.QLineEdit.Normal,
                mode_name
        )
        if user_input:
            if name in gremlin.profile.mode_list(self._profile):
                gremlin.util.display_error(
                    "A mode with the name \"{}\" already exists".format(name)
                )
            else:
                # Update the renamed mode in each device
                for device in self._profile.devices.values():
                    device.modes[name] = device.modes[mode_name]
                    device.modes[name].name = name
                    del device.modes[mode_name]

                    # Update inheritance information
                    for mode in device.modes.values():
                        if mode.inherit == mode_name:
                            mode.inherit = name

                self.modes_changed.emit()

            self._populate_mode_layout()

    def _delete_mode(self, mode_name):
        """Removes the specified mode.

        Performs an update of the inheritance of all modes that inherited
        from the deleted mode.

        :param mode_name the name of the mode to delete
        """
        # Obtain mode from which the mode we want to delete inherits
        parent_of_deleted = None
        for mode in list(self._profile.devices.values())[0].modes.values():
            if mode.name == mode_name:
                parent_of_deleted = mode.inherit

        # Assign the inherited mode of the the deleted one to all modes that
        # inherit from the mode to be deleted
        for device in self._profile.devices.values():
            for mode in device.modes.values():
                if mode.inherit == mode_name:
                    mode.inherit = parent_of_deleted

        # Remove the mode from the profile
        for device in self._profile.devices.values():
            del device.modes[mode_name]

        # Update the ui
        self._populate_mode_layout()
        self.modes_changed.emit()

    def _add_mode_cb(self, checked):
        """Asks the user for a new mode to add.

        If the user provided name for the mode is invalid no mode is
        added.

        :param checked flag indicating whether or not the checkbox is active
        """
        name, user_input = QtWidgets.QInputDialog.getText(None, "Mode name", "")
        if user_input:
            if name in gremlin.profile.mode_list(self._profile):
                gremlin.util.display_error(
                    "A mode with the name \"{}\" already exists".format(name)
                )
            else:
                for device in self._profile.devices.values():
                    new_mode = gremlin.profile.Mode(device)
                    new_mode.name = name
                    device.modes[name] = new_mode
                self.modes_changed.emit()

            self._populate_mode_layout()


class ModuleManagerUi(common.BaseDialogUi):

    """UI which allows the user to manage custom python modules to
    be loaded by the program."""

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the profile with which to populate the ui
        :param parent the parent widget
        """
        super().__init__(parent)
        self._profile = profile_data
        self.setWindowTitle("User Module Manager")

        self._create_ui()

        # Disable keyboard event handler
        el = gremlin.event_handler.EventListener()
        el.keyboard_hook.stop()

    def closeEvent(self, event):
        """Emits the closed event when this widget is being closed.

        :param event the close event details
        """
        # Re-enable keyboard event handler
        el = gremlin.event_handler.EventListener()
        el.keyboard_hook.start()
        super().closeEvent(event)

    def _create_ui(self):
        """Creates all the UI elements."""
        self.model = QtCore.QStringListModel()
        self.model.setStringList(sorted(self._profile.imports))

        self.view = QtWidgets.QListView()
        self.view.setModel(self.model)
        self.view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Add widgets which allow modifying the mode list
        self.add = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_add.svg"), "Add"
        )
        self.add.clicked.connect(self._add_cb)
        self.delete = QtWidgets.QPushButton(
            QtGui.QIcon("gfx/list_delete.svg"), "Delete"
        )
        self.delete.clicked.connect(self._delete_cb)

        self.actions_layout = QtWidgets.QHBoxLayout()
        self.actions_layout.addWidget(self.add)
        self.actions_layout.addWidget(self.delete)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.view)
        self.main_layout.addLayout(self.actions_layout)

    def _add_cb(self):
        """Asks the user for the name of a new module to add to the list
        of imported modules.

        If the name is not a valid python identifier nothing is added.
        """
        new_import, input_ok = QtWidgets.QInputDialog.getText(
            self,
            "Module name",
            "Enter the name of the module to import"
        )
        if input_ok and new_import != "":
            if not gremlin.util.valid_python_identifier(new_import):
                gremlin.util.display_error(
                    "\"{}\" is not a valid python module name"
                    .format(new_import)
                )
            else:
                import_list = self.model.stringList()
                import_list.append(new_import)
                self.model.setStringList(sorted(import_list))
                self._profile.imports = list(import_list)

    def _delete_cb(self):
        """Removes the currently selected module from the list."""
        import_list = self.model.stringList()
        index = self.view.currentIndex().row()
        if 0 <= index <= len(import_list):
            del import_list[index]
            self.model.setStringList(import_list)
            self.view.setCurrentIndex(self.model.index(0, 0))
            self._profile.imports = list(import_list)


class DeviceInformationUi(common.BaseDialogUi):

    """Widget which displays information about all connected joystick
    devices."""

    def __init__(self, devices, parent=None):
        """Creates a new instance.

        :param devices the list of device information objects
        :param parent the parent widget
        """
        super().__init__(parent)

        self.devices = devices

        self.setWindowTitle("Device Information")
        self.main_layout = QtWidgets.QGridLayout(self)

        self.main_layout.addWidget(QtWidgets.QLabel("<b>Name</b>"), 0, 0)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Axes</b>"), 0, 1)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Buttons</b>"), 0, 2)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Hats</b>"), 0, 3)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>System ID</b>"), 0, 4)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Hardware ID</b>"), 0, 5)

        for i, entry in enumerate(self.devices):
            self.main_layout.addWidget(
                QtWidgets.QLabel(entry.name), i+1, 0
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.axis_count)), i+1, 1
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.buttons)), i+1, 2
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.hats)), +i+1, 3
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.windows_id)), i+1, 4
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.hardware_id)), i+1, 5
            )

        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(lambda: self.close())
        self.main_layout.addWidget(self.close_button, len(devices)+1, 3)
