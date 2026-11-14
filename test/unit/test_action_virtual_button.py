# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid

import pytest

from action_plugins.description import DescriptionData
from action_plugins.virtual_button import (
    VirtualButtonData,
    VirtualButtonFunctor,
)
from gremlin.base_classes import Value
from gremlin.profile import Profile
from gremlin.types import (
    AxisButtonDirection,
    Event,
    HatDirection,
    InputType,
    ModeType,
)

_PROFILE = "action_virtual_button.xml"


class _ChildRecorder:
    """Stands in for a child functor, recording what reaches it."""

    def __init__(self) -> None:
        self.received: list[tuple[InputType, bool, ModeType]] = []
        self.data = DescriptionData()
        self.functors: dict = {}

    def __call__(self, event: Event, value: Value, properties: list = []) -> bool:
        self.received.append((event.event_type, value.current, value.mode_type))
        return False

    def waiting_for_event(self) -> bool:
        return False

    def reset(self) -> None:
        pass


def _functor(
    xml_dir: pathlib.Path, action_id: str
) -> tuple[VirtualButtonFunctor, _ChildRecorder]:
    profile = Profile()
    profile.from_xml(xml_dir / _PROFILE)
    functor = VirtualButtonFunctor(profile.library.get_action(uuid.UUID(action_id)))
    child = _ChildRecorder()
    functor.functors["children"] = [child]
    return functor, child


def _send(
    functor: VirtualButtonFunctor,
    input_type: InputType,
    current: float | HatDirection,
    mode_type: ModeType = ModeType.Native,
) -> bool:
    event = Event(input_type, 1, uuid.uuid4(), "Default", value=current)
    return functor(event, Value(current, mode_type))


def test_from_xml(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(xml_dir / _PROFILE)

    axis_button = p.library.get_action(
        uuid.UUID("b7c10000-0000-4000-8000-000000000002")
    )
    hat_button = p.library.get_action(uuid.UUID("b7c10000-0000-4000-8000-000000000003"))

    assert isinstance(axis_button, VirtualButtonData)
    assert axis_button.lower_limit == pytest.approx(0.5)
    assert axis_button.upper_limit == pytest.approx(1.0)
    assert axis_button.direction == AxisButtonDirection.Below
    assert [child.description for child in axis_button.children] == ["afterburner"]
    assert hat_button.hat_directions == [HatDirection.North, HatDirection.NorthEast]


def test_to_xml_round_trips_settings(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(xml_dir / _PROFILE)
    original = p.library.get_action(uuid.UUID("b7c10000-0000-4000-8000-000000000003"))

    restored = VirtualButtonData()
    restored.from_xml(original.to_xml(), p.library)

    assert restored.hat_directions == [HatDirection.North, HatDirection.NorthEast]
    assert [child.id for child in restored.children] == [
        child.id for child in original.children
    ]


def test_axis_button_presses_children_on_entering_range(xml_dir: pathlib.Path) -> None:
    functor, child = _functor(xml_dir, "b7c10000-0000-4000-8000-000000000001")

    _send(functor, InputType.JoystickAxis, 0.0)
    assert child.received == []

    assert _send(functor, InputType.JoystickAxis, 0.75)
    assert not _send(functor, InputType.JoystickAxis, 0.25)
    assert child.received == [
        (InputType.VirtualButton, True, ModeType.Native),
        (InputType.VirtualButton, False, ModeType.Native),
    ]


def test_directional_button_stays_released_on_entry_from_above(
    xml_dir: pathlib.Path,
) -> None:
    functor, child = _functor(xml_dir, "b7c10000-0000-4000-8000-000000000002")

    _send(functor, InputType.JoystickAxis, 1.0)
    _send(functor, InputType.JoystickAxis, 0.75)
    assert child.received == []

    _send(functor, InputType.JoystickAxis, 0.0)
    _send(functor, InputType.JoystickAxis, 0.75)
    assert child.received == [(InputType.VirtualButton, True, ModeType.Native)]


def test_hat_button_presses_children_on_selected_direction(
    xml_dir: pathlib.Path,
) -> None:
    functor, child = _functor(xml_dir, "b7c10000-0000-4000-8000-000000000003")

    _send(functor, InputType.JoystickHat, HatDirection.East)
    assert child.received == []

    _send(functor, InputType.JoystickHat, HatDirection.NorthEast)
    _send(functor, InputType.JoystickHat, HatDirection.North)
    _send(functor, InputType.JoystickHat, HatDirection.Center)
    assert child.received == [
        (InputType.VirtualButton, True, ModeType.Native),
        (InputType.VirtualButton, False, ModeType.Native),
    ]


def test_axis_button_releases_children_as_foreign_on_foreign_event(
    xml_dir: pathlib.Path,
) -> None:
    functor, child = _functor(xml_dir, "b7c10000-0000-4000-8000-000000000001")

    _send(functor, InputType.JoystickAxis, 0.75)
    assert child.received == [(InputType.VirtualButton, True, ModeType.Native)]

    _send(functor, InputType.JoystickAxis, 0.0, ModeType.Foreign)
    assert child.received[1:] == [(InputType.VirtualButton, False, ModeType.Foreign)]


def test_directional_button_forgets_movement_on_reset(xml_dir: pathlib.Path) -> None:
    functor, child = _functor(xml_dir, "b7c10000-0000-4000-8000-000000000002")

    _send(functor, InputType.JoystickAxis, 0.0)
    functor.reset()
    _send(functor, InputType.JoystickAxis, 0.75)

    assert child.received == []
