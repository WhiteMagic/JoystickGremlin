# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pytest
from PySide6 import QtCore

from gremlin.ui.profile import (
    LabelValueSelectionModel,
    reuse_or_replace_selection_model,
)


@pytest.fixture
def scheduled_deletions(
    monkeypatch: pytest.MonkeyPatch,
) -> list[LabelValueSelectionModel]:
    # Mock Qt's deleteLater behavior.
    scheduled: list[LabelValueSelectionModel] = []

    def record(model: LabelValueSelectionModel) -> None:
        scheduled.append(model)

    monkeypatch.setattr(LabelValueSelectionModel, "deleteLater", record)
    return scheduled


def test_reuse_returns_matching_model(
    scheduled_deletions: list[LabelValueSelectionModel],
) -> None:
    owner = QtCore.QObject()
    current = LabelValueSelectionModel(["A", "B"], ["1", "2"], parent=owner)

    result = reuse_or_replace_selection_model(current, ["A", "B"], ["1", "2"], owner)

    assert result is current
    assert scheduled_deletions == []


@pytest.mark.parametrize(
    ("labels", "values", "bootstrap"),
    [
        (["A", "C"], ["1", "2"], []),
        (["A", "B"], ["1", "3"], []),
        (["A", "B"], ["1", "2"], ["x", "y"]),
    ],
)
def test_replace_creates_owned_model_and_deletes_current(
    scheduled_deletions: list[LabelValueSelectionModel],
    labels: list[str],
    values: list[str],
    bootstrap: list[str],
) -> None:
    owner = QtCore.QObject()
    current = LabelValueSelectionModel(["A", "B"], ["1", "2"], parent=owner)

    result = reuse_or_replace_selection_model(
        current, labels, values, owner, bootstrap=bootstrap
    )

    assert result is not current
    assert result.parent() is owner
    assert scheduled_deletions == [current]


def test_replace_without_current_creates_owned_model() -> None:
    owner = QtCore.QObject()

    result = reuse_or_replace_selection_model(None, ["A"], ["1"], owner)

    assert result.rowCount() == 1
    assert result.parent() is owner


def test_replace_keeps_selected_value(
    scheduled_deletions: list[LabelValueSelectionModel],
) -> None:
    owner = QtCore.QObject()
    current = LabelValueSelectionModel(["A", "B"], ["1", "2"], parent=owner)
    current.currentValue = "2"

    result = reuse_or_replace_selection_model(
        current, ["Z", "A", "B"], ["0", "1", "2"], owner
    )

    assert result.currentValue == "2"


def test_replace_without_selected_value_starts_at_first_entry(
    scheduled_deletions: list[LabelValueSelectionModel],
) -> None:
    owner = QtCore.QObject()
    current = LabelValueSelectionModel(["A", "B"], ["1", "2"], parent=owner)
    current.currentValue = "2"

    result = reuse_or_replace_selection_model(current, ["A", "C"], ["1", "3"], owner)

    assert result.currentValue == "1"


def test_replace_empty_current_starts_at_first_entry(
    scheduled_deletions: list[LabelValueSelectionModel],
) -> None:
    owner = QtCore.QObject()
    current = LabelValueSelectionModel([], [], parent=owner)

    result = reuse_or_replace_selection_model(current, ["A"], ["1"], owner)

    assert result.currentValue == "1"
