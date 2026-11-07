# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator

import pytest

from gremlin.event_handler import EventHandler
from gremlin.mode_manager import (
    Mode,
    ModeManager,
)
from gremlin.types import (
    Event,
    HatDirection,
    InputBindingCallback,
    InputType,
    ModeType,
)

_DEVICE_GUID = uuid.UUID("6a0c4f3e-2b1d-4e8a-9f75-c3d2e1b0a987")

type Callback = InputBindingCallback | Callable[[Event], None]
type Bind = Callable[[Event, list[Callback]], None]


class _RecordingBinding:
    """Stands in for a profile binding, answering with a fixed sequence."""

    # Required by InputBindingCallback, otherwise the handler calls it as a script.
    always_execute = True

    def __init__(self, answers: list[bool]) -> None:
        self._answers = answers
        self.received: list[tuple[Event, ModeType]] = []

    def __call__(self, event: Event, mode_type: ModeType) -> bool:
        self.received.append((event, mode_type))
        return self._answers[min(len(self.received), len(self._answers)) - 1]

    def reset(self) -> None:
        pass

    def teardown(self) -> None:
        pass


@pytest.fixture
def bind(monkeypatch: pytest.MonkeyPatch) -> Iterator[Bind]:
    """Provides a function binding callbacks to an input in the event's mode.

    The current mode starts as A.
    """
    handler = EventHandler()
    monkeypatch.setattr(ModeManager(), "_mode_stack", [Mode("A", None)])
    monkeypatch.setattr(handler, "process_callbacks", True)
    monkeypatch.setattr(handler, "callbacks", {})
    monkeypatch.setattr(handler, "_pending_callbacks", {})

    def add(event: Event, callbacks: list[Callback]) -> None:
        for callback in callbacks:
            handler.add_callback(event.device_guid, event.mode, event, callback)

    yield add
    handler.clear()


def _set_current_mode(monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    monkeypatch.setattr(ModeManager(), "_mode_stack", [Mode(mode, None)])


def _button_event(mode: str, is_pressed: bool) -> Event:
    return Event(
        event_type=InputType.JoystickButton,
        identifier=1,
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


def test_pending_binding_gets_next_event_of_other_mode_as_foreign(bind: Bind) -> None:
    binding = _RecordingBinding([True, False])
    bind(_button_event("A", True), [binding])

    EventHandler().process_event(_button_event("A", True))
    EventHandler().process_event(_button_event("B", False))

    assert [(event.is_pressed, mode_type) for event, mode_type in binding.received] == [
        (True, ModeType.Native),
        (False, ModeType.Foreign),
    ]


@pytest.mark.parametrize(
    ("current_mode", "mode_type"),
    [
        pytest.param("A", ModeType.Native, id="also_bound"),
        pytest.param("B", ModeType.Foreign, id="only_pending"),
    ],
)
def test_pending_binding_gets_each_event_once(
    bind: Bind,
    monkeypatch: pytest.MonkeyPatch,
    current_mode: str,
    mode_type: ModeType,
) -> None:
    binding = _RecordingBinding([True])
    bind(_axis_event("A", 0.0), [binding])
    EventHandler().process_event(_axis_event("A", 0.7))
    _set_current_mode(monkeypatch, current_mode)
    binding.received.clear()

    EventHandler().process_event(_axis_event(current_mode, 0.75))
    EventHandler().process_event(_axis_event(current_mode, 0.8))

    assert [
        (event.value, received_mode_type)
        for event, received_mode_type in binding.received
    ] == [(0.75, mode_type), (0.8, mode_type)]


def test_binding_answering_false_gets_no_further_foreign_event(bind: Bind) -> None:
    binding = _RecordingBinding([True, False])
    bind(_button_event("A", True), [binding])
    EventHandler().process_event(_button_event("A", True))
    EventHandler().process_event(_button_event("B", False))
    binding.received.clear()

    EventHandler().process_event(_button_event("B", True))

    assert binding.received == []


def test_script_callback_gets_release_in_other_mode_once(bind: Bind) -> None:
    received: list[bool | None] = []
    bind(_button_event("A", True), [lambda event: received.append(event.is_pressed)])

    EventHandler().process_event(_button_event("A", True))
    EventHandler().process_event(_button_event("B", False))
    EventHandler().process_event(_button_event("B", True))

    assert received == [True, False]


def test_script_callback_gets_centre_for_hat_direction_in_other_mode(
    bind: Bind,
) -> None:
    received: list[float | HatDirection | None] = []
    bind(
        _hat_event("A", HatDirection.North),
        [lambda event: received.append(event.value)],
    )

    EventHandler().process_event(_hat_event("A", HatDirection.North))
    EventHandler().process_event(_hat_event("B", HatDirection.East))

    assert received == [HatDirection.North, HatDirection.Center]


def test_clear_forgets_pending_bindings(bind: Bind) -> None:
    binding = _RecordingBinding([True])
    bind(_button_event("A", True), [binding])
    EventHandler().process_event(_button_event("A", True))
    handler = EventHandler()

    handler.clear()
    binding.received.clear()
    handler.process_event(_button_event("B", False))

    assert binding.received == []
