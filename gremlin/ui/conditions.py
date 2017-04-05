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

from PyQt5 import QtCore, QtGui, QtWidgets

import gremlin


class AbstractConditionWidget(QtWidgets.QWidget):

    modified = QtCore.pyqtSignal()

    def __init__(self, action_data, parent=None):
        super().__init__(parent)
        self.action_data = action_data

    def from_profile(self):
        gremlin.error.MissingImplementationError(
            "AbstractConditionWidget.from_profile not implemented in subclass."
        )


class AxisConditionWidget(AbstractConditionWidget):

    """Widget allowing the configuration of the activation condition
    of axis triggers."""

    def __init__(self, action_data, parent=None):
        """Creates a new AxisConditionWidget object.

        :param parent the parent of this widget
        """
        super().__init__(action_data, parent)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.checkbox = QtWidgets.QCheckBox("Trigger between")

        self.range_layout = QtWidgets.QHBoxLayout()
        self.lower_limit = QtWidgets.QDoubleSpinBox()
        self.lower_limit.setRange(-1.0, 1.0)
        self.lower_limit.setSingleStep(0.05)
        self.upper_limit = QtWidgets.QDoubleSpinBox()
        self.upper_limit.setRange(-1.0, 1.0)
        self.upper_limit.setSingleStep(0.05)
        self.and_label = QtWidgets.QLabel("and")
        self.and_label.setAlignment(QtCore.Qt.AlignHCenter)

        self.range_layout.addWidget(self.lower_limit)
        self.range_layout.addWidget(self.and_label)
        self.range_layout.addWidget(self.upper_limit)

        self.main_layout.addWidget(self.checkbox)
        self.main_layout.addLayout(self.range_layout)

        self.main_layout.addStretch()
        self.main_layout.setContentsMargins(0, 0, 5, 0)

        self.checkbox.stateChanged.connect(self._checkbox_cb)
        self.lower_limit.valueChanged.connect(self._lower_limit_cb)
        self.upper_limit.valueChanged.connect(self._upper_limit_cb)

        self.from_profile()

    def from_profile(self):
        self.checkbox.setChecked(self.action_data.condition.is_active)
        self.lower_limit.setValue(self.action_data.condition.lower_limit)
        self.upper_limit.setValue(self.action_data.condition.upper_limit)

    def _checkbox_cb(self, state):
        self.action_data.condition.is_active = state == QtCore.Qt.Checked
        self.modified.emit()

    def _lower_limit_cb(self, value):
        self.action_data.condition.lower_limit = value
        self.modified.emit()

    def _upper_limit_cb(self, value):
        self.action_data.condition.upper_limit = value
        self.modified.emit()


class ButtonConditionWidget(AbstractConditionWidget):

    """Widget allowing the configuration of the activation condition
    of button like actions."""

    def __init__(self, action_data, parent=None):
        """Creates a new ButtonConditionWidget object.


        :param parent the parent of this widget
        """
        super().__init__(action_data, parent)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel("Activate on:"))
        self.press = QtWidgets.QCheckBox("press")
        self.press.stateChanged.connect(self._press_cb)
        self.release = QtWidgets.QCheckBox("release")
        self.release.stateChanged.connect(self._release_cb)
        self.main_layout.addWidget(self.press)
        self.main_layout.addWidget(self.release)

        self.main_layout.addStretch()
        self.main_layout.setContentsMargins(0, 0, 5, 0)

        self.from_profile()

    def from_profile(self):
        self.press.setChecked(self.action_data.condition.on_press)
        self.release.setChecked(self.action_data.condition.on_release)

    def _press_cb(self, state):
        self.action_data.condition.on_press = state == QtCore.Qt.Checked
        self.modified.emit()

    def _release_cb(self, state):
        self.action_data.condition.on_release = state == QtCore.Qt.Checked
        self.modified.emit()

    # FIXME: this will become it's own container
    # def _shift_button_cb(self):
    #     """Queries the user for the shift button to use."""
    #     self.button_press_dialog = common.InputListenerWidget(
    #         self._assign_shift_button_cb,
    #         [
    #             InputType.Keyboard,
    #             InputType.JoystickButton
    #         ]
    #     )
    #
    #     gremlin.shared_state.set_suspend_input_highlighting(True)
    #
    #     # Display the dialog centered in the middle of the UI
    #     geom = self.geometry()
    #     point = self.mapToGlobal(QtCore.QPoint(
    #         geom.x() + geom.width() / 2 - 150,
    #         geom.y() + geom.height() / 2 - 75,
    #     ))
    #     self.button_press_dialog.setGeometry(
    #         point.x(),
    #         point.y(),
    #         300,
    #         150
    #     )
    #     self.button_press_dialog.show()
    #
    # def _assign_shift_button_cb(self, value):
    #     """Sets the shift button once it has been pressed by the user.
    #
    #     :param value holds the shift button information
    #     """
    #     if isinstance(value, gremlin.event_handler.Event):
    #         devices = gremlin.joystick_handling.joystick_devices()
    #         for dev in devices:
    #             if gremlin.util_simple.device_id(value) == gremlin.util_simple.device_id(dev):
    #                 # Set the button label
    #                 self.shift_button.setText("{} - Button {:d}".format(
    #                     dev.name,
    #                     value.identifier
    #                 ))
    #
    #                 # Store the information inside the profile
    #                 self.shift_data = {
    #                     "id": value.identifier,
    #                     "hardware_id": dev.hardware_id,
    #                     "windows_id": dev.windows_id
    #                 }
    #                 break
    #     elif isinstance(value, gremlin.macro.Keys.Key):
    #         self.shift_button.setText(value.name)
    #         self.shift_data = {
    #             "id": (value.scan_code, value.is_extended),
    #             "hardware_id": 0,
    #             "windows_id": 0
    #         }
    #
    #         gremlin.shared_state.set_suspend_input_highlighting(False)
    #     self.change_cb()


class HatConditionWidget(AbstractConditionWidget):

    """Widget allowing the configuration of the activation condition
    of hat actions."""

    def __init__(self, action_data, parent=None):
        """Creates a new ButtonConditionWidget object.

        :param change_cb callback function to execute when data is changed
        :param parent the parent of this widget
        """
        super().__init__(action_data, parent)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel("Activate on"))
        self.widgets = {}

        names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        positions = [(0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0), (0, 0)]

        self.direction_layout = QtWidgets.QGridLayout()
        for pos, name in zip(positions, names):
            self.widgets[name] = QtWidgets.QCheckBox(name)
            self.direction_layout.addWidget(self.widgets[name], pos[0], pos[1])
        self.main_layout.addLayout(self.direction_layout)

        self.main_layout.addStretch()
        self.main_layout.setContentsMargins(0, 0, 5, 0)

        self.from_profile()
        self.connect_signals()

    def connect_signals(self):
        """Connects widget signals to the callback function."""
        for name in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
            self.widgets[name].stateChanged.connect(self._emit_modified)

    def disconnect_signals(self):
        """Disconnects widget signals from the callback function."""
        for name in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
            try:
                self.widgets[name].stateChanged.disconnect(self._emit_modified)
            except TypeError:
                pass

    def from_profile(self):
        self.disconnect_signals()
        self.widgets["N"].setChecked(self.action_data.condition.on_n)
        self.widgets["NE"].setChecked(self.action_data.condition.on_ne)
        self.widgets["E"].setChecked(self.action_data.condition.on_e)
        self.widgets["SE"].setChecked(self.action_data.condition.on_se)
        self.widgets["S"].setChecked(self.action_data.condition.on_s)
        self.widgets["SW"].setChecked(self.action_data.condition.on_sw)
        self.widgets["W"].setChecked(self.action_data.condition.on_w)
        self.widgets["NW"].setChecked(self.action_data.condition.on_nw)
        self.connect_signals()

    def to_profile(self):
        self.action_data.condition.on_n = self.widgets["N"].isChecked()
        self.action_data.condition.on_ne = self.widgets["NE"].isChecked()
        self.action_data.condition.on_e = self.widgets["E"].isChecked()
        self.action_data.condition.on_se = self.widgets["SE"].isChecked()
        self.action_data.condition.on_s = self.widgets["S"].isChecked()
        self.action_data.condition.on_sw = self.widgets["SW"].isChecked()
        self.action_data.condition.on_e = self.widgets["W"].isChecked()
        self.action_data.condition.on_nw = self.widgets["NW"].isChecked()

    def _emit_modified(self, state):
        self.modified.emit()
