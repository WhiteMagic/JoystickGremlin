# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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

import time
from typing import List, Optional
import uuid

from gremlin.error import GremlinError, MissingImplementationError
from gremlin.common import SingletonDecorator
from gremlin.types import InputType
from gremlin.util import parse_guid


@SingletonDecorator
class IntermediateOutput:

    """Implements a device like system for arbitrary amonuts of intermediate
    outputs that can be used to combine and further modify inputs before
    ultimately feeding them to a vJoy device."""

    device_guid = parse_guid("f0af472f-8e17-493b-a1eb-7333ee8543f2")

    class Input:

        """General input class, base class for all other inputs."""

        def __init__(self, label: str, index: uuid.UUID):
            """Creates a new Input instance.

            Args:
                label: textual label associated with this input
                index: per InputType unique index
            """
            self._label = label
            self._guid = index

        @property
        def label(self) -> str:
            return self._label

        @property
        def guid(self) -> uuid.UUID:
            return self._guid

        @property
        def type(self) -> InputType:
            return self._input_type()

        @property
        def suffix(self):
            return str(self._guid).split("-")[0]

        def _input_type(self):
            raise MissingImplementationError("Input._input_type not implemented")


    class Axis(Input):

        def __init__(self, label: str, index: uuid.UUID):
            super().__init__(label, index)

        def _input_type(self):
            return InputType.JoystickAxis

    class Button(Input):

        def __init__(self, label: str, index: uuid.UUID):
            super().__init__(label, index)

        def _input_type(self):
            return InputType.JoystickButton

    class Hat(Input):

        def __init__(self, label: str, index: uuid.UUID):
            super().__init__(label, index)

        def _input_type(self):
            return InputType.JoystickHat


    def __init__(self):
        self._inputs = {}
        self._label_lookup = {}

    def __getitem__(self, identifier: uuid.UUID | str):
        return self._inputs[self._identifier_to_guid(identifier)]

    def create(self, type: InputType, label: Optional[str]=None) -> None:
        """Creates a new input instance of the given type.

        Args:
            type: the type of input to create
            label: if given will be used as the label of the new input
        """
        if label in self.labels_of_type():
            raise GremlinError(f"An input named {label} already exists")

        do_create = {
            InputType.JoystickAxis: self.Axis,
            InputType.JoystickButton: self.Button,
            InputType.JoystickHat: self.Hat
        }

        # Geberate a valid label if none has been provided
        guid = uuid.uuid4()
        if label == None:
            # Create a key and check it is valid and if not, make it valid
            suffix = str(guid).split("-")[0]
            label = f"{InputType.to_string(type).capitalize()} {suffix}"
            if label in self.labels_of_type():
                label = f"{label} - {time.time()}"
        self._inputs[guid] = do_create[type](label, guid)
        self._label_lookup[label] = guid

    def reset(self):
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
        self._label_lookup[new_label] = input.guid
        del self._label_lookup[old_label]

    def delete(self, identifier: str | uuid.UUID) -> None:
        """Deletes an input based on the given identifier.

        Args:
            identifier: The label or guid of the input to delete
        """
        input = self._inputs[self._identifier_to_guid(identifier)]
        del self._inputs[input.guid]
        del self._label_lookup[input.label]

    def labels_of_type(self, type_list: None | List[InputType]=None) -> List[str]:
        """Returns all labels for inputs of the matching types.

        Args:
            type_list: List of input types to match against

        Returns:
            List of all labels matching the specified inputs types
        """
        x = [e.label for e in self.inputs_of_type(type_list)]
        return x

    def inputs_of_type(self, type_list: None | List[InputType]) -> List[Input]:
        """Returns input corresponding to the specified types.

        Args:
            type_list: List of types for which to return inputs

        Returns:
            List of inputs that have the specified type
        """
        if type_list is None:
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
                f"Attempting to access an input item of type " +
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

    def _get_input(
            self,
            type: InputType,
            key: uuid.UUID | str
    ) -> Axis | Button | Hat:
        """Returns the input instance corresponding to the given type and key.

        Args:
            type: InputType of the input to return
            key: the index or label associated with the input to return

        Returns:
            Input instance matching the type and key specification
        """
        try:
            if isinstance(key, uuid.UUID):
                key = self._index_lookup[(type, key)]
            return self._inputs[type][key]
        except KeyError:
            raise GremlinError(
                f"No input with key '{key} for type {InputType.to_string(type)}"
            )

    def _identifier_to_guid(self, identifier: str | uuid.UUID) -> uuid.UUID:
        """Returns the guid for the provided identifier.

        This will perform a lookup if necessary.

        Args:
            identifier: The identifier to transform into a guid

        Returns:
            Guid corresponding to the provided identifier
        """
        try:
            if isinstance(identifier, str):
                return self._label_lookup[identifier]
            elif isinstance(identifier, uuid.UUID):
                return identifier
            else:
                raise GremlinError(
                    f"Provided identifier '{identifier}' is invalid"
            )
        except KeyError:
            raise GremlinError(
                f"No input with identifier '{identifier}' exists"
            )
