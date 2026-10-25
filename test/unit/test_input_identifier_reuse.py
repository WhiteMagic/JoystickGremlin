# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import uuid

import pytest
from PySide6 import QtCore

from gremlin.logical_device import LogicalDevice
from gremlin.types import InputType, ScanCode
from gremlin.ui.backend import UIState
from gremlin.ui.device import (
    InputIdentifier,
    LogicalDeviceManagementModel,
    reuse_or_replace_identifier,
)

_DEVICE_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
_DEVICE_B = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture(autouse=True)
def reset_logical() -> None:
    LogicalDevice().reset()


@pytest.fixture
def scheduled_deletions(monkeypatch: pytest.MonkeyPatch) -> list[InputIdentifier]:
    # Mock Qt's deleteLater behavior.
    scheduled: list[InputIdentifier] = []

    def record(identifier: InputIdentifier) -> None:
        scheduled.append(identifier)

    monkeypatch.setattr(InputIdentifier, "deleteLater", record)
    return scheduled


def identifier_tuple(
    identifier: InputIdentifier,
) -> tuple[uuid.UUID | None, InputType | None, int | ScanCode | None]:
    # InputIdentifier has no __repr__, compare fields for readable failures.
    return (identifier.device_guid, identifier.input_type, identifier.input_id)


def test_model_identifier_matches_input() -> None:
    logical = LogicalDevice()
    logical.create(InputType.JoystickButton, label="First")
    logical.create(InputType.JoystickButton, label="Second")
    model = LogicalDeviceManagementModel()

    first = model.inputIdentifier(0)
    second = model.inputIdentifier(1)

    assert identifier_tuple(first) == (
        LogicalDevice.device_guid,
        InputType.JoystickButton,
        1,
    )
    assert identifier_tuple(second) == (
        LogicalDevice.device_guid,
        InputType.JoystickButton,
        2,
    )
    assert first.parent() is model
    assert not model.inputIdentifier(-1).isValid


def test_ui_state_remembers_selection_per_device() -> None:
    ui_state = UIState()
    ui_state.setCurrentInput(InputIdentifier(_DEVICE_A, InputType.JoystickButton, 3), 5)
    ui_state.setCurrentInput(InputIdentifier(_DEVICE_B, InputType.JoystickAxis, 2), 1)

    ui_state.setCurrentDevice(str(_DEVICE_A))
    assert identifier_tuple(ui_state.currentInput) == (
        _DEVICE_A,
        InputType.JoystickButton,
        3,
    )
    assert ui_state.currentInputIndex == 5

    ui_state.setCurrentDevice(str(_DEVICE_B))
    assert identifier_tuple(ui_state.currentInput) == (
        _DEVICE_B,
        InputType.JoystickAxis,
        2,
    )
    assert ui_state.currentInputIndex == 1

    # Ensure that setting input doesn't change device selection.
    ui_state.setCurrentInput(InputIdentifier(_DEVICE_A, InputType.JoystickButton, 4), 6)
    assert identifier_tuple(ui_state.currentInput) == (
        _DEVICE_B,
        InputType.JoystickAxis,
        2,
    )
    assert ui_state.currentInputIndex == 1

    ui_state.setCurrentDevice(str(_DEVICE_A))
    assert identifier_tuple(ui_state.currentInput) == (
        _DEVICE_A,
        InputType.JoystickButton,
        4,
    )
    assert ui_state.currentInputIndex == 6


def test_ui_state_repeated_selection_keeps_stored_identifier(
    scheduled_deletions: list[InputIdentifier],
) -> None:
    ui_state = UIState()
    ui_state.setCurrentDevice(str(_DEVICE_A))
    stored = InputIdentifier(_DEVICE_A, InputType.JoystickButton, 3)
    duplicate = InputIdentifier(_DEVICE_A, InputType.JoystickButton, 3)
    ui_state.setCurrentInput(stored, 5)

    ui_state.setCurrentInput(duplicate, 5)

    assert ui_state.currentInput is stored
    assert scheduled_deletions[0] is duplicate


@pytest.mark.parametrize(("input_id", "index"), [(3, 6), (4, 5)])
def test_ui_state_changed_selection_replaces_previous(
    scheduled_deletions: list[InputIdentifier], input_id: int, index: int
) -> None:
    ui_state = UIState()
    ui_state.setCurrentDevice(str(_DEVICE_A))
    previous = InputIdentifier(_DEVICE_A, InputType.JoystickButton, 3)
    replacement = InputIdentifier(_DEVICE_A, InputType.JoystickButton, input_id)
    ui_state.setCurrentInput(previous, 5)
    emissions: list[bool] = []
    ui_state.inputChanged.connect(lambda: emissions.append(True))

    ui_state.setCurrentInput(replacement, index)

    assert ui_state.currentInput is replacement
    assert ui_state.currentInputIndex == index
    assert replacement.parent() is ui_state
    assert scheduled_deletions[0] is previous
    assert emissions == [True]


def test_reuse_returns_matching_identifier() -> None:
    owner = QtCore.QObject()
    current = InputIdentifier(_DEVICE_A, InputType.JoystickButton, 3, parent=owner)

    result = reuse_or_replace_identifier(
        current, _DEVICE_A, InputType.JoystickButton, 3, owner
    )

    assert result is current


@pytest.mark.parametrize(
    ("device_guid", "input_type", "input_id"),
    [
        (_DEVICE_B, InputType.JoystickButton, 3),
        (_DEVICE_A, InputType.JoystickAxis, 3),
        (_DEVICE_A, InputType.JoystickButton, 4),
    ],
)
def test_replace_creates_owned_identifier_and_deletes_current(
    scheduled_deletions: list[InputIdentifier],
    device_guid: uuid.UUID,
    input_type: InputType,
    input_id: int,
) -> None:
    owner = QtCore.QObject()
    current = InputIdentifier(_DEVICE_A, InputType.JoystickButton, 3, parent=owner)

    result = reuse_or_replace_identifier(
        current, device_guid, input_type, input_id, owner
    )

    assert identifier_tuple(result) == (device_guid, input_type, input_id)
    assert result.parent() is owner
    assert scheduled_deletions[0] is current


def test_replace_without_current_creates_owned_identifier() -> None:
    owner = QtCore.QObject()

    result = reuse_or_replace_identifier(
        None, _DEVICE_A, InputType.JoystickButton, 3, owner
    )

    assert identifier_tuple(result) == (_DEVICE_A, InputType.JoystickButton, 3)
    assert result.parent() is owner
