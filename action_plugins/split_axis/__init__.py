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


import logging
import os
from PyQt5 import QtCore, QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
from gremlin.profile import safe_read, safe_format
from gremlin import util
import gremlin.ui.common
import gremlin.ui.input_item


class SplitAxisWidget(gremlin.ui.input_item.AbstractActionWidget):

    def __init__(self, action_data, parent=None):
        """Creates a new RemapWidget.

        :param action_data profile.InputItem data for this widget
        :param parent of this widget
        """
        super().__init__(action_data, parent=parent)
        assert isinstance(action_data, SplitAxis)

    def _create_ui(self):
        # Slider and readout setup
        self.split_slider_layout = QtWidgets.QHBoxLayout()
        self.split_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.split_slider.setRange(-1e5, 1e5)
        self.split_slider.setTickInterval(1e4)
        self.split_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.split_readout = gremlin.ui.common.DynamicDoubleSpinBox()
        self.split_readout.setRange(-1, 1)
        self.split_readout.setSingleStep(0.1)
        self.split_slider_layout.addWidget(self.split_slider)
        self.split_slider_layout.addWidget(self.split_readout)

        # Connect slider and spinner
        self.split_slider.valueChanged.connect(self._update_readout)
        self.split_readout.valueChanged.connect(self._update_slider)

        # Device selection
        self.split_device_layout = QtWidgets.QHBoxLayout()
        self.vjoy_selector_1 = gremlin.ui.common.VJoySelector(
            self._create_vjoy_selector_callback(1),
            [InputType.JoystickAxis]
        )
        self.vjoy_selector_2 = gremlin.ui.common.VJoySelector(
            self._create_vjoy_selector_callback(2),
            [InputType.JoystickAxis]
        )
        self.split_device_layout.addWidget(self.vjoy_selector_1)
        self.split_device_layout.addWidget(self.vjoy_selector_2)

        # Assemble complete UI
        self.main_layout.addLayout(self.split_slider_layout)
        self.main_layout.addLayout(self.split_device_layout)

    def _populate_ui(self):
        self.split_slider.setValue(self.action_data.center_point * 1e5)
        self.split_readout.setValue(self.action_data.center_point)
        try:
            if self.action_data.device_low_vjoy_id is None or \
                    self.action_data.device_low_axis is None:
                self.vjoy_selector_1.set_selection(
                    InputType.JoystickAxis,
                    -1,
                    -1
                )
            else:
                self.vjoy_selector_1.set_selection(
                    InputType.JoystickAxis,
                    self.action_data.device_low_vjoy_id,
                    self.action_data.device_low_axis
                )
            if self.action_data.device_high_vjoy_id is None or \
                    self.action_data.device_high_axis is None:
                self.vjoy_selector_2.set_selection(
                    InputType.JoystickAxis,
                    -1,
                    -1
                )
            else:
                self.vjoy_selector_2.set_selection(
                    InputType.JoystickAxis,
                    self.action_data.device_high_vjoy_id,
                    self.action_data.device_high_axis
                )

            self.save_vjoy_selection(1, self.vjoy_selector_1.get_selection())
            self.save_vjoy_selection(2, self.vjoy_selector_2.get_selection())
        except gremlin.error.GremlinError as e:
            # FIXME: This error here should only have been needed due to the
            #        vJoy selector attempting to acquire a vJoy device, this
            #        should no longer occur, check if this here is still needed
            util.display_error(
                "A needed vJoy device is not accessible: {}\n\n".format(e) +
                "Default values have been set for the input, but they are "
                "not what has been specified."
            )
            logging.getLogger("system").error(str(e))

    def save_vjoy_selection(self, axis_id, data):
        """Stores the data of a vJoy selector.

        A separate method to handle saving the vJoy selection changes is needed
        to prevent overwriting of valid data when updating center point data.

        Parameters
        ----------
        axis_id : int
            Identifier of the axis to save the data of
        """
        if axis_id == 1:
            self.action_data.device_low_vjoy_id = data["device_id"]
            self.action_data.device_low_axis = data["input_id"]
        elif axis_id == 2:
            self.action_data.device_high_vjoy_id = data["device_id"]
            self.action_data.device_high_axis = data["input_id"]

    def save_center_point(self):
        self.action_data.center_point = self.split_readout.value()

    def _update_readout(self, value):
        self.split_readout.setValue(value / 1e5)
        self.save_center_point()

    def _update_slider(self, value):
        self.split_slider.setValue(value * 1e5)
        self.save_center_point()

    def _create_vjoy_selector_callback(self, axis_id):
        """Returns a lambda expression updating the specified axis.

        Parameters
        ----------
        axis_id : int
            Identifier of the axis to save the data of
        Returns
        -------
        lambda
            Callable lambda expression which will update the specified axis
            information
        """
        return lambda data: self.save_vjoy_selection(axis_id, data)


class SplitAxisFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)
        self.action = action
        self.vjoy = gremlin.joystick_handling.VJoyProxy()

    def process_event(self, event, value):
        if value.current < self.action.center_point:
            value_range = -1.0 - self.action.center_point

            self.vjoy[self.action.device_low_vjoy_id].axis(
                self.action.device_low_axis
            ).value = ((value.current - self.action.center_point) /
                       value_range) * 2.0 - 1.0
            self.vjoy[self.action.device_high_vjoy_id].axis(
                self.action.device_high_axis
            ).value = -1.0
        else:
            # Compute value range guarding against division by zero
            value_range = max(1.0 - self.action.center_point, 0.001)

            self.vjoy[self.action.device_high_vjoy_id].axis(
                self.action.device_high_axis
            ).value = ((value.current - self.action.center_point) /
                       value_range) * 2.0 - 1.0
            self.vjoy[self.action.device_low_vjoy_id].axis(
                self.action.device_low_axis
            ).value = -1.0

        return True


class SplitAxis(AbstractAction):

    name = "Split Axis"
    tag = "split-axis"

    default_button_activation = (True, True)
    input_types = [
        InputType.JoystickAxis
    ]

    functor = SplitAxisFunctor
    widget = SplitAxisWidget

    def __init__(self, parent):
        super().__init__(parent)

        self.center_point = 0.0
        self.device_low_axis = None
        self.device_low_vjoy_id = None
        self.device_high_axis = None
        self.device_high_vjoy_id = None

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        return False

    def _parse_xml(self, node):
        self.center_point = float(node.get("center-point"))
        self.device_low_vjoy_id = safe_read(node, "device-low-vjoy-id", int)
        self.device_high_vjoy_id = safe_read(node, "device-high-vjoy-id", int)
        self.device_low_axis = safe_read(node, "device-low-axis", int)
        self.device_high_axis = safe_read(node, "device-high-axis", int)

    def _generate_xml(self):
        node = ElementTree.Element("split-axis")
        node.set("center-point", safe_format(self.center_point, float))
        node.set("device-low-vjoy-id", safe_format(self.device_low_vjoy_id, int))
        node.set("device-high-vjoy-id", safe_format(self.device_high_vjoy_id, int))
        node.set("device-low-axis", safe_format(self.device_low_axis, int))
        node.set("device-high-axis", safe_format(self.device_high_axis, int))

        return node

    def _is_valid(self):
        return True


version = 1
name = "split-axis"
create = SplitAxis
