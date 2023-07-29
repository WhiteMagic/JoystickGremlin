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

from gremlin.error import GremlinError
from gremlin.common import InputType, SingletonDecorator


@SingletonDecorator
class IntermediateOutput:

    class Input:

        def __init__(self, label: str, index: int):
            self._label = label
            self._index = index
        
        @property
        def label(self) -> str:
            return self._label
        
        @property
        def index(self) -> str:
            return self._index


    class Axis(Input):
        
        def __init__(self, label: str, index: int):
            super().__init__(label, index)


    class Button(Input):

        def __init__(self, label: str, index: int):
            super().__init__(label, index)


    class Hat(Input):

        def __init__(self, label: str, index: int):
            super().__init__(label, index)


    def __init__(self):
        self._inputs = {
            InputType.JoystickAxis: {},
            InputType.JoystickButton: {},
            InputType.JoystickHat: {}
        }
        self._label_lookup = {}
        self._index_lookup = {}

    def set_label(self, old_label: str, new_label: str) -> None:
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
        if label in self.all_keys():
            raise GremlinError(f"An input named {label} already exists")
        
        do_create = {
            InputType.JoystickAxis: self.Axis,
            InputType.JoystickButton: self.Button,
            InputType.JoystickHat: self.Hat
        }

        index = self._next_index(type)
        self._inputs[type][label] = do_create[type](label, index)
        self._index_lookup[(type, index)] = label
        self._label_lookup[label] = (type, index)

    def delete_by_index(self, type: InputType, index: int) -> None:
        key = (type, index)
        if key not in self._index_lookup:
            raise GremlinError(
                f"No input of type {InputType.to_string(type)} with index {index}"
            )
        self.delete_by_label(self._index_lookup[key])

    def delete_by_label(self, label: str) -> None:
        if label not in self._label_lookup:
            raise GremlinError(f"No input with label '{label}' exists")
        
        del self._inputs[self._label_lookup[label][0]][label]

    def all_keys(self) -> List[str]:
        keys = []
        for container in self._inputs.values():
            keys.extend(container.keys())
        return keys
    
    def axis(self, key: int | str) -> Axis:
        return self._get_input(InputType.JoystickAxis, key)

    def button(self, key: int | str) -> Button:
        return self._get_input(InputType.JoystickButton, key)

    def hat(self, key: int | str) -> Hat:
        return self._get_input(InputType.JoystickHat, key)

    def _get_input(self, type: InputType, key: int | str) -> Input:
        try:
            if isinstance(key, int):
                key = self._index_lookup[(type, key)]
            return self._inputs[type][key]
        except KeyError:
            raise GremlinError(
                f"No input with key '{key} for type {InputType.to_string(type)}"
            )

    def _next_index(self, type: InputType) -> int:
        indices = sorted([dev.index for dev in self._inputs[type].values()])
        start_index = 0
        for idx in indices:
            if start_index < idx:
                return start_index
            start_index += 1
        return start_index