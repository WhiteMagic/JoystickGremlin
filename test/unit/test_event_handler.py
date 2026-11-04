# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from unittest import mock

import pytest

from gremlin.event_handler import EventGenerator, EventHandler
from gremlin.mode_manager import (
    Mode,
    ModeManager,
)
from gremlin.types import Event, HatDirection, InputType

_DEVICE_GUID = uuid.UUID("6a0c4f3e-2b1d-4e8a-9f75-c3d2e1b0a987")


class _HeldBinding:
    """Stands in for the binding of a pressed axis virtual button."""

    # Runs regardless of any pause state left behind by other tests.
    always_execute = True

    def __init__(self) -> None:
        self.received_values: list[float] = []

    def __call__(self, event: Event) -> None:
        self.received_values.append(event.value)

    def is_held(self) -> bool:
        return True

    def reset(self) -> None:
        pass

    def teardown(self) -> None:
        pass


@pytest.fixture
def generator() -> Iterator[EventGenerator]:
    """Provides an event generator that stops following mode changes afterwards."""
    instance = EventGenerator()
    yield instance
    ModeManager().modeChanged.disconnect(instance._mode_changed_cb)


@pytest.fixture
def leave_mode_a(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Callable[[list[Callable[[Event], None]]], None]]:
    """Provides a function binding callbacks to an axis in A, then switching to B."""
    manager = ModeManager()
    monkeypatch.setattr(manager, "_mode_stack", [Mode("A", None)])

    def leave(callbacks: list[Callable[[Event], None]]) -> None:
        bound = {_DEVICE_GUID: {"A": {_axis_event("A", 0.0): callbacks}}}
        monkeypatch.setattr(EventHandler(), "callbacks", bound)
        manager.switch_to(Mode("B", "A"), refresh_axes=False)

    yield leave
    EventHandler().clear()


def _same_binding(is_same: bool) -> AbstractContextManager[mock.MagicMock]:
    """Makes the handler report whether two modes share the binding."""
    return mock.patch.object(EventHandler(), "is_same_binding", return_value=is_same)


def _button_event(
    mode: str,
    is_pressed: bool,
    event_type: InputType = InputType.JoystickButton,
    identifier: int | tuple[int, bool] = 1,
) -> Event:
    return Event(
        event_type=event_type,
        identifier=identifier,
        device_guid=_DEVICE_GUID,
        mode=mode,
        is_pressed=is_pressed,
    )


def _axis_event(mode: str, value: float) -> Event:
    return Event(
        event_type=InputType.JoystickAxis,
        identifier=1,
        device_guid=_DEVICE_GUID,
        mode=mode,
        value=value,
    )


def _hat_event(mode: str, direction: HatDirection) -> Event:
    return Event(
        event_type=InputType.JoystickHat,
        identifier=1,
        device_guid=_DEVICE_GUID,
        mode=mode,
        value=direction,
    )


@pytest.mark.parametrize(
    ("event_type", "identifier"),
    [
        pytest.param(InputType.JoystickButton, 1, id="joystick_button"),
        pytest.param(InputType.Keyboard, (30, False), id="keyboard"),
        pytest.param(InputType.VirtualButton, 1, id="virtual_button"),
    ],
)
def test_release_follows_press_mode(
    generator: EventGenerator,
    event_type: InputType,
    identifier: int | tuple[int, bool],
) -> None:
    list(generator(_button_event("A", True, event_type, identifier)))
    released = list(generator(_button_event("B", False, event_type, identifier)))

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


def test_held_axis_binding_gets_each_event_once(
    leave_mode_a: Callable[[list[Callable[[Event], None]]], None],
) -> None:
    # What: a held binding of an inactive mode receives every axis event exactly once.
    # Why: today its list doubles on each event, which hangs the app after a few dozen
    # events. Outputs can't show this because the virtual button ignores repeated
    # states.
    binding = _HeldBinding()
    leave_mode_a([binding])

    for value in [0.7, 0.75, 0.8]:
        binding.received_values.clear()
        EventHandler().process_event(_axis_event("B", value))
        assert binding.received_values == [value]


def test_clear_forgets_held_axis_bindings(
    leave_mode_a: Callable[[list[Callable[[Event], None]]], None],
) -> None:
    # What: clearing the handler drops held bindings, so a stopped profile's binding
    # gets no further axis events.
    # Why: a binding kept across a profile stop would run actions of the unloaded
    # profile.
    binding = _HeldBinding()
    leave_mode_a([binding])
    handler = EventHandler()
    callbacks = handler.callbacks

    handler.clear()
    handler.callbacks = callbacks
    handler.process_event(_axis_event("B", 0.7))

    assert binding.received_values == []
