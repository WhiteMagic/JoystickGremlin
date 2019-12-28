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


from gremlin.keyboard import key_from_code
from gremlin.types import InputType, AxisNames


class SingletonDecorator:

    """Decorator turning a class into a singleton."""

    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance


# Mapping from hat direction tuples to their textual representation
direction_tuple_lookup = {
    (0, 0): "Center",
    (0, 1): "North",
    (1, 1): "North East",
    (1, 0): "East",
    (1, -1): "South East",
    (0, -1): "South",
    (-1, -1): "South West",
    (-1, 0): "West",
    (-1, 1): "North West",
    "Center": (0, 0),
    "North": (0, 1),
    "North East": (1, 1),
    "East": (1, 0),
    "South East": (1, -1),
    "South": (0, -1),
    "South West": (-1, -1),
    "West": (-1, 0),
    "North West": (-1, 1)
}


def input_to_ui_string(input_type: InputType, input_id: int) -> str:
    """Returns a string for UI usage of an input.

    :param input_type the InputType being shown
    :param input_id the corresponding id
    :return string for UI usage of the given data
    """
    if input_type == InputType.JoystickAxis:
        try:
            return AxisNames.to_string(AxisNames(input_id))
        except gremlin.error.GremlinError:
            return "Axis {:d}".format(input_id)
    elif input_type == InputType.Keyboard:
        return key_from_code(*input_id).name
    else:
        return "{} {}".format(
            InputType.to_string(input_type).capitalize(),
            input_id
        )
