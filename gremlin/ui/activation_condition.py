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

from PyQt5 import QtCore, QtWidgets

import logging

from gremlin import base_classes, input_devices, macro
from gremlin.common import InputType
from . import common


class ActivationConditionWidget(QtWidgets.QWidget):

    # Signal which is emitted whenever the widget's contents change
    activation_condition_modified = QtCore.pyqtSignal()

    # Maps activation type name to index
    activation_type_to_index = {
        None: 0,
        "action": 1,
        "container": 2
    }

    def __init__(self, profile_data, parent=None):
        super().__init__(parent)
        self.profile_data = profile_data
        self.main_layout = QtWidgets.QVBoxLayout(self)
        # self.setTitle("Activation Condition")
        self._create_ui()

    def _create_ui(self):
        self.granularity_selector = QtWidgets.QComboBox()
        self.granularity_selector.addItem("None")
        self.granularity_selector.addItem("Action")
        self.granularity_selector.addItem("Container")
        self.granularity_selector.setCurrentIndex(
            ActivationConditionWidget.activation_type_to_index[
                self.profile_data.activation_condition_type
            ]
        )
        self.granularity_selector.currentIndexChanged.connect(
            self._granularity_changed_cb
        )

        self.controls_layout = QtWidgets.QHBoxLayout()
        self.controls_layout.addWidget(QtWidgets.QLabel("Condition on: "))
        self.controls_layout.addWidget(self.granularity_selector)
        self.controls_layout.addStretch()

        self.main_layout.addLayout(self.controls_layout)

        if self.profile_data.activation_condition_type == "container":
            self.condition_model = ConditionModel(
                self.profile_data.activation_condition
            )
            self.condition_view = ConditionView()
            self.condition_view.set_model(self.condition_model)
            self.condition_view.redraw()
            self.main_layout.addWidget(self.condition_view)

        self.main_layout.addStretch()

    def _granularity_changed_cb(self, index):
        index_to_type = {
            0: None,
            1: "action",
            2: "container"
        }
        self.profile_data.activation_condition_type = index_to_type[index]

        if self.profile_data.activation_condition_type == "container":
            if self.profile_data.activation_condition is None:
                self.profile_data.activation_condition = \
                    base_classes.ActivationCondition()
            else:
                self.profile_data.activation_condition = None

        self.activation_condition_modified.emit()


class AbstractConditionWidget(QtWidgets.QWidget):

    deleted = QtCore.pyqtSignal(base_classes.AbstractCondition)

    def __init__(self, condition_data, parent=None):
        super().__init__(parent)
        self.condition_data = condition_data

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self._create_ui()

    def _create_ui(self):
        pass


class KeyboardConditionWidget(AbstractConditionWidget):

    def __init__(self, condition_data, parent=None):
        super().__init__(condition_data, parent)

    def _create_ui(self):
        self.key_label = QtWidgets.QLabel("Not set")
        if self.condition_data.scan_code is not None:
            self.key_label.setText("<b>{}</b>".format(
                macro.key_from_code(
                    self.condition_data.scan_code,
                    self.condition_data.is_extended
                ).name
            ))
        self.record_button = QtWidgets.QPushButton("Change")
        self.record_button.clicked.connect(self._request_user_input)
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.clicked.connect(
            lambda: self.deleted.emit(self.condition_data)
        )

        self.comparison_dropdown = QtWidgets.QComboBox()
        self.comparison_dropdown.addItem("Pressed")
        self.comparison_dropdown.addItem("Released")
        if self.condition_data.comparison:
            self.comparison_dropdown.setCurrentText(
                self.condition_data.comparison.capitalize()
            )
        self.comparison_dropdown.currentTextChanged.connect(
            self._comparison_changed_cb
        )

        self.main_layout.addWidget(QtWidgets.QLabel("Activate if"))
        self.main_layout.addWidget(self.key_label)
        self.main_layout.addWidget(QtWidgets.QLabel("is"))
        self.main_layout.addWidget(self.comparison_dropdown)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.record_button)
        self.main_layout.addWidget(self.delete_button)

    def _key_pressed_cb(self, key):
        self.condition_data.scan_code = key.identifier[0]
        self.condition_data.is_extended = key.identifier[1]
        self.condition_data.comparison = self.comparison_dropdown.currentText().lower()
        self.key_label.setText("<b>{}</b>".format(
            macro.key_from_code(
                self.condition_data.scan_code,
                self.condition_data.is_extended
            ).name
        ))

    def _comparison_changed_cb(self, text):
        self.condition_data.comparison = text.lower()

    def _request_user_input(self):
        """Prompts the user for the input to bind to this item."""
        self.button_press_dialog = common.InputListenerWidget(
            self._key_pressed_cb,
            [InputType.Keyboard],
            return_kb_event=True,
            multi_keys=False
        )

        # Display the dialog centered in the middle of the UI
        root = self
        while root.parent():
            root = root.parent()
        geom = root.geometry()

        self.button_press_dialog.setGeometry(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
            300,
            150
        )
        self.button_press_dialog.show()


class JoystickConditionWidget(AbstractConditionWidget):

    def __init__(self, condition_data, parent=None):
        self.input_event = None
        super().__init__(condition_data, parent)

    def _create_ui(self):
        common.clear_layout(self.main_layout)

        self.record_button = QtWidgets.QPushButton("Change")
        self.record_button.clicked.connect(self._request_user_input)
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.clicked.connect(
            lambda: self.deleted.emit(self.condition_data)
        )

        if self.condition_data.input_type == InputType.JoystickAxis:
            self._axis_ui()
        elif self.condition_data.input_type == InputType.JoystickButton:
            self._button_ui()
        elif self.condition_data.input_type == InputType.JoystickHat:
            self._hat_ui()
        self.main_layout.addWidget(self.record_button)
        self.main_layout.addWidget(self.delete_button)

    def _axis_ui(self):
        self.lower = common.DynamicDoubleSpinBox()
        self.lower.setMinimum(-1.0)
        self.lower.setMaximum(1.0)
        self.lower.setSingleStep(0.05)
        self.lower.setDecimals(4)
        self.lower.setValue(self.condition_data.range[0])
        self.lower.valueChanged.connect(self._range_lower_changed_cb)
        self.upper = common.DynamicDoubleSpinBox()
        self.upper.setMinimum(-1.0)
        self.upper.setMaximum(1.0)
        self.upper.setDecimals(4)
        self.upper.setSingleStep(0.05)
        self.upper.setValue(self.condition_data.range[1])
        self.upper.valueChanged.connect(self._range_upper_changed_cb)

        self.comparison_dropdown = QtWidgets.QComboBox()
        self.comparison_dropdown.addItem("Inside")
        self.comparison_dropdown.addItem("Outside")
        self.comparison_dropdown.setCurrentText(
            self.condition_data.comparison.capitalize()
        )
        self.comparison_dropdown.currentTextChanged.connect(
            self._comparison_changed_cb
        )

        self.main_layout.addWidget(QtWidgets.QLabel(
            "Activate if {} Axis {:d} is".format(
                self.condition_data.device_name,
                self.condition_data.input_id
            )
        ))
        self.main_layout.addWidget(self.comparison_dropdown)
        self.main_layout.addWidget(self.lower)
        self.main_layout.addWidget(QtWidgets.QLabel("and"))
        self.main_layout.addWidget(self.upper)

    def _button_ui(self):
        self.comparison_dropdown = QtWidgets.QComboBox()
        self.comparison_dropdown.addItem("Pressed")
        self.comparison_dropdown.addItem("Released")
        self.comparison_dropdown.setCurrentText(
            self.condition_data.comparison.capitalize()
        )
        self.comparison_dropdown.currentTextChanged.connect(
            self._comparison_changed_cb
        )

        self.main_layout.addWidget(QtWidgets.QLabel(
            "Activate if {} Button {:d} is".format(
                self.condition_data.device_name,
                self.condition_data.input_id
            )
        ))
        self.main_layout.addWidget(self.comparison_dropdown)

    def _hat_ui(self):
        pass

    def _input_pressed_cb(self, event):
        self.condition_data.device_id = event.hardware_id
        self.condition_data.windows_id = event.windows_id
        self.condition_data.input_type = event.event_type
        self.condition_data.input_id = event.identifier
        self.condition_data.device_name = input_devices.JoystickProxy()[event.windows_id].name
        self._create_ui()

    def _request_user_input(self):
        """Prompts the user for the input to bind to this item."""
        self.input_dialog = common.InputListenerWidget(
            self._input_pressed_cb,
            [
                InputType.JoystickAxis,
                InputType.JoystickButton,
                InputType.JoystickHat
            ],
            return_kb_event=False,
            multi_keys=False
        )

        # Display the dialog centered in the middle of the UI
        root = self
        while root.parent():
            root = root.parent()
        geom = root.geometry()

        self.input_dialog.setGeometry(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
            300,
            150
        )
        self.input_dialog.show()

    def _range_lower_changed_cb(self, value):
        self.condition_data.range[0] = value

    def _range_upper_changed_cb(self, value):
        self.condition_data.range[1] = value

    def _comparison_changed_cb(self, text):
        self.condition_data.comparison = text.lower()


class InputActionConditionWidget(AbstractConditionWidget):

    def __init__(self, condition_data, parent=None):
        super().__init__(condition_data, parent)

    def _create_ui(self):
        self.state_dropdown = QtWidgets.QComboBox()
        self.state_dropdown.addItem("Pressed")
        self.state_dropdown.addItem("Released")
        if self.condition_data.comparison:
            self.state_dropdown.setCurrentText(
                self.condition_data.comparison.capitalize()
            )
        self.state_dropdown.currentTextChanged.connect(
            self._state_selection_changed
        )
        self.main_layout.addWidget(
            QtWidgets.QLabel("Activate when (virtual) button is")
        )
        self.main_layout.addWidget(self.state_dropdown)
        self.main_layout.addStretch()

    def _state_selection_changed(self, label):
        self.condition_data.comparison = label.lower()


class ConditionModel(common.AbstractModel):

    def __init__(self, condition_data, parent=None):
        super().__init__(parent)
        self.condition_data = condition_data

    def rows(self):
        return len(self.condition_data.conditions)

    def data(self, index):
        return self.condition_data.conditions[index]

    def add_condition(self, condition_data):
        self.condition_data.conditions.append(condition_data)
        self.data_changed.emit()

    def delete_condition(self, condition_data):
        idx = self.condition_data.conditions.index(condition_data)
        if idx != -1:
            del self.condition_data.conditions[idx]
        self.data_changed.emit()

    @property
    def rule(self):
        return self.condition_data.rule

    @rule.setter
    def rule(self, rule):
        self.condition_data.rule = rule


class ConditionView(common.AbstractView):

    condition_map = {
        "Keyboard": [base_classes.KeyboardCondition,
                     KeyboardConditionWidget],
        "Joystick": [base_classes.JoystickCondition,
                     JoystickConditionWidget],
        "Action": [base_classes.InputActionCondition,
                         InputActionConditionWidget]
    }

    rules_map = {
        "All": base_classes.ActivationCondition.Rules.All,
        "Any": base_classes.ActivationCondition.Rules.Any,
        base_classes.ActivationCondition.Rules.All: "All",
        base_classes.ActivationCondition.Rules.Any: "Any"
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.controls_layout = QtWidgets.QHBoxLayout()
        self.conditions_layout = QtWidgets.QVBoxLayout()

        self.main_layout.addLayout(self.controls_layout)
        self.main_layout.addLayout(self.conditions_layout)

        self.rule_selector = QtWidgets.QComboBox()
        self.rule_selector.addItem("All")
        self.rule_selector.addItem("Any")
        self.rule_selector.currentTextChanged.connect(self._rule_changed_cb)
        self.controls_layout.addWidget(QtWidgets.QLabel("Execute if"))
        self.controls_layout.addWidget(self.rule_selector)
        self.controls_layout.addWidget(QtWidgets.QLabel("condition(s) are met"))

        self.condition_selector = QtWidgets.QComboBox()
        self.condition_selector.addItem("Keyboard")
        self.condition_selector.addItem("Joystick")
        self.condition_selector.addItem("Action")
        self.condition_add_button = QtWidgets.QPushButton("Add")
        self.condition_add_button.clicked.connect(self._add_condition)
        self.controls_layout.addWidget(QtWidgets.QLabel("Add condition"))
        self.controls_layout.addWidget(self.condition_selector)
        self.controls_layout.addWidget(self.condition_add_button)

    def redraw(self):
        common.clear_layout(self.conditions_layout)

        lookup = {}
        for entry in ConditionView.condition_map.values():
            lookup[entry[0]] = entry[1]

        for i in range(self.model.rows()):
            data = self.model.data(i)
            condition_widget = lookup[type(data)](data)
            condition_widget.deleted.connect(
                lambda data: self.model.delete_condition(data)
            )
            self.conditions_layout.addWidget(condition_widget)

    def _add_condition(self):
        data_type = ConditionView.condition_map[
            self.condition_selector.currentText()
        ][0]
        self.model.add_condition(data_type())

    def _rule_changed_cb(self, text):
        self.model.rule = ConditionView.rules_map[text]

    def _model_changed(self):
        self.rule_selector.setCurrentText(
            ConditionView.rules_map[self.model.rule]
        )
