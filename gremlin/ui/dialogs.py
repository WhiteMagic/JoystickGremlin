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
import re
import copy
import logging
import traceback
import subprocess
import sys
import winreg
import importlib
from inspect import getdoc

from PyQt5 import QtCore, QtGui, QtWidgets

import dill

import gremlin
import gremlin.error
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
        self._create_hidguardian_page()

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

        # Switch to highlighted device
        self.highlight_device = QtWidgets.QCheckBox(
            "Highlight swaps device tabs"
        )
        self.highlight_device.clicked.connect(self._highlight_device)
        self.highlight_device.setChecked(self.config.highlight_device)

        # Close to system tray option
        self.close_to_systray = QtWidgets.QCheckBox(
            "Closing minimizes to system tray"
        )
        self.close_to_systray.clicked.connect(self._close_to_systray)
        self.close_to_systray.setChecked(self.config.close_to_tray)

        # Activate profile on launch
        self.activate_on_launch = QtWidgets.QCheckBox(
            "Activate profile on launch"
        )
        self.activate_on_launch.clicked.connect(self._activate_on_launch)
        self.activate_on_launch.setChecked(self.config.activate_on_launch)

        # Start minimized option
        self.start_minimized = QtWidgets.QCheckBox(
            "Start Joystick Gremlin minimized"
        )
        self.start_minimized.clicked.connect(self._start_minimized)
        self.start_minimized.setChecked(self.config.start_minimized)

        # Start on user login
        self.start_with_windows = QtWidgets.QCheckBox(
            "Start Joystick Gremlin with Windows"
        )
        self.start_with_windows.clicked.connect(self._start_windows)
        self.start_with_windows.setChecked(self._start_windows_enabled())

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

        # Macro axis polling rate
        self.macro_axis_polling_layout = QtWidgets.QHBoxLayout()
        self.macro_axis_polling_label = \
            QtWidgets.QLabel("Macro axis polling rate")
        self.macro_axis_polling_value = common.DynamicDoubleSpinBox()
        self.macro_axis_polling_value.setRange(0.001, 1.0)
        self.macro_axis_polling_value.setSingleStep(0.05)
        self.macro_axis_polling_value.setDecimals(3)
        self.macro_axis_polling_value.setValue(
            self.config.macro_axis_polling_rate
        )
        self.macro_axis_polling_value.valueChanged.connect(
            self._macro_axis_polling_rate
        )
        self.macro_axis_polling_layout.addWidget(self.macro_axis_polling_label)
        self.macro_axis_polling_layout.addWidget(self.macro_axis_polling_value)
        self.macro_axis_polling_layout.addStretch()

        # Macro axis minimum change value
        self.macro_axis_minimum_change_layout = QtWidgets.QHBoxLayout()
        self.macro_axis_minimum_change_label = \
            QtWidgets.QLabel("Macro axis minimum change value")
        self.macro_axis_minimum_change_value = common.DynamicDoubleSpinBox()
        self.macro_axis_minimum_change_value.setRange(0.00001, 1.0)
        self.macro_axis_minimum_change_value.setSingleStep(0.01)
        self.macro_axis_minimum_change_value.setDecimals(5)
        self.macro_axis_minimum_change_value.setValue(
            self.config.macro_axis_minimum_change_rate
        )
        self.macro_axis_minimum_change_value.valueChanged.connect(
            self._macro_axis_minimum_change_value
        )
        self.macro_axis_minimum_change_layout.addWidget(
            self.macro_axis_minimum_change_label
        )
        self.macro_axis_minimum_change_layout.addWidget(
            self.macro_axis_minimum_change_value
        )
        self.macro_axis_minimum_change_layout.addStretch()

        self.general_layout.addWidget(self.highlight_input)
        self.general_layout.addWidget(self.highlight_device)
        self.general_layout.addWidget(self.close_to_systray)
        self.general_layout.addWidget(self.activate_on_launch)
        self.general_layout.addWidget(self.start_minimized)
        self.general_layout.addWidget(self.start_with_windows)
        self.general_layout.addWidget(self.show_mode_change_message)
        self.general_layout.addLayout(self.default_action_layout)
        self.general_layout.addLayout(self.macro_axis_polling_layout)
        self.general_layout.addLayout(self.macro_axis_minimum_change_layout)
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

        self.keep_last_autoload_checkbox = QtWidgets.QCheckBox(
            "Keep profile active on focus loss"
        )
        self.keep_last_autoload_checkbox.setToolTip("""If this option is off, profiles that have been configured to load automatically when an application gains focus
will deactivate when that application loses focus.

If this option is on, the last active profile will remain active until a different profile is loaded.""")
        self.keep_last_autoload_checkbox.clicked.connect(self._keep_last_autoload)
        self.keep_last_autoload_checkbox.setChecked(self.config.keep_last_autoload)
        self.keep_last_autoload_checkbox.setEnabled(self.config.autoload_profiles)

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
        self.executable_edit = QtWidgets.QPushButton()
        self.executable_edit.setIcon(QtGui.QIcon("gfx/button_edit.png"))
        self.executable_edit.clicked.connect(self._edit_executable)
        self.executable_list = QtWidgets.QPushButton()
        self.executable_list.setIcon(QtGui.QIcon("gfx/list_show.png"))
        self.executable_list.clicked.connect(self._list_executables)

        self.executable_layout.addWidget(self.executable_label)
        self.executable_layout.addWidget(self.executable_selection)
        self.executable_layout.addWidget(self.executable_add)
        self.executable_layout.addWidget(self.executable_remove)
        self.executable_layout.addWidget(self.executable_edit)
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
        self.profile_page_layout.addWidget(self.keep_last_autoload_checkbox)
        self.profile_page_layout.addLayout(self.executable_layout)
        self.profile_page_layout.addLayout(self.profile_layout)
        self.profile_page_layout.addStretch()

        self.tab_container.addTab(self.profile_page, "Profiles")

        self.populate_executables()

    def _create_hidguardian_page(self):
        self.hg_page = QtWidgets.QWidget()
        self.hg_page_layout = QtWidgets.QVBoxLayout(self.hg_page)

        # Display instructions for non admin users
        if not gremlin.util.is_user_admin():
            label = QtWidgets.QLabel(
                "In order to use HidGuardian to both specify the devices to "
                "hide via HidGuardian as well as have Gremlin see them, "
                "Gremlin has to be run as Administrator."
            )
            label.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
            label.setWordWrap(True)
            label.setFrameShape(QtWidgets.QFrame.Box)
            label.setMargin(10)
            self.hg_page_layout.addWidget(label)

        else:
            # Get list of devices affected by HidGuardian
            hg = gremlin.hid_guardian.HidGuardian()
            hg_device_list = hg.get_device_list()

            self.hg_device_layout = QtWidgets.QGridLayout()
            self.hg_device_layout.addWidget(
                QtWidgets.QLabel("<b>Device Name</b>"), 0, 0
            )
            self.hg_device_layout.addWidget(
                QtWidgets.QLabel("<b>Hidden</b>"), 0, 1
            )

            devices = gremlin.joystick_handling.joystick_devices()
            devices_added = []
            for i, dev in enumerate(devices):
                # Don't add vJoy to this list
                if dev.name == "vJoy Device":
                    continue

                # For identical VID / PID devices only add one instance
                vid_pid_key = (dev.vendor_id, dev.product_id)
                if vid_pid_key in devices_added:
                    continue

                # Set checkbox state based on whether or not HidGuardian tracks
                # the device. Add a callback with pid/vid to add / remove said
                # device from the list of devices handled by HidGuardian
                self.hg_device_layout.addWidget(
                    QtWidgets.QLabel(dev.name), i+1, 0
                )
                checkbox = QtWidgets.QCheckBox("")
                checkbox.setChecked(vid_pid_key in hg_device_list)
                checkbox.stateChanged.connect(self._create_hg_cb(dev))
                self.hg_device_layout.addWidget(checkbox, i+1, 1)
                devices_added.append(vid_pid_key)

            self.hg_page_layout.addLayout(self.hg_device_layout)

            self.hg_page_layout.addStretch()
            label = QtWidgets.QLabel(
                "After making changes to the devices hidden by HidGuardian "
                "the devices that should now be hidden or shown to other"
                "applications need to be unplugged and plugged back in for "
                "the changes to take effect."
            )
            label.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
            label.setWordWrap(True)
            label.setFrameShape(QtWidgets.QFrame.Box)
            label.setMargin(10)
            self.hg_page_layout.addWidget(label)

        self.tab_container.addTab(self.hg_page, "HidGuardian")

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
        executable_list = self.config.get_executable_list()
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
        self.keep_last_autoload_checkbox.setEnabled(clicked)
        self.config.autoload_profiles = clicked
        self.config.save()

    def _keep_last_autoload(self, clicked):
        """Stores keep last autoload preference.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.keep_last_autoload = clicked
        self.config.save()

    def _activate_on_launch(self, clicked):
        """Stores activation of profile on launch preference.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.activate_on_launch = clicked
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

    def _start_windows(self, clicked):
        """Set registry entry to launch Joystick Gremlin on login.

        :param clicked True if launch should happen on login, False otherwise
        """
        if clicked:
            path = os.path.abspath(sys.argv[0])
            subprocess.run(
                'reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /V "Joystick Gremlin" /t REG_SZ /F /D "{}"'.format(path)
            )
        else:
            subprocess.run(
                'reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /F /V "Joystick Gremlin"'
            )
        self.activateWindow()

    def _start_windows_enabled(self):
        """Returns whether or not Gremlin should launch on login.

        :return True if Gremlin launches on login, False otherwise
        """
        key_handle = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run"
            )
        key_info = winreg.QueryInfoKey(key_handle)

        for i in range(key_info[1]):
            value_info = winreg.EnumValue(key_handle, i)
            if value_info[0] == "Joystick Gremlin":
                return True
        return False

    def _highlight_input(self, clicked):
        """Stores preference for input highlighting.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.highlight_input = clicked
        self.config.save()

    def _highlight_device(self, clicked):
        """Stores preference for device highlighting.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.highlight_device = clicked
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
        else:
            self.executable_selection.setCurrentIndex(
                self.executable_selection.findText(fname)
            )

    def _edit_executable(self):
        """Allows editing the path of an executable."""
        new_text, flag = QtWidgets.QInputDialog.getText(
            self,
            "Change Executable / RegExp",
            "Change the executable text or enter a regular expression to use.",
            QtWidgets.QLineEdit.Normal,
            self.executable_selection.currentText()
        )

        # If the user did click on ok update the entry
        old_entry = self.executable_selection.currentText()
        if flag:
            if old_entry not in self.config.get_executable_list():
                self._add_executable(new_text)
            else:
                self.config.set_profile(
                    new_text,
                    self.config.get_profile(old_entry)
                )
                self.config.remove_profile(old_entry)
                self.populate_executables(new_text)

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

    def _macro_axis_polling_rate(self, value):
        """Updates the config with the newly set polling rate.

        :param value the new polling rate
        """
        self.config.macro_axis_polling_rate = value
        self.config.save()

    def _macro_axis_minimum_change_value(self, value):
        """Updates the config with the newly set minimum change value.

        :param value the new minimum change value
        """
        self.config.macro_axis_minimum_change_rate = value

    def _create_hg_cb(self, *params):
        return lambda x: self._update_hg_device(x, *params)

    def _update_hg_device(self, state, device):
        hg = gremlin.hid_guardian.HidGuardian()
        if state == QtCore.Qt.Checked:
            hg.add_device(device.vendor_id, device.product_id)
        else:
            hg.remove_device(device.vendor_id, device.product_id)


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

        self.ui.about.setHtml(
            open(gremlin.util.resource_path("about/about.html")).read()
        )

        self.ui.jg_license.setHtml(
            open(gremlin.util.resource_path("about/joystick_gremlin.html")).read()
        )

        license_list = [
            "about/third_party_licenses.html",
            "about/modernuiicons.html",
            "about/pyqt.html",
            "about/pywin32.html",
            "about/qt5.html",
            "about/reportlab.html",
            "about/vjoy.html",
        ]
        third_party_licenses = ""
        for fname in license_list:
            third_party_licenses += open(gremlin.util.resource_path(fname)).read()
            third_party_licenses += "<hr>"
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
        self.main_layout.addStretch()
        self.add_button = QtWidgets.QPushButton("Add Mode")
        self.add_button.clicked.connect(self._add_mode_cb)

        label = QtWidgets.QLabel(
            "Modes are by default self contained configurations. Specifying "
            "a parent for a mode causes the the mode \"inherits\" all actions "
            "defined in the parent, unless the mode configures its own actions "
            "for specific inputs."
        )
        label.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
        label.setWordWrap(True)
        label.setFrameShape(QtWidgets.QFrame.Box)
        label.setMargin(10)
        self.main_layout.addWidget(label)

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

        # Add header information
        self.mode_layout.addWidget(QtWidgets.QLabel("<b>Name</b>"), 0, 0)
        self.mode_layout.addWidget(QtWidgets.QLabel("<b>Parent</b>"), 0, 1)

        # Create UI element for each mode
        row = 1
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
                device.ensure_mode_exists(mode)
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


class DeviceInformationUi(common.BaseDialogUi):

    """Widget which displays information about all connected joystick
    devices."""

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent widget
        """
        super().__init__(parent)

        self.devices = gremlin.joystick_handling.joystick_devices()

        self.setWindowTitle("Device Information")
        self.main_layout = QtWidgets.QGridLayout(self)

        self.main_layout.addWidget(QtWidgets.QLabel("<b>Name</b>"), 0, 0)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Axes</b>"), 0, 1)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Buttons</b>"), 0, 2)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Hats</b>"), 0, 3)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Vendor ID</b>"), 0, 4)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Product ID</b>"), 0, 5)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>GUID"), 0, 6)

        for i, entry in enumerate(self.devices):
            self.main_layout.addWidget(
                QtWidgets.QLabel(entry.name), i+1, 0
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.axis_count)), i+1, 1
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.button_count)), i+1, 2
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.hat_count)), i+1, 3
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel("{:04X}".format(entry.vendor_id)), i+1, 4
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel("{:04X}".format(entry.product_id)), i+1, 5
            )
            guid_field = QtWidgets.QLineEdit()
            guid_field.setText(str(entry.device_guid))
            guid_field.setReadOnly(True)
            guid_field.setMinimumWidth(230)
            guid_field.setMaximumWidth(230)
            self.main_layout.addWidget(guid_field, i+1, 6)

        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(lambda: self.close())
        self.main_layout.addWidget(self.close_button, len(self.devices)+1, 3)


class SwapDevicesUi(common.BaseDialogUi):

    """UI Widget that allows users to swap identical devices."""

    def __init__(self, profile, parent=None):
        """Creates a new instance.

        :param profile the current profile
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.profile = profile

        # Create UI elements
        self.setWindowTitle("Swap Devices")
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self._create_swap_ui()

    def _create_swap_ui(self):
        """Displays possible groups of swappable devices."""
        common.clear_layout(self.main_layout)

        profile_modifier = gremlin.profile.ProfileModifier(self.profile)
        device_list = profile_modifier.device_information_list()

        device_layout = QtWidgets.QGridLayout()
        for i, data in enumerate(device_list):
            # Ignore the keyboard
            if data.device_guid == dill.GUID_Keyboard:
                continue

            # Ignore devices with no remappable entries
            if (data.containers + data.conditions + data.merge_axis) == 0:
                continue

            # UI elements for this devic
            name = QtWidgets.QLabel(data.name)
            name.setAlignment(QtCore.Qt.AlignTop)
            labels = QtWidgets.QLabel("Containers\nConditions\nMerge Axis")
            counts = QtWidgets.QLabel("{:d}\n{:d}\n{:d}".format(
                data.containers, data.conditions, data.merge_axis
            ))
            counts.setAlignment(QtCore.Qt.AlignRight)
            record_button = QtWidgets.QPushButton(
                "Assigned to: {} - {}".format(data.device_guid, data.name)
            )
            record_button.clicked.connect(
                self._create_request_user_input_cb(data.device_guid)
            )

            # Combine labels and counts into it's own layout
            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(labels)
            layout.addWidget(counts)
            layout.addStretch()

            # Put everything together
            device_layout.addWidget(name, i, 0)
            device_layout.addLayout(layout, i, 1)
            device_layout.addWidget(record_button, i, 2, QtCore.Qt.AlignTop)

        self.main_layout.addLayout(device_layout)
        self.main_layout.addStretch()

    def _create_request_user_input_cb(self, device_guid):
        """Creates the callback handling user device selection.

        :param device_guid GUID of the associated device
        :return callback function for user input selection handling
        """
        return lambda: self._request_user_input(
            lambda event: self._user_input_cb(event, device_guid)
        )

    def _user_input_cb(self, event, device_guid):
        """Processes input events to update the UI and model.

        :param event the input event to process
        :param device_guid GUID of the selected device
        """
        profile_modifier = gremlin.profile.ProfileModifier(self.profile)
        profile_modifier.change_device_guid(
            device_guid,
            event.device_guid
        )

        self._create_swap_ui()

    def _request_user_input(self, callback):
        """Prompts the user for the input to bind to this item.

        :param callback function to call with the accepted input
        """
        self.input_dialog = common.InputListenerWidget(
            callback,
            [
                gremlin.common.InputType.JoystickAxis,
                gremlin.common.InputType.JoystickButton,
                gremlin.common.InputType.JoystickHat
            ],
            return_kb_event=False,
            multi_keys=False
        )

        # Display the dialog centered in the middle of the UI
        root = self
        while root.parent():
            root = root.parent()
        geom = root.geometry()

        self.input_dialog.setGeometry(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
            300,
            150
        )
        self.input_dialog.show()

class BindingExportUi(common.BaseDialogUi):

    """UI allowing user to export current bindings to game-specific file."""

    def __init__(self, profile_data, parent=None):
        """Creates a new exporter UI instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        # Actual configuration object being managed
        self.config = gremlin.config.Configuration()
        self._profile = profile_data
        self.setMinimumWidth(400)
        self.setWindowTitle("Binding Export")

        # create exporter dialog
        self._exporter_module = None
        self._create_ui()

    def _create_ui(self):
        """Creates the binding exporter page."""
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # edit in place option
        self.overwrite_checkbox = QtWidgets.QCheckBox(
            "Overwrite Config Template on Export"
        )
        self.overwrite_checkbox.clicked.connect(self._overwrite_template)

        # exporter dropdown list
        self.exporter_layout = QtWidgets.QHBoxLayout()
        self.exporter_label = QtWidgets.QLabel("Exporter")
        self.exporter_selection = QtWidgets.QComboBox()
        self.exporter_selection.setMinimumWidth(300)
        self.exporter_selection.currentTextChanged.connect(self._select_exporter)
        self.exporter_add = QtWidgets.QPushButton()
        self.exporter_add.setIcon(QtGui.QIcon("gfx/button_add.png"))
        self.exporter_add.setToolTip("Add custom exporter script to config")
        self.exporter_add.clicked.connect(self._new_exporter)
        self.exporter_remove = QtWidgets.QPushButton()
        self.exporter_remove.setIcon(QtGui.QIcon("gfx/button_delete.png"))
        self.exporter_add.setToolTip("Remove custom exporter script from config")
        self.exporter_remove.clicked.connect(self._remove_exporter)
        self.exporter_edit = QtWidgets.QPushButton()
        self.exporter_edit.setIcon(QtGui.QIcon("gfx/button_edit.png"))
        self.exporter_add.setToolTip("Edit saved exporter script path")
        self.exporter_edit.clicked.connect(self._edit_exporter)

        self.exporter_layout.addWidget(self.exporter_label)
        self.exporter_layout.addWidget(self.exporter_selection)
        self.exporter_layout.addWidget(self.exporter_add)
        self.exporter_layout.addWidget(self.exporter_remove)
        self.exporter_layout.addWidget(self.exporter_edit)
        self.exporter_layout.addStretch()

        # arguments text field
        self.args_layout = QtWidgets.QHBoxLayout()
        self.args_label = QtWidgets.QLabel("Arguments")
        self.args_field = QtWidgets.QLineEdit()
        self.args_field.setToolTip("POSIX-style arguments to pass to selected exporter")
        self.args_field.textEdited.connect(self._update_args)

        self.args_layout.addWidget(self.args_label)
        self.args_layout.addWidget(self.args_field)

        # exporter template text field
        self.template_layout = QtWidgets.QHBoxLayout()
        self.template_label = QtWidgets.QLabel("Config Template")
        self.template_field = QtWidgets.QLineEdit()
        self.template_field.setToolTip("Output file template to use")
        self.template_field.textChanged.connect(self._update_template)
        self.template_select = QtWidgets.QPushButton()
        self.template_select.setIcon(QtGui.QIcon("gfx/button_edit.png"))
        self.template_select.clicked.connect(self._select_template)

        self.template_layout.addWidget(self.template_label)
        self.template_layout.addWidget(self.template_field)
        self.template_layout.addWidget(self.template_select)

        self.main_layout.addWidget(self.overwrite_checkbox)
        self.main_layout.addLayout(self.exporter_layout)
        self.main_layout.addLayout(self.args_layout)
        self.main_layout.addLayout(self.template_layout)
        self.main_layout.addStretch()

        self.exporter_help = QtWidgets.QLabel("")
        self.exporter_help.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
        self.exporter_help.setWordWrap(True)
        self.exporter_help.setFrameShape(QtWidgets.QFrame.Box)
        self.exporter_help.setMargin(10)
        self.main_layout.addWidget(self.exporter_help)

        self.export_button = QtWidgets.QPushButton("Export")
        self.export_button.clicked.connect(self._run_exporter)
        self.main_layout.addWidget(self.export_button)

        # pre-populate profile and config setttings, if any
        self.populate_exporters(self._profile.settings.exporter_path)
        self.template_field.setText(self._profile.settings.exporter_template_path)
        self.args_field.setText(self._profile.settings.exporter_arg_string)
        self.overwrite_checkbox.setChecked(self.config.overwrite_exporter_template)

    def closeEvent(self, event):
        """Closes the calibration window.

        :param event the close event
        """
        super().closeEvent(event)

    def populate_exporters(self, exporter_path=""):
        """Populates the exporter drop down menu.

        Menu begins with empty entry, then valid custom exporters in alphabetical order,
        then built-in exporters in alphabetical order.

        :param exporter_path name of the exporter to pre select, if any
        """
        self.exporter_selection.clear()
        self.exporter_selection.addItem("")
        exporter_list = self.config.get_exporter_list()
        for path in exporter_list:
            if os.path.isfile(path):
                self.exporter_selection.addItem(path)
            else:
                msg = "Could not find custom exporter '{}'. Removed from config.".format(path)
                self.config.remove_exporter(path)
                logging.getLogger("system").warning(msg)
        for path in self._discover_exporters():
            self.exporter_selection.addItem(path)

        # Select the provided executable if it exists
        # otherwise the first one in the list
        index = max(0, self.exporter_selection.findText(exporter_path))
        self.exporter_selection.setCurrentIndex(index)

    def _discover_exporters(self):
        """Find builtin exporter scripts"""

        exporters_list = []
        for root, dirs, files in os.walk("exporter_plugins"):
            for file in files:
                if os.path.splitext(file)[1] == ".py":
                    exporters_list.append(os.path.join(root,file))

        return sorted(
            exporters_list,
            key=lambda x: x.lower()
            )

    def _select_exporter(self, exporter_path):
        """React to exporter selection by user"""

        self._profile.settings.exporter_path = exporter_path

        # load module spec from path, if any
        # reject exporter if no 'main' function defined
        if exporter_path:
            exporter_spec = importlib.util.spec_from_file_location("gremlin_binding_export", exporter_path)
            self._exporter_module = importlib.util.module_from_spec(exporter_spec)
            exporter_spec.loader.exec_module(self._exporter_module)
            try:
                if not callable(self._exporter_module.main):
                    raise AttributeError()
            except AttributeError:
                msg = ("Invalid exporter!\n"
                       "EntryPointError: exporter module '{}' "
                       "does not contain an entry point function 'main'"
                      ).format(exporter_path)
                gremlin.util.display_error(msg)
                self.exporter_selection.setCurrentIndex(0)
                return
        else:
            self._exporter_module = None
        
        self._show_help(self._exporter_module)
        self._update_button_status()

    def _add_exporter(self, fname):
        """Adds the provided exporter to the list of configurations.

        :param fname the exporter script path
        """
        if fname not in self.config.get_exporter_list():
            self.config.add_exporter(fname)
            self.populate_exporters(fname)
        else:
            self.exporter_selection.setCurrentIndex(
                self.exporter_selection.findText(fname)
            )

    def _edit_exporter(self):
        """Allows editing the path of an exporter."""
        new_text, flag = QtWidgets.QInputDialog.getText(
            self,
            "Change exporter",
            "Change the exporter path entry.",
            QtWidgets.QLineEdit.Normal,
            self.exporter_selection.currentText()
        )

        # if the user did click on ok and entry is valid
        # try to remove existing entry, add new entry
        if flag:
            if not os.path.isfile(new_text):
                logging.getLogger("system").warning("Could not find exporter at {}! Ignoring".format(new_text))
            elif os.path.splitext(new_text)[1] == ".py":
                logging.getLogger("system").warning("Exporter at {} is not a valid python file! Ignoring".format(new_text))
            else:
                self.config.remove_exporter(self.exporter_selection.currentText())
                self._add_exporter(new_text)

    def _new_exporter(self):
        """Prompts the user to select a new exporter to add to the
        profile.
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Path to Exporter",
            gremlin.util.userprofile_path(),
            "Exporter Script (*.py)"
        )
        if fname != "":
            self._add_exporter(fname)

    def _remove_exporter(self):
        """Removes the current executable from the configuration."""
        self.config.remove_exporter(self.exporter_selection.currentText())
        self.populate_exporters()

    def _show_help(self, module):
        """Show selected exporter help"""

        # get docstring, if module selected
        if module is not None:
            docstring = getdoc(module)
        else:
            docstring = (
                "Exporters print VJoy bindings to a game-specific configuration file. "
                "Optional arguments may be passed to the exporter function above. "
                "Help for the selected exporter is listed in this dialog once an "
                "exporter is selected.\n\nFor more information about custom exporters "
                "see 'exporter_plugins/README.md' in your Joystick Gremlin install "
                "directory."
                )
            
        # if non-empty docstring, unwrap paragraph blocks for textbox wrapping
        if not docstring.strip():
            self.exporter_help.setText("Selected exporter has no docstring.")
        else: 
            wrap_friendly_doc = re.sub(r"(?<=.) *\n(?=\S)", " ", docstring)
            self.exporter_help.setText(wrap_friendly_doc)
            
    def _update_button_status(self):
        """Enable/disable buttons based on current exporter selection"""
        
        # enable edit/remove for custom exporters only
        is_custom = self.exporter_selection.currentText() in self.config.get_exporter_list()
        if self.exporter_selection.currentText() and is_custom:
            self.exporter_edit.setEnabled(True)
            self.exporter_remove.setEnabled(True)
        else:
            self.exporter_edit.setEnabled(False)
            self.exporter_remove.setEnabled(False)
            
        # enable export button if a valid exporter and template are selected
        if self._exporter_module is None:
            self.export_button.setEnabled(False)
            self.export_button.setToolTip("Select an Exporter and Config Template first!")
        elif not os.path.isfile(self.template_field.text()):
            self.export_button.setEnabled(False)
            self.export_button.setToolTip("Config Template not found!")
        else:
            self.export_button.setEnabled(True)
            self.export_button.setToolTip("Export current bindings using selected Exporter")

    def _run_exporter(self):
        """Execute selected exporter with optional args"""

        # reload module now, in case user has changed module since initial selection
        self._exporter_module.__loader__.exec_module(self._exporter_module)
        self._show_help(self._exporter_module)

        # try to run the exporter
        # display full trace for non-gremlin errors
        template_path = self._profile.settings.exporter_template_path
        try:
            template_fid = open(template_path, 'r')
            logging.getLogger("system").debug((
                "Template '{:s}' found! Preparing binding export with '{:s}'..."
                ).format(template_path, self._exporter_module.__file__)
            )
            outfile = self._exporter_module.main(
                copy.deepcopy(self._profile.get_all_bound_vjoys()),
                template_fid.readlines(),
                self._profile.settings.exporter_arg_string
                )
        except gremlin.error.GremlinError as e:
            msg = "Failed to export!\n"
            msg += e.value
            gremlin.util.display_error(msg)
            return
        except Exception as e:
            msg = "Failed to export!\n"
            msg += " ".join(traceback.format_exception(*sys.exc_info()))
            gremlin.util.display_error(msg)
            return
        finally:
            template_fid.close()

        # write to template in-place or prompt for new file
        if self.config.overwrite_exporter_template:
            fname = template_path
        else:
            fname, _ = QtWidgets.QFileDialog.getSaveFileName(
                None,
                "Save As",
                template_path,
                self._template_filter
                )
            
        # try to write to file
        if fname != "":
            try:
                fid = open(fname, "w")
                logging.getLogger("system").debug((
                    "Attempting to write bindings to '{:s}'..."
                    ).format(fname)
                )
                fid.writelines(outfile)
                logging.getLogger("system").debug("Binding export complete!")
            except Exception as e:
                msg = "Failed to write to {}!".format(fname)
                msg += " ".join(traceback.format_exception(*sys.exc_info()))
                gremlin.util.display_error(msg)
            finally:
                fid.close()

    def _update_args(self, arg_string):
        """Stores exporter argument string.

        :param arg_string POSIX-style command-line arg string
        """
        self._profile.settings.exporter_arg_string = arg_string

    def _overwrite_template(self, clicked):
        """Stores config exporter template overwrite preference.

        :param clicked whether or not the checkbox is ticked
        """
        self.config.overwrite_exporter_template = clicked

    def _select_template(self):
        """Displays file selection dialog for an exporter template file.

        If a valid file is selected, the template path is saved to profile.
        """

        # load dialog with file filter
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Select Export Template",
            gremlin.util.userprofile_path(),
            self._template_filter
        )
        if fname != "":
            self.template_field.setText(fname)
            # note save to profile handled by _update_template on text change
            
    @property
    def _template_filter(self):
        """Return QFileDialog filter string from selected exporter, if any
        
        Assembles from "template_filter" in current exporter. Always allows
        for All Files by default.
        
        Per QFileDialog docs:
        - File type filters included in parentheses
        - Entries are separated by ";;"
        
        :return filter string for QFileDialog
        """
        
        # search for "template_filter" defined in current exporter, if any
        file_filter = "All Files (*.*)"
        if self._exporter_module is not None:
            try: 
                # re-load module in case user has edited it after selection
                self._exporter_module.__loader__.exec_module(self._exporter_module)
                file_filter = "{};;{}".format(self._exporter_module.template_filter, file_filter)
            except:
                msg = "Expected var 'template_filter' not defined in {}!".format(self._exporter_module.__file__)
                logging.getLogger("system").warning(msg)
        return file_filter

    def _update_template(self, new_path):
        """Updates the exporter template path"""
        self._profile.settings.exporter_template_path = new_path
        self._update_button_status()

class BindingImportUi(common.BaseDialogUi):

    """UI allowing user to import binding settings from game-specific file."""
    
    # Signal emitted when importer completed to trigger UI refresh
    bindings_changed = QtCore.pyqtSignal()

    def __init__(self, profile_data, parent=None):
        """Creates a new importer UI instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        # Actual configuration object being managed
        self.config = gremlin.config.Configuration()
        self._profile = profile_data
        self.setMinimumWidth(400)
        self.setWindowTitle("Binding Import")
        
        # define possible importer overwrite options
        self._overwrite_options = [
            "clear-all", 
            "overwrite", 
            "preserve",
            ]

        # create importer dialog
        self._importer_module = None
        self._create_ui()

    def _create_ui(self):
        """Creates the binding importer page."""
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # overwrite options radio dials
        self.button_layout = QtWidgets.QVBoxLayout()
        self.button_group_label = QtWidgets.QLabel("Import conflict resolution")
        self.button_group = QtWidgets.QButtonGroup()
        self.button_group.idClicked.connect(self._select_overwrite_option)
        
        clear_button = QtWidgets.QRadioButton("Clear all existing")
        clear_button.setToolTip("Remove all bindings and binding "
                                "descriptions from current profile "
                                "before applying bindings from file"
                                )
        self.button_group.addButton(
            clear_button, 
            self._overwrite_options.index("clear-all")
            )
        
        overwrite_button = QtWidgets.QRadioButton("Overwrite conflicts")
        overwrite_button.setToolTip("Imported VJoy ID and Input ID binding "
                                    "assignments are prioritized; conflicting "
                                    "binding assignments in current "
                                    "profile will be cleared"
                                    )
        self.button_group.addButton(
            overwrite_button, 
            self._overwrite_options.index("overwrite")
            )
        
        preserve_button = QtWidgets.QRadioButton("Preserve existing")
        preserve_button.setToolTip("All imported VJoy ID and Input ID "
                                   "assignments are ignored; existing "
                                   "binding assignments in current "
                                   "profile will not be modified"
                                    )
        self.button_group.addButton(
            preserve_button, 
            self._overwrite_options.index("preserve")
            )
        
        self.button_layout.addWidget(self.button_group_label)
        self.button_layout.addWidget(overwrite_button)
        self.button_layout.addWidget(preserve_button)
        self.button_layout.addWidget(clear_button)

        # importer dropdown list
        self.importer_layout = QtWidgets.QHBoxLayout()
        self.importer_label = QtWidgets.QLabel("Importer")
        self.importer_selection = QtWidgets.QComboBox()
        self.importer_selection.setMinimumWidth(300)
        self.importer_selection.currentTextChanged.connect(self._select_importer)
        self.importer_add = QtWidgets.QPushButton()
        self.importer_add.setIcon(QtGui.QIcon("gfx/button_add.png"))
        self.importer_add.setToolTip("Add custom importer script to config")
        self.importer_add.clicked.connect(self._new_importer)
        self.importer_remove = QtWidgets.QPushButton()
        self.importer_remove.setIcon(QtGui.QIcon("gfx/button_delete.png"))
        self.importer_add.setToolTip("Remove custom importer script from config")
        self.importer_remove.clicked.connect(self._remove_importer)
        self.importer_edit = QtWidgets.QPushButton()
        self.importer_edit.setIcon(QtGui.QIcon("gfx/button_edit.png"))
        self.importer_add.setToolTip("Edit saved importer script path")
        self.importer_edit.clicked.connect(self._edit_importer)

        self.importer_layout.addWidget(self.importer_label)
        self.importer_layout.addWidget(self.importer_selection)
        self.importer_layout.addWidget(self.importer_add)
        self.importer_layout.addWidget(self.importer_remove)
        self.importer_layout.addWidget(self.importer_edit)
        self.importer_layout.addStretch()

        # arguments text field
        self.args_layout = QtWidgets.QHBoxLayout()
        self.args_label = QtWidgets.QLabel("Arguments")
        self.args_field = QtWidgets.QLineEdit()
        self.args_field.setToolTip("POSIX-style arguments to pass to selected importer")
        self.args_field.textEdited.connect(self._update_args)

        self.args_layout.addWidget(self.args_label)
        self.args_layout.addWidget(self.args_field)

        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.importer_layout)
        self.main_layout.addLayout(self.args_layout)
        self.main_layout.addStretch()

        self.importer_help = QtWidgets.QLabel("")
        self.importer_help.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
        self.importer_help.setWordWrap(True)
        self.importer_help.setFrameShape(QtWidgets.QFrame.Box)
        self.importer_help.setMargin(10)
        self.main_layout.addWidget(self.importer_help)

        self.import_button = QtWidgets.QPushButton("Import")
        self.import_button.clicked.connect(self._run_importer)
        self.main_layout.addWidget(self.import_button)

        # pre-populate profile and config settings, if any
        self.populate_importers(self._profile.settings.importer_path)
        self.args_field.setText(self._profile.settings.importer_arg_string)
        self.button_group.button(
            self._overwrite_options.index(self._overwrite)
            ).setChecked(True)

    def closeEvent(self, event):
        """Closes the calibration window.

        :param event the close event
        """
        super().closeEvent(event)

    def populate_importers(self, importer_path=""):
        """Populates the importer drop down menu.

        Menu begins with empty entry, then valid custom importers in alphabetical order,
        then built-in importers in alphabetical order.

        :param importer_path name of the importer to pre select, if any
        """
        self.importer_selection.clear()
        self.importer_selection.addItem("")
        importer_list = self.config.get_importer_list()
        for path in importer_list:
            if os.path.isfile(path):
                self.importer_selection.addItem(path)
            else:
                msg = "Could not find custom importer '{}'. Removed from config.".format(path)
                self.config.remove_importer(path)
                logging.getLogger("system").warning(msg)
        for path in self._discover_importers():
            self.importer_selection.addItem(path)

        # Select the provided executable if it exists
        # otherwise the first one in the list
        index = max(0, self.importer_selection.findText(importer_path))
        self.importer_selection.setCurrentIndex(index)

    def _discover_importers(self):
        """Find builtin importer scripts"""

        importers_list = []
        for root, dirs, files in os.walk("importer_plugins"):
            for file in files:
                if os.path.splitext(file)[1] == ".py":
                    importers_list.append(os.path.join(root,file))

        return sorted(
            importers_list,
            key=lambda x: x.lower()
            )

    def _select_importer(self, importer_path):
        """React to importer selection by user"""

        self._profile.settings.importer_path = importer_path

        # load module spec from path, if any
        # reject importer if no 'main' function defined
        if importer_path:
            importer_spec = importlib.util.spec_from_file_location("gremlin_binding_import", importer_path)
            self._importer_module = importlib.util.module_from_spec(importer_spec)
            importer_spec.loader.exec_module(self._importer_module)
            try:
                if not callable(self._importer_module.main):
                    raise AttributeError()
            except AttributeError:
                msg = ("Invalid importer!\n"
                       "EntryPointError: importer module '{}' "
                       "does not contain an entry point function 'main'"
                      ).format(importer_path)
                gremlin.util.display_error(msg)
                self.importer_selection.setCurrentIndex(0)
                return
        else:
            self._importer_module = None
        
        self._show_help(self._importer_module)
        self._update_button_status()

    def _add_importer(self, fname):
        """Adds the provided importer to the list of configurations.

        :param fname the importer script path
        """
        if fname not in self.config.get_importer_list():
            self.config.add_importer(fname)
            self.populate_importers(fname)
        else:
            self.importer_selection.setCurrentIndex(
                self.importer_selection.findText(fname)
            )

    def _edit_importer(self):
        """Allows editing the path of an importer."""
        new_text, flag = QtWidgets.QInputDialog.getText(
            self,
            "Change importer",
            "Change the importer path entry.",
            QtWidgets.QLineEdit.Normal,
            self.importer_selection.currentText()
        )

        # if the user did click on ok and entry is valid
        # try to remove existing entry, add new entry
        if flag:
            if not os.path.isfile(new_text):
                logging.getLogger("system").warning("Could not find importer at {}! Ignoring".format(new_text))
            elif os.path.splitext(new_text)[1] == ".py":
                logging.getLogger("system").warning("Importer at {} is not a valid python file! Ignoring".format(new_text))
            else:
                self.config.remove_importer(self.importer_selection.currentText())
                self._add_importer(new_text)

    def _new_importer(self):
        """Prompts the user to select a new importer to add to the
        profile.
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Path to Importer",
            gremlin.util.userprofile_path(),
            "Importer Script (*.py)"
        )
        if fname != "":
            self._add_importer(fname)

    def _remove_importer(self):
        """Removes the current executable from the configuration."""
        self.config.remove_importer(self.importer_selection.currentText())
        self.populate_importers()

    def _show_help(self, module):
        """Show selected importer help"""

        # get docstring, if module selected
        if module is not None:
            docstring = getdoc(module)
        else:
            docstring = (
                "Importers populate bindings from file to the current profile. "
                "Optional arguments may be passed to the importer function above. "
                "Help for the selected importer is listed in this dialog once an "
                "importer is selected. The profile is only modified if no errors "
                "occur during import.\n\nFor more information about custom importers "
                "see 'import_plugins/README.md' in your Joystick Gremlin install "
                "directory."
                )
       
        # if non-empty docstring, unwrap paragraph blocks for textbox wrapping
        if not docstring.strip():
            self.importer_help.setText("Selected importer has no docstring.")
        else: 
            wrap_friendly_doc = re.sub(r"(?<=.) *\n(?=\S)", " ", docstring)
            self.importer_help.setText(wrap_friendly_doc)
            
    def _update_button_status(self):
        """Enable/disable buttons based on current importer selection"""
        
        # enable edit/remove for custom importers only
        is_custom = self.importer_selection.currentText() in self.config.get_importer_list()
        if self.importer_selection.currentText() and is_custom:
            self.importer_edit.setEnabled(True)
            self.importer_remove.setEnabled(True)
        else:
            self.importer_edit.setEnabled(False)
            self.importer_remove.setEnabled(False)
            
        # enable import button if a valid importer is selected
        if self._importer_module is None:
            self.import_button.setEnabled(False)
            self.import_button.setToolTip("Select an Importer first!")
        else:
            self.import_button.setEnabled(True)
            self.import_button.setToolTip("Import bindings from file using selected Importer")

    def _run_importer(self):
        """Execute selected importer with optional args"""

        # reload module now, in case user has changed module since initial selection
        self._importer_module.__loader__.exec_module(self._importer_module)
        self._show_help(self._importer_module)
        
        # prompt for file to import; return if none given
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Open file for import",
            gremlin.util.userprofile_path(),
            self._import_filter
            )
        if fname == "":
            return

        # try to run the importer
        # display full trace for non-gremlin importer errors
        try:
            fid = open(fname, 'r')
            logging.getLogger("system").debug((
                "File '{:s}' found! Attempting to import bindings with '{:s}'..."
                ).format(fname, self._importer_module.__file__)
            )
            bindings = self._importer_module.main(
                fid.readlines(),
                self._profile.settings.importer_arg_string
                )
        except gremlin.error.GremlinError as e:
            msg = "Failed to import! Profile has not been modified.\n"
            msg += e.value
            gremlin.util.display_error(msg)
            return
        except Exception as e:
            msg = "Failed to import! Profile has not been modified.\n"
            msg += " ".join(traceback.format_exception(*sys.exc_info()))
            gremlin.util.display_error(msg)
            return
        finally:
            fid.close()
            
        # validate imported bindings
        try:
            logging.getLogger("system").debug("Validating imported bindings...")
            bindings = self._validate_import(bindings)
        except gremlin.error.GremlinError as e:
            msg = "Failed to import! Profile has not been modified.\n"
            msg += e.value
            gremlin.util.display_error(msg)
            return
        
        # apply imported bindings to profile
        # report if errors or warnings were encountered
        if self._overwrite == "clear-all":
            logging.getLogger("system").debug("Cleaning existing bindings as requested...")
            self._profile.clear_device_bindings()
        logging.getLogger("system").debug("Applying bindings to profile...")
        count = self._profile.update_bound_vjoy_registry_from_dict(bindings)
        nErrors = count["error"]
        nWarnings = count["warning"]
        if nErrors > 0:
            logging.getLogger("system").debug("Binding import finished with errors!")
            gremlin.util.display_error((
                "At least one binding could not be assigned!\n"
                "\tNumber of missing bindings: \t{:d}\n"
                "\tNumber of reassigned bindings: \t{:d}\n"
                "An additional VJoy device may be needed. "
                "Review system log for details before saving profile changes."
                ).format(nErrors, nWarnings))
        elif nWarnings > 0:
            logging.getLogger("system").debug("Binding import finished with warnings!")
            gremlin.util.display_error((
                "At least one binding was reassigned!\n"
                "\tNumber of missing bindings: \t{:d}\n"
                "\tNumber of reassigned bindings: \t{:d}\n"
                "Available VJoy axes/buttons may not match expected. "
                "Review system log for details before saving profile changes."
                ).format(nErrors, nWarnings))
        else:
            logging.getLogger("system").debug("Binding import finished successfully!")
            
        # emit mode change to trigger UI update
        self.bindings_changed.emit()
    
    def _validate_import(self, bindings):
        """Check for errors in binding import"""
        
        valid = {}
        for input_name, assignments in bindings.items():
            
            # check input_name is valid input_type
            try:
                input_type = gremlin.common.InputType.to_enum(input_name)
            except gremlin.error.GremlinError:
                msg = (("Importer returned unknown input type {}."
                       ).format(input_name))
                raise gremlin.error.ImporterError(msg)
            valid[input_type] = {}
            
            # validate each binding assignment
            for binding, assignment in assignments.items():
                try:
                    binding = str(binding)
                    input_id = str(assignment["input_id"])
                    device_id = str(assignment["device_id"])
                    description = str(assignment["description"])
                except KeyError:
                    msg = (("Missing expected assignment attribute. "
                            "Check 'description', 'device_id', and 'input_id' "
                            "are present dictionary keys for '{:s}'").format(binding))
                    raise gremlin.error.ImporterError(msg)
                try:
                    if input_id:
                        input_id = int(input_id)
                    if device_id:
                        device_id = int(device_id)
                except ValueError:
                    msg = (("Could not cast 'device_id' and/or 'input_id' values to int. "
                            "Check assignments for '{:s}'").format(binding))
                    raise gremlin.error.ImporterError(msg)
                valid[input_type][binding] = {}
                valid[input_type][binding]["description"] = description
                if self._overwrite != "preserve" and device_id and input_id:
                    valid[input_type][binding]["device_id"] = device_id
                    valid[input_type][binding]["input_id"] = input_id
                if input_id and not device_id:
                    logging.getLogger("system").warning((
                        "No target VJoy device specified for '{:s}'! "
                        "Replacing assigned VJoy and input id with first unbound."
                        ).format(binding)
                    )
                if device_id and not input_id:
                    logging.getLogger("system").warning((
                        "No target input id specified for '{:s}'! "
                        "Replacing assigned VJoy and input id with first unbound."
                        ).format(binding)
                    )
        return valid

    def _update_args(self, arg_string):
        """Stores importer argument string.

        :param arg_string POSIX-style command-line arg string
        """
        self._profile.settings.importer_arg_string = arg_string

    def _select_overwrite_option(self, clicked_id):
        """Stores import conflict resolution option to config.

        :param clicked_id Button id for selected option
        """
        self.config.overwrite_on_import = self._overwrite_options[clicked_id]
        
    @property
    def _overwrite(self):
        """Return current overwrite option
        
        Defaults to first option from list if invalid flag given
        
        :return option string stored in config
        """
        flag = self.config.overwrite_on_import
        if flag not in self._overwrite_options:
            flag = self._overwrite_options[0]
        return flag

    @property
    def _import_filter(self):
        """Return QFileDialog filter string from selected importer, if any
        
        Assembles from "import_filter" in current importer. Always allows
        for All Files by default.
        
        Per QFileDialog docs:
        - File type filters included in parentheses
        - Entries are separated by ";;"
        
        :return filter string for QFileDialog
        """
        
        # search for "import_filter" defined in current importer, if any
        file_filter = "All Files (*.*)"
        if self._importer_module is not None:
            try: 
                # re-load module in case user has edited it after selection
                self._importer_module.__loader__.exec_module(self._importer_module)
                file_filter = "{};;{}".format(self._importer_module.import_filter, file_filter)
            except:
                msg = "Expected var 'import_filter' not defined in {}!".format(self._importer_module.__file__)
                logging.getLogger("system").warning(msg)
        return file_filter
