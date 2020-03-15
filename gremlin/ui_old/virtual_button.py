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


from PyQt5 import QtWidgets, QtCore, QtGui

import gremlin


class AbstractVirtualButtonWidget(QtWidgets.QGroupBox):

    """Base class for activation condition widgets."""

    virtual_button_modified = QtCore.pyqtSignal()

    def __init__(self, condition_data, parent=None, layout_direction="vertical"):
        """Creates a new activation condition widget.

        :param condition_data the data managed by the widget
        :param parent the parent of the widget
        :param layout_direction which layout direction to use, vertical or
            horizontal
        """
        super().__init__(parent)
        self.condition_data = condition_data
        if layout_direction == "vertical":
            self.main_layout = QtWidgets.QVBoxLayout(self)
        else:
            self.main_layout = QtWidgets.QHBoxLayout(self)

        self._create_ui()
        self._populate_ui()

    def _create_ui(self):
        """Creates all required UI elements."""
        raise gremlin.error.MissingImplementationError(
            "AbstractVirtualButtonWidget._create_ui not "
            "implemented in subclass."
        )

    def _populate_ui(self):
        """Populates the UI elements with data."""
        raise gremlin.error.MissingImplementationError(
            "AbstractVirtualButtonWidget._populate_ui not "
            "implemented in subclass."
        )


class VirtualAxisButtonWidget(AbstractVirtualButtonWidget):

    """Condition widget for axis, turning an axis area into a button."""

    def __init__(self, condition_data, parent=None):
        """Creates a new axis activation condition widget.

        :param condition_data the data managed by the widget
        :param parent the parent of the widget
        """
        super().__init__(condition_data, parent)

    def _create_ui(self):
        """Creates all required UI elements."""
        self.range_layout = QtWidgets.QHBoxLayout()
        self.lower_limit = gremlin.ui.common.DynamicDoubleSpinBox()
        self.lower_limit.setRange(-1.0, 1.0)
        self.lower_limit.setSingleStep(0.05)
        self.upper_limit = gremlin.ui.common.DynamicDoubleSpinBox()
        self.upper_limit.setRange(-1.0, 1.0)
        self.upper_limit.setSingleStep(0.05)
        self.direction = QtWidgets.QComboBox()
        self.direction.addItem("Anywhere")
        self.direction.addItem("Above")
        self.direction.addItem("Below")

        self.setTitle("Virtual Button")
        self.range_layout.addWidget(
            QtWidgets.QLabel("Activate when axis is between: ")
        )
        self.range_layout.addWidget(self.lower_limit)
        self.range_layout.addWidget(QtWidgets.QLabel("and"))
        self.range_layout.addWidget(self.upper_limit)
        self.range_layout.addWidget(
            QtWidgets.QLabel("when entering the range from")
        )
        self.range_layout.addWidget(self.direction)

        self.range_layout.addStretch(1)

        self.help_button = QtWidgets.QPushButton(QtGui.QIcon("gfx/help"), "")
        self.help_button.clicked.connect(self._show_hint)
        self.range_layout.addWidget(self.help_button)

        self.main_layout.addLayout(self.range_layout)

        self.lower_limit.valueChanged.connect(self._lower_limit_cb)
        self.upper_limit.valueChanged.connect(self._upper_limit_cb)
        self.direction.currentTextChanged.connect(self._direction_changed_cb)

    def _populate_ui(self):
        """Populates the UI elements with data."""
        self.lower_limit.setValue(self.condition_data.lower_limit)
        self.upper_limit.setValue(self.condition_data.upper_limit)
        self.direction.setCurrentText(
            gremlin.common.AxisButtonDirection.to_string(
                self.condition_data.direction
            ).capitalize()
        )

    def _lower_limit_cb(self, value):
        """Updates the lower limit value.

        :param value the new value of the virtual button's lower limit
        """
        self.condition_data.lower_limit = value
        self.virtual_button_modified.emit()

    def _upper_limit_cb(self, value):
        """Updates the upper limit value.

        :param value the new value of the virtual button's upper limit
        """
        self.condition_data.upper_limit = value
        self.virtual_button_modified.emit()

    def _direction_changed_cb(self, value):
        self.condition_data.direction = \
            gremlin.common.AxisButtonDirection.to_enum(value.lower())
        self.virtual_button_modified.emit()

    def _show_hint(self):
        """Displays a hint explaining the activation condition."""
        QtWidgets.QWhatsThis.showText(
            self.help_button.mapToGlobal(QtCore.QPoint(0, 10)),
            gremlin.hints.hint.get("axis-condition", "")
        )


class VirtualHatButtonWidget(AbstractVirtualButtonWidget):

    """Condition widget for hats, turning a set of directions into a button."""

    def __init__(self, condition_data, parent=None):
        """Creates a new hat activation condition widget.

        :param condition_data the data managed by the widget
        :param parent the parent of the widget
        """
        self._widgets = {}
        super().__init__(condition_data, parent, "horizontal")

    def _create_ui(self):
        """Creates all required UI elements."""
        self.setTitle("Virtual Button")

        directions = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]

        for direction in directions:
            self._widgets[direction] = QtWidgets.QCheckBox()
            self._widgets[direction].setIcon(
                QtGui.QIcon("gfx/hat_{}.png".format(direction))
            )
            self._widgets[direction].toggled.connect(
                self._create_state_changed_cb(direction)
            )
            self.main_layout.addWidget(self._widgets[direction])

        self.main_layout.addStretch(1)

        self.help_button = QtWidgets.QPushButton(QtGui.QIcon("gfx/help"), "")
        self.help_button.clicked.connect(self._show_hint)
        self.main_layout.addWidget(self.help_button)

    def _populate_ui(self):
        """Populates the UI elements with data."""
        direction_map = {
            "north": "n",
            "north-east": "ne",
            "east": "e",
            "south-east": "se",
            "south": "s",
            "south-west": "sw",
            "west": "w",
            "north-west": "nw"
        }

        for direction in self.condition_data.directions:
            self._widgets[direction_map[direction]].setCheckState(
                QtCore.Qt.Checked
            )

    def _state_changed(self, direction, state):
        """Updates the set of directions making up the button.

        :param direction the direction being modified
        :param state the change being performed
        """
        direction_map = {
            "n": "north",
            "ne": "north-east",
            "e": "east",
            "se": "south-east",
            "s": "south",
            "sw": "south-west",
            "w": "west",
            "nw": "north-west"
        }

        name = direction_map[direction]
        if state is False and name in self.condition_data.directions:
            idx = self.condition_data.directions.index(name)
            del self.condition_data.directions[idx]
        elif state is True and name not in self.condition_data.directions:
            self.condition_data.directions.append(name)
        self.condition_data.directions = \
            list(set(self.condition_data.directions))

    def _create_state_changed_cb(self, direction):
        """Creates a state change callback.

        :param direction the direction for which to customize the callback
        :return callback function to update the state of a direction
        """
        return lambda x: self._state_changed(direction, x)

    def _show_hint(self):
        """Displays a hint explaining the activation condition."""
        QtWidgets.QWhatsThis.showText(
            self.help_button.mapToGlobal(QtCore.QPoint(0, 10)),
            gremlin.hints.hint.get("hat-condition", "")
        )
