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
from PyQt5 import QtCore, QtWidgets
from xml.etree import ElementTree

import action_plugins.common
from action_plugins.common import AbstractAction, AbstractActionWidget
from gremlin.common import UiInputType


class SplitAxisWidget(AbstractActionWidget):

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        """Creates a new RemapWidget.

        :param action_data profile.InputItem data for this widget
        :param vjoy_devices the list of available vjoy devices
        :param change_cb callback to execute when the widget changes
        :param parent of this widget
        """
        AbstractActionWidget.__init__(
            self,
            action_data,
            vjoy_devices,
            change_cb,
            parent
        )
        assert(isinstance(action_data, SplitAxis))

    def _setup_ui(self):
        # Slider and readout setup
        self.split_slider_layout = QtWidgets.QHBoxLayout()
        self.split_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.split_slider.setRange(-1e5, 1e5)
        self.split_slider.setTickInterval(1e4)
        self.split_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.split_readout = QtWidgets.QDoubleSpinBox()
        self.split_readout.setRange(-1, 1)
        self.split_readout.setSingleStep(0.1)
        self.split_slider_layout.addWidget(self.split_slider)
        self.split_slider_layout.addWidget(self.split_readout)

        # Connect slider and spinner
        self.split_slider.valueChanged.connect(self._update_readout)
        self.split_readout.valueChanged.connect(self._update_slider)

        # Device selection
        self.split_device_layout = QtWidgets.QHBoxLayout()
        self.vjoy_selector_1 = action_plugins.common.VJoySelector(
            self.vjoy_devices,
            self.change_cb,
            [UiInputType.JoystickAxis]
        )
        self.vjoy_selector_2 = action_plugins.common.VJoySelector(
            self.vjoy_devices,
            self.change_cb,
            [UiInputType.JoystickAxis]
        )
        self.split_device_layout.addWidget(self.vjoy_selector_1)
        self.split_device_layout.addWidget(self.vjoy_selector_2)

        # Assemble complete UI
        self.main_layout.addLayout(self.split_slider_layout)
        self.main_layout.addLayout(self.split_device_layout)

    def to_profile(self):
        tmp = self.vjoy_selector_1.get_selection()
        self.action_data.axis1 = (tmp["device_id"], tmp["input_id"])
        tmp = self.vjoy_selector_2.get_selection()
        self.action_data.axis2 = (tmp["device_id"], tmp["input_id"])
        self.action_data.center_point = self.split_readout.value()
        self.action_data.is_valid = True

    def initialize_from_profile(self, action_data):
        self.action_data = action_data

        if self.action_data.is_valid:
            self.split_slider.setValue(self.action_data.center_point * 1e5)
            self.split_readout.setValue(self.action_data.center_point)
            self.vjoy_selector_1.set_selection(
                UiInputType.JoystickAxis,
                self.action_data.axis1[0],
                self.action_data.axis1[1]
            )
            self.vjoy_selector_2.set_selection(
                UiInputType.JoystickAxis,
                self.action_data.axis2[0],
                self.action_data.axis2[1]
            )

    def _update_readout(self, value):
        self.split_readout.setValue(value / 1e5)
        self.change_cb()

    def _update_slider(self, value):
        self.split_slider.setValue(value * 1e5)
        self.change_cb()


class SplitAxis(AbstractAction):

    name = "Split Axis"
    tag = "split-axis"
    widget = SplitAxisWidget
    input_types = [
        UiInputType.JoystickAxis
    ]
    callback_params = ["vjoy"]

    def __init__(self, parent):
        AbstractAction.__init__(self, parent)

        self.center_point = 0.0
        self.axis1 = None
        self.axis2 = None

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def _parse_xml(self, node):
        self.center_point = float(node.get("center-point"))
        self.axis1 = (int(node.get("device1")), int(node.get("axis1")))
        self.axis2 = (int(node.get("device2")), int(node.get("axis2")))

    def _generate_xml(self):
        node = ElementTree.Element("split-axis")
        node.set("center-point", str(self.center_point))
        node.set("device1", str(self.axis1[0]))
        node.set("axis1", str(self.axis1[1]))
        node.set("device2", str(self.axis2[0]))
        node.set("axis2", str(self.axis2[1]))
        return node

    def _generate_code(self):
        return self._code_generation("split_axis", {"entry": self})


version = 1
name = "split-axis"
create = SplitAxis
