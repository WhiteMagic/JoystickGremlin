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


import threading
import time
import os
from xml.etree import ElementTree

from PyQt5 import QtCore, QtWidgets

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
from gremlin.error import GremlinError
from gremlin.input_devices import ButtonReleaseActions
from gremlin.sendinput import mouse_relative_motion
from gremlin.profile import safe_read
import gremlin.ui.common
import gremlin.ui.input_item


class MapToMouseWidget(gremlin.ui.input_item.AbstractActionWidget):

    """UI widget for mapping inputs to keyboard key combinations."""

    def __init__(self, action_data, parent=None):
        """Creates a new instance.

        :param action_data the data managed by this widget
        :param parent the parent of this widget
        """
        super().__init__(action_data, QtWidgets.QGridLayout, parent=parent)

    def _create_ui(self):
        """Creates the UI components."""
        if self.action_data.get_input_type() == InputType.JoystickAxis:
            self._create_axis_ui()
        elif self.action_data.get_input_type() == InputType.JoystickHat:
            self._create_hat_ui()

    def _create_axis_ui(self):
        self.axis_layout = QtWidgets.QHBoxLayout()
        self.x_axis = QtWidgets.QRadioButton("X Axis")
        self.x_axis.setChecked(True)
        self.y_axis = QtWidgets.QRadioButton("Y Axis")

        self.main_layout.addWidget(QtWidgets.QLabel("Control"), 0, 0, QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(self.x_axis, 0, 1, QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(self.y_axis, 0, 2, 1, 2, QtCore.Qt.AlignLeft)

        self.min_speed = QtWidgets.QSpinBox()
        self.min_speed.setRange(0, 1e5)
        self.max_speed = QtWidgets.QSpinBox()
        self.max_speed.setRange(0, 1e5)
        self.main_layout.addWidget(
            QtWidgets.QLabel("Minimum speed"), 1, 0, QtCore.Qt.AlignLeft
        )
        self.main_layout.addWidget(self.min_speed, 1, 1, QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(
            QtWidgets.QLabel("Maximum speed"), 1, 2, QtCore.Qt.AlignLeft
        )
        self.main_layout.addWidget(self.max_speed, 1, 3, QtCore.Qt.AlignLeft)

        self._connect_axis()

    def _create_hat_ui(self):
        self.min_speed = QtWidgets.QSpinBox()
        self.min_speed.setRange(0, 1e5)
        self.max_speed = QtWidgets.QSpinBox()
        self.max_speed.setRange(0, 1e5)
        self.acceleration = gremlin.ui.common.DynamicDoubleSpinBox()
        self.acceleration.setRange(0.0, 100.0)
        self.acceleration.setValue(0.0)
        self.acceleration.setDecimals(2)
        self.acceleration.setSingleStep(0.1)

        self.main_layout.addWidget(QtWidgets.QLabel("Minimum speed"), 0, 0)
        self.main_layout.addWidget(self.min_speed, 0, 1, QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(QtWidgets.QLabel("Maximum speed"), 0, 2)
        self.main_layout.addWidget(self.max_speed, 0, 3, QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(QtWidgets.QLabel("Acceleration"), 0, 4)
        self.main_layout.addWidget(self.acceleration, 0, 5, QtCore.Qt.AlignLeft)

        self._connect_hat()

    def _populate_ui(self):
        """Populates the UI components."""
        if self.action_data.get_input_type() == InputType.JoystickAxis:
            self._populate_axis_ui()
        elif self.action_data.get_input_type() == InputType.JoystickHat:
            self._populate_hat_ui()

    def _populate_axis_ui(self):
        self._disconnect_axis()
        if self.action_data.axis == "x":
            self.x_axis.setChecked(True)
        else:
            self.y_axis.setChecked(True)

        self.min_speed.setValue(self.action_data.min_speed)
        self.max_speed.setValue(self.action_data.max_speed)
        self._connect_axis()

    def _populate_hat_ui(self):
        self._disconnect_hat()
        self.min_speed.setValue(self.action_data.min_speed)
        self.max_speed.setValue(self.action_data.max_speed)
        self.acceleration.setValue(self.action_data.acceleration)
        self._connect_hat()

    def _update_axis(self):
        self._disconnect_axis()

        min_speed = self.min_speed.value()
        max_speed = self.max_speed.value()
        if min_speed > max_speed:
            # Maximum value was decreased below minimum
            if max_speed != self.action_data.max_speed:
                min_speed = max_speed
            # Minimum value was increased above maximum
            elif min_speed != self.action_data.min_speed:
                max_speed = min_speed
        self.min_speed.setValue(min_speed)
        self.max_speed.setValue(max_speed)

        self.action_data.axis = "x" if self.x_axis.isChecked() else "y"
        self.action_data.min_speed = min_speed
        self.action_data.max_speed = max_speed

        self._connect_axis()

    def _update_hat(self):
        self._disconnect_hat()

        min_speed = self.min_speed.value()
        max_speed = self.max_speed.value()
        if min_speed > max_speed:
            # Maximum value was decreased below minimum
            if max_speed != self.action_data.max_speed:
                min_speed = max_speed
            # Minimum value was increased above maximum
            elif min_speed != self.action_data.min_speed:
                max_speed = min_speed
        self.min_speed.setValue(min_speed)
        self.max_speed.setValue(max_speed)

        self.action_data.min_speed = min_speed
        self.action_data.max_speed = max_speed

        self.action_data.acceleration = self.acceleration.value()

        self._connect_hat()

    def _connect_axis(self):
        self.x_axis.toggled.connect(self._update_axis)
        self.y_axis.toggled.connect(self._update_axis)
        self.min_speed.valueChanged.connect(self._update_axis)
        self.max_speed.valueChanged.connect(self._update_axis)

    def _disconnect_axis(self):
        self.x_axis.toggled.disconnect(self._update_axis)
        self.y_axis.toggled.disconnect(self._update_axis)
        self.min_speed.valueChanged.disconnect(self._update_axis)
        self.max_speed.valueChanged.disconnect(self._update_axis)

    def _connect_hat(self):
        self.min_speed.valueChanged.connect(self._update_hat)
        self.max_speed.valueChanged.connect(self._update_hat)
        self.acceleration.valueChanged.connect(self._update_hat)

    def _disconnect_hat(self):
        self.min_speed.valueChanged.disconnect(self._update_hat)
        self.max_speed.valueChanged.disconnect(self._update_hat)
        self.acceleration.valueChanged.disconnect(self._update_hat)


class MapToMouseFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)

        self.axis = action.axis
        self.min_speed = action.min_speed
        self.max_speed = action.max_speed
        self.acceleration = action.acceleration

        self.mouse_controller = gremlin.sendinput.MouseController()

        if action.get_input_type() == InputType.JoystickAxis:
            self.process_event = lambda x, y: self._process_axis_event(x, y)
        elif action.get_input_type() == InputType.JoystickHat:
            self.process_event = lambda x, y: self._process_hat_event(x, y)

    def process_event(self, event, value):
        raise GremlinError(
            "MapToMouseFunctor.process_event should never be called"
        )

    def _process_axis_event(self, event, value):
        delta_motion = round(
            self.min_speed + value.current * (self.max_speed - self.min_speed)
        )
        delta_motion = 0.0 if abs(value.current) < 0.05 else delta_motion

        if self.axis == "x":
            self.mouse_controller.dx = delta_motion
        else:
            self.mouse_controller.dy = delta_motion

    def _process_hat_event(self, event, value):
        self.mouse_controller.acceleration = self.acceleration
        self.mouse_controller.dx = value.current[0] * self.min_speed
        self.mouse_controller.dy = -value.current[1] * self.min_speed
        self.mouse_controller.max_speed = self.max_speed

        if value.current == (0, 0):
            self.mouse_controller.acceleration = 0.0
            self.mouse_controller.dx = 0
            self.mouse_controller.dy = 0


class MapToKeyboard(AbstractAction):

    """Action data for the map to mouse action.

    Map to mouse allows controlling of the mouse cursor using either a joystick
    or a hat.
    """

    name = "Map to Mouse"
    tag = "map-to-mouse"

    default_button_activation = (True, True)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickHat,
    ]

    functor = MapToMouseFunctor
    widget = MapToMouseWidget

    def __init__(self, parent):
        """Creates a new instance.

        :param parent the container this action is part of
        """
        super().__init__(parent)
        assert self.get_input_type() in [
            InputType.JoystickAxis,
            InputType.JoystickHat
        ]

        self.axis = None
        self.min_speed = 0
        self.max_speed = 0
        self.acceleration = 0

    def icon(self):
        """Returns the icon to use for this action.

        :return icon representing this action
        """
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        """Returns whether or not an activation condition is needed.

        :return True if an activation condition is required for this particular
            action instance, False otherwise
        """
        return False

    def _parse_xml(self, node):
        """Reads the contents of an XML node to populate this instance.

        :param node the node whose content should be used to populate this
            instance
        """
        self.axis = safe_read(node, "axis", default_value="x")
        self.min_speed = safe_read(node, "min-speed", int, 5)
        self.max_speed = safe_read(node, "max-speed", int, 5)
        self.acceleration = safe_read(node, "acceleration", float, 0.0)

    def _generate_xml(self):
        """Returns an XML node containing this instance's information.

        :return XML node containing the information of this  instance
        """
        node = ElementTree.Element("map-to-mouse")
        if self.get_input_type() == InputType.JoystickAxis:
            node.set("axis", str(self.axis))
            node.set("min-speed", str(self.min_speed))
            node.set("max-speed", str(self.max_speed))
        elif self.get_input_type() == InputType.JoystickHat:
            node.set("min-speed", str(self.min_speed))
            node.set("max-speed", str(self.max_speed))
            node.set("acceleration", str(self.acceleration))
        return node

    def _is_valid(self):
        """Returns whether or not this action is valid.

        :return True if the action is configured correctly, False otherwise
        """
        return True


version = 1
name = "map-to-mouse"
create = MapToKeyboard
