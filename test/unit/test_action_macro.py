# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import pathlib
import uuid
from typing import cast

import pytest

from action_plugins import macro
from action_plugins.root import RootData
from gremlin.macro import PauseAction
from gremlin.profile import (
    InputItem,
    InputItemBinding,
    Profile,
)
from gremlin.types import InputType
from gremlin.ui.profile import (
    InputItemBindingModel,
    InputItemModel,
)

_PROFILE = "action_macro.xml"
_ACTION_UUID = uuid.UUID("8759f48d-8879-488a-9895-07503bf0dc0c")
_INPUT_1_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540000")
_INPUT_2_DEVICE_UUID = uuid.UUID("97b77b40-07d8-11f0-8028-444553540001")


def test_from_xml(subtests: pytest.Subtests, xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))

    a = p.library.get_action(_ACTION_UUID)

    assert isinstance(a, macro.MacroData)
    with subtests.test("macro high level data"):
        assert not a.is_exclusive
        assert a.repeat_mode == macro.MacroRepeatModes.Single
        assert a.repeat_data.count == 1
        assert a.repeat_data.delay == 0.1
        assert a.is_valid()
        assert len(a.actions) == 10


def test_swap_uuid(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))

    a = p.library.get_action(_ACTION_UUID)

    new_device_uuid = uuid.uuid4()
    assert a.swap_uuid(_INPUT_1_DEVICE_UUID, new_device_uuid)
    assert a.actions[0].device_guid == new_device_uuid
    assert a.actions[2].device_guid == _INPUT_2_DEVICE_UUID


def _make_macro_model(
    step_count: int = 4,
) -> tuple[macro.MacroModel, macro.MacroData, InputItemModel]:
    """Builds a macro model holding `step_count` distinguishable pause steps.

    Returns:
        The macro model, its data and the owner keeping the tree alive.
    """
    behavior = InputType.JoystickButton
    profile = Profile()
    input_item = InputItem(profile.library)
    binding = InputItemBinding(input_item)
    binding.root_action = RootData(behavior)
    binding.behavior = behavior
    profile.library.add_action(binding.root_action)

    macro_data = macro.MacroData(behavior)
    macro_data.actions = [PauseAction(float(index)) for index in range(step_count)]
    profile.library.add_action(macro_data)
    binding.root_action.insert_action(macro_data, "children")

    binding_model = InputItemBindingModel(binding)
    # A real parent keeps _check_user_feedback resolvable when the global signal fires.
    owner = InputItemModel(input_item, 0)
    binding_model.setParent(owner)

    macro_model = cast(macro.MacroModel, binding_model.get_action_model_by_sidx(1))
    return macro_model, macro_data, owner


def _step_order(macro_data: macro.MacroData) -> list[float]:
    return [action.duration for action in macro_data.actions]


def test_drop_callback_append_moves_forward() -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    macro_model.dropCallback(2, 0, "append")

    assert _step_order(macro_data) == [1.0, 2.0, 0.0, 3.0]


def test_drop_callback_append_moves_backward() -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    macro_model.dropCallback(0, 3, "append")

    assert _step_order(macro_data) == [0.0, 3.0, 1.0, 2.0]


def test_drop_callback_prepend_moves_to_front() -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    macro_model.dropCallback(2, 3, "prepend")

    assert _step_order(macro_data) == [3.0, 0.0, 1.0, 2.0]


def test_drop_callback_prepend_ignores_garbage_target_index() -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    # Prepend never reads target_index, so QML is free to pass a placeholder.
    macro_model.dropCallback(-1, 2, "prepend")
    assert _step_order(macro_data) == [2.0, 0.0, 1.0, 3.0]

    macro_model.dropCallback(9999, 3, "prepend")
    assert _step_order(macro_data) == [3.0, 2.0, 0.0, 1.0]


@pytest.mark.parametrize("source_index", [-1, 4, 9999])
def test_drop_callback_rejects_out_of_range_source(source_index: int) -> None:
    macro_model, macro_data, _owner = _make_macro_model()
    emit_count = 0

    def _count_changed() -> None:
        nonlocal emit_count
        emit_count += 1

    macro_model.changed.connect(_count_changed)

    macro_model.dropCallback(1, source_index, "append")
    macro_model.dropCallback(1, source_index, "prepend")

    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]
    assert emit_count == 0


@pytest.mark.parametrize("target_index", [-1, 4, 9999])
def test_drop_callback_rejects_out_of_range_append_target(target_index: int) -> None:
    macro_model, macro_data, _owner = _make_macro_model()
    emit_count = 0

    def _count_changed() -> None:
        nonlocal emit_count
        emit_count += 1

    macro_model.changed.connect(_count_changed)

    macro_model.dropCallback(target_index, 0, "append")

    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]
    assert emit_count == 0


def test_drop_callback_logs_warning_on_invalid_indices(
    caplog: pytest.LogCaptureFixture,
) -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    with caplog.at_level(logging.WARNING, logger="system"):
        macro_model.dropCallback(1, 99, "append")

    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_drop_callback_unknown_mode_is_ignored(
    caplog: pytest.LogCaptureFixture,
) -> None:
    macro_model, macro_data, _owner = _make_macro_model()
    emit_count = 0

    def _count_changed() -> None:
        nonlocal emit_count
        emit_count += 1

    macro_model.changed.connect(_count_changed)

    # QML cannot act on an exception crossing back into it, so this must not raise.
    with caplog.at_level(logging.WARNING, logger="system"):
        macro_model.dropCallback(1, 0, "insert")

    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]
    assert emit_count == 0
    assert any(record.levelno == logging.WARNING for record in caplog.records)


@pytest.mark.parametrize("destination_index", [-1, 5, 9999])
def test_move_from_to_rejects_out_of_range_destination(destination_index: int) -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    assert macro_model._action_list_model.move_from_to(0, destination_index) is False

    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]


def test_move_from_to_allows_destination_at_end() -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    # Inserting past the last row is a legal destination for beginMoveRows.
    macro_model._action_list_model.move_from_to(0, 4)

    assert _step_order(macro_data) == [1.0, 2.0, 3.0, 0.0]


def test_move_from_to_returns_true_for_genuine_move() -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    assert macro_model._action_list_model.move_from_to(3, 1) is True

    assert _step_order(macro_data) == [0.0, 3.0, 1.0, 2.0]


@pytest.mark.parametrize("source_index", [-1, 4, 9999])
def test_move_from_to_returns_false_for_out_of_range_source(source_index: int) -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    assert macro_model._action_list_model.move_from_to(source_index, 1) is False

    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]


@pytest.mark.parametrize("source_index", [0, 1, 3])
def test_move_from_to_returns_false_for_self_move(source_index: int) -> None:
    macro_model, macro_data, _owner = _make_macro_model()

    # beginMoveRows refuses destinations inside [source_index, source_index + 1].
    assert (
        macro_model._action_list_model.move_from_to(source_index, source_index) is False
    )
    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]

    assert (
        macro_model._action_list_model.move_from_to(source_index, source_index + 1)
        is False
    )
    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]


@pytest.mark.parametrize(
    ("target_index", "source_index", "mode"),
    [
        # append passes target_index + 1, so both of these land on the source itself.
        (2, 2, "append"),
        (1, 2, "append"),
        (0, 0, "append"),
        (2, 0, "prepend"),
        (0, 0, "prepend"),
    ],
)
def test_drop_callback_does_not_emit_changed_on_self_move(
    target_index: int, source_index: int, mode: str
) -> None:
    macro_model, macro_data, _owner = _make_macro_model()
    emit_count = 0

    def _count_changed() -> None:
        nonlocal emit_count
        emit_count += 1

    macro_model.changed.connect(_count_changed)

    macro_model.dropCallback(target_index, source_index, mode)

    assert _step_order(macro_data) == [0.0, 1.0, 2.0, 3.0]
    assert emit_count == 0


@pytest.mark.parametrize(
    ("target_index", "source_index", "mode", "expected_order"),
    [
        (2, 0, "append", [1.0, 2.0, 0.0, 3.0]),
        (0, 3, "append", [0.0, 3.0, 1.0, 2.0]),
        (2, 3, "prepend", [3.0, 0.0, 1.0, 2.0]),
    ],
)
def test_drop_callback_emits_changed_once_for_genuine_reorder(
    target_index: int, source_index: int, mode: str, expected_order: list[float]
) -> None:
    macro_model, macro_data, _owner = _make_macro_model()
    emit_count = 0

    def _count_changed() -> None:
        nonlocal emit_count
        emit_count += 1

    macro_model.changed.connect(_count_changed)

    macro_model.dropCallback(target_index, source_index, mode)

    assert _step_order(macro_data) == expected_order
    assert emit_count == 1
