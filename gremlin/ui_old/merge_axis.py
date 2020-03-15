# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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

from PyQt5 import QtWidgets, QtCore, QtGui

import gremlin
from . import common


class MergeAxisUi(common.BaseDialogUi):

    """Allows merging physical axes into a single virtual ones."""

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data complete profile data
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.setWindowTitle("Merge Axis")

        self.profile_data = profile_data
        self.entries = []
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.merge_layout = QtWidgets.QVBoxLayout()

        # If there are no valid output vJoy devices present we can't show
        # the merge dialog.
        if len(self._output_vjoy_devices()) == 0:
            label = QtWidgets.QLabel(
                "No virtual devices available for axis merging. Either no "
                "vJoy devices are configured or all vJoy devices are defined "
                "as physical inputs."
            )
            label.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
            label.setWordWrap(True)
            label.setFrameShape(QtWidgets.QFrame.Box)
            label.setMargin(10)
            self.main_layout.addWidget(label)
        else:
            self.add_button = QtWidgets.QPushButton("New Axis")
            self.add_button.clicked.connect(self._add_entry)

            self.main_layout.addLayout(self.merge_layout)
            self.main_layout.addWidget(self.add_button)

            self.from_profile()

    def _add_entry(self, without_saving=False):
        """Adds a new axis to merge configuration entry."""
        entry = MergeAxisEntry(self.to_profile, self.profile_data)
        entry.closed.connect(self._remove_entry)

        self.entries.append(entry)
        self.merge_layout.addWidget(entry)
        if not without_saving:
            self.to_profile()

    def _remove_entry(self, widget):
        """Removes a widget from the dialog.

        :param widget the widget to remove
        """
        assert(isinstance(widget, MergeAxisEntry))

        # Remove profile data
        del self.profile_data.merge_axes[self.entries.index(widget)]

        # Remove UI entry
        self.merge_layout.removeWidget(widget)
        self.entries.remove(widget)

        # Update the profile
        self.to_profile()

    def to_profile(self):
        """Saves all merge axis entries to the profile."""
        self.profile_data.merge_axes = []
        for entry in self.entries:
            vjoy_sel = entry.vjoy_selector.get_selection()
            joy1_sel = entry.joy1_selector.get_selection()
            joy2_sel = entry.joy2_selector.get_selection()
            mode_idx = entry.mode_selector.selector.currentIndex()
            operation_str = entry.operation_selector.currentText()
            self.profile_data.merge_axes.append({
                "mode": entry.mode_selector.mode_list[mode_idx],
                "operation": gremlin.common.MergeAxisOperation.to_enum(
                    operation_str
                ),
                "vjoy": {
                    "vjoy_id": vjoy_sel["device_id"],
                    "axis_id": vjoy_sel["input_id"]
                },
                "lower": {
                    "device_guid": joy1_sel["device_id"],
                    "axis_id": joy1_sel["input_id"]
                },
                "upper": {
                    "device_guid": joy2_sel["device_id"],
                    "axis_id": joy2_sel["input_id"]
                }
            })

    def from_profile(self):
        """Populates the merge axis entries of the ui from the profile data."""
        entries_to_remove = []
        for entry in self.profile_data.merge_axes:
            # Show an error if the desired vJoy device is no longer available
            # as an output
            if self.profile_data.settings.vjoy_as_input.get(
                    entry["vjoy"]["vjoy_id"],
                    False
            ):
                entries_to_remove.append(entry)
                gremlin.util.display_error(
                    "vJoy device {} used as physical input".format(
                        entry["vjoy"]["vjoy_id"]
                    )
                )
            else:
                self._add_entry(True)
                new_entry = self.entries[-1]
                new_entry.select(entry)

        for entry in entries_to_remove:
            del self.profile_data.merge_axes[
                self.profile_data.merge_axes.index(entry)
            ]

    def _output_vjoy_devices(self):
        output_devices = []
        for dev in gremlin.joystick_handling.vjoy_devices():
            is_virtual = not self.profile_data.settings.vjoy_as_input.get(
                dev.vjoy_id,
                False
            )
            has_axes = dev.axis_count > 0
            if is_virtual and has_axes:
                output_devices.append(dev)
        return output_devices


class MergeAxisEntry(QtWidgets.QDockWidget):

    """UI dialog which allows configuring how to merge two axes."""

    # Signal which is emitted whenever the widget is closed
    closed = QtCore.pyqtSignal(QtWidgets.QWidget)

    # Palette used to render widgets
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Background, QtCore.Qt.lightGray)

    def __init__(self, change_cb, profile_data, parent=None):
        """Creates a new instance.

        :param change_cb function to execute when changes occur
        :param profile_data profile information
        :param parent the parent of this widget
        """
        QtWidgets.QDockWidget.__init__(self, parent)

        self.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)

        # Setup the dock widget in which the entire dialog will sit
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setAutoFillBackground(True)
        self.main_widget.setPalette(MergeAxisEntry.palette)

        self.main_layout = QtWidgets.QGridLayout(self.main_widget)
        self.setWidget(self.main_widget)

        # Selectors for both physical and virtual joystick axis for the
        # mapping selection
        self.vjoy_selector = common.VJoySelector(
            lambda x: change_cb(),
            [gremlin.common.InputType.JoystickAxis],
            profile_data.settings.vjoy_as_input
        )
        self.joy1_selector = common.JoystickSelector(
            lambda x: change_cb(),
            [gremlin.common.InputType.JoystickAxis]
        )
        self.joy2_selector = common.JoystickSelector(
            lambda x: change_cb(),
            [gremlin.common.InputType.JoystickAxis]
        )

        # Operation selection
        self.operation_selector = QtWidgets.QComboBox()
        self.operation_selector.addItem("Average")
        self.operation_selector.addItem("Minimum")
        self.operation_selector.addItem("Maximum")
        self.operation_selector.addItem("Sum")
        self.operation_selector.currentIndexChanged.connect(
            lambda x: change_cb()
        )

        # Mode selection
        self.mode_selector = gremlin.ui.common.ModeWidget()
        self.mode_selector.populate_selector(profile_data)
        self.mode_selector.mode_changed.connect(change_cb)

        # Assemble the complete ui
        self.main_layout.addWidget(
            QtWidgets.QLabel("<b><center>Lower Half</center></b>"), 0, 0
        )
        self.main_layout.addWidget(
            QtWidgets.QLabel("<b><center>Upper Half</center></b>"), 0, 1
        )
        self.main_layout.addWidget(
            QtWidgets.QLabel("<b><center>Merge Axis</center></b>"), 0, 2
        )
        self.main_layout.addWidget(
            QtWidgets.QLabel("<b><center>Operation</center></b>"), 0, 3
        )
        self.main_layout.addWidget(
            QtWidgets.QLabel("<b><center>Mode</center></b>"), 0, 4
        )
        self.main_layout.addWidget(self.joy1_selector, 1, 0)
        self.main_layout.addWidget(self.joy2_selector, 1, 1)
        self.main_layout.addWidget(self.vjoy_selector, 1, 2)
        self.main_layout.addWidget(self.operation_selector, 1, 3)
        self.main_layout.addWidget(self.mode_selector, 1, 4)

    def closeEvent(self, event):
        """Emits the closed event when this widget is being closed.

        :param event the close event details
        """
        QtWidgets.QDockWidget.closeEvent(self, event)
        self.closed.emit(self)

    def select(self, data):
        """Selects the specified entries in all drop downs.

        :param data information about which entries to select
        """
        try:
            self.vjoy_selector.set_selection(
                gremlin.common.InputType.JoystickAxis,
                data["vjoy"]["vjoy_id"],
                data["vjoy"]["axis_id"]
            )
        except gremlin.error.GremlinError as e:
            gremlin.util.display_error(
                "A needed vJoy device is not accessible: {}\n\n".format(e) +
                "Default values have been set for the input, but they are "
                "not what has been specified."
            )
            logging.getLogger("system").error(str(e))

        # Create correct physical device id
        joy1_id = data["lower"]["device_guid"]
        joy2_id = data["upper"]["device_guid"]

        self.joy1_selector.set_selection(
            gremlin.common.InputType.JoystickAxis,
            joy1_id,
            data["lower"]["axis_id"]
        )
        self.joy2_selector.set_selection(
            gremlin.common.InputType.JoystickAxis,
            joy2_id,
            data["upper"]["axis_id"]
        )
        if data["mode"] in self.mode_selector.mode_list:
            self.mode_selector.selector.setCurrentIndex(
                self.mode_selector.mode_list.index(data["mode"])
            )

        self.operation_selector.setCurrentText(
            gremlin.common.MergeAxisOperation.to_string(
                data["operation"]
            ).capitalize()
        )
