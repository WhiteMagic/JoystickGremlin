# -*- coding: utf-8; -*-

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


from __future__ import annotations


from abc import ABC, abstractmethod
from collections.abc import Sequence
import importlib
import inspect
import logging
import os
from pathlib import Path
import random
import string
from typing import Any
import uuid
from xml.etree import ElementTree

from gremlin.types import InputType, PropertyType
from gremlin import common, error, joystick_handling, shared_state, util


class Script:

    """Represents the prototype of a script."""

    def __init__(self, path: Path=Path(), name: str=""):
        """Creates a new Script."""
        self.path = path
        self.name = name
        self.variables: dict[str, AbstractVariable] = {}

        if self.path.is_file():
            self._retrieve_variable_definitions()

    @property
    def is_configured(self) -> bool:
        """Returns if the instance is fully configured.

        Returns:
            True if the instance is fully configured, False otherwise
        """
        return all([
            var.value is not None for var in self.variables.values()
            if not var.is_optional
        ])

    def has_variable(self, name: str) -> bool:
        """Returns if this instance has a particular variable.

        Args:
            name: name of the variable to check the existence of

        Returns:
            True if a variable with the given name exists, False otherwise
        """
        return name in self.variables

    def set_variable(self, name: str, variable: AbstractVariable) -> None:
        """Sets the value of a named variable.

        Args:
            name: Name of the variable object to be set
            variable: Variable to store
        """
        self.variables[name] = variable

    def get_variable(self, name: str) -> AbstractVariable:
        """Returns the variable stored under the specified name.

        Attempting to retrieve a non-existent variable will raise an error.

        Args:
            name: Name of the variable to return

        Returns:
            Variable corresponding to the specified name
        """
        if not self.has_variable(name):
            raise error.GremlinError(
                f"Script '{self.path}' does not contain a variable '{name}'"
            )
        return self.variables[name]

    def from_xml(self, node: ElementTree.Element) -> None:
        """Initializes the values of this instance based on the node's contents.

        Args:
            node: XML node containing this instance's configuration
        """
        lookup = {
            "bool": BoolVariable,
            "float": FloatVariable,
            "int": IntegerVariable,
            "mode": ModeVariable,
            "physical-input": PhysicalInputVariable,
            "selection": SelectionVariable,
            "string": StringVariable,
            "vjoy": VirtualInputVariable,
        }

        self.path = Path(util.read_property(node, "path", PropertyType.String))
        self.name = util.read_property(node, "name", PropertyType.String)

        # Retrieve variable information from the script and instantiate them
        self._retrieve_variable_definitions()

        # Populate variables with data from the XML if they are present
        for entry in node.iter("variable"):
            name = util.read_property(entry, "name", PropertyType.String)
            print(name)
            # Don't parse variables that don't exist anymore, they will be
            # removed upon the next save
            if name not in self.variables:
                logging.getLogger("system").warning(
                    f"Script: Unknown variable '{name}' ignored"
                )
                continue
            type_name = entry.get("type")
            if not isinstance(self.variables[name], lookup[type_name]):
                raise error.GremlinError(
                    f"Script: Type mismatch, profile contains '{type_name}' " + \
                    f"while script expects '{self.variables[name]}'"
                )
            self.variables[name].from_xml(entry)

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
            raise error.GremlinError(f"Invalid script file '{self.path}'")

        spec = importlib.util.spec_from_file_location(
            "".join(random.choices(string.ascii_lowercase, k=16)),
            str(self.path)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for key, value in module.__dict__.items():
            if isinstance(value, AbstractVariable):
                if value.name in self.variables:
                    logging.getLogger("system").error(
                        f"Script: Duplicate label {value.label} present in {path}"
                    )
                self.variables[value.name] = value


class AbstractVariable(ABC):

    xml_tag = "abstract"

    def __init__(
            self,
            name: str|None=None,
            description: str="",
            is_optional: bool=True
    ):
        self.name = name
        self.description = description
        self.is_optional = is_optional
        self.is_set = False

    @property
    @abstractmethod
    def value(self) -> Any:
        pass

    @value.setter
    @abstractmethod
    def value(self, value: Any) -> None:
        pass

    def from_xml(self, node: ElementTree.Element) -> None:
        self.name = util.read_property(node, "name", PropertyType.String)
        self._from_xml(node)

    def to_xml(self) -> ElementTree.Element:
        node = ElementTree.Element("variable")
        node.set("type", self.xml_tag)
        util.append_property_nodes(
            node,
            [
                ["name", self.name, PropertyType.String]
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


# class ScriptVariable:
#
#     """A single variable of a user script instance."""
#
#     to_property_type = {
#         ScriptVariableType.Int: PropertyType.Int,
#         ScriptVariableType.Float: PropertyType.Float,
#         ScriptVariableType.String: PropertyType.String,
#         ScriptVariableType.Bool: PropertyType.Bool,
#         ScriptVariableType.Selection: PropertyType.String,
#         ScriptVariableType.Mode: PropertyType.String
#     }
#
#     def __init__(self, parent: Script):
#         """Creates a new instance.
#
#         Args:
#             parent: The parent object of this script
#         """
#         self.parent = parent
#         self.name : str|None = None
#         self.type : ScriptVariableType|None = None
#         self.value : Any = None
#         self.is_optional : bool = False
#
#     def from_xml(self, node: ElementTree.Element) -> None:
#         """Initializes the contents of this instance.
#
#         Args:
#             node: XML node containing this instance's configuration
#         """
#         self.name = util.read_property(node, "name", PropertyType.String)
#         self.type = util.read_property(
#             node, "type", PropertyType.ScriptVariableType
#         )
#         self.is_optional = util.read_property(
#             node, "is-optional", PropertyType.Bool
#         )
#
#         match self.type:
#             case ScriptVariableType.PhysicalInput:
#                 self.value = {
#                     "device_guid": util.read_property(
#                         node, "device-guid", PropertyType.UUID
#                     ),
#                     "input_id": util.read_property(
#                         node, "input-id", PropertyType.Int
#                     ),
#                     "input_type": util.read_property(
#                         node, "input-type", PropertyType.InputType
#                     )
#                 }
#             case ScriptVariableType.VirtualInput:
#                 self.value = {
#                     "vjoy_id": util.read_property(
#                         node, "vjoy-id", PropertyType.Int
#                     ),
#                     "input_id": util.read_property(
#                         node, "input-id", PropertyType.Int
#                     ),
#                     "input_type": util.read_property(
#                         node, "input-type", PropertyType.InputType
#                     )
#                 }
#             case _:
#                 self.value = util.read_property(
#                     node, "value", ScriptVariable.to_property_type[self.type]
#                 )
#
#     def to_xml(self) -> ElementTree.Element|None:
#         """Returns an XML node representing this instance.
#
#         Returns:
#             XML node representing this instance
#         """
#         if self.value is None:
#             return None
#
#         node = ElementTree.Element("variable")
#         util.append_property_nodes(
#             node,
#             [
#                 ["name", self.name, PropertyType.String],
#                 ["type", self.type, PropertyType.ScriptVariableType],
#                 ["is-optional", self.is_optional, PropertyType.Bool],
#             ]
#         )
#
#         # Write out content based on the type
#         match self.type:
#             case ScriptVariableType.PhysicalInput:
#                 util.append_property_nodes(
#                     node,
#                     [
#                         ("device-guid", self.value["device_guid"], PropertyType.UUID),
#                         ("input-id", self.value["input_id"], PropertyType.Int),
#                         ("input-type", self.value["input_type"], PropertyType.InputType),
#                     ]
#                 )
#             case ScriptVariableType.VirtualInput:
#                 util.append_property_nodes(
#                     node,
#                     [
#                         ("vjoy-id", self.value["vjoy_id"], PropertyType.Int),
#                         ("input-id", self.value["input_id"], PropertyType.Int),
#                         ("input-type", self.value["input_type"], PropertyType.InputType),
#                     ]
#                 )
#             case _:
#                 node.append(util.create_property_node(
#                     "value",
#                     self.value,
#                     ScriptVariable.to_property_type[self.type]
#                 ))
#
#         return node


class BoolVariable(AbstractVariable):

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


class FloatVariable(AbstractVariable):

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

    @property
    def min_value(self) -> float:
        return self._min_value

    @property
    def max_value(self) -> float:
        return self._max_value

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.Float)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._value, PropertyType.Float
        ))


class IntegerVariable(AbstractVariable):

    xml_tag = "int"

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

    @property
    def min_value(self) -> int:
        return self._min_value

    @property
    def max_value(self) -> int:
        return self._max_value

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.Int)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._value, PropertyType.Int
        ))


class ModeVariable(AbstractVariable):

    xml_tag = "mode"

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool
    ):
        super().__init__(name, description, is_optional)

        self._mode = shared_state.current_profile.modes.first_mode

    @property
    def value(self) -> str:
        return self._mode

    @value.setter
    def value(self, value: str) -> None:
        self._mode = value

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._mode = util.read_property(node, "value", PropertyType.String)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._mode, PropertyType.String
        ))


class SelectionVariable(AbstractVariable):

    xml_tag = "selection"

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            option_list: Sequence[str],
            default_index: int=0
    ):
        super().__init__(name, description, is_optional)

        self._option_list = option_list
        self._current_index = default_index

    @property
    def options(self) -> list[str]:
        return self._option_list

    @property
    def value(self) -> str:
        return self._option_list[self._current_index]

    @value.setter
    def value(self, value: str) -> None:
        self._current_index = self._option_list.index(value)

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._current_index = util.read_property(
            node, "index", PropertyType.Int
        )

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "index", self._current_index, PropertyType.Int
        ))


class StringVariable(AbstractVariable):

    xml_tag = "string"

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


class PhysicalInputVariable(AbstractVariable):

    xml_tag = "physical-input"

    type Identifier = tuple[uuid.UUID, InputType, int]

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            valid_types: Sequence[InputType],
    ):
        super().__init__(name, description, is_optional)

        self._valid_types = valid_types
        self._device_guid = None
        self._input_type = valid_types[0]
        self._input_id = 1

    @property
    def device_guid(self) -> uuid.UUID:
        return self._device_guid

    @property
    def input_type(self) -> InputType:
        return self._input_type

    @property
    def input_id(self) -> int:
        return self._input_id

    @property
    def value(self) -> Identifier:
        return (self._device_guid, self._input_type, self._input_id)

    @property
    def valid_types(self) -> list[InputType]:
        return self._valid_types

    @value.setter
    def value(self, value: Identifier) -> None:
        self._device_guid = value[0]
        self._input_type = value[1]
        self._input_id = value[2]

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._device_guid = util.read_property(
            node, "device-guid", PropertyType.UUID
        )
        self._input_type = util.read_property(
            node, "input-type", PropertyType.InputType
        )
        self._input_id = util.read_property(node, "input-id", PropertyType.Int)

    def _to_xml(self, node: ElementTree.Element) -> None:
        util.append_property_nodes(
            node,
            [
                ["device-guid", self._device_guid, PropertyType.UUID],
                ["input-type", self._input_type, PropertyType.InputType],
                ["input-id", self._input_id, PropertyType.Int],
            ]
        )


class VirtualInputVariable(AbstractVariable):

    xml_tag = "vjoy"

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            valid_types: Sequence[InputType],
    ):
        super().__init__(name, description, is_optional)

        self._valid_types = valid_types
        self._vjoy_id = 1
        self._input_type = valid_types[0]
        self._input_id = 1

    @property
    def value(self) -> bool:
        pass

    @value.setter
    def value(self, value: bool) -> None:
        pass

    @property
    def vjoy_id(self) -> int:
        return self._vjoy_id

    @property
    def input_id(self) -> int:
        return self._input_id

    @property
    def input_type(self) -> InputType:
        return self._input_type

    @property
    def valid_types(self) -> list[InputType]:
        return self._valid_types

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._vjoy_id = util.read_property(node, "vjoy-id", PropertyType.Int)
        self._input_type = util.read_property(
            node, "input-type", PropertyType.InputType
        )
        self._input_id = util.read_property(node, "input-id", PropertyType.Int)

    def _to_xml(self, node: ElementTree.Element) -> None:
        util.append_property_nodes(
            node,
            [
                ["vjoy-id", self._vjoy_id, PropertyType.Int],
                ["input-type", self._input_type, PropertyType.InputType],
                ["input-id", self._input_id, PropertyType.Int],
            ]
        )


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
