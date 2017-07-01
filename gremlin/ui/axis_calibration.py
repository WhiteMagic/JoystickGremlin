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

from PyQt5 import QtWidgets, QtCore

import gremlin
from . import common


class CalibrationUi(common.BaseDialogUi):

    """Dialog to calibrate joystick axes."""

    def __init__(self, parent=None):
        """Creates the calibration UI.

        :param parent the parent widget of this object
        """
        super().__init__(parent)
        self.devices = [
            dev for dev in gremlin.joystick_handling.joystick_devices()
            if not dev.is_virtual
        ]
        self.current_selection_id = 0

        # Create the required layouts
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.axes_layout = QtWidgets.QVBoxLayout()
        self.button_layout = QtWidgets.QHBoxLayout()

        self._create_ui()

    def _create_ui(self):
        """Creates all widgets required for the user interface."""
        # Device selection drop down
        self.device_dropdown = QtWidgets.QComboBox()
        self.device_dropdown.currentIndexChanged.connect(
            self._create_axes
        )
        for device in self.devices:
            self.device_dropdown.addItem(device.name)

        # Set the title
        self.setWindowTitle("Calibration")

        # Various buttons
        self.button_close = QtWidgets.QPushButton("Close")
        self.button_close.pressed.connect(self.close)
        self.button_save = QtWidgets.QPushButton("Save")
        self.button_save.pressed.connect(self._save_calibration)
        self.button_centered = QtWidgets.QPushButton("Centered")
        self.button_centered.pressed.connect(self._calibrate_centers)
        self.button_layout.addWidget(self.button_save)
        self.button_layout.addWidget(self.button_close)
        self.button_layout.addStretch(0)
        self.button_layout.addWidget(self.button_centered)

        # Axis widget readout headers
        self.label_layout = QtWidgets.QGridLayout()
        label_spacer = QtWidgets.QLabel()
        label_spacer.setMinimumWidth(200)
        label_spacer.setMaximumWidth(200)
        self.label_layout.addWidget(label_spacer, 0, 0, 0, 3)
        label_current = QtWidgets.QLabel("<b>Current</b>")
        label_current.setAlignment(QtCore.Qt.AlignRight)
        self.label_layout.addWidget(label_current, 0, 3)
        label_minimum = QtWidgets.QLabel("<b>Minimum</b>")
        label_minimum.setAlignment(QtCore.Qt.AlignRight)
        self.label_layout.addWidget(label_minimum, 0, 4)
        label_center = QtWidgets.QLabel("<b>Center</b>")
        label_center.setAlignment(QtCore.Qt.AlignRight)
        self.label_layout.addWidget(label_center, 0, 5)
        label_maximum = QtWidgets.QLabel("<b>Maximum</b>")
        label_maximum.setAlignment(QtCore.Qt.AlignRight)
        self.label_layout.addWidget(label_maximum, 0, 6)

        # Organizing everything into the various layouts
        self.main_layout.addWidget(self.device_dropdown)
        self.main_layout.addLayout(self.label_layout)
        self.main_layout.addLayout(self.axes_layout)
        self.main_layout.addStretch(0)
        self.main_layout.addLayout(self.button_layout)

        # Create the axis calibration widgets
        self.axes = []
        self._create_axes(self.current_selection_id)

        # Connect to the joystick events
        el = gremlin.event_handler.EventListener()
        el.joystick_event.connect(self._handle_event)

    def _calibrate_centers(self):
        """Records the centered or neutral position of the current device."""
        for widget in self.axes:
            widget.centered()

    def _save_calibration(self):
        """Saves the current calibration data to the hard drive."""
        cfg = gremlin.config.Configuration()
        dev_id = gremlin.util.device_id(
            self.devices[self.current_selection_id]
        )
        cfg.set_calibration(dev_id, [axis.limits for axis in self.axes])

    def _create_axes(self, index):
        """Creates the axis calibration widget for the current device.

        :param index the index of the currently selected device
            in the dropdown menu
        """
        common.clear_layout(self.axes_layout)
        self.axes = []
        self.current_selection_id = index
        for i in range(self.devices[index].axes):
            self.axes.append(AxisCalibrationWidget())
            self.axes_layout.addWidget(self.axes[-1])

    def _handle_event(self, event):
        """Process a single joystick event.

        :param event the event to process
        """
        selection_id = gremlin.util.device_id(
            self.devices[self.current_selection_id]
        )
        if gremlin.util.device_id(event) == selection_id \
                and event.event_type == gremlin.common.InputType.JoystickAxis:
            self.axes[event.identifier-1].set_current(event.raw_value)

    def closeEvent(self, event):
        """Closes the calibration window.

        :param event the close event
        """
        el = gremlin.event_handler.EventListener()
        el.joystick_event.disconnect(self._handle_event)
        super().closeEvent(event)


class AxisCalibrationWidget(QtWidgets.QWidget):

    """Widget displaying calibration information about a single axis."""

    def __init__(self, parent=None):
        """Creates a new object.

        :param parent the parent widget of this one
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.main_layout = QtWidgets.QGridLayout(self)
        self.limits = [0, 0, 0]

        # Create slider showing the axis position graphically
        self.slider = QtWidgets.QProgressBar()
        self.slider.setMinimum(-32768)
        self.slider.setMaximum(32767)
        self.slider.setValue(self.limits[1])
        self.slider.setMinimumWidth(200)
        self.slider.setMaximumWidth(200)

        # Create the labels
        self.current = QtWidgets.QLabel("0")
        self.current.setAlignment(QtCore.Qt.AlignRight)
        self.minimum = QtWidgets.QLabel("0")
        self.minimum.setAlignment(QtCore.Qt.AlignRight)
        self.center = QtWidgets.QLabel("0")
        self.center.setAlignment(QtCore.Qt.AlignRight)
        self.maximum = QtWidgets.QLabel("0")
        self.maximum.setAlignment(QtCore.Qt.AlignRight)
        self._update_labels()

        # Populate the layout
        self.main_layout.addWidget(self.slider, 0, 0, 0, 3)
        self.main_layout.addWidget(self.current, 0, 3)
        self.main_layout.addWidget(self.minimum, 0, 4)
        self.main_layout.addWidget(self.center, 0, 5)
        self.main_layout.addWidget(self.maximum, 0, 6)

    def set_current(self, value):
        """Updates the limits of the axis.

        :param value the new value
        """
        self.slider.setValue(value)
        if value > self.limits[2]:
            self.limits[2] = value
        if value < self.limits[0]:
            self.limits[0] = value
        self._update_labels()

    def centered(self):
        """Records the value of the center or neutral position."""
        self.limits[1] = self.slider.value()
        self._update_labels()

    def _update_labels(self):
        """Updates the axis limit values."""
        self.current.setText("{: 5d}".format(self.slider.value()))
        self.minimum.setText("{: 5d}".format(self.limits[0]))
        self.center.setText("{: 5d}".format(self.limits[1]))
        self.maximum.setText("{: 5d}".format(self.limits[2]))
