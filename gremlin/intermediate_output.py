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

from typing import List, Optional
import uuid

from gremlin.error import GremlinError, MissingImplementationError
from gremlin.common import SingletonDecorator
from gremlin.types import InputType


@SingletonDecorator
class IntermediateOutput:

    """Implements a device like system for arbitrary amonuts of intermediate
    outputs that can be used to combine and further modify inputs before
    ultimately feeding them to a vJoy device."""

    guid = uuid.UUID("f0af472f-8e17-493b-a1eb-7333ee8543f2")

    class Input:

        """General input class, base class for all other inputs."""

        def __init__(self, label: str, index: int):
            """Creates a new Input instance.

            Args:
                label: textual label associated with this input
                index: per InputType unique index
            """
            self._label = label
            self._index = index

        @property
        def label(self) -> str:
            return self._label

        @property
        def index(self) -> str:
            return self._index

        @property
        def type(self) -> InputType:
            return self._input_type()

        def _input_type(self):
            raise MissingImplementationError("Input._input_type not implemented")


    class Axis(Input):

        def __init__(self, label: str, index: int):
            super().__init__(label, index)

        def _input_type(self):
            return InputType.JoystickAxis

    class Button(Input):

        def __init__(self, label: str, index: int):
            super().__init__(label, index)

        def _input_type(self):
            return InputType.JoystickButton

    class Hat(Input):

        def __init__(self, label: str, index: int):
            super().__init__(label, index)

        def _input_type(self):
            return InputType.JoystickHat


    def __init__(self):
        self._inputs = {
            InputType.JoystickAxis: {},
            InputType.JoystickButton: {},
            InputType.JoystickHat: {}
        }
        self._label_lookup = {}
        self._index_lookup = {}

        self.create(InputType.JoystickButton, "Test 123")

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

        input = self._get_input(self._label_lookup[old_label][0], old_label)
        type = self._label_lookup[old_label][0]

        input._label = new_label
        self._inputs[type][new_label] = input
        self._index_lookup[(type, input.index)] = new_label
        self._label_lookup[new_label] = self._label_lookup[old_label]

        del self._inputs[type][old_label]
        del self._label_lookup[old_label]

    def create(self, type: InputType, label: Optional[str]=None) -> None:
        """Creates a new input instance of the given type.

        Args:
            type: the type of input to create
            label: if given will be used as the label of the new input
        """
        if label in self.all_keys():
            raise GremlinError(f"An input named {label} already exists")

        do_create = {
            InputType.JoystickAxis: self.Axis,
            InputType.JoystickButton: self.Button,
            InputType.JoystickHat: self.Hat
        }

        index = self._next_index(type)
        if label == None:
            label = f"{InputType.to_string(type).capitalize()} {index+1}"
        self._inputs[type][label] = do_create[type](label, index)
        self._index_lookup[(type, index)] = label
        self._label_lookup[label] = (type, index)

    def delete_by_index(self, type: InputType, index: int) -> None:
        """Deletes an input based on the type and index information.

        Args:
            type: the type of the input to delete
            index: indexo of the input to delete
        """
        key = (type, index)
        if key not in self._index_lookup:
            raise GremlinError(
                f"No input of type {InputType.to_string(type)} with index {index}"
            )
        self.delete_by_label(self._index_lookup[key])

    def delete_by_label(self, label: str) -> None:
        """Deletes an input based on the label.

        Args:
            label: the label of the input to delete
        """
        if label not in self._label_lookup:
            raise GremlinError(f"No input with label '{label}' exists")

        del self._inputs[self._label_lookup[label][0]][label]

    def all_keys(self) -> List[str]:
        """Returns the list of all labels in use.

        Returns:
            List of all labels of the existing inputs
        """
        keys = []
        for container in self._inputs.values():
            keys.extend(container.keys())
        return keys

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
        if len(self._inputs[type]) <= offset:
            raise GremlinError(
                f"Attempting to access an input item of type " +
                f"{InputType.to_string(type)} with invalid offset {offset}"
            )
        return sorted(self._inputs[type].values(), key=lambda x: x.index)[offset]

    def axis(self, key: int | str) -> Axis:
        """Returns an axis instance.

        Args:
            key: either the index or label of the axis to return

        Returns:
            Axis instance corresponding to the given key
        """
        return self._get_input(InputType.JoystickAxis, key)

    def button(self, key: int | str) -> Button:
        """Returns a button instance.

        Args:
            key: either the index or label of the button to return

        Returns:
            Button instance corresponding to the given key
        """
        return self._get_input(InputType.JoystickButton, key)

    def hat(self, key: int | str) -> Hat:
        """Returns a hat instance.

        Args:
            key: either the index or label of the hat to return

        Returns:
            Hat instance corresponding to the given key
        """
        return self._get_input(InputType.JoystickHat, key)

    @property
    def axis_count(self) -> int:
        return len(self._inputs[InputType.JoystickAxis])

    @property
    def button_count(self) -> int:
        return len(self._inputs[InputType.JoystickButton])

    @property
    def hat_count(self) -> int:
        return len(self._inputs[InputType.JoystickHat])

    def _get_input(self, type: InputType, key: int | str) -> Input:
        """Returns the input instance corresponding to the given type and key.

        Args:
            type: InputType of the input to return
            key: the index or label associated with the input to return

        Returns:
            Input instance matching the type and key specification
        """
        try:
            if isinstance(key, int):
                key = self._index_lookup[(type, key)]
            return self._inputs[type][key]
        except KeyError:
            raise GremlinError(
                f"No input with key '{key} for type {InputType.to_string(type)}"
            )

    def _next_index(self, type: InputType) -> int:
        """Determines the next free index for a given input type.

        Args:
            type: InputType for which to determine the next free index

        Returns:
            Next free index for the given InputType
        """
        indices = sorted([dev.index for dev in self._inputs[type].values()])
        start_index = 0
        for idx in indices:
            if start_index < idx:
                return start_index
            start_index += 1
        return start_index