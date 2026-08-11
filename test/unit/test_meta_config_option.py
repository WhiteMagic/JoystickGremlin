# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import sys

sys.path.append(".")

from collections.abc import Iterator

import pytest
from PySide6 import QtCore

import gremlin.config
import gremlin.error
import gremlin.types
from gremlin.common import SingletonMetaclass
from gremlin.ui.option import (
    ActionSequenceOrdering,
    BaseMetaConfigOptionWidget,
    MetaConfigOption,
)

NAME_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
PRIORITY_KEY = ("action", "general", "action-priorities")


class DummyWidget(BaseMetaConfigOptionWidget):
    def _qml_type(self) -> str:
        return "DummyOption"


class RowSignalRecorder:
    """Records row insertion/removal signals along with the row count seen at
    emit time."""

    def __init__(self, model: QtCore.QAbstractListModel) -> None:
        self._model = model
        self.insertions: list[tuple[int, int, int]] = []
        self.removals: list[tuple[int, int, int]] = []

        model.rowsAboutToBeInserted.connect(self._record_insertion)
        model.rowsAboutToBeRemoved.connect(self._record_removal)

    def _record_insertion(
        self, parent: QtCore.QModelIndex, first: int, last: int
    ) -> None:
        self.insertions.append((first, last, self._model.rowCount()))

    def _record_removal(
        self, parent: QtCore.QModelIndex, first: int, last: int
    ) -> None:
        self.removals.append((first, last, self._model.rowCount()))

    def assert_valid(self) -> None:
        for first, last, row_count in self.insertions:
            assert 0 <= first <= row_count, (
                f"beginInsertRows({first}, {last}) with rowCount {row_count}"
            )
            assert first <= last
        for first, last, row_count in self.removals:
            assert 0 <= first < row_count, (
                f"beginRemoveRows({first}, {last}) with rowCount {row_count}"
            )
            assert first <= last < row_count


@pytest.fixture
def option() -> MetaConfigOption:
    SingletonMetaclass._instances.pop(MetaConfigOption, None)
    return MetaConfigOption()


@pytest.fixture
def ordering() -> Iterator[ActionSequenceOrdering]:
    config = gremlin.config.Configuration()
    original = [list(entry) for entry in config.value(*PRIORITY_KEY)]
    config.set(
        *PRIORITY_KEY,
        [["first", True], ["second", True], ["third", True], ["fourth", True]],
    )
    try:
        yield ActionSequenceOrdering()
    finally:
        config.set(*PRIORITY_KEY, original)


def action_names(model: ActionSequenceOrdering) -> list[str]:
    return [
        model.data(model.index(row, 0), NAME_ROLE) for row in range(model.rowCount())
    ]


def test_basic(option: MetaConfigOption) -> None:
    assert option.count() == 0

    option.register("some", "test", "option 1", "description 1", DummyWidget)
    option.register("some", "test", "option 2", "description 2", DummyWidget)

    assert option.count() == 2

    assert len(option.sections()) == 1
    assert len(option.groups("some")) == 1
    assert len(option.entries("some", "test")) == 2
    assert option.description("some", "test", "option 1") == "description 1"
    assert option.description("some", "test", "option 2") == "description 2"
    assert option.qml_widget("some", "test", "option 1") == DummyWidget
    assert option.qml_widget("some", "test", "option 2") == DummyWidget


def test_empty_entries(option: MetaConfigOption) -> None:
    assert option.count() == 0

    option.register("some", "test", "option 1", "description 1", DummyWidget)

    assert option.count() == 1

    assert len(option.sections()) == 1
    assert len(option.groups("some")) == 1
    assert len(option.entries("some", "test")) == 1
    assert option.entries("no", "such") == []
    assert option.entries("some", "no such") == []


def test_register_duplicate_logs_warning(
    option: MetaConfigOption, caplog: pytest.LogCaptureFixture
) -> None:
    option.register("dup", "grp", "name", "desc", DummyWidget)
    option.register("dup", "grp", "name", "desc", DummyWidget)

    assert caplog.record_tuples == [
        ("system", logging.WARNING, "Option dup.grp.name already registered.")
    ]


def test_retrieve_nonexistent_raises(option: MetaConfigOption) -> None:
    with pytest.raises(gremlin.error.GremlinError):
        option.qml_widget("no", "such", "option")

    option.register("sec", "grp", "name", "desc", DummyWidget)
    with pytest.raises(gremlin.error.GremlinError):
        option.description("sec", "grp", "other")


def test_move_to_end(ordering: ActionSequenceOrdering) -> None:
    recorder = RowSignalRecorder(ordering)

    ordering.move(0, ordering.rowCount())

    assert action_names(ordering) == ["second", "third", "fourth", "first"]
    assert recorder.insertions == [(3, 3, 3)]
    recorder.assert_valid()


def test_move_beyond_end(ordering: ActionSequenceOrdering) -> None:
    recorder = RowSignalRecorder(ordering)

    ordering.move(1, 17)

    assert action_names(ordering) == ["first", "third", "fourth", "second"]
    recorder.assert_valid()


def test_move_forward(ordering: ActionSequenceOrdering) -> None:
    recorder = RowSignalRecorder(ordering)

    ordering.move(0, 2)

    assert action_names(ordering) == ["second", "first", "third", "fourth"]
    assert recorder.removals == [(0, 0, 4)]
    assert recorder.insertions == [(1, 1, 3)]
    recorder.assert_valid()


def test_move_backward(ordering: ActionSequenceOrdering) -> None:
    recorder = RowSignalRecorder(ordering)

    ordering.move(3, 1)

    assert action_names(ordering) == ["first", "fourth", "second", "third"]
    assert recorder.removals == [(3, 3, 4)]
    assert recorder.insertions == [(1, 1, 3)]
    recorder.assert_valid()


@pytest.mark.parametrize(
    ("source_index", "target_index"),
    [(-1, 2), (4, 0), (99, 1), (2, 2)],
)
def test_move_no_op(
    ordering: ActionSequenceOrdering, source_index: int, target_index: int
) -> None:
    recorder = RowSignalRecorder(ordering)

    ordering.move(source_index, target_index)

    assert action_names(ordering) == ["first", "second", "third", "fourth"]
    assert recorder.insertions == []
    assert recorder.removals == []
