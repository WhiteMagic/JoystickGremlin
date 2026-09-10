# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import uuid

from action_plugins.root import RootData
from gremlin.profile import (
    InputItem,
    InputItemBinding,
    Profile,
)
from gremlin.signal import signal
from gremlin.types import InputType
from gremlin.ui.profile import InputItemModel


def _make_input_item(sequence_count: int) -> InputItem:
    profile = Profile()
    input_item = InputItem(profile.library)
    input_item.input_type = InputType.JoystickButton

    for _ in range(sequence_count):
        binding = InputItemBinding(input_item)
        binding.root_action = RootData(InputType.JoystickButton)
        binding.behavior = InputType.JoystickButton
        profile.library.add_action(binding.root_action)
        input_item.action_sequences.append(binding)

    return input_item


def _sequence_ids(input_item: InputItem) -> list[uuid.UUID]:
    return [entry.root_action.id for entry in input_item.action_sequences]


def _drop_action_emit_counts(
    model: InputItemModel, source: str, target: str, prepend: bool
) -> tuple[int, int]:
    """Runs dropAction and returns the reload and inputItemChanged emission counts."""
    reload_count = 0
    changed_count = 0

    def _count_reload() -> None:
        nonlocal reload_count
        reload_count += 1

    def _count_changed(enumeration_index: int) -> None:
        nonlocal changed_count
        changed_count += 1

    signal.reloadCurrentInputItem.connect(_count_reload)
    signal.inputItemChanged.connect(_count_changed)
    try:
        model.dropAction(source, target, prepend)
    finally:
        signal.reloadCurrentInputItem.disconnect(_count_reload)
        signal.inputItemChanged.disconnect(_count_changed)

    return reload_count, changed_count


def test_drop_action_target_before_source() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    first, second, third, fourth = _sequence_ids(input_item)

    model.dropAction(str(fourth), str(first), False)

    assert _sequence_ids(input_item) == [first, fourth, second, third]


def test_drop_action_target_after_source() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    first, second, third, fourth = _sequence_ids(input_item)

    model.dropAction(str(first), str(third), False)

    assert _sequence_ids(input_item) == [second, third, first, fourth]


def test_drop_action_onto_immediate_predecessor() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    first, second, third, fourth = _sequence_ids(input_item)

    model.dropAction(str(third), str(second), False)

    assert _sequence_ids(input_item) == [first, second, third, fourth]


def test_drop_action_prepend() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    first, second, third, fourth = _sequence_ids(input_item)

    model.dropAction(str(third), str(first), True)

    assert _sequence_ids(input_item) == [third, first, second, fourth]


def test_drop_action_reorder_emits_reload_and_change() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    expected = _sequence_ids(input_item)

    counts = _drop_action_emit_counts(model, str(expected[3]), str(expected[0]), False)

    assert counts == (1, 1)


def test_drop_action_prepend_emits_reload_and_change() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    expected = _sequence_ids(input_item)

    counts = _drop_action_emit_counts(model, str(expected[2]), str(expected[0]), True)

    assert counts == (1, 1)


def test_drop_action_unknown_target_keeps_sequences() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    expected = _sequence_ids(input_item)

    counts = _drop_action_emit_counts(model, str(expected[1]), str(uuid.uuid4()), False)

    assert _sequence_ids(input_item) == expected
    assert counts == (1, 0)


def test_drop_action_unknown_source_keeps_sequences() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    expected = _sequence_ids(input_item)

    counts = _drop_action_emit_counts(model, str(uuid.uuid4()), str(expected[1]), False)

    assert _sequence_ids(input_item) == expected
    assert counts == (1, 0)


def test_drop_action_malformed_identifier_keeps_sequences() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    expected = _sequence_ids(input_item)

    source_counts = _drop_action_emit_counts(
        model, "not-a-uuid", str(expected[1]), False
    )
    target_counts = _drop_action_emit_counts(
        model, str(expected[1]), "not-a-uuid", False
    )

    assert _sequence_ids(input_item) == expected
    assert source_counts == (1, 0)
    assert target_counts == (1, 0)


def test_drop_action_identical_source_and_target_is_noop() -> None:
    input_item = _make_input_item(4)
    model = InputItemModel(input_item, 0)
    expected = _sequence_ids(input_item)

    counts = _drop_action_emit_counts(model, str(expected[2]), str(expected[2]), False)

    assert _sequence_ids(input_item) == expected
    # A no-op changed nothing, so only the view refresh may fire.
    assert counts == (1, 0)
