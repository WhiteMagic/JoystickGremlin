# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid
from collections.abc import Iterator
from unittest import mock
from xml.etree import ElementTree

import pytest

from action_plugins.map_to_mouse import (
    MapToMouseData,
    MapToMouseFunctor,
    MapToMouseMode,
)
from gremlin.base_classes import Value
from gremlin.profile import Library
from gremlin.sendinput import MouseMotionManager, Vector2
from gremlin.types import HatDirection, InputType, MouseButton

_ACTION_MAP_TO_MOUSE_SIMPLE = "action_map_to_mouse_simple.xml"
_MAP_TO_MOUSE_UUID = uuid.UUID("3f8c1d07-5b2a-4e61-9c84-06ad7e2b41f9")


@pytest.fixture(autouse=True)
def manager() -> Iterator[MouseMotionManager]:
    """Provides a motion manager isolated from other tests.

    The manager is a process wide singleton, so its state has to be dropped
    around every test.
    """
    instance = MouseMotionManager()
    instance.reset()
    yield instance
    instance.reset()


def _event(input_type: InputType) -> mock.MagicMock:
    """Returns an event standing in for an input of the given type."""
    event = mock.MagicMock()
    event.event_type = input_type
    return event


def _axis_functor(direction: int) -> MapToMouseFunctor:
    """Returns a functor driving mouse motion from an axis."""
    action = MapToMouseData(InputType.JoystickAxis)
    action.direction = direction
    return MapToMouseFunctor(action)


def _hat_functor(speed: int = 100) -> MapToMouseFunctor:
    """Returns a functor driving hat motion at a constant speed."""
    action = MapToMouseData(InputType.JoystickHat)
    action.min_speed = speed
    action.max_speed = speed
    return MapToMouseFunctor(action)


def _sole_velocity(manager: MouseMotionManager) -> Vector2:
    """Returns the velocity of the single registered contribution."""
    assert len(manager._sources) == 1
    return next(iter(manager._sources.values())).velocity(0.0)


def _sign(value: float) -> int:
    """Returns the sign of a value, treating tiny magnitudes as zero."""
    if abs(value) < 1e-6:
        return 0
    return 1 if value > 0 else -1


@pytest.mark.parametrize(
    ("behavior", "mode"),
    [
        (InputType.JoystickButton, MapToMouseMode.Button),
        (InputType.JoystickAxis, MapToMouseMode.Motion),
        (InputType.JoystickHat, MapToMouseMode.Motion),
    ],
)
def test_ctor(behavior: InputType, mode: MapToMouseMode) -> None:
    action = MapToMouseData(behavior)

    assert action.mode == mode
    assert action.direction == 0
    assert action.min_speed == 50
    assert action.max_speed == 250
    assert action.time_to_max_speed == 1.0


def test_from_xml(xml_dir: pathlib.Path) -> None:
    library = Library()
    action = MapToMouseData(InputType.JoystickAxis)
    action.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_MAP_TO_MOUSE_SIMPLE).read_text()),
        library,
    )

    assert action.id == _MAP_TO_MOUSE_UUID
    assert action.mode == MapToMouseMode.Motion
    assert action.direction == 90
    assert action.min_speed == 25
    assert action.max_speed == 175
    assert action.time_to_max_speed == 2.5


@pytest.mark.parametrize("mode", [MapToMouseMode.Button, MapToMouseMode.Motion])
def test_roundtrip(mode: MapToMouseMode) -> None:
    """Both modes serialize a different set of properties."""
    action = MapToMouseData(InputType.JoystickButton)
    action.mode = mode
    action.button = MouseButton.Middle
    action.direction = 135
    action.min_speed = 25
    action.max_speed = 175
    action.time_to_max_speed = 2.5

    node = action.to_xml()
    assert node is not None
    restored = MapToMouseData(InputType.JoystickButton)
    restored.from_xml(node, Library())

    assert restored.mode == mode
    if mode == MapToMouseMode.Button:
        assert restored.button == MouseButton.Middle
    else:
        assert restored.direction == 135
        assert restored.min_speed == 25
        assert restored.max_speed == 175
        assert restored.time_to_max_speed == 2.5


@pytest.mark.parametrize(
    ("direction", "value", "expected_x", "expected_y"),
    [
        # 0 and 90 are legacy selectors for the screen axes, not headings
        (0, 0.5, 0, 1),
        (90, 0.5, 1, 0),
        (90, -0.5, -1, 0),
        # Anything else is treated as a compass heading
        (45, 0.5, 1, -1),
    ],
)
def test_axis_motion_direction(
    manager: MouseMotionManager,
    direction: int,
    value: float,
    expected_x: int,
    expected_y: int,
) -> None:
    functor = _axis_functor(direction)

    functor(_event(InputType.JoystickAxis), Value(value))

    velocity = _sole_velocity(manager)
    assert _sign(velocity.x) == expected_x
    assert _sign(velocity.y) == expected_y


def test_axis_at_rest_removes_contribution(manager: MouseMotionManager) -> None:
    """A centered axis must not keep moving the cursor at min_speed."""
    functor = _axis_functor(90)
    event = _event(InputType.JoystickAxis)
    functor(event, Value(0.5))

    functor(event, Value(0.0))

    assert manager._sources == {}


@pytest.mark.parametrize("residual", [5e-6, -5e-6, 5e-4, -5e-4])
def test_axis_values_below_threshold_remove_contribution(
    manager: MouseMotionManager, residual: float
) -> None:
    functor = _axis_functor(90)
    event = _event(InputType.JoystickAxis)
    functor(event, Value(0.5))

    functor(event, Value(residual))

    assert manager._sources == {}


def test_hat_north_east_is_unit_length(manager: MouseMotionManager) -> None:
    """Hat coordinates are cartesian, screen coordinates grow downwards."""
    functor = _hat_functor()

    functor(_event(InputType.JoystickHat), Value(HatDirection.NorthEast))

    velocity = _sole_velocity(manager)
    assert velocity.magnitude() == pytest.approx(100.0)
    assert velocity.x == pytest.approx(70.7107, abs=1e-3)
    assert velocity.y == pytest.approx(-70.7107, abs=1e-3)


def test_hat_center_clears_contribution(manager: MouseMotionManager) -> None:
    functor = _hat_functor()
    event = _event(InputType.JoystickHat)
    functor(event, Value(HatDirection.North))

    functor(event, Value(HatDirection.Center))

    assert manager._sources == {}


def test_button_release_clears_contribution(manager: MouseMotionManager) -> None:
    action = MapToMouseData(InputType.JoystickButton)
    action.mode = MapToMouseMode.Motion
    functor = MapToMouseFunctor(action)
    event = _event(InputType.JoystickButton)
    event.is_pressed = True
    functor(event, Value(True))
    assert len(manager._sources) == 1

    event.is_pressed = False
    functor(event, Value(False))

    assert manager._sources == {}


def test_distinct_actions_get_distinct_keys(manager: MouseMotionManager) -> None:
    """Two actions on one input must not overwrite each other."""
    event = _event(InputType.JoystickAxis)
    _axis_functor(90)(event, Value(0.5))
    _axis_functor(0)(event, Value(0.5))

    assert len(manager._sources) == 2
