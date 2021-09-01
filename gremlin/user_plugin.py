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


import enum
import importlib
import inspect
import logging
import os
import random
import string
import uuid

from PyQt5 import QtCore, QtGui, QtWidgets

import dill
from gremlin import common, error, input_devices, joystick_handling, profile, shared_state
import gremlin.ui.common


def get_variable_definitions(fname):
    """Returns all variable definitions contained in the provided module.

    Parameters
    ----------
    fname : str
        module file to process

    Returns
    -------
    list
        Collection of user configurable variables contained within the
        provided module
    """
    if not os.path.isfile(fname):
        return {}

    spec = importlib.util.spec_from_file_location(
        "".join(random.choices(string.ascii_lowercase, k=16)),
        fname
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    variables = {}
    for key, value in module.__dict__.items():
        if isinstance(value, AbstractVariable):
            if value.label in variables:
                logging.getLogger("system").error(
                    "Plugin: Duplicate label {} present in {} ".format(
                        value.label,
                        fname
                    )
                )
            variables[value.label] = value
    return variables.values()


def clamp_value(value, min_val, max_val):
    """Returns the value clamped to the provided range.

    Parameters
    ----------
    value : Number
        the input value
    min_val : Number
        minimum value
    max_val : Number
        maximum value

    Returns
    -------
    Number
        The input value clamped to the provided range
    """
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return min(max_val, max(min_val, value))


class VariableRegistry:

    """Stores variables of plugin instances."""

    def __init__(self):
        """Creates a new registry instance."""
        self._registry = {}

    def clear(self):
        """Removes all entries in the registry."""
        self._registry = {}

    def set(self, module, name, key, value):
        """Sets the value of a plugin instance variable.

        Parameters
        ----------
        module : str
            Name of the plugin
        name : str
            Name associated with the plugin instance
        key : str
            Variable name
        value : any
            Value of the associated key
        """
        self._get_instance(module, name)[key] = value

    def get(self, module, name, key):
        """Returns the value of a plugin instance variable.

        Parameters
        ----------
        module : str
            Name of the plugin
        name : str
            Name associated with the plugin instance
        key : str
            Variable name

        Returns
        -------
        any
            Value of the associated variable
        """
        return self._get_instance(module, name).get(key, None)

    def _get_instance(self, module, name):
        """Returns all values associated with a particular plugin instance.

        Parameters
        ----------
        module : str
            Name of the plugin
        name : str
            Name associated with the plugin instance

        Returns
        -------
        dict
            List of variable and values associated with the plugin instance
        """
        if module not in self._registry:
            self._registry[module] = {}
        if name not in self._registry[module]:
            self._registry[module][name] = {}

        return self._registry[module][name]


# Global registry for custom module variable values
variable_registry = VariableRegistry()


# Lookup for variable value casting
_cast_variable = {
    common.PluginVariableType.Int: int,
    common.PluginVariableType.Float: float,
    common.PluginVariableType.String: str,
}


def _init_numerical(var, default_value, min_value, max_value):
    """Initialize a numerical variable with the given parameters.

    Parameters
    ----------
    var : AbstractVariable
        Instance that is to be initialized
    default_value : numerical
        Default value for the variable
    min_value : numerical
        Minimum value the variable can take on
    max_value : numerical
        Maximum value the variable can take on
    """
    if not isinstance(var.value, type(default_value)):
        var.value = default_value
    if not isinstance(var.min_value, type(max_value)):
        var.min_value = min_value
    if not isinstance(var.max_value, type(max_value)):
        var.max_value = max_value


class AbstractVariable(QtCore.QObject):

    """Represents the base class of all variables used in plugins."""

    # Signal emitted when the value of the variable changes
    value_changed = QtCore.pyqtSignal(dict)

    def __init__(self, label, description, variable_type, is_optional=False):
        """Creates a new instance.

        Parameters
        ----------
        label : str
            the user facing label given to the variable
        description : str
            description of the variable's function and intent
        variable_type : gremlin.common.PluginVariableType
            data type represented by the variable
        is_optional : bool
            if True the variable is optional and will not impact saving
        """
        super().__init__(None)
        self.label = label
        self.description = description
        self.variable_type = variable_type
        self.variable_set = False
        self.is_optional = is_optional

    def create_ui_element(self):
        """Returns a UI element to configure this variable.

        Returns
        -------
        str
             UI element allowing the configuration of this variable
        """
        raise error.PluginError("create_ui_element method not implemented")

    def get_label(self):
        """Returns the text label to use for UI display purposes.

        Returns
        -------
        str
            text label representing the variable
        """
        label = self.label
        if self.is_optional:
            label += " (optional)"
        return label

    def _load_from_registry(self, identifier):
        """Loads the variable's state from the variable registry.

        Parameters
        ----------
        identifier : (str, str)
            Contains the module name and instance name to use when loading
            content from the variable registry
        """
        if identifier is not None:
            val = variable_registry.get(
                identifier[0],
                identifier[1],
                self.label
            )
            if val is not None:
                self.value = self._process_registry_value(val)
                self.variable_set = True

    def _process_registry_value(self, value):
        """Processes the value obtained from the registry.

        Parameters
        ----------
        value : object
            The registry value associated with this variable

        Returns
        -------
        object
            Processed value suitable for this variable
        """
        raise error.PluginError("_process_registry_value method not implemented")

    def _get_identifier(self):
        """Returns the identifier associated with the module of this variable.

        Attempts to find the identifier for the module. This returns the path
        to the module and the instance name if present, otherwise None is
        returned.

        Returns
        -------
        tuple / None
            Tuple of (file name, instance name) or None
        """
        for frame in inspect.stack():
            identifier = frame.frame.f_locals.get("_CodeRunner__gremlin_identifier", None)
            if identifier is not None:
                return identifier
        return None


class NumericalVariable(AbstractVariable):

    """Base class for numerical variable types."""

    def __init__(
            self,
            label,
            description,
            variable_type,
            initial_value=None,
            min_value=None,
            max_value=None,
            is_optional=False
    ):
        super().__init__(label, description, variable_type, is_optional)

        # Store properties before further constructor business happens which
        # relies on these properties existing
        self.value = initial_value
        self.min_value = min_value
        self.max_value = max_value

    def create_ui_element(self, value):
        layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel(self.get_label())
        label.setToolTip(self.description)
        layout.addWidget(label, 0, 0)

        value_widget = None
        if self.variable_type == common.PluginVariableType.Int:
            value_widget = QtWidgets.QSpinBox()
            value_widget.setRange(self.min_value, self.max_value)
            value_widget.setValue(clamp_value(
                int(value),
                self.min_value,
                self.max_value
            ))
            value_widget.valueChanged.connect(
                lambda x: self.value_changed.emit({"value": x})
            )
        elif self.variable_type == common.PluginVariableType.Float:
            value_widget = QtWidgets.QDoubleSpinBox()
            value_widget.setDecimals(3)
            value_widget.setRange(self.min_value, self.max_value)
            value_widget.setValue(float(value))
            value_widget.valueChanged.connect(
                lambda x: self.value_changed.emit({"value": x})
            )

        if value_widget is not None:
            layout.addWidget(value_widget, 0, 1)
            layout.setColumnStretch(1, 1)

        layout.setColumnMinimumWidth(0, 150)

        return layout

    def _process_registry_value(self, value):
        return clamp_value(
            _cast_variable[self.variable_type](value),
            self.min_value,
            self.max_value
        )


class IntegerVariable(NumericalVariable):

    """Variable representing an integer value."""

    def __init__(
            self,
            label,
            description,
            initial_value=None,
            min_value=None,
            max_value=None,
            is_optional=False
    ):
        super().__init__(
            label,
            description,
            common.PluginVariableType.Int,
            initial_value,
            min_value,
            max_value,
            is_optional
        )

        _init_numerical(self, 0, 0, 10)
        self._load_from_registry(self._get_identifier())


class FloatVariable(NumericalVariable):

    """Variable representing an float value."""

    def __init__(
            self,
            label,
            description,
            initial_value=None,
            min_value=None,
            max_value=None,
            is_optional=False
    ):
        super().__init__(
            label,
            description,
            common.PluginVariableType.Float,
            initial_value,
            min_value,
            max_value,
            is_optional
        )

        _init_numerical(self, 0.0, -1.0, 1.0)
        self._load_from_registry(self._get_identifier())


class BoolVariable(AbstractVariable):

    """Variable representing a boolean value."""

    def __init__(
            self,
            label,
            description,
            initial_value=False,
            is_optional=False
    ):
        super().__init__(
            label,
            description,
            common.PluginVariableType.Bool,
            is_optional
        )

        self.value = initial_value
        if not isinstance(self.value, bool):
            self.default_value = False

        self._load_from_registry(self._get_identifier())

    def create_ui_element(self, value):
        layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel(self.get_label())
        label.setToolTip(self.description)
        layout.addWidget(label, 0, 0)

        value_widget = QtWidgets.QCheckBox()
        if isinstance(value, bool):
            value_widget.setCheckState(
                QtCore.Qt.Checked if value else QtCore.Qt.Unchecked
            )
        value_widget.stateChanged.connect(
            lambda x: self.value_changed.emit({"value": x})
        )

        if value_widget is not None:
            layout.addWidget(value_widget, 0, 1)
            layout.setColumnStretch(1, 1)

        layout.setColumnMinimumWidth(0, 150)

        return layout

    def _process_registry_value(self, value):
        return value


class StringVariable(AbstractVariable):

    """Variable representing a string value."""

    def __init__(
            self,
            label,
            description,
            initial_value=None,
            is_optional=False
    ):
        super().__init__(
            label,
            description,
            common.PluginVariableType.String,
            is_optional
        )

        self.value = initial_value
        if not isinstance(self.value, str):
            self.value = ""

        self._load_from_registry(self._get_identifier())

    def create_ui_element(self, value):
        layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel(self.get_label())
        label.setToolTip(self.description)
        layout.addWidget(label, 0, 0)

        value_widget = QtWidgets.QLineEdit()
        value_widget.setText(str(value))
        value_widget.textChanged.connect(
            lambda x: self.value_changed.emit({"value": x})
        )

        if value_widget is not None:
            layout.addWidget(value_widget, 0, 1)
            layout.setColumnStretch(1, 1)

        layout.setColumnMinimumWidth(0, 150)

        return layout

    def _process_registry_value(self, value):
        return str(value)


class ModeVariable(AbstractVariable):

    """Variable representing a mode present in a profile."""

    def __init__(
            self,
            label,
            description,
            is_optional=False
    ):
        super().__init__(
            label,
            description,
            common.PluginVariableType.Mode,
            is_optional
        )

        self.value = profile.mode_list(shared_state.current_profile)[0]

        self._load_from_registry(self._get_identifier())

    def create_ui_element(self, value):
        layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel(self.get_label())
        label.setToolTip(self.description)
        layout.addWidget(label, 0, 0)

        value_widget = gremlin.ui.common.ModeWidget()
        value_widget.populate_selector(shared_state.current_profile, value)
        value_widget.mode_changed.connect(
            lambda x: self.value_changed.emit({"value": x})
        )

        layout.addWidget(value_widget, 0, 1)
        layout.setColumnStretch(1, 1)

        layout.setColumnMinimumWidth(0, 150)

        return layout

    def _process_registry_value(self, value):
        return value


class VirtualInputVariable(AbstractVariable):

    """Variable representing a vJoy input."""

    def __init__(self, label, description, valid_types=None, is_optional=False):
        super().__init__(
            label,
            description,
            common.PluginVariableType.VirtualInput,
            is_optional
        )

        joystick_handling.vjoy_devices()

        self.valid_types = valid_types
        if self.valid_types is None:
            self.valid_types = [
                common.InputType.JoystickAxis,
                common.InputType.JoystickButton,
                common.InputType.JoystickHat
            ]
        self.value = joystick_handling.select_first_valid_vjoy_input(
            self.valid_types
        )

        self._load_from_registry(self._get_identifier())

    @property
    def input_id(self):
        if isinstance(self.value, dict):
            return self.value.get("input_id", 0)
        else:
            return 0

    @property
    def vjoy_id(self):
        if isinstance(self.value, dict):
            return self.value.get("device_id", 1)
        else:
            return 1

    def set(self, vjoy, event):
        if event.event_type != self.value["input_type"]:
            logging.getLogger("system").warning(
                "Invalid types for vJoy set action for vjoy {} {} {:d}".format(
                    str(self.value["device_id"]),
                    gremlin.common.InputType.to_string(self.value["input_type"]),
                    self.value["input_id"]
                )
            )
            return

        device = vjoy[self.value["device_id"]]
        if self.value["input_type"] == gremlin.common.InputType.JoystickAxis:
            device.axis(self.value["input_id"]).value = event.value
        elif self.value["input_type"] == gremlin.common.InputType.JoystickButton:
            device.button(self.value["input_id"]).is_pressed = event.is_pressed
        elif self.value["input_type"] == gremlin.common.InputType.JoystickHat:
            device.hat(self.value["input_id"]).direction = event.value

    def create_ui_element(self, value):
        layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel(self.get_label())
        label.setToolTip(self.description)
        layout.addWidget(label, 0, 0)

        value_widget = gremlin.ui.common.VJoySelector(
            lambda data: self.value_changed.emit(data),
            self.valid_types
        )
        if value is not None:
            value_widget.set_selection(
                value["input_type"],
                value["device_id"],
                value["input_id"]
            )

        layout.addWidget(value_widget, 0, 1)
        layout.setColumnStretch(1, 1)

        layout.setColumnMinimumWidth(0, 150)

        return layout

    def _process_registry_value(self, value):
        return value


class PhysicalInputVariable(AbstractVariable):

    """Variable representing a physical device input."""

    def __init__(self, label, description, valid_types=None, is_optional=False):
        super().__init__(
            label,
            description,
            common.PluginVariableType.PhysicalInput,
            is_optional
        )

        self.value = None
        self.valid_types = valid_types
        if self.valid_types is None:
            self.valid_types = [
                common.InputType.JoystickAxis,
                common.InputType.JoystickButton,
                common.InputType.JoystickHat
            ]

        self._load_from_registry(self._get_identifier())

    @property
    def input_id(self):
        if isinstance(self.value, dict):
            return self.value.get("input_id", 0)
        else:
            return 0

    @property
    def device_guid(self):
        if isinstance(self.value, dict):
            return self.value.get("device_id", None)
        else:
            return None

    def create_decorator(self, mode_name):
        if self.value is None:
            return gremlin.input_devices.JoystickDecorator(
                "", str(dill.GUID_Invalid), ""
            )
        else:
            return gremlin.input_devices.JoystickDecorator(
                self.value["device_name"],
                str(self.value["device_id"]),
                mode_name
            )

    def create_ui_element(self, value):
        layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel(self.get_label())
        label.setToolTip(self.description)
        layout.addWidget(label, 0, 0)

        value_widget = QtWidgets.QPushButton("Press")
        if value is not None:
            input_id = "{:d}".format(value["input_id"])
            if value["input_type"] == gremlin.common.InputType.JoystickAxis:
                input_id = gremlin.common.AxisNames.to_string(
                    gremlin.common.AxisNames(value["input_id"])
                )
            value_widget.setText("{} {} {}".format(
                value["device_name"],
                gremlin.common.InputType.to_string(value["input_type"]).capitalize(),
                input_id
            ))
        value_widget.clicked.connect(self._record_user_input)

        layout.addWidget(value_widget, 0, 1)
        layout.setColumnStretch(1, 1)

        layout.setColumnMinimumWidth(0, 150)

        return layout

    def _record_user_input(self):
        widget = gremlin.ui.common.InputListenerWidget(
            self._user_input,
            self.valid_types
        )

        # Display the dialog centered in the middle of the UI
        geom = QtWidgets.QApplication.topLevelWindows()[0].geometry()
        widget.setGeometry(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
            300,
            150
        )

        widget.show()

    def _user_input(self, event):
        self.value_changed.emit({
            "device_id": event.device_guid,
            "device_name": dill.DILL.get_device_name(event.device_guid),
            "input_id": event.identifier,
            "input_type": event.event_type,
        })

    def _process_registry_value(self, value):
        return value


class SelectionVariable(AbstractVariable):

    """Permits selecting a value out of a list of possibilities."""

    def __init__(
            self,
            label,
            description,
            option_list,
            default_index=0,
            is_optional=False
    ):
        super().__init__(
            label,
            description,
            common.PluginVariableType.Selection,
            is_optional
        )

        assert(isinstance(option_list, list))
        assert(len(option_list) > 0)

        self.options = list(sorted(set(option_list)))
        self.value = option_list[default_index]

        self._load_from_registry(self._get_identifier())

    def create_ui_element(self, value):
        layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel(self.get_label())
        label.setToolTip(self.description)
        layout.addWidget(label, 0, 0)

        # Populate drop down list
        value_widget = QtWidgets.QComboBox()
        for entry in self.options:
            value_widget.addItem(str(entry))

        # Select correct value if present
        if value in self.options:
            value_widget.setCurrentIndex(self.options.index(value))

        # Hookup selection change callback
        value_widget.currentTextChanged.connect(
            lambda x: self.value_changed.emit({"value": x})
        )

        if value_widget is not None:
            layout.addWidget(value_widget, 0, 1)
            layout.setColumnStretch(1, 1)

        layout.setColumnMinimumWidth(0, 150)

        return layout