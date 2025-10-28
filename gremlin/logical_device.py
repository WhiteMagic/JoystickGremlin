# -*- coding: utf-8; -*-

# Copyright (C) 2023 Lionel Ott
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

import collections
import time
from typing import cast, List, Optional

import dill

from gremlin.error import GremlinError, MissingImplementationError
from gremlin.common import SingletonMetaclass
from gremlin.types import InputType, HatDirection


class LogicalDevice(metaclass=SingletonMetaclass):

    """Implements a device like system for arbitrary amonuts of logical device
    inputs that can be used to combine and further modify inputs before
    ultimately feeding them to a vJoy device."""

    device_guid = dill.UUID_LogicalDevice

    class Input:

        """General input class, base class for all other inputs."""

        Identifier = collections.namedtuple("Identifier", ["type", "id"])

        def __init__(self, label: str, id: int) -> None:
            """Creates a new Input instance.

            Args:
                label: textual label associated with this input
                index: per InputType index
            """
            self._label = label
            self._id = id
            self._value = None

        def update(self, value: float | bool | HatDirection) -> None:
            self._value = value

        @property
        def label(self) -> str:
            return self._label

        @property
        def id(self) -> int:
            return self._id

        @property
        def type(self) -> InputType:
            return self._input_type()

        @property
        def identifier(self) -> Identifier:
            return self.Identifier(self.type, self.id)

        def _input_type(self) -> InputType:
            raise MissingImplementationError("Input._input_type not implemented")

    class Axis(Input):

        def __init__(self, label: str, id: int) -> None:
            super().__init__(label, id)
            self._value = 0.0

        def _input_type(self) -> InputType:
            return InputType.JoystickAxis

        @property
        def value(self) -> float:
            return self._value

    class Button(Input):

        def __init__(self, label: str, id: int) -> None:
            super().__init__(label, id)
            self._value = False

        def _input_type(self) -> InputType:
            return InputType.JoystickButton

        @property
        def is_pressed(self) -> bool:
            return self._value

    class Hat(Input):

        def __init__(self, label: str, id: int) -> None:
            super().__init__(label, id)
            self._value = HatDirection.Center

        def _input_type(self) -> InputType:
            return InputType.JoystickHat

        @property
        def direction(self) -> HatDirection:
            return self._value


    def __init__(self) -> None:
        self._inputs = {}
        self._label_lookup = {}

    def __getitem__(self, identifier_or_label: Input.Identifier | str) -> Input:
        return self._inputs[self._resolve_to_identifier(identifier_or_label)]

    def create(
            self,
            type: InputType,
            input_id: Optional[int]=None,
            label: Optional[str]=None
    ) -> Input:
        """Creates a new input instance of the given type.

        Args:
            type: the type of input to create
            input_id: unique id identifying this input
            label: if given will be used as the label of the new input
        """
        if label in self.labels_of_type():
            raise GremlinError(f"An input named {label} already exists")

        do_create = {
            InputType.JoystickAxis: self.Axis,
            InputType.JoystickButton: self.Button,
            InputType.JoystickHat: self.Hat
        }

        # Use provided input id or generate a new onw if the provided one is
        # currently in use.
        if input_id is None or self._is_id_in_use(input_id, type):
            input_id = self._lowest_available_id(type)

        # Generate a valid label if none has been provided.
        if label is None:
            # Create a key and check it is valid and if not, make it valid.
            label = f"{InputType.to_string(type).capitalize()} {input_id}"
            if label in self.labels_of_type():
                label = f"{label} - {time.time()}"

        # Create input store information and return it.
        new_input = do_create[type](label, input_id)
        self._inputs[new_input.identifier] = new_input
        self._label_lookup[label] = new_input.identifier
        return new_input

    def reset(self) -> None:
        """Resets the IO system to contain no entries."""
        self._inputs = {}
        self._label_lookup = {}

    def set_label(self, old_label: str, new_label: str) -> None:
        """Changes the label of an existing input instance.

        Args:
            old_label: label of the instance to change the label of
            new_label: new label to use
        """
        if old_label == new_label:
            return

        if old_label not in self._label_lookup:
            raise GremlinError(f"No input with label '{old_label}' exists")
        if new_label in self._label_lookup:
            raise GremlinError(f"Input with label '{new_label}' already exists")

        input = self._inputs[self._label_lookup[old_label]]
        input._label = new_label
        self._label_lookup[new_label] = input.identifier
        del self._label_lookup[old_label]

    def delete(self, identifier_or_label: Input.Identifier | str) -> None:
        """Deletes the specified input if it is present.

        Args:
            identifier_or_label: Identifier or label of the input to delete
        """
        input = self[identifier_or_label]
        del self._inputs[input.identifier]
        del self._label_lookup[input.label]
        del input

    def labels_of_type(self, type_list: List[InputType]=[]) -> List[str]:
        """Returns all labels for inputs of the matching types.

        Args:
            type_list: List of input types to match against, if empty all types
                are matched against.

        Returns:
            List of all labels matching the specified inputs types
        """
        x = [e.label for e in self.inputs_of_type(type_list)]
        return x

    def inputs_of_type(self, type_list: List[InputType]=[]) -> list[Input]:
        """Returns input corresponding to the specified types.

        Args:
            type_list: List of input types to match against, if empty all types
                are matched against.

        Returns:
            List of inputs that have the specified type
        """
        if len(type_list) == 0:
            type_list = [
                InputType.JoystickAxis,
                InputType.JoystickButton,
                InputType.JoystickHat
            ]
        return [
            e for e in
            sorted(self._inputs.values(), key=lambda x: (x.type.name, x.label))
            if e.type in type_list
        ]

    def input_by_offset(self, type: InputType, offset: int) -> Input:
        """Returns an input item based on the input type and the offset.

        The offset is the index an input instance has based on a linear internal
        index-based ordering of the inputs of the specified type.

        Args:
            type: the InputType to perform the lookup over
            offset: linear offset into the ordered list of inputs

        Returns:
            Input instance of the correct type with the specified offset
        """
        inputs = self.inputs_of_type([type])
        if len(inputs) <= offset:
            raise GremlinError(
                "Attempting to access an input item of type " +
                f"{InputType.to_string(type)} with invalid offset {offset}"
            )
        return inputs[offset]

    @property
    def axis_count(self) -> int:
        return len(self.inputs_of_type([InputType.JoystickAxis]))

    @property
    def button_count(self) -> int:
        return len(self.inputs_of_type([InputType.JoystickButton]))

    @property
    def hat_count(self) -> int:
        return len(self.inputs_of_type([InputType.JoystickHat]))

    def axis(self, index: int) -> Axis:
        if index not in [e.id for e in self.inputs_of_type([InputType.JoystickAxis])]:
            raise GremlinError(f"No logical axis with id {index} exists.")
        return cast(
            LogicalDevice.Axis,
            self[LogicalDevice.Input.Identifier(InputType.JoystickAxis, index)]
        )

    def button(self, index: int) -> Button:
        if index not in [e.id for e in self.inputs_of_type([InputType.JoystickButton])]:
            raise GremlinError(f"No logical button with id {index} exists.")
        return cast(
            LogicalDevice.Button,
            self[LogicalDevice.Input.Identifier(InputType.JoystickButton, index)]
        )

    def hat(self, index: int) -> Hat:
        if index not in [e.id for e in self.inputs_of_type([InputType.JoystickHat])]:
            raise GremlinError(f"No logical hat with id {index} exists.")
        return cast(
            LogicalDevice.Hat,
            self[LogicalDevice.Input.Identifier(InputType.JoystickHat, index)]
        )

    def _lowest_available_id(self, type: InputType) -> int:
        """Returns the next lowest available id for the specified input type.

        Args:
            type: The input type to return the next id for

        Returns:
            The next available id for the specified input type
        """
        next_id = 1
        while next_id in sorted([e.id for e in self.inputs_of_type([type])]):
            next_id += 1
        return next_id

    def _is_id_in_use(self, id: int, type: InputType) -> bool:
        """Returns whether the specified id is already in use by the given type.

        Args:
            id: The id to check for usage
            type: The input type to check for usage of the id
        """
        return id in [e.id for e in self.inputs_of_type([type])]

    def _resolve_to_identifier(
        self,
        identifier_or_label: Input.Identifier | str
    ) -> Input.Identifier:
        """Returns the identifier associated with the given lookup.

        Args:
            identifier_or_label: The query key that may need to be converted to
                an identifier

        Returns:
            Identifier corresponding to the provided input
        """
        try:
            if isinstance(identifier_or_label, str):
                return self._label_lookup[identifier_or_label]
            elif isinstance(identifier_or_label, self.Input.Identifier):
                return identifier_or_label
            else:
                raise GremlinError(
                    f"Provided lookup '{identifier_or_label}' is invalid."
            )
        except KeyError:
            raise GremlinError(
                f"No input exists for '{identifier_or_label}'."
            )
