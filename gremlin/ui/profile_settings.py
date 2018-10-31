# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2018 Lionel Ott
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


from PyQt5 import QtCore, QtWidgets

import gremlin.joystick_handling
import gremlin.ui.common


class ProfileSettingsWidget(QtWidgets.QWidget):

    """Widget allowing changing profile specific settings."""

    # Signal emitted when a change occurs
    changed = QtCore.pyqtSignal()

    def __init__(self, profile_settings, parent=None):
        """Creates a new UI widget.

        :param profile_settings the settings of the profile
        :param parent the parent widget
        """
        super().__init__(parent)

        self.profile_settings = profile_settings

        self.main_layout = QtWidgets.QVBoxLayout(self)

        # Create required scroll UI elements
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout()

        # Configure the widget holding the layout with all the buttons
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Configure the scroll area
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

        self._create_ui()

    def refresh_ui(self, emit_change=False):
        """Refreshes the entire UI."""
        gremlin.ui.common.clear_layout(self.scroll_layout)
        self._create_ui()
        if emit_change:
            self.changed.emit()

    def _create_ui(self):
        """Creates the UI elements of this widget."""
        # Default start mode selection
        self.scroll_layout.addWidget(DefaultModeSelector(self.profile_settings))

        # vJoy devices as inputs
        vjoy_as_input_widget = VJoyAsInputWidget(self.profile_settings)
        self.scroll_layout.addWidget(vjoy_as_input_widget)
        vjoy_as_input_widget.changed.connect(lambda: self.refresh_ui(True))

        # vJoy axis initialization value setup
        for dev in sorted(
                gremlin.joystick_handling.vjoy_devices(),
                key=lambda x: x.vjoy_id
        ):
            # Only show devices that are not treated as inputs
            if self.profile_settings.vjoy_as_input.get(dev.vjoy_id) == True:
                continue

            widget = QtWidgets.QGroupBox("{} #{}".format(dev.name, dev.vjoy_id))
            box_layout = QtWidgets.QVBoxLayout()
            widget.setLayout(box_layout)
            box_layout.addWidget(VJoyAxisDefaultsWidget(
                dev,
                self.profile_settings
            ))

            self.scroll_layout.addWidget(widget)

        self.scroll_layout.addStretch(1)

        # Information label
        label = QtWidgets.QLabel(
            "This tab allows setting default initialization of vJoy axis "
            "values. These values  will be used when activating Gremlin."
        )
        label.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
        label.setWordWrap(True)
        label.setFrameShape(QtWidgets.QFrame.Box)
        label.setMargin(10)
        self.scroll_layout.addWidget(label)


class DefaultModeSelector(QtWidgets.QGroupBox):

    """Allows selecting the mode in which Gremlin starts."""

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data profile settings managed by the widget
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.profile_data = profile_data

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self._create_ui()

    def _create_ui(self):
        """Creates the UI used to configure the startup mode."""
        self.setTitle("Startup Mode")

        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.addItem("Use Heuristic")
        for mode in gremlin.profile.mode_list(self.profile_data):
            self.dropdown.addItem(mode)
        if self.profile_data.startup_mode:
            self.dropdown.setCurrentText(self.profile_data.startup_mode)
        self.dropdown.currentIndexChanged.connect(self._update_cb)

        self.main_layout.addWidget(self.dropdown)
        self.main_layout.addStretch()

    def _update_cb(self, index):
        """Handles changes in the mode selection drop down.

        :param index the index of the entry selected
        """
        if index == 0:
            self.profile_data.startup_mode = None
        else:
            self.profile_data.startup_mode = self.dropdown.currentText()


class VJoyAxisDefaultsWidget(QtWidgets.QWidget):

    """UI widget allowing modification of axis initialization values."""

    def __init__(self, joy_data, profile_data, parent=None):
        """Creates a new UI widget.

        :param joy_data JoystickDeviceData object containing device information
        :param profile_data profile settings managed by the widget
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.joy_data = joy_data
        self.profile_data = profile_data
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setColumnMinimumWidth(0, 100)
        self.main_layout.setColumnStretch(2, 1)

        self._spin_boxes = []
        self._create_ui()

    def _create_ui(self):
        """Creates the UI elements."""
        vjoy_proxy = gremlin.joystick_handling.VJoyProxy()
        for i in range(self.joy_data.axis_count):
            # FIXME: This is a workaround to not being able to read a vJoy
            #   device's axes names when it is grabbed by another process
            #   and the inability of SDL to provide canoncal axis names
            axis_name = "Axis {:d}".format(i+1)
            try:
                axis_name = vjoy_proxy[self.joy_data.vjoy_id]\
                    .axis_name(linear_index=i+1)
            except gremlin.error.VJoyError:
                pass
            self.main_layout.addWidget(
                QtWidgets.QLabel(axis_name),
                i,
                0
            )

            box = gremlin.ui.common.DynamicDoubleSpinBox()
            box.setRange(-1, 1)
            box.setSingleStep(0.05)
            box.setValue(self.profile_data.get_initial_vjoy_axis_value(
                self.joy_data.vjoy_id,
                i+1
            ))
            box.valueChanged.connect(self._create_value_cb(i+1))

            self.main_layout.addWidget(box, i, 1)
        vjoy_proxy.reset()

    def _create_value_cb(self, axis_id):
        """Creates a callback function which updates axis values.

        :param axis_id id of the axis to change the value of
        :return callback customized for the given axis_id
        """
        return lambda x: self._update_axis_value(axis_id, x)

    def _update_axis_value(self, axis_id, value):
        """Updates an axis' default value.

        :param axis_id id of the axis to update
        :param value the value to update the axis to
        """
        self.profile_data.set_initial_vjoy_axis_value(
            self.joy_data.vjoy_id,
            axis_id,
            value
        )


class VJoyAsInputWidget(QtWidgets.QGroupBox):

    """Configures which vJoy devices are treated as physical inputs."""

    # Signal emitted when a change occurs
    changed = QtCore.pyqtSignal()

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data profile information read and modified by the
            widget
        :param parent the paren of this widget
        """
        super().__init__(parent)

        self.profile_data = profile_data

        self.setTitle("vJoy as Input")
        self.main_layout = QtWidgets. QHBoxLayout(self)
        self.vjoy_layout = QtWidgets.QVBoxLayout()

        self._create_ui()

    def _create_ui(self):
        """Creates the UI to set physical input state."""
        for dev in sorted(
                gremlin.joystick_handling.vjoy_devices(),
                key=lambda x: x.vjoy_id
        ):
            check_box = QtWidgets.QCheckBox("vJoy {:d}".format(dev.vjoy_id))
            if self.profile_data.vjoy_as_input.get(dev.vjoy_id, False):
                check_box.setChecked(True)
            check_box.stateChanged.connect(
                self._create_update_state_cb(dev.vjoy_id)
            )
            self.vjoy_layout.addWidget(check_box)

        # Information label
        label = QtWidgets.QLabel(
            "Declaring a vJoy device as an input device will allow it to be"
            "used like a physical device, i.e. it can be forwarded to other"
            "vJoy devices. However, this also means that it won't be available"
            "as a virtual device."
        )
        label.setStyleSheet("QLabel { background-color : '#FFF4B0'; }")
        label.setWordWrap(True)
        label.setFrameShape(QtWidgets.QFrame.Box)
        label.setMargin(10)

        self.main_layout.addLayout(self.vjoy_layout)
        self.main_layout.addWidget(label)

    def _update_state_cb(self, vid, state):
        """Callback executed when an entry is modified.

        :param vid the id of the vJoy device being modified
        :param state the state of the checkbox
        """
        self.profile_data.vjoy_as_input[vid] = state == QtCore.Qt.Checked
        self.changed.emit()

    def _create_update_state_cb(self, vid):
        """Creates the callback allowing handling of state changes.

        :param vid the id of the vJoy device being modified
        """
        return lambda x: self._update_state_cb(vid, x)
