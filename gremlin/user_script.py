# -*- coding: utf-8; -*-

# Copyright (C) 2019 Lionel Ott
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
import copy
import functools
import heapq
import importlib
import inspect
import logging
import numbers
import os
from pathlib import Path
import random
import string
import threading
import time
from typing import Any, Callable
import uuid
from xml.etree import ElementTree

import dill
from vjoy.vjoy import VJoyProxy

from gremlin.input_cache import Joystick, Keyboard
from gremlin.types import InputType, PropertyType
from gremlin import error, event_handler, shared_state, util


def _resolve_path(script_path: Path) -> Path:
    """If script_path is relative, resolve (not strictly) it to the standard scripts directory."""
    if script_path.is_absolute():
        return script_path
    return Path(util.resource_path("user_scripts")) / script_path


class CallbackRegistry:

    """Registry of all callbacks known to the system."""

    def __init__(self):
        """Creates a new callback registry instance."""
        self._registry = {}
        self._current_id = 0

    def add(
            self,
            callback: Callable,
            event: event_handler.Event,
            mode: str
    ) -> None:
        """Adds a new callback to the registry.

        Args:
            callback: function to add as a callback
            event: the event on which to trigger the callback
            mode: the mode in which to trigger the callback
        """
        self._current_id += 1
        function_name = "{}_{:d}".format(callback.__name__, self._current_id)

        if event.device_guid not in self._registry:
            self._registry[event.device_guid] = {}
        if mode not in self._registry[event.device_guid]:
            self._registry[event.device_guid][mode] = {}
        if event not in self._registry[event.device_guid][mode]:
            self._registry[event.device_guid][mode][event] = {}

        self._registry[event.device_guid][mode][event][function_name] = callback

    @property
    def registry(self) -> dict:
        """Returns the registry dictionary.

        Returns:
            The callback registry dictionary
        """
        return self._registry

    def clear(self) -> None:
        """Clears the registry entries."""
        self._registry = {}


class PeriodicRegistry:

    """Registry for periodically executed functions."""

    def __init__(self):
        """Creates a new instance."""
        self._registry = {}
        self._running = False
        self._thread = threading.Thread(target=self._thread_loop)
        self._queue = []
        self._plugins = []

    def start(self) -> None:
        """Starts the event loop."""
        # Only proceed if we have functions to call
        if len(self._registry) == 0:
            return

        # Only create a new thread and start it if the thread is not
        # currently running
        self._running = True
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._thread_loop)
            self._thread.start()

    def stop(self) -> None:
        """Stops the event loop."""
        self._running = False
        if self._thread.is_alive():
            self._thread.join()

    def add(self, callback: Callable, interval: float) -> None:
        """Adds a function to execute periodically.

        Args:
            callback: the function to execute
            interval: the time in seconds between executions
        """
        self._registry[callback] = (interval, callback)

    def clear(self) -> None:
        """Clears the registry."""
        self._registry = {}

    def _install_plugins(self, callback: Callable) -> Callable:
        """Installs the current plugins into the given callback.

        Args:
            callback: the callback function to install the plugins into

        Returns:
            new callback with plugins installed
        """
        signature = inspect.signature(callback).parameters
        partial_fn = functools.partial
        if "self" in signature:
            partial_fn = functools.partialmethod
        for plugin in self._plugins:
            if plugin.keyword in signature:
                callback = plugin.install(callback, partial_fn)
        return callback

    def _thread_loop(self) -> None:
        """Main execution loop run in a separate thread."""
        # Setup plugins to use
        self._plugins = [
            JoystickPlugin(),
            VJoyPlugin(),
            KeyboardPlugin()
        ]
        callback_map = {}

        # Populate the queue
        self._queue = []
        for item in self._registry.values():
            plugin_cb = self._install_plugins(item[1])
            callback_map[plugin_cb] = item[0]
            heapq.heappush(
                self._queue,
                (time.time() + callback_map[plugin_cb], plugin_cb)
            )

        # Main thread loop
        while self._running:
            # Process all events that require running
            while self._queue[0][0] < time.time():
                item = heapq.heappop(self._queue)
                item[1]()

                heapq.heappush(
                    self._queue,
                    (time.time() + callback_map[item[1]], item[1])
                )

            # Sleep until either the next function needs to be run or
            # our timeout expires
            time.sleep(min(self._queue[0][0] - time.time(), 1.0))


callback_registry = CallbackRegistry()
periodic_registry = PeriodicRegistry()


class JoystickDecorator:

    """Creates customized decorators for physical joystick devices."""

    def __init__(self, name: str, device_guid: str, mode: str):
        """Creates a new instance with customized decorators.

        Args:
            name: name of the device
            device_guid: the device's guid in the system
            mode: the mode in which the decorated functions should be active
        """
        self.name = name
        self.mode = mode

        # Convert string-based GUID to the actual GUID object
        try:
            self.device_guid = uuid.UUID(device_guid)
        except ValueError:
            logging.getLogger("system").error(
                f"Invalid guid value '{device_guid}' received."
            )
            self.device_guid = diill.UUID_Invalid

        # Create decorators for the different input types
        self.axis = functools.partial(
            _input_callback,
            device_guid=self.device_guid,
            input_type=InputType.JoystickAxis,
            mode=self.mode
        )
        self.button = functools.partial(
            _input_callback,
            device_guid=self.device_guid,
            input_type=InputType.JoystickButton,
            mode=self.mode
        )
        self.hat = functools.partial(
            _input_callback,
            device_guid=self.device_guid,
            input_type=InputType.JoystickHat,
            mode=self.mode
        )


class VJoyPlugin:

    """Plugin providing automatic access to the VJoyProxy object.

    For a function to use this plugin it requires one of its parameters
    to be named "vjoy".
    """

    vjoy = VJoyProxy()

    def __init__(self):
        self.keyword = "vjoy"

    def install(self, callback: Callable, partial_fn: Callable) -> Callable:
        """Decorates the given callback function to provide access to
        the VJoyProxy object.

        Only if the signature contains the plugin's keyword is the
        decorator applied.

        Args:
            callback: the callback to decorate
            partial_fn: function to create the partial function / method

        Returns:
            callback with the plugin parameter bound
        """
        return partial_fn(callback, vjoy=VJoyPlugin.vjoy)


class JoystickPlugin:

    """Plugin providing automatic access to the Joystick object.

    For a function to use this plugin it requires one of its parameters
    to be named "joy".
    """

    joystick = Joystick()

    def __init__(self):
        self.keyword = "joy"

    def install(self, callback: Callable, partial_fn: Callable) -> Callable:
        """Decorates the given callback function to provide access
        to the Joystick object.

        Only if the signature contains the plugin's keyword is the
        decorator applied.

        Args:
            callback: the callback to decorate
            partial_fn: function to create the partial function / method

        Returns:
            callback with the plugin parameter bound
        """
        return partial_fn(callback, joy=JoystickPlugin.joystick)


class KeyboardPlugin:

    """Plugin providing automatic access to the Keyboard object.

    For a function to use this plugin it requires one of its parameters
    to be named "keyboard".
    """

    keyboard = Keyboard()

    def __init__(self):
        self.keyword = "keyboard"

    def install(self, callback, partial_fn):
        """Decorates the given callback function to provide access to
        the Keyboard object.

        Args:
            callback: the callback to decorate
            partial_fn: function to create the partial function / method

        Returns:
            callback with the plugin parameter bound
        """
        return partial_fn(callback, keyboard=KeyboardPlugin.keyboard)



class ScriptVariableRegistry:

    def __init__(self):
        self._registry = {}

    def clear(self):
        """Clears all registry entries."""
        self._registry = {}

    def register_script(self, script: Script) -> None:
        """Registers all variables of a script.

        This will forcibly overwrite existing entries for the same script.

        Args:
            script: the Script instance to register
        """
        self._registry[script.id] = {}
        for variable in script.variables.values():
            self._registry[script.id][variable.name] = variable

    def remove_script(self, script: Script) -> None:
        """Removes the specified script's variables.

        Args:
            script: the script to remove variables for
        """
        if script.id in self._registry:
            del self._registry[script.id]

    def set(self, script_id: uuid.UUID, variable: AbstractVariable) -> None:
        """Stores a variable in the registry.

        Args:
            script_id: unique identifier of the script
            variable: the variable to register
        """
        if script_id not in self._registry:
            self._registry[script_id] = {}
        self._registry[script_id][variable.name] = variable

    def get(self, script_id: uuid.UUID, name: str) -> AbstractVariable|None:
        """Returns a variable from the registry.

        Args:
            script_id: unique identifier of the script
            name: the name of the variable to retrieve

        Returns:
            Variable instance corresponding to the script and name
        """
        if script_id not in self._registry:
            return None
        return self._registry[script_id].get(name, None)


class Script:

    """Represents the prototype of a script."""

    variable_registry = ScriptVariableRegistry()

    def __init__(self, path: Path=Path(), name: str=""):
        """Creates a new Script."""
        self._id = uuid.uuid4()
        self.path = _resolve_path(path)
        self.name = name
        self.variables: dict[str, AbstractVariable] = {}

        if self.path.is_file():
            self._retrieve_variable_definitions()
            self.variable_registry.register_script(self)

    @property
    def id(self) -> uuid.UUID:
        """Returns the UUID of the script.

        Returns:
            Unique identifier of this script.
        """
        return self._id

    @property
    def is_configured(self) -> bool:
        """Returns if the instance is fully configured.

        Returns:
            True if the instance is fully configured, False otherwise
        """
        return all([
            var.is_valid() for var in self.variables.values() if not var.is_optional
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
        # Remove information of this script in case the ID changes
        Script.variable_registry.remove_script(self)

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

        self._id = util.read_uuid(node, "script", "id")
        self.path = _resolve_path(util.read_property(node, "path", PropertyType.Path))
        self.name = util.read_property(node, "name", PropertyType.String)

        # Retrieve variable information from the script and instantiate them
        self._retrieve_variable_definitions()

        # Populate variables with data from the XML if they are present
        for entry in node.iter("variable"):
            name = util.read_property(entry, "name", PropertyType.String)
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

        # Store script values in the registry
        Script.variable_registry.register_script(self)

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing this instance.

        Returns:
            XML node representing this instance
        """
        node = util.create_node_from_data(
            "script",
            [
                ("path", self.path, PropertyType.Path),
                ("name", str(self.name), PropertyType.String),
            ]
        )
        node.set("id", util.safe_format(self._id, uuid.UUID))
        for entry in self.variables.values():
            variable_node = entry.to_xml()
            if variable_node is not None:
                node.append(variable_node)
        return node

    def reload(self):
        Script.variable_registry.register_script(self)
        self.module._script_id = self.id
        self.spec.loader.exec_module(self.module)

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

        self.spec = importlib.util.spec_from_file_location(
            "".join(random.choices(string.ascii_lowercase, k=16)),
            str(self.path)
        )
        self.module = importlib.util.module_from_spec(self.spec)
        self.module._script_id = self.id
        self.spec.loader.exec_module(self.module)

        for key, value in self.module.__dict__.items():
            if isinstance(value, AbstractVariable):
                if value.name in self.variables:
                    logging.getLogger("system").error(
                        f"Script: Duplicate label {value.label} present in {path}"
                    )
                self.variables[value.name] = copy.deepcopy(value)


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
        if not self.is_valid():
            return None
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
    def is_valid(self) -> bool:
        pass

    @abstractmethod
    def _from_xml(self, node: ElementTree.Element) -> None:
        pass

    @abstractmethod
    def _to_xml(self, node: ElementTree.Element) -> None:
        pass

    @abstractmethod
    def _assign_value_from(self, other: AbstractVariable) -> None:
        pass

    def _get_script_id(self) -> uuid.UUID|None:
        for frame in inspect.stack():
            identifier = frame.frame.f_locals.get(
                "_script_id",
                None
            )
            if isinstance(identifier, uuid.UUID):
                return identifier
        return None

    def _initialize_from_registry(self) -> None:
        idx = self._get_script_id()
        var = Script.variable_registry.get(idx, self.name)
        if isinstance(var, AbstractVariable):
            self._assign_value_from(var)


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
        self._initialize_from_registry()

    @property
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, value: bool) -> None:
        self._value = value

    def is_valid(self) -> bool:
        return self._value in [True, False]

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.Bool)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self.value, PropertyType.Bool
        ))

    def _assign_value_from(self, other: BoolVariable) -> None:
        self._value = other.value


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
        self._initialize_from_registry()

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

    def is_valid(self) -> bool:
        return isinstance(self._value, numbers.Number)

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.Float)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._value, PropertyType.Float
        ))

    def _assign_value_from(self, other: FloatVariable) -> None:
        self._value = other.value


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
        self._initialize_from_registry()

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

    def is_valid(self) -> bool:
        return isinstance(self._value, int)

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.Int)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._value, PropertyType.Int
        ))

    def _assign_value_from(self, other: IntegerVariable) -> None:
        self._value = other.value


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
        self._initialize_from_registry()

    @property
    def value(self) -> str:
        return self._mode

    @value.setter
    def value(self, value: str) -> None:
        self._mode = value

    def is_valid(self) -> bool:
        return self._mode in shared_state.current_profile.modes.mode_names()

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._mode = util.read_property(node, "value", PropertyType.String)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._mode, PropertyType.String
        ))

    def _assign_value_from(self, other: ModeVariable) -> None:
        self._mode = other.value


class SelectionVariable(AbstractVariable):

    xml_tag = "selection"

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            option_list: list[str],
            default_index: int=0
    ):
        super().__init__(name, description, is_optional)

        self._option_list = option_list
        self._current_index = default_index
        self._initialize_from_registry()

    @property
    def options(self) -> list[str]:
        return self._option_list

    @property
    def value(self) -> str:
        return self._option_list[self._current_index]

    @value.setter
    def value(self, value: str) -> None:
        self._current_index = self._option_list.index(value)

    def is_valid(self) -> bool:
        return True

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._current_index = util.read_property(
            node, "index", PropertyType.Int
        )

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "index", self._current_index, PropertyType.Int
        ))

    def _assign_value_from(self, other: SelectionVariable) -> None:
        self._current_index = other._current_index


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
        self._initialize_from_registry()

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        self._value = value

    def is_valid(self) -> bool:
        return isinstance(self._value, str) and len(self._value) > 0

    def _from_xml(self, node: ElementTree.Element) -> None:
        self._value = util.read_property(node, "value", PropertyType.String)

    def _to_xml(self, node: ElementTree.Element) -> None:
        node.append(util.create_property_node(
            "value", self._value, PropertyType.String
        ))

    def _assign_value_from(self, other: StringVariable) -> None:
        self._value = other.value


class PhysicalInputVariable(AbstractVariable):

    xml_tag = "physical-input"

    type Identifier = tuple[uuid.UUID, InputType, int]

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            valid_types: list[InputType],
    ):
        super().__init__(name, description, is_optional)

        self._valid_types = valid_types
        self._device_guid = None
        self._input_type = valid_types[0]
        self._input_id = 1
        self._initialize_from_registry()

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

    def decorator(self, mode: ModeVariable) -> Callable:
        dec = self.create_decorator(mode.value)
        match self._input_type:
            case InputType.JoystickButton:
                return dec.button(self._input_id)
            case InputType.JoystickAxis:
                return dec.axis(self._input_id)
            case InputType.JoystickHat:
                return dec.hat(self._input_id)
            case _:
                raise error.GremlinError(
                    f"Received invalid input type '{self._input_type}'"
                )

    def create_decorator(self, mode: str):
        if not self.is_valid():
            return JoystickDecorator(
                "", str(dill.GUID_Invalid), ""
            )
        else:
            return JoystickDecorator(
                "device name",
                str(self._device_guid),
                mode
            )

    def is_valid(self) -> bool:
        return (
            self._device_guid is not None
            and self._input_type in self._valid_types
            and isinstance(self._input_id, int)
        )

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

    def _assign_value_from(self, other: PhysicalInputVariable) -> None:
        self._valid_types = other._valid_types
        self._device_guid = other.device_guid
        self._input_type = other.input_type
        self._input_id = other.input_id


class VirtualInputVariable(AbstractVariable):

    xml_tag = "vjoy"

    def __init__(
            self,
            name: str,
            description: str,
            is_optional: bool,
            valid_types: list[InputType],
    ):
        super().__init__(name, description, is_optional)

        self._valid_types = valid_types
        self._vjoy_id = 1
        self._input_type = valid_types[0]
        self._input_id = 1
        self._initialize_from_registry()

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

    def remap(self, value: float|bool|Tuple[int, int]) -> None:
        device = VJoyProxy()[self._vjoy_id]
        match self._input_type:
            case InputType.JoystickButton:
                device.button(self._input_id).is_pressed = value
            case InputType.JoystickAxis:
                device.axis(self._input_id).value = value
            case InputType.JoystickHat:
                device.hat(self._input_id).direction = value
            case _:
                raise error.GremlinError(
                    f"Received invalid input type '{self._input_type}'"
                )

    def is_valid(self) -> bool:
        return (
            self._vjoy_id is not None
            and self._input_type in self._valid_types
            and isinstance(self._input_id, int)
        )

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

    def _assign_value_from(self, other: VirtualInputVariable) -> None:
        self._valid_types = other._valid_types
        self._vjoy_id = other.vjoy_id
        self._input_type = other.input_type
        self._input_id = other.input_id


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


def keyboard(key_name: str, mode: str) -> Callable:
    """Decorator for keyboard key callbacks.

    Args:
        key_name: name of key triggering the callback
        mode: mode in which this callback is active
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        key = gremlin.keyboard.key_from_name(key_name)
        event = event_handler.Event.from_key(key)
        callback_registry.add(wrapper_fn, event, mode)

        return wrapper_fn

    return wrap


def periodic(interval: float) -> Callable:
    """Decorator for periodic function callbacks.

    Args:
        interval: the duration between executions of the function
    """

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        periodic_registry.add(wrapper_fn, interval)

        return wrapper_fn

    return wrap


def _input_callback(
        input_id: int,
        device_guid: uuid.UUID,
        input_type: InputType,
        mode: str
):
    """Decorator for a specific input on a physical device.

    Args:
        device_guid: GUID of the physical device
        input_type: type of the input being wrapped in the decorator
        input_id: identifier of the axis, button, or hat being decorated
        mode: name of the mode the callback is active in
    """

    # The order of the input arguments has to be this specific one as otherwise
    # the positional argument part of the decorator breaks.

    def wrap(callback):

        @functools.wraps(callback)
        def wrapper_fn(*args, **kwargs):
            callback(*args, **kwargs)

        event = event_handler.Event(
            event_type=input_type,
            identifier=input_id,
            device_guid=device_guid,
            mode=mode
        )
        callback_registry.add(wrapper_fn, event, mode)

        return wrapper_fn

    return wrap
