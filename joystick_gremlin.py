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

"""
Main UI of JoystickGremlin.
"""

import ctypes
import logging
import os
import sys
import time
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets

os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(os.path.realpath(sys.argv[0]))
import sdl2.hints

import gremlin
from gremlin.code_runner import CodeRunner
from gremlin.code_generator import CodeGenerator
from gremlin.common import UiInputType
from gremlin.event_handler import EventListener, InputType
from gremlin.repeater import Repeater

import gremlin.ui_widgets as widgets
import gremlin.ui_dialogs as dialogs
import gremlin.util as util

from ui_gremlin import Ui_Gremlin


class GremlinUi(QtWidgets.QMainWindow):

    """Main window of the Joystick Gremlin user interface."""

    def __init__(self, parent=None):
        """Creates a new main ui window.

        :param parent the parent of this window
        """
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_Gremlin()
        self.ui.setupUi(self)

        # Process monitor
        self.process_monitor = gremlin.process_monitor.ProcessMonitor()
        self.process_monitor.process_changed.connect(
            self._process_changed_cb
        )

        # Default path variable before any runtime changes
        self._base_path = list(sys.path)

        self.tabs = {}
        self.config = gremlin.config.Configuration()
        self.devices = util.joystick_devices()
        self.runner = CodeRunner()
        self.repeater = Repeater([], self._update_statusbar_repeater)
        self.runner.event_handler.mode_changed.connect(
            self._update_statusbar_mode
        )
        self.runner.event_handler.is_active.connect(
            self._update_statusbar_active
        )

        self.mode_selector = widgets.ModeWidget()
        self.mode_selector.mode_changed.connect(self._mode_changed_cb)

        self.ui.toolBar.addWidget(self.mode_selector)

        # Setup profile storage
        self._current_mode = None
        self._profile = gremlin.profile.Profile()
        self._profile_fname = None
        self._profile_auto_activated = False
        # Input selection storage
        self._last_input_timestamp = time.time()
        self._last_input_event = None

        # Create all required UI elements
        self._create_system_tray()
        self._setup_icons()
        self._connect_actions()
        self._create_statusbar()
        self._update_statusbar_active(False)

        # Load existing configuration or create a new one otherwise
        if self.config.last_profile and os.path.isfile(self.config.last_profile):
            self._do_load_profile(self.config.last_profile)
        else:
            self.new_profile()

        # Create device tabs
        # FIXME: why was this added initially?
        #self._create_tabs()

        # Modal windows
        self.about_window = None
        self.calibration_window = None
        self.device_information = None
        self.merge_axis_ui = None
        self.module_manager = None
        self.mode_manager = None
        self.options_window = None
        self.log_window = None

        # Enable reloading for when a user connects / disconnects a
        # device. Sleep for a bit to avert race with devices being added
        # when they already exist.
        el = EventListener()
        time.sleep(0.1)
        el.device_change_event.connect(self._device_change_cb)

        # Enable mode change callback handling only once all the setup
        # has been completed
        #self.mode_selector.mode_changed.connect(self._mode_changed_cb)

        self.apply_user_settings()

    def closeEvent(self, evt):
        """Terminate the entire application if the main window is closed.

        :param evt the closure event
        """
        if self.config.close_to_tray and self.ui.tray_icon.isVisible():
            self.hide()
            evt.ignore()
        else:
            self.process_monitor.running = False
            del self.ui.tray_icon
            QtCore.QCoreApplication.quit()

        # Terminate file watcher thread
        if self.log_window:
            self.log_window.watcher.stop()

    # +---------------------------------------------------------------
    # | Modal window creation
    # +---------------------------------------------------------------

    def about(self):
        """Opens the about window."""
        self.about_window = dialogs.AboutUi()
        self.about_window.show()

    def calibration(self):
        """Opens the calibration window."""
        self.calibration_window = dialogs.CalibrationUi()
        self.calibration_window.show()
        gremlin.shared_state.set_suspend_input_highlighting(True)
        self.calibration_window.closed.connect(
            lambda: gremlin.shared_state.set_suspend_input_highlighting(False)
        )

    def device_information(self):
        """Opens the device information window."""
        self.device_information = \
            widgets.DeviceInformationWidget(self.devices)
        geom = self.geometry()
        self.device_information.setGeometry(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
            300,
            150
        )
        self.device_information.show()

    def log_window(self):
        """Opens the log display window."""
        self.log_window = dialogs.LogWindowUi()
        self.log_window.show()

    def manage_custom_modules(self):
        """Opens the custom module management window."""
        self.module_manager = dialogs.ModuleManagerUi(self._profile)
        self.module_manager.show()

    def manage_modes(self):
        """Opens the mode management window."""
        self.mode_manager = dialogs.ModeManagerUi(self._profile)
        self.mode_manager.modes_changed.connect(
            self._mode_configuration_changed
        )
        self.mode_manager.show()

    def merge_axis(self):
        self.merge_axis_ui = dialogs.MergeAxisUi(self._profile)
        self.merge_axis_ui.show()

    def options_dialog(self):
        """Opens the options dialog."""
        self.options_window = dialogs.OptionsUi()
        self.options_window.show()
        self.options_window.closed.connect(
            lambda: self.apply_user_settings()
        )

    # +---------------------------------------------------------------
    # | Action implementations
    # +---------------------------------------------------------------

    def activate(self, checked):
        """Activates and deactivates the code runner.

        :param checked True when the runner is to be activated, False
            otherwise
        """
        if checked:
            # Generate the code for the profile and run it
            self._profile_auto_activated = False
            self.generate()
            self.runner.start(self._profile.build_inheritance_tree())
            # Retrieve last active profile and switch to it
            eh = gremlin.event_handler.EventHandler()
            eh.change_mode(self.config.get_last_mode(self._profile_fname))
        else:
            # Stop running the code
            self.runner.stop()
            self._update_statusbar_active(False)
            self._profile_auto_activated = False

    def create_1to1_mapping(self):
        """Creates a 1 to 1 mapping of the given device to the first
        vJoy device.
        """
        # Don't attempt to create the mapping for the "Getting Started"
        # widget
        if isinstance(self.ui.devices.currentWidget(), QtWidgets.QTextEdit):
            return

        device_profile = self.ui.devices.currentWidget().device_profile
        # Don't create mappings for non joystick devices
        if device_profile.type != gremlin.profile.DeviceType.Joystick:
            return

        action_plugins = gremlin.plugin_manager.ActionPlugins()

        vjoy_devices = [dev for dev in self.devices if dev.is_virtual]
        mode = device_profile.modes[self._current_mode]
        input_types = [
            UiInputType.JoystickAxis,
            UiInputType.JoystickButton,
            UiInputType.JoystickHat
        ]
        type_name = {
            UiInputType.JoystickAxis: "axis",
            UiInputType.JoystickButton: "button",
            UiInputType.JoystickHat: "hat",
        }
        main_profile = device_profile.parent
        from action_plugins.common import ButtonCondition
        for input_type in input_types:
            for entry in mode.config[input_type].values():
                item_list = main_profile.list_unused_vjoy_inputs(
                    vjoy_devices
                )
                act = action_plugins.repository["remap"](entry)
                act.input_type = input_type
                act.vjoy_device_id = 1
                if len(item_list[1][type_name[input_type]]) > 0:
                    act.vjoy_input_id = item_list[1][type_name[input_type]][0]
                else:
                    act.vjoy_input_id = 1
                act.is_valid = True

                if input_type == UiInputType.JoystickButton:
                    act.condition = ButtonCondition(True, True)
                entry.actions.append(act)
        self._create_tabs()

    def load_as_template(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Profile to load as template",
            util.userprofile_path(),
            "XML files (*.xml)"
        )
        if fname == "":
            return

        profile_data = gremlin.profile.Profile()
        profile_data.from_xml(fname)

        self.bla = dialogs.TemplateViewer(profile_data)
        self.bla.show()

    def generate(self):
        """Generates python code for the code runner from the current
        profile.
        """
        generator = CodeGenerator(self._profile)
        generator.write_code(
            os.path.join(
                util.userprofile_path(),
                "gremlin_code.py"
            )
        )

    def input_repeater(self):
        """Enables or disables the forwarding of events to the repeater."""
        el = EventListener()
        if self.ui.actionInputRepeater.isChecked():
            el.keyboard_event.connect(self._handle_input_repeat)
            el.joystick_event.connect(self._handle_input_repeat)
            self._update_statusbar_repeater("Waiting for input")
        else:
            el.keyboard_event.disconnect(self._handle_input_repeat)
            el.joystick_event.disconnect(self._handle_input_repeat)
            self.status_bar_repeater.setText("")

    def load_profile(self):
        """Prompts the user to select a profile file to load."""
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Load Profile",
            util.userprofile_path(),
            "XML files (*.xml)"
        )
        if fname != "":
            self._do_load_profile(fname)
            self.config.last_profile = fname

    def new_profile(self):
        """Creates a new empty profile."""
        self._profile = gremlin.profile.Profile()

        # For each connected device create a new empty device entry
        # in the new profile
        for device in [entry for entry in self.devices if not entry.is_virtual]:
            new_device = gremlin.profile.Device(self._profile)
            new_device.name = device.name
            new_device.hardware_id = device.hardware_id
            new_device.windows_id = device.windows_id
            new_device.type = gremlin.profile.DeviceType.Joystick
            self._profile.devices[util.device_id(new_device)] = new_device

        # Create keyboard device entry
        keyboard_device = gremlin.profile.Device(self._profile)
        keyboard_device.name = "keyboard"
        keyboard_device.hardware_id = 0
        keyboard_device.windows_id = 0
        keyboard_device.type = gremlin.profile.DeviceType.Keyboard
        self._profile.devices[util.device_id(keyboard_device)] = keyboard_device

        # Update profile information
        self._profile_fname = None
        self._current_mode = None
        self._update_window_title()

        # Create a default mode
        for device in self._profile.devices.values():
            device.ensure_mode_exists("Default")
            # new_mode = profile.Mode(device)
            # new_mode.name = "Default"
            # device.modes["Default"] = new_mode
        self._current_mode = "Default"

        # Create device tabs
        self._create_tabs()

        # Update everything to the new mode
        self._mode_configuration_changed()

        # Select the last tab which contains the Getting started guide
        self.ui.devices.setCurrentIndex(len(self.tabs))

    def save_profile(self):
        """Saves the current profile to the hard drive.

        If the file was loaded from an existing profile that file is
        updated, otherwise the user is prompted for a new file.
        """
        if self._profile_fname:
            self._profile.to_xml(self._profile_fname)
        else:
            self.save_profile_as()
        self._update_window_title()

    def save_profile_as(self):
        """Prompts the user for a file to save to profile to."""
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            None,
            "Save Profile",
            util.userprofile_path(),
            "XML files (*.xml)"
        )
        if fname != "":
            self._profile.to_xml(fname)
            self._profile_fname = fname
        self._update_window_title()

    # +---------------------------------------------------------------
    # | Create UI elements
    # +---------------------------------------------------------------

    def _connect_actions(self):
        """Connects all QAction items to their corresponding callbacks."""
        # Menu actions
        # File
        self.ui.actionLoadProfile.triggered.connect(self.load_profile)
        self.ui.actionNewProfile.triggered.connect(self.new_profile)
        self.ui.actionSaveProfile.triggered.connect(self.save_profile)
        self.ui.actionSaveProfileAs.triggered.connect(self.save_profile_as)
        self.ui.actionLoadAsTemplate.triggered.connect(self.load_as_template)
        self.ui.actionExit.triggered.connect(self._force_close)
        # Actions
        self.ui.actionCreate1to1Mapping.triggered.connect(
            self.create_1to1_mapping
        )
        self.ui.actionMergeAxis.triggered.connect(self.merge_axis)

        # Tools
        self.ui.actionDeviceInformation.triggered.connect(
            self.device_information
        )
        self.ui.actionManageModes.triggered.connect(self.manage_modes)
        self.ui.actionManageCustomModules.triggered.connect(
            self.manage_custom_modules
        )
        self.ui.actionInputRepeater.triggered.connect(self.input_repeater)
        self.ui.actionCalibration.triggered.connect(self.calibration)
        self.ui.actionHTMLCheatsheet.triggered.connect(
            lambda: self._create_cheatsheet("html")
        )
        self.ui.actionPDFCheatsheet.triggered.connect(
            lambda: self._create_cheatsheet("pdf")
        )
        self.ui.actionOptions.triggered.connect(self.options_dialog)
        self.ui.actionLogDisplay.triggered.connect(
            self.log_window
        )
        # About
        self.ui.actionAbout.triggered.connect(self.about)

        # Toolbar actions
        self.ui.actionActivate.triggered.connect(self.activate)
        self.ui.actionOpen.triggered.connect(self.load_profile)

        # Tray icon
        self.ui.tray_icon.activated.connect(self._tray_icon_activated_cb)

    def _create_statusbar(self):
        """Creates the ui widgets used in the status bar."""
        self.status_bar_mode = QtWidgets.QLabel("")
        self.status_bar_mode.setContentsMargins(5, 0, 5, 0)
        self.status_bar_is_active = QtWidgets.QLabel("")
        self.status_bar_is_active.setContentsMargins(5, 0, 5, 0)
        self.status_bar_repeater = QtWidgets.QLabel("")
        self.status_bar_repeater.setContentsMargins(5, 0, 5, 0)
        self.ui.statusbar.addWidget(self.status_bar_is_active, 0)
        self.ui.statusbar.addWidget(self.status_bar_mode, 3)
        self.ui.statusbar.addWidget(self.status_bar_repeater, 1)

    def _create_system_tray(self):
        """Creates the system tray icon and menu."""
        self.ui.tray_menu = QtWidgets.QMenu("Menu")
        self.ui.action_tray_show = \
            QtWidgets.QAction("Show / Hide", self)
        self.ui.action_tray_enable = \
            QtWidgets.QAction("Enable / Disable", self)
        self.ui.action_tray_quit = QtWidgets.QAction("Quit", self)
        self.ui.tray_menu.addAction(self.ui.action_tray_show)
        self.ui.tray_menu.addAction(self.ui.action_tray_enable)
        self.ui.tray_menu.addAction(self.ui.action_tray_quit)

        self.ui.action_tray_show.triggered.connect(
            lambda: self.setHidden(not self.isHidden())
        )
        self.ui.action_tray_enable.triggered.connect(
            self.ui.actionActivate.trigger
        )
        self.ui.action_tray_quit.triggered.connect(
            self._force_close
        )

        self.ui.tray_icon = QtWidgets.QSystemTrayIcon()
        self.ui.tray_icon.setIcon(QtGui.QIcon("gfx/icon.ico"))
        self.ui.tray_icon.setContextMenu(self.ui.tray_menu)
        self.ui.tray_icon.show()

    def _create_tabs(self):
        """Creates the tabs of the configuration dialog representing
        the different connected devices.
        """
        # Disconnect the old tabs before deleting them (eventually)
        for widget in self.tabs.values():
            self.mode_selector.mode_changed.disconnect(
                widget.input_item_list.mode_changed_cb
            )
            self.mode_selector.mode_changed.disconnect(
                widget.configuration_panel.mode_changed_cb
            )
        self.ui.devices.clear()
        self.tabs = {}

        # Create joystick devices
        vjoy_devices = [dev for dev in self.devices if dev.is_virtual]
        phys_devices = [dev for dev in self.devices if not dev.is_virtual]
        for device in sorted(phys_devices, key=lambda x: x.name):
            device_profile = self._profile.get_device_modes(
                util.device_id(device),
                gremlin.profile.DeviceType.Joystick,
                device.name
            )

            widget = widgets.DeviceTabWidget(
                vjoy_devices,
                device,
                device_profile,
                self._current_mode
            )
            self.tabs[util.device_id(device)] = widget
            self.ui.devices.addTab(widget, device.name)

        # Create keyboard tab
        device_profile = self._profile.get_device_modes(
            util.device_id(gremlin.event_handler.Event.from_key(
                gremlin.macro.Keys.A)
            ),
            gremlin.profile.DeviceType.Keyboard,
            "keyboard"
        )
        widget = widgets.DeviceTabWidget(
            vjoy_devices,
            None,
            device_profile,
            self._current_mode
        )
        self.tabs[util.device_id(device_profile)] = widget
        self.ui.devices.addTab(widget, "Keyboard")

        # Create the vjoy devices tab
        for device in sorted(vjoy_devices, key=lambda x: x.vjoy_id):
            device_profile = self._profile.get_device_modes(
                device.vjoy_id,
                gremlin.profile.DeviceType.VJoy,
                device.name
            )

            widget = widgets.DeviceTabWidget(
                vjoy_devices,
                device,
                device_profile,
                self._current_mode
            )
            self.tabs[util.device_id(device)] = widget
            self.ui.devices.addTab(
                widget,
                "{} #{:d}".format(device.name, device.vjoy_id)
            )

        # Connect the mode changed event to all tabs
        for widget in self.tabs.values():
            self.mode_selector.mode_changed.connect(
                widget.input_item_list.mode_changed_cb
            )
            self.mode_selector.mode_changed.connect(
                widget.configuration_panel.mode_changed_cb
            )

        # Add the getting started tab
        widget = QtWidgets.QTextEdit()
        widget.setReadOnly(True)
        widget.setHtml(open("doc/getting_started.html").read())
        self.ui.devices.addTab(widget, "Getting Started")

    def _setup_icons(self):
        """Sets the icons of all QAction items."""
        # Menu actions
        self.ui.actionLoadProfile.setIcon(
            QtGui.QIcon("gfx/profile_open.svg")
        )
        self.ui.actionNewProfile.setIcon(
            QtGui.QIcon("gfx/profile_new.svg")
        )
        self.ui.actionSaveProfile.setIcon(
            QtGui.QIcon("gfx/profile_save.svg")
        )
        self.ui.actionSaveProfileAs.setIcon(
            QtGui.QIcon("gfx/profile_save_as.svg")
        )
        self.ui.actionDeviceInformation.setIcon(
            QtGui.QIcon("gfx/device_information.svg")
        )
        self.ui.actionManageCustomModules.setIcon(
            QtGui.QIcon("gfx/manage_modules.svg")
        )
        self.ui.actionManageModes.setIcon(
            QtGui.QIcon("gfx/manage_modes.svg")
        )
        self.ui.actionInputRepeater.setIcon(
            QtGui.QIcon("gfx/input_repeater.svg")
        )
        self.ui.actionCalibration.setIcon(
            QtGui.QIcon("gfx/calibration.svg")
        )
        self.ui.actionAbout.setIcon(QtGui.QIcon("gfx/about.svg"))

        # Toolbar actions
        activate_icon = QtGui.QIcon()
        activate_icon.addPixmap(
            QtGui.QPixmap("gfx/activate.svg"),
            QtGui.QIcon.Normal
        )
        activate_icon.addPixmap(
            QtGui.QPixmap("gfx/activate_on.svg"),
            QtGui.QIcon.Active,
            QtGui.QIcon.On
        )
        self.ui.actionActivate.setIcon(activate_icon)
        self.ui.actionOpen.setIcon(
            QtGui.QIcon("gfx/profile_open.svg")
        )

    # +---------------------------------------------------------------
    # | Signal handlers
    # +---------------------------------------------------------------

    def _device_change_cb(self):
        """Handles addition and removal of joystick devices."""
        self.devices = util.joystick_devices()
        self._create_tabs()

    def _joystick_input_selection(self, event):
        """Handles joystick events to select the appropriate input item.

        :param event the event to process
        """
        if event.event_type == gremlin.event_handler.InputType.Keyboard:
            return
        if self.runner.is_running() or self._current_mode is None:
            return
        if gremlin.shared_state.suspend_input_highlighting():
            return

        # Only handle events for the currently active device
        widget = self.ui.devices.currentWidget()
        if isinstance(widget, QtWidgets.QTextEdit):
            return

        # If we want to act on the given even figure out which button
        # needs to be pressed and press is
        if util.device_id(event) == util.device_id(widget.device_profile):
            if self._should_process_input(event):
                ui_event_type = gremlin.event_handler.\
                    system_event_to_input_event(event.event_type)
                btn = widget.input_item_list.input_items[ui_event_type][event.identifier]
                btn.mousePressEvent(None)

    def _mode_changed_cb(self, new_mode):
        """Updates the current mode to the provided one.

        :param new_mode the name of the new current mode
        """
        self._current_mode = new_mode

    def _process_changed_cb(self, path):
        """Handles changes in the active process.

        If the active process has a known associated profile it is
        loaded and activated if none exists the application is
        disabled.

        :param path the path to the currently active process executable
        """
        profile_path = self.config.get_profile(path)
        if profile_path:
            if self._profile_fname != profile_path:
                self.ui.actionActivate.setChecked(False)
                self.activate(False)
                self._do_load_profile(profile_path)
            self.ui.actionActivate.setChecked(True)
            self.activate(True)
            self._profile_auto_activated = True
        elif self._profile_auto_activated:
            self.ui.actionActivate.setChecked(False)
            self.activate(False)
            self._profile_auto_activated = False

    def _tray_icon_activated_cb(self, reason):
        """Callback triggered by clicking on the system tray icon.

        :param reason the type of click performed on the icon
        """
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.setHidden(not self.isHidden())

    def _update_statusbar_active(self, is_active):
        """Updates the status bar with the current state of the system.

        :param is_active True if the system is active, False otherwise
        """
        if is_active:
            text_active = "<font color=\"green\">Active</font>"
        else:
            text_active = "<font color=\"red\">Paused</font>"
        if self.ui.actionActivate.isChecked():
            text_running = "Running and {}".format(text_active)
        else:
            text_running = "Not Running"

        self.status_bar_is_active.setText(
            "<b>Status: </b> {}".format(text_running)
        )

    def _update_statusbar_mode(self, mode):
        """Updates the status bar display of the current mode.

        :param mode the now current mode
        """
        self.status_bar_mode.setText("<b>Mode:</b> {}".format(mode))
        if self.config.mode_change_message:
            self.ui.tray_icon.showMessage(
                "Mode: {}".format(mode),
                "",
                0,
                250
            )

    # +---------------------------------------------------------------
    # | Utilities
    # +---------------------------------------------------------------

    def apply_user_settings(self):
        """Configures the program based on user settings."""
        self._set_joystick_input_highlighting(
            self.config.highlight_input
        )
        self.setHidden(self.config.start_minimized)
        if self.config.autoload_profiles:
            self.process_monitor.start()
        else:
            self.process_monitor.stop()

    def _create_cheatsheet(self, file_format):
        """Creates the cheatsheet and stores it in the desired place.

        :param file_format the format of the cheatsheet, html or pdf
        """
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            None,
            "Save cheatsheet",
            util.userprofile_path(),
            "{} files (*.{})".format(file_format.upper(), file_format)
        )
        gremlin.documenter.generate_cheatsheet(
            file_format,
            fname,
            self._profile
        )

    def _do_load_profile(self, fname):
        """Load the profile with the given filename.

        :param fname the name of the profile file to load
        """
        # Disable the program if it is running when we're loading a
        # new profile
        self.ui.actionActivate.setChecked(False)
        self.activate(False)

        # Attempt to load the new profile
        try:
            new_profile = gremlin.profile.Profile()
            new_profile.from_xml(fname)

            profile_folder = os.path.dirname(fname)
            if profile_folder not in sys.path:
                sys.path = list(self._base_path)
                sys.path.insert(0, profile_folder)

            self._sanitize_profile(new_profile)
            self._profile = new_profile
            self._profile_fname = fname
            self._update_window_title()

            self._current_mode = sorted(self._profile.get_root_modes())[0]
            self._create_tabs()

            # Make the first root node the default active mode
            self.mode_selector.populate_selector(
                self._profile, self._current_mode
            )
            # FIXME: no longer required above line does all of this
            #self._mode_configuration_changed()
        except TypeError as e:
            # An error occurred while parsing an existing profile,
            # creating an empty profile instead
            logging.getLogger("system").exception(
                "Invalid profile content:\n{}".format(e)
            )
            self.new_profile()

    def _force_close(self):
        """Forces the closure of the program."""
        self.ui.tray_icon.hide()
        self.close()

    def _get_device_profile(self, device):
        """Returns a profile for the given device.

        If no profile exists for the given device a new empty one is
        created.

        :param device the device for which to return the profile
        :return profile for the provided device
        """
        if device.hardware_id in self._profile.devices:
            device_profile = self._profile.devices[device.hardware_id]
        else:
            device_profile = {}

        return device_profile

    def _handle_input_repeat(self, event):
        """Performs setup for event repetition.

        :param event the event to repeat
        """
        vjoy_device_id = \
            [dev.hardware_id for dev in self.devices if dev.is_virtual][0]
        # Ignore VJoy events
        if self.repeater.is_running or event.hardware_id == vjoy_device_id:
            return
        # Ignore small joystick movements
        elif event.event_type == InputType.JoystickAxis and abs(event.value) < 0.25:
            return
        # Ignore neutral hat positions
        if event.event_type == InputType.JoystickHat and event.value == (0, 0):
            return

        event_list = []
        if event.event_type in [InputType.Keyboard, InputType.JoystickButton]:
            event_list = [event.clone(), event.clone()]
            event_list[0].is_pressed = False
            event_list[1].is_pressed = True
        elif event.event_type == InputType.JoystickAxis:
            event_list = [
                event.clone(),
                event.clone(),
                event.clone(),
                event.clone()
            ]
            event_list[0].value = -0.75
            event_list[1].value = 0.0
            event_list[2].value = 0.75
            event_list[3].value = 0.0
        elif event.event_type == InputType.JoystickHat:
            event_list = [event.clone(), event.clone()]
            event_list[0].value = (0, 0)

        self.repeater.events = event_list

    def _mode_configuration_changed(self):
        """Updates the mode configuration of the selector and profile."""
        self.mode_selector.populate_selector(
            self._profile,
            self._current_mode
        )

    def _sanitize_profile(self, profile_data):
        """Validates a profile file before actually loading it.

        :param profile_data the profile to verify
        """
        profile_devices = {}
        for device in profile_data.devices.values():
            # Ignore the keyboard
            if device.hardware_id == 0:
                continue
            profile_devices[util.device_id(device)] = device.name

        physical_devices = {}
        for device in self.devices:
            if device.is_virtual:
                continue
            physical_devices[util.device_id(device)] = device.name

        # Find profile data that conflicts with currently connected
        # hardware and warn the user
        hardware_id_clash = False
        for dev_id, dev_name in physical_devices.items():
            if dev_id in profile_devices and profile_devices[dev_id] != dev_name:
                hardware_id_clash = True

        if hardware_id_clash:
            util.display_error(
                "The profile contains duplicate / wrong device ids. "
                "The profile may no longer work as intended."
            )

    def _set_joystick_input_highlighting(self, is_enabled):
        """Enables / disables the highlighting of the current input
        when used."""
        el = EventListener()
        if is_enabled:
            el.joystick_event.connect(
                self._joystick_input_selection
            )
        else:
            el.joystick_event.disconnect(
                self._joystick_input_selection
            )

    def _should_process_input(self, event):
        """Returns True when to process and input, False otherwise.

        This enforces a certain downtime between subsequent inputs
        triggering an update of the UI as well as preventing inputs
        from the same, currently active input to trigger another
        update.

        :param event the event to make the decision about
        :return True if the event is to be processed, False otherwise
        """
        # Check if the input in general is something we want to process
        process_input = False
        if event.event_type == InputType.JoystickButton:
            process_input = event.is_pressed
        elif event.event_type == InputType.JoystickAxis:
            process_input = abs(event.value) > 0.25
        elif event.event_type == InputType.JoystickHat:
            process_input = event.value != (0, 0)
        else:
            logging.getLogger("system").warning(
                "Event with bad content received"
            )
            process_input = False

        # Check if we should actually react to the event
        if event == self._last_input_event:
            return False
        elif self._last_input_timestamp + 0.25 > time.time():
            return False
        elif not process_input:
            return False
        else:
            self._last_input_event = event
            self._last_input_timestamp = time.time()
            return True

    def _update_statusbar_repeater(self, text):
        """Updates the statusbar with information from the input
        repeater module.

        :param text the text to display
        """
        self.status_bar_repeater.setText(
            "<b>Repeater: </b> {}".format(text)
        )

    def _update_window_title(self):
        """Updates the window title to include the current profile."""
        if self._profile_fname is not None:
            self.setWindowTitle("{}".format(
                os.path.basename(self._profile_fname))
            )
        else:
            self.setWindowTitle("")


def configure_logger(config):
    """Creates a new logger instance.

    :param config configuration information for the new logger
    """
    logger = logging.getLogger(config["name"])
    logger.setLevel(config["level"])
    handler = logging.FileHandler(config["logfile"])
    handler.setLevel(config["level"])
    formatter = logging.Formatter(config["format"], "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.debug("-" * 80)
    logger.debug(time.strftime("%Y-%m-%d %H:%M"))
    logger.debug("Starting Joystick Gremlin R6")
    logger.debug("-" * 80)


def exception_hook(exception_type, value, trace):
    """Logs any uncaught exceptions.

    :param exception_type type of exception being caught
    :param value content of the exception
    :param trace the stack trace which produced the exception
    """
    msg = "Uncaught exception:\n"
    msg += " ".join(traceback.format_exception(exception_type, value, trace))
    logging.getLogger("system").error(msg)
    util.display_error(msg)


if __name__ == "__main__":
    sys.path.insert(0, util.userprofile_path())
    util.setup_userprofile()

    # Configure logging for system and user events
    configure_logger({
        "name": "system",
        "level": logging.DEBUG,
        "logfile": os.path.join(util.userprofile_path(), "system.log"),
        "format": "%(asctime)s %(levelname)10s %(message)s"
    })
    configure_logger({
        "name": "user",
        "level": logging.DEBUG,
        "logfile": os.path.join(util.userprofile_path(), "user.log"),
        "format": "%(asctime)s %(message)s"
    })

    # Unhandled exception traceback
    #sys.excepthook = exception_hook

    # Initialize SDL
    sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
    sdl2.SDL_SetHint(
                sdl2.hints.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS,
                ctypes.c_char_p(b"1")
    )
    sdl2.ext.init()

    # Check if vJoy is properly setup and if not display an error
    # and terminate Gremlin
    vjoy_working = len([dev for dev in util.joystick_devices() if dev.is_virtual]) != 0

    # Setup device key generator based on whether or not we have
    # duplicate devices connected.
    util.setup_duplicate_joysticks()

    # Initialize action plugins
    gremlin.plugin_manager.ActionPlugins()

    # Create user interface
    app_id = u"joystick.gremlin"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("gfx/icon.png"))
    app.setApplicationDisplayName("Joystick Gremlin")

    if not vjoy_working:
        util.display_error(
            "vJoy is not present or incorrectly setup, terminating.")
    else:
        ui = GremlinUi()
        ui.show()
        ui.apply_user_settings()

    # Run UI
    app.exec_()

    # Terminate potentially running EventListener loop
    event_listener = gremlin.event_handler.EventListener()
    event_listener.terminate()

    if vjoy_working:
        # Properly terminate the runner instance should it be running
        ui.runner.stop()

    # Relinquish control over all VJoy devices used
    gremlin.input_devices.VJoyProxy.reset()

    sys.exit(0)
