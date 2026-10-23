# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import AbstractContextManager
from unittest import mock

import pytest

from gremlin.event_handler import EventGenerator, EventHandler
from gremlin.mode_manager import ModeManager
from gremlin.types import Event, HatDirection, InputType

_DEVICE_GUID = uuid.UUID("6a0c4f3e-2b1d-4e8a-9f75-c3d2e1b0a987")


@pytest.fixture
def generator() -> Iterator[EventGenerator]:
    """Provides an event generator that stops following mode changes afterwards."""
    instance = EventGenerator()
    yield instance
    ModeManager().modeChanged.disconnect(instance._mode_changed_cb)


def _same_binding(is_same: bool) -> AbstractContextManager[mock.MagicMock]:
    """Makes the handler report whether two modes share the binding."""
    return mock.patch.object(EventHandler(), "is_same_binding", return_value=is_same)


def _button_event(mode: str, is_pressed: bool) -> Event:
    return Event(
        event_type=InputType.JoystickButton,
        identifier=1,
        device_guid=_DEVICE_GUID,
        mode=mode,
        is_pressed=is_pressed,
    )


def _hat_event(mode: str, direction: HatDirection) -> Event:
    return Event(
        event_type=InputType.JoystickHat,
        identifier=1,
        device_guid=_DEVICE_GUID,
        mode=mode,
        value=direction,
    )


def test_release_follows_press_mode(generator: EventGenerator) -> None:
    list(generator(_button_event("A", True)))
    released = list(generator(_button_event("B", False)))

    assert len(released) == 1
    assert [(e.is_pressed, e.mode) for e in released] == [(False, "A")]


def test_release_without_press_keeps_mode(generator: EventGenerator) -> None:
    released = list(generator(_button_event("B", False)))

    assert len(released) == 1
    assert [(e.is_pressed, e.mode) for e in released] == [(False, "B")]


def test_hat_center_follows_direction_mode(generator: EventGenerator) -> None:
    list(generator(_hat_event("A", HatDirection.North)))
    centered = list(generator(_hat_event("B", HatDirection.Center)))

    assert len(centered) == 1
    assert [(e.value, e.mode) for e in centered] == [(HatDirection.Center, "A")]


def test_hat_direction_in_other_binding_centers_previous_mode(
    generator: EventGenerator,
) -> None:
    with _same_binding(False):
        list(generator(_hat_event("A", HatDirection.North)))
        events = list(generator(_hat_event("B", HatDirection.East)))

    assert len(events) == 2
    assert [(e.value, e.mode) for e in events] == [
        (HatDirection.Center, "A"),
        (HatDirection.East, "B"),
    ]


def test_hat_direction_in_same_binding_yields_only_event(
    generator: EventGenerator,
) -> None:
    with _same_binding(True):
        list(generator(_hat_event("A", HatDirection.North)))
        events = list(generator(_hat_event("B", HatDirection.East)))

    assert [(e.value, e.mode) for e in events] == [(HatDirection.East, "B")]


def test_reset_forgets_dispatch_mode(generator: EventGenerator) -> None:
    list(generator(_button_event("A", True)))
    generator.reset()
    released = list(generator(_button_event("B", False)))

    assert [(e.is_pressed, e.mode) for e in released] == [(False, "B")]
