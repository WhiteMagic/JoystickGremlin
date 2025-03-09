# -*- coding: utf-8; -*-
import msilib.schema
import xml.etree.ElementTree
# Copyright (C) 2015 - 2024 Lionel Ott
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


from abc import ABC, abstractmethod
import importlib
import inspect
import logging
import os
from pathlib import Path
import random
import string
from typing import Any
import uuid

# from PySide6 import QtCore, QtGui, QtWidgets

# import dill
from gremlin.types import PropertyType
from gremlin import common, error, input_devices, joystick_handling, shared_state


class Script:

    """Represents the prototype of a script."""

    def __init__(self, path: Path=Path(), name: str=""):
        """Creates a new Script."""
        self.path = path
        self.name = name
        self.variables: dict[str, ScriptVariable] = {}

    def is_configured(self) -> bool:
        """Returns if the instance is properly configured.

        Returns:
            True if the instance is fully configured, False otherwise
        """
        is_configured = True
        for var in [v for v in self.variables.values() if not v.is_optional]:
            is_configured &= var.value is not None
        return is_configured

    def has_variable(self, name: str) -> bool:
        """Returns if this instance has a particular variable.

        Args:
            name: ame of the variable to check the existence of

        Returns:
            True if a variable with the given name exists, False otherwise
        """
        return name in self.variables

    def set_variable(self, name: str, variable: ScriptVariable) -> None:
        """Sets the value of a named variable.

        Args:
            name: Name of the variable object to be set
            variable: Variable to store
        """
        self.variables[name] = variable

    def get_variable(self, name: str) -> ScriptVariable:
        """Returns the variable stored under the specified name.

        If no variable with the specified name exists, an empty variable
        will be created and returned.

        Args:
            name: Name of the variable to return

        Returns:
            Variable corresponding to the specified name
        """
        if name not in self.variables:
            var = ScriptVariable(self)
            var.name = name
            self.variables[name] = var

        return self.variables[name]

    def from_xml(self, node: ElementTree.Element) -> None:
        """Initializes the values of this instance based on the node's contents.

        Args:
            node: XML node containing this instance's configuration
        """
        self.path = Path(util.read_property(node, "path", PropertyType.String))
        self.name = util.read_property(node, "name", PropertyType.String)
        for entry in node.iter("variable"):
            variable = ScriptVariable(self)
            variable.from_xml(entry)
            self.variables[variable.name] = variable

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing this instance.

        Returns:
            XML node representing this instance
        """
        node = util.create_node_from_data(
            "script",
            [
                ("path", str(self.path), PropertyType.String),
                ("name", str(self.name), PropertyType.String),
            ]
        )
        for entry in self.variables.values():
            variable_node = entry.to_xml()
            if variable_node is not None:
                node.append(variable_node)
        return node

    def _retrieve_variable_definitions(self):
        """Returns all variable definitions used in the provided script.

        Args:
            path: Path to the script file

        Returns:
            List of variiables used in the script
        """
        self.variables = {}
        if not self.path.is_file():
            return

        spec = importlib.util.spec_from_file_location(
            "".join(random.choices(string.ascii_lowercase, k=16)),
            str(path)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for key, value in module.__dict__.items():
            if isinstance(value, AbstractScriptValue):
                if value.name in self.variables:
                    logging.getLogger("system").error(
                        f"Script: Duplicate label {value.label} present in {path}"
                    )
                self.variables[value.name] = value



class ScriptValue:

    def __init__(self, script: Script):
        pass



class AbstractScriptValue(ABC):

    xml_tag = "abstract"

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool
    ):
        self.name = name
        self.description = description
        self.is_optional = is_optional
        self.is_set = False

    @abstractmethod
    @property
    def value(self) -> Any:
        pass

    @abstractmethod
    @value.setter
    def value(self, value: Any) -> None:
        pass

    def from_xml(self, node: ElementTree.Element) -> None:
        self.name = util.read_property(node, "name", PropertyType.String)
        self.description = \
            util.read_property(node, "description", PropertyType.String)
        self.is_optional = \
            util.read_property(node, "is-optional", PropertyType.Bool)
        self._from_xml(node)

    def to_xml(self) -> ElementTree.Element:
        node = ElementTree.Element("variable")
        node.set("type", self.xml_tag)
        util.append_property_nodes(
            node,
            [
                ["name", self.name, PropertyType.String],
                ["description", self.description, gremlin.PropertyType.String],
                ["is-optional", self.is_optional, PropertyType.Bool],
            ]
        )
        self._to_xml(node)
        return node

    @abstractmethod
    def _from_xml(self, node: ElementTree.Element) -> None:
        pass

    @abstractmethod
    def _to_xml(self, node: ElementTree.Element) -> None:
        pass


class ScriptVariable:

    """A single variable of a user script instance."""

    to_property_type = {
        ScriptVariableType.Int: PropertyType.Int,
        ScriptVariableType.Float: PropertyType.Float,
        ScriptVariableType.String: PropertyType.String,
        ScriptVariableType.Bool: PropertyType.Bool,
        ScriptVariableType.Selection: PropertyType.String,
        ScriptVariableType.Mode: PropertyType.String
    }

    def __init__(self, parent: Script):
        """Creates a new instance.

        Args:
            parent: The parent object of this script
        """
        self.parent = parent
        self.name : str|None = None
        self.type : ScriptVariableType|None = None
        self.value : Any = None
        self.is_optional : bool = False

    def from_xml(self, node: ElementTree.Element) -> None:
        """Initializes the contents of this instance.

        Args:
            node: XML node containing this instance's configuration
        """
        self.name = util.read_property(node, "name", PropertyType.String)
        self.type = util.read_property(
            node, "type", PropertyType.ScriptVariableType
        )
        self.is_optional = util.read_property(
            node, "is-optional", PropertyType.Bool
        )

        match self.type:
            case ScriptVariableType.PhysicalInput:
                self.value = {
                    "device_guid": util.read_property(
                        node, "device-guid", PropertyType.UUID
                    ),
                    "input_id": util.read_property(
                        node, "input-id", PropertyType.Int
                    ),
                    "input_type": util.read_property(
                        node, "input-type", PropertyType.InputType
                    )
                }
            case ScriptVariableType.VirtualInput:
                self.value = {
                    "vjoy_id": util.read_property(
                        node, "vjoy-id", PropertyType.Int
                    ),
                    "input_id": util.read_property(
                        node, "input-id", PropertyType.Int
                    ),
                    "input_type": util.read_property(
                        node, "input-type", PropertyType.InputType
                    )
                }
            case _:
                self.value = util.read_property(
                    node, "value", ScriptVariable.to_property_type[self.type]
                )

    def to_xml(self) -> ElementTree.Element|None:
        """Returns an XML node representing this instance.

        Returns:
            XML node representing this instance
        """
        if self.value is None:
            return None

        node = ElementTree.Element("variable")
        util.append_property_nodes(
            node,
            [
                ["name", self.name, PropertyType.String],
                ["type", self.type, PropertyType.ScriptVariableType],
                ["is-optional", self.is_optional, PropertyType.Bool],
            ]
        )

        # Write out content based on the type
        match self.type:
            case ScriptVariableType.PhysicalInput:
                util.append_property_nodes(
                    node,
                    [
                        ("device-guid", self.value["device_guid"], PropertyType.UUID),
                        ("input-id", self.value["input_id"], PropertyType.Int),
                        ("input-type", self.value["input_type"], PropertyType.InputType),
                    ]
                )
            case ScriptVariableType.VirtualInput:
                util.append_property_nodes(
                    node,
                    [
                        ("vjoy-id", self.value["vjoy_id"], PropertyType.Int),
                        ("input-id", self.value["input_id"], PropertyType.Int),
                        ("input-type", self.value["input_type"], PropertyType.InputType),
                    ]
                )
            case _:
                node.append(util.create_property_node(
                    "value",
                    self.value,
                    ScriptVariable.to_property_type[self.type]
                ))

        return node


class BoolVariable(AbstractScriptValue):

    xml_tag = "bool"

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            initial_value: bool
    ):
        super().__init__(name, description, is_optional)

        self._value = initial_value

    @property
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, value: bool) -> None:
        self._value = value

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.Bool)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self.value, PropertyType.Bool
        ))


class FloatVariable(AbstractScriptValue):

    xml_tag = "float"

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            initial_value: float,
            min_value: float,
            max_value: float,
    ):
        super().__init__(name, description, is_optional)

        self._value = initial_value
        self._min_value = min_value
        self._max_value = max_value

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        self._value = clamp_value(value, self._min_value, self._max_value)

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.Float)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._value, PropertyType.Float
        ))


class IntegerVariable(AbstractScriptValue):

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            initial_value: int,
            min_value: int,
            max_value: int,
    ):
        super().__init__(name, description, is_optional)

        self._value = initial_value
        self._min_value = min_value
        self._max_value = max_value

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        self._value = clamp_value(value, self._min_value, self._max_value)

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.Int)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._value, PropertyType.Int
        ))


class StringVariable(AbstractScriptValue):

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            initial_value: str
    ):
        super().__init__(name, description, is_optional)

        self._value = initial_value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        self._value = value

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.String)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._value, PropertyType.String
        ))


# class ModeVariable(AbstractScriptValue):
#
#     def __init__(self, parent: Script):
#         super().__init__(parent)
#
#     @property
#     def value(self) -> bool:
#         pass
#
#     @value.setter
#     def value(self, value: bool) -> None:
#         pass
#
#     def _from_xml(self, node: ElementTree.Element) -> None:
#         pass
#
#     def _to_xml(self, node: ElementTree.Element) -> None:
#         pass
#
#
# class PhysicalInputVariable(AbstractScriptValue):
#
#     def __init__(self, parent: Script):
#         super().__init__(parent)
#
#     @property
#     def value(self) -> bool:
#         pass
#
#     @value.setter
#     def value(self, value: bool) -> None:
#         pass
#
#     def _from_xml(self, node: ElementTree.Element) -> None:
#         pass
#
#     def _to_xml(self, node: ElementTree.Element) -> None:
#         pass
#
#
# class SelectionVariable(AbstractScriptValue):
#
#     def __init__(self, parent: Script):
#         super().__init__(parent)
#
#     @property
#     def value(self) -> bool:
#         pass
#
#     @value.setter
#     def value(self, value: bool) -> None:
#         pass
#
#     def _from_xml(self, node: ElementTree.Element) -> None:
#         pass
#
#     def _to_xml(self, node: ElementTree.Element) -> None:
#         pass
#
#
# class VirtualInputVariable(AbstractScriptValue):
#
#     def __init__(self, parent: Script):
#         super().__init__(parent)
#
#     @property
#     def value(self) -> bool:
#         pass
#
#     @value.setter
#     def value(self, value: bool) -> None:
#         pass
#
#     def _from_xml(self, node: ElementTree.Element) -> None:
#         pass
#
#     def _to_xml(self, node: ElementTree.Element) -> None:
#         pass

def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Returns the value clamped to the provided range.

    Args:
        value: numerical value to clamp
        min_val: lower bound of the range
        max_val: upper bound of the range

    Returns:
        The input value clamped to the provided range
    """
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return min(max_val, max(min_val, value))


# class VariableRegistry:
#
#     """Stores variables of plugin instances."""
#
#     def __init__(self):
#         """Creates a new registry instance."""
#         self._registry = {}
#
#     def clear(self):
#         """Removes all entries in the registry."""
#         self._registry = {}
#
#     def set(self, script: Path, name: str, key: str, value: Any) -> None:
#         """Sets the value of a script's instance variable.
#
#         Args:
#             script: path to the script
#             name: name associated  with the plugin instance
#             key: name of the variable
#             value: value of the associated key
#         """
#         self._get_instance(script, name)[key] = value
#
#     def get(self, script: Path, name: str, key: str) -> Any:
#         """Returns the value of a script's instance variable.
#
#         Args:
#             script: path to the script
#             name: name associated  with the plugin instance
#             key: name of the variable
#
#         Returns:
#             Value of the associated variable
#         """
#         return self._get_instance(script, name).get(key, None)
#
#     def _get_instance(self, script: Path, name: str) -> dict[str, Any]:
#         """Returns all values associated with a particular plugin instance.
#
#         Args:
#             script: path to the script
#             name: name associated  with the plugin instance
#
#         Returns:
#             Dictionary of variable names and associated values
#         """
#         if script not in self._registry:
#             self._registry[script] = {}
#         if name not in self._registry[script]:
#             self._registry[script][name] = {}
#
#         return self._registry[script][name]
#
#
# # Global registry for custom module variable values
# variable_registry = VariableRegistry()
#
#
# # Lookup for variable value casting
# _cast_variable = {
#     gremlin.types.ScriptVariableType.Int: int,
#     gremlin.types.ScriptVariableType.Float: float,
#     gremlin.types.ScriptVariableType.String: str,
# }
#
#
# def _init_numerical(var, default_value, min_value, max_value):
#     """Initialize a numerical variable with the given parameters.
#
#     Parameters
#     ----------
#     var : AbstractVariable
#         Instance that is to be initialized
#     default_value : numerical
#         Default value for the variable
#     min_value : numerical
#         Minimum value the variable can take on
#     max_value : numerical
#         Maximum value the variable can take on
#     """
#     if not isinstance(var.value, type(default_value)):
#         var.value = default_value
#     if not isinstance(var.min_value, type(max_value)):
#         var.min_value = min_value
#     if not isinstance(var.max_value, type(max_value)):
#         var.max_value = max_value


# class AbstractVariable(QtCore.QObject):
#
#     """Represents the base class of all variables used in plugins."""
#
#     # Signal emitted when the value of the variable changes
#     value_changed = QtCore.Signal(dict)
#
#     def __init__(self, label, description, variable_type, is_optional=False):
#         """Creates a new instance.
#
#         Parameters
#         ----------
#         label : str
#             the user facing label given to the variable
#         description : str
#             description of the variable's function and intent
#         variable_type : gremlin.types.ScriptVariableType
#             data type represented by the variable
#         is_optional : bool
#             if True the variable is optional and will not impact saving
#         """
#         super().__init__(None)
#         self.label = label
#         self.description = description
#         self.variable_type = variable_type
#         self.variable_set = False
#         self.is_optional = is_optional
#
#     def create_ui_element(self):
#         """Returns a UI element to configure this variable.
#
#         Returns
#         -------
#         str
#              UI element allowing the configuration of this variable
#         """
#         raise error.PluginError("create_ui_element method not implemented")
#
#     def get_label(self):
#         """Returns the text label to use for UI display purposes.
#
#         Returns
#         -------
#         str
#             text label representing the variable
#         """
#         label = self.label
#         if self.is_optional:
#             label += " (optional)"
#         return label
#
#     def _load_from_registry(self, identifier):
#         """Loads the variable's state from the variable registry.
#
#         Parameters
#         ----------
#         identifier : (str, str)
#             Contains the module name and instance name to use when loading
#             content from the variable registry
#         """
#         if identifier is not None:
#             val = variable_registry.get(
#                 identifier[0],
#                 identifier[1],
#                 self.label
#             )
#             if val is not None:
#                 self.value = self._process_registry_value(val)
#                 self.variable_set = True
#
#     def _process_registry_value(self, value):
#         """Processes the value obtained from the registry.
#
#         Parameters
#         ----------
#         value : object
#             The registry value associated with this variable
#
#         Returns
#         -------
#         object
#             Processed value suitable for this variable
#         """
#         raise error.PluginError("_process_registry_value method not implemented")
#
#     def _get_identifier(self):
#         """Returns the identifier associated with the module of this variable.
#
#         Attempts to find the identifier for the module. This returns the path
#         to the module and the instance name if present, otherwise None is
#         returned.
#
#         Returns
#         -------
#         tuple / None
#             Tuple of (file name, instance name) or None
#         """
#         for frame in inspect.stack():
#             identifier = frame.frame.f_locals.get("_CodeRunner__gremlin_identifier", None)
#             if identifier is not None:
#                 return identifier
#         return None
#
#
# class NumericalVariable(AbstractVariable):
#
#     """Base class for numerical variable types."""
#
#     def __init__(
#             self,
#             label,
#             description,
#             variable_type,
#             initial_value=None,
#             min_value=None,
#             max_value=None,
#             is_optional=False
#     ):
#         super().__init__(label, description, variable_type, is_optional)
#
#         # Store properties before further constructor business happens which
#         # relies on these properties existing
#         self.value = initial_value
#         self.min_value = min_value
#         self.max_value = max_value
#
#     # def create_ui_element(self, value):
#     #     layout = QtWidgets.QGridLayout()
#     #     label = QtWidgets.QLabel(self.get_label())
#     #     label.setToolTip(self.description)
#     #     layout.addWidget(label, 0, 0)
#     #
#     #     value_widget = None
#     #     if self.variable_type == gremlin.types.ScriptVariableType.Int:
#     #         value_widget = QtWidgets.QSpinBox()
#     #         value_widget.setRange(self.min_value, self.max_value)
#     #         value_widget.setValue(clamp_value(
#     #             int(value),
#     #             self.min_value,
#     #             self.max_value
#     #         ))
#     #         value_widget.valueChanged.connect(
#     #             lambda x: self.value_changed.emit({"value": x})
#     #         )
#     #     elif self.variable_type == gremlin.types.ScriptVariableType.Float:
#     #         value_widget = QtWidgets.QDoubleSpinBox()
#     #         value_widget.setDecimals(3)
#     #         value_widget.setRange(self.min_value, self.max_value)
#     #         value_widget.setValue(float(value))
#     #         value_widget.valueChanged.connect(
#     #             lambda x: self.value_changed.emit({"value": x})
#     #         )
#     #
#     #     if value_widget is not None:
#     #         layout.addWidget(value_widget, 0, 1)
#     #         layout.setColumnStretch(1, 1)
#     #
#     #     layout.setColumnMinimumWidth(0, 150)
#     #
#     #     return layout
#
#     def _process_registry_value(self, value):
#         return clamp_value(
#             _cast_variable[self.variable_type](value),
#             self.min_value,
#             self.max_value
#         )
#
#
# class IntegerVariable(NumericalVariable):
#
#     """Variable representing an integer value."""
#
#     def __init__(
#             self,
#             label,
#             description,
#             initial_value=None,
#             min_value=None,
#             max_value=None,
#             is_optional=False
#     ):
#         super().__init__(
#             label,
#             description,
#             gremlin.types.ScriptVariableType.Int,
#             initial_value,
#             min_value,
#             max_value,
#             is_optional
#         )
#
#         _init_numerical(self, 0, 0, 10)
#         self._load_from_registry(self._get_identifier())
#
#
# class FloatVariable(NumericalVariable):
#
#     """Variable representing an float value."""
#
#     def __init__(
#             self,
#             label,
#             description,
#             initial_value=None,
#             min_value=None,
#             max_value=None,
#             is_optional=False
#     ):
#         super().__init__(
#             label,
#             description,
#             gremlin.types.ScriptVariableType.Float,
#             initial_value,
#             min_value,
#             max_value,
#             is_optional
#         )
#
#         _init_numerical(self, 0.0, -1.0, 1.0)
#         self._load_from_registry(self._get_identifier())
#
#
# class BoolVariable(AbstractVariable):
#
#     """Variable representing a boolean value."""
#
#     def __init__(
#             self,
#             label,
#             description,
#             initial_value=False,
#             is_optional=False
#     ):
#         super().__init__(
#             label,
#             description,
#             gremlin.types.ScriptVariableType.Bool,
#             is_optional
#         )
#
#         self.value = initial_value
#         if not isinstance(self.value, bool):
#             self.default_value = False
#
#         self._load_from_registry(self._get_identifier())
#
#     # def create_ui_element(self, value):
#     #     layout = QtWidgets.QGridLayout()
#     #     label = QtWidgets.QLabel(self.get_label())
#     #     label.setToolTip(self.description)
#     #     layout.addWidget(label, 0, 0)
#     #
#     #     value_widget = QtWidgets.QCheckBox()
#     #     if isinstance(value, bool):
#     #         value_widget.setCheckState(
#     #             QtCore.Qt.Checked if value else QtCore.Qt.Unchecked
#     #         )
#     #     value_widget.stateChanged.connect(
#     #         lambda x: self.value_changed.emit({"value": x})
#     #     )
#     #
#     #     if value_widget is not None:
#     #         layout.addWidget(value_widget, 0, 1)
#     #         layout.setColumnStretch(1, 1)
#     #
#     #     layout.setColumnMinimumWidth(0, 150)
#     #
#     #     return layout
#
#     def _process_registry_value(self, value):
#         return value
#
#
# class StringVariable(AbstractVariable):
#
#     """Variable representing a string value."""
#
#     def __init__(
#             self,
#             label,
#             description,
#             initial_value=None,
#             is_optional=False
#     ):
#         super().__init__(
#             label,
#             description,
#             gremlin.types.ScriptVariableType.String,
#             is_optional
#         )
#
#         self.value = initial_value
#         if not isinstance(self.value, str):
#             self.value = ""
#
#         self._load_from_registry(self._get_identifier())
#
#     # def create_ui_element(self, value):
#     #     layout = QtWidgets.QGridLayout()
#     #     label = QtWidgets.QLabel(self.get_label())
#     #     label.setToolTip(self.description)
#     #     layout.addWidget(label, 0, 0)
#     #
#     #     value_widget = QtWidgets.QLineEdit()
#     #     value_widget.setText(str(value))
#     #     value_widget.textChanged.connect(
#     #         lambda x: self.value_changed.emit({"value": x})
#     #     )
#     #
#     #     if value_widget is not None:
#     #         layout.addWidget(value_widget, 0, 1)
#     #         layout.setColumnStretch(1, 1)
#     #
#     #     layout.setColumnMinimumWidth(0, 150)
#     #
#     #     return layout
#
#     def _process_registry_value(self, value):
#         return str(value)
#
#
# class ModeVariable(AbstractVariable):
#
#     """Variable representing a mode present in a profile."""
#
#     def __init__(
#             self,
#             label,
#             description,
#             is_optional=False
#     ):
#         super().__init__(
#             label,
#             description,
#             gremlin.types.ScriptVariableType.Mode,
#             is_optional
#         )
#
#         self.value = profile.mode_list(shared_state.current_profile)[0]
#
#         self._load_from_registry(self._get_identifier())
#
#     # def create_ui_element(self, value):
#     #     layout = QtWidgets.QGridLayout()
#     #     label = QtWidgets.QLabel(self.get_label())
#     #     label.setToolTip(self.description)
#     #     layout.addWidget(label, 0, 0)
#     #
#     #     value_widget = gremlin.ui.common.ModeWidget()
#     #     value_widget.populate_selector(shared_state.current_profile, value)
#     #     value_widget.mode_changed.connect(
#     #         lambda x: self.value_changed.emit({"value": x})
#     #     )
#     #
#     #     layout.addWidget(value_widget, 0, 1)
#     #     layout.setColumnStretch(1, 1)
#     #
#     #     layout.setColumnMinimumWidth(0, 150)
#     #
#     #     return layout
#
#     def _process_registry_value(self, value):
#         return value
#
#
# class VirtualInputVariable(AbstractVariable):
#
#     """Variable representing a vJoy input."""
#
#     def __init__(self, label, description, valid_types=None, is_optional=False):
#         super().__init__(
#             label,
#             description,
#             gremlin.types.ScriptVariableType.VirtualInput,
#             is_optional
#         )
#
#         joystick_handling.vjoy_devices()
#
#         self.valid_types = valid_types
#         if self.valid_types is None:
#             self.valid_types = [
#                 gremlin.types.InputType.JoystickAxis,
#                 gremlin.types.InputType.JoystickButton,
#                 gremlin.types.InputType.JoystickHat
#             ]
#         self.value = joystick_handling.select_first_valid_vjoy_input(
#             self.valid_types
#         )
#
#         self._load_from_registry(self._get_identifier())
#
#     @property
#     def input_id(self):
#         if isinstance(self.value, dict):
#             return self.value.get("input_id", 0)
#         else:
#             return 0
#
#     @property
#     def vjoy_id(self):
#         if isinstance(self.value, dict):
#             return self.value.get("device_id", 1)
#         else:
#             return 1
#
#     def set(self, vjoy, event):
#         if event.event_type != self.value["input_type"]:
#             logging.getLogger("system").warning(
#                 "Invalid types for vJoy set action for vjoy {} {} {:d}".format(
#                     str(self.value["device_id"]),
#                     gremlin.types.InputType.to_string(self.value["input_type"]),
#                     self.value["input_id"]
#                 )
#             )
#             return
#
#         device = vjoy[self.value["device_id"]]
#         if self.value["input_type"] == gremlin.types.InputType.JoystickAxis:
#             device.axis(self.value["input_id"]).value = event.value
#         elif self.value["input_type"] == gremlin.types.InputType.JoystickButton:
#             device.button(self.value["input_id"]).is_pressed = event.is_pressed
#         elif self.value["input_type"] == gremlin.types.InputType.JoystickHat:
#             device.hat(self.value["input_id"]).direction = event.value
#
#     # def create_ui_element(self, value):
#     #     layout = QtWidgets.QGridLayout()
#     #     label = QtWidgets.QLabel(self.get_label())
#     #     label.setToolTip(self.description)
#     #     layout.addWidget(label, 0, 0)
#     #
#     #     value_widget = gremlin.ui.common.VJoySelector(
#     #         lambda data: self.value_changed.emit(data),
#     #         self.valid_types
#     #     )
#     #     if value is not None:
#     #         value_widget.set_selection(
#     #             value["input_type"],
#     #             value["device_id"],
#     #             value["input_id"]
#     #         )
#     #
#     #     layout.addWidget(value_widget, 0, 1)
#     #     layout.setColumnStretch(1, 1)
#     #
#     #     layout.setColumnMinimumWidth(0, 150)
#     #
#     #     return layout
#
#     def _process_registry_value(self, value):
#         return value
#
#
# class PhysicalInputVariable(AbstractVariable):
#
#     """Variable representing a physical device input."""
#
#     def __init__(self, label, description, valid_types=None, is_optional=False):
#         super().__init__(
#             label,
#             description,
#             gremlin.types.ScriptVariableType.PhysicalInput,
#             is_optional
#         )
#
#         self.value = None
#         self.valid_types = valid_types
#         if self.valid_types is None:
#             self.valid_types = [
#                 gremlin.types.InputType.JoystickAxis,
#                 gremlin.types.InputType.JoystickButton,
#                 gremlin.types.InputType.JoystickHat
#             ]
#
#         self._load_from_registry(self._get_identifier())
#
#     @property
#     def input_id(self):
#         if isinstance(self.value, dict):
#             return self.value.get("input_id", 0)
#         else:
#             return 0
#
#     @property
#     def device_guid(self):
#         if isinstance(self.value, dict):
#             return self.value.get("device_id", None)
#         else:
#             return None
#
#     def create_decorator(self, mode_name):
#         if self.value is None:
#             return gremlin.input_devices.JoystickDecorator(
#                 "", str(dill.GUID_Invalid), ""
#             )
#         else:
#             return gremlin.input_devices.JoystickDecorator(
#                 self.value["device_name"],
#                 str(self.value["device_id"]),
#                 mode_name
#             )
#
#     # def create_ui_element(self, value):
#     #     layout = QtWidgets.QGridLayout()
#     #     label = QtWidgets.QLabel(self.get_label())
#     #     label.setToolTip(self.description)
#     #     layout.addWidget(label, 0, 0)
#     #
#     #     value_widget = QtWidgets.QPushButton("Press")
#     #     if value is not None:
#     #         input_id = "{:d}".format(value["input_id"])
#     #         if value["input_type"] == gremlin.types.InputType.JoystickAxis:
#     #             input_id = gremlin.types.AxisNames.to_string(
#     #                 gremlin.types.AxisNames(value["input_id"])
#     #             )
#     #         value_widget.setText("{} {} {}".format(
#     #             value["device_name"],
#     #             gremlin.types.InputType.to_string(value["input_type"]).capitalize(),
#     #             input_id
#     #         ))
#     #     value_widget.clicked.connect(self._record_user_input)
#     #
#     #     layout.addWidget(value_widget, 0, 1)
#     #     layout.setColumnStretch(1, 1)
#     #
#     #     layout.setColumnMinimumWidth(0, 150)
#     #
#     #     return layout
#
#     # def _record_user_input(self):
#     #     widget = gremlin.ui.common.InputListenerWidget(
#     #         self._user_input,
#     #         self.valid_types
#     #     )
#     #
#     #     # Display the dialog centered in the middle of the UI
#     #     geom = QtWidgets.QApplication.topLevelWindows()[0].geometry()
#     #     widget.setGeometry(
#     #         geom.x() + geom.width() / 2 - 150,
#     #         geom.y() + geom.height() / 2 - 75,
#     #         300,
#     #         150
#     #     )
#     #
#     #     widget.show()
#
#     # def _user_input(self, event):
#     #     self.value_changed.emit({
#     #         "device_id": event.device_guid,
#     #         "device_name": dill.DILL.get_device_name(event.device_guid),
#     #         "input_id": event.identifier,
#     #         "input_type": event.event_type,
#     #     })
#
#     def _process_registry_value(self, value):
#         return value
#
#
# class SelectionVariable(AbstractVariable):
#
#     """Permits selecting a value out of a list of possibilities."""
#
#     def __init__(
#             self,
#             label,
#             description,
#             option_list,
#             default_index=0,
#             is_optional=False
#     ):
#         super().__init__(
#             label,
#             description,
#             gremlin.types.ScriptVariableType.Selection,
#             is_optional
#         )
#
#         assert(isinstance(option_list, list))
#         assert(len(option_list) > 0)
#
#         self.options = list(sorted(set(option_list)))
#         self.value = option_list[default_index]
#
#         self._load_from_registry(self._get_identifier())
#
#     # def create_ui_element(self, value):
#     #     layout = QtWidgets.QGridLayout()
#     #     label = QtWidgets.QLabel(self.get_label())
#     #     label.setToolTip(self.description)
#     #     layout.addWidget(label, 0, 0)
#     #
#     #     # Populate drop down list
#     #     value_widget = QtWidgets.QComboBox()
#     #     for entry in self.options:
#     #         value_widget.addItem(str(entry))
#     #
#     #     # Select correct value if present
#     #     if value in self.options:
#     #         value_widget.setCurrentIndex(self.options.index(value))
#     #
#     #     # Hookup selection change callback
#     #     value_widget.currentTextChanged.connect(
#     #         lambda x: self.value_changed.emit({"value": x})
#     #     )
#     #
#     #     if value_widget is not None:
#     #         layout.addWidget(value_widget, 0, 1)
#     #         layout.setColumnStretch(1, 1)
#     #
#     #     layout.setColumnMinimumWidth(0, 150)
#     #
#     #     return layout