# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import (
    Any,
    Generic,
    TypeVar,
)

from gremlin import error
from gremlin.keyboard import key_from_code
from gremlin.types import (
    AxisNames,
    InputType,
    ScanCode,
)

T = TypeVar("T")


class SingletonDecorator(Generic[T]):
    """Decorator turning a class into a singleton."""

    def __init__(self, klass: type[T]) -> None:
        self.klass = klass
        self.instance: T | None = None

    def __call__(self, *args: Any, **kwargs: dict) -> T:  # noqa: ANN401
        if self.instance is None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance


class SingletonMetaclass(type):
    # https://stackoverflow.com/a/6798042

    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: dict) -> Any:  # noqa: ANN401
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMetaclass, cls).__call__(
                *args, **kwargs
            )
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
            return f"Axis {input_id:d}"
    elif input_type == InputType.Keyboard:
        assert isinstance(input_id, tuple) and len(input_id) == 2
        return key_from_code(*input_id).name
    else:
        return f"{InputType.to_string(input_type).capitalize()} {input_id}"


def parse_ui_string(ui_str: str) -> tuple[InputType, int]:
    """Parses a UI string into proper Python types.

    Args:
        ui_str: String from the UI to parse.

    Returns:
        Tuple containing the InputType and index/identifier of it.
    """
    if ui_str.startswith("Button") or ui_str.startswith("Hat"):
        parts = ui_str.split(" ")
        if parts[0] == "Button":
            return InputType.JoystickButton, int(parts[1])
        elif parts[0] == "Hat":
            return InputType.JoystickHat, int(parts[1])
        else:
            raise error.GremlinError(f"Invalid input string: {ui_str}")
    try:
        return InputType.JoystickAxis, AxisNames.to_enum(ui_str).value
    except error.GremlinError:
        raise error.GremlinError(f"Invalid input string: {ui_str}")
