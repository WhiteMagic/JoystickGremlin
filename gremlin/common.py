# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from typing import (
    Any,
    Dict,
    Generic,
    List,
    TypeVar
)

from gremlin import error
from gremlin.keyboard import (
    key_from_code,
    Key
)
from gremlin.types import (
    AxisNames,
    InputType,
    ScanCode,
)


class SingletonDecorator:

    """Decorator turning a class into a singleton."""

    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance



class SingletonMetaclass(type):

    # https://stackoverflow.com/a/6798042

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = \
                super(SingletonMetaclass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def input_to_ui_string(input_type: InputType, input_id: int | ScanCode) -> str:
    """Returns a string for UI usage of an input.

    Args:
        input_type: Type of the input
        input_id: Identifier of the input, usually a numerical index but for
            keyboard keys it is the key's scan code

    Returns:
        String for UI usage of the given data.
    """
    if input_type == InputType.JoystickAxis:
        try:
            return AxisNames.to_string(AxisNames(input_id))
        except error.GremlinError:
            return "Axis {:d}".format(input_id)
    elif input_type == InputType.Keyboard:
        assert isinstance(input_id, tuple) and len(input_id) == 2
        return key_from_code(*input_id).name
    else:
        return "{} {}".format(
            InputType.to_string(input_type).capitalize(),
            input_id
        )
