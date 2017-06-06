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


from PyQt5 import QtWidgets, QtCore, QtGui

import gremlin


class AbstractActivationConditionWidget(QtWidgets.QGroupBox):

    modified = QtCore.pyqtSignal()

    def __init__(self, condition_data, parent=None):
        super().__init__(parent)
        self.condition_data = condition_data
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self._create_ui()
        self._populate_ui()

    def _create_ui(self):
        gremlin.error.MissingImplementationError(
            "AbstractActivationConditionWidget._create_ui not "
            "implemented in subclass."
        )

    def _populate_ui(self):
        gremlin.error.MissingImplementationError(
            "AbstractActivationConditionWidget._populate_ui not "
            "implemented in subclass."
        )


class AxisActivationConditionWidget(AbstractActivationConditionWidget):

    def __init__(self, condition_data, parent=None):
        super().__init__(condition_data, parent)

    def _create_ui(self):
        self.range_layout = QtWidgets.QHBoxLayout()
        self.lower_limit = QtWidgets.QDoubleSpinBox()
        self.lower_limit.setRange(-1.0, 1.0)
        self.lower_limit.setSingleStep(0.05)
        self.upper_limit = QtWidgets.QDoubleSpinBox()
        self.upper_limit.setRange(-1.0, 1.0)
        self.upper_limit.setSingleStep(0.05)

        self.setTitle("Activate when")
        self.range_layout.addWidget(QtWidgets.QLabel("Axis value is between: "))
        self.range_layout.addWidget(self.lower_limit)
        self.range_layout.addWidget(QtWidgets.QLabel("and"))
        self.range_layout.addWidget(self.upper_limit)
        self.range_layout.addStretch(1)

        self.main_layout.addLayout(self.range_layout)

        self.lower_limit.valueChanged.connect(self._lower_limit_cb)
        self.upper_limit.valueChanged.connect(self._upper_limit_cb)

    def _popuplate_ui(self):
        self.lower_limit.setValue(self.condition_data.lower_limit)
        self.upper_limit.setValue(self.condition_data.upper_limit)

    def _lower_limit_cb(self, value):
        self.condition_data.lower_limit = value
        self.modified.emit()

    def _upper_limit_cb(self, value):
        self.condition_data.upper_limit = value
        self.modified.emit()