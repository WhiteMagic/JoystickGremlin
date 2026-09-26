# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import os

import pytest

from dill import (
    DILL,
    DeviceSummary,
    DILLError,
    _DeviceSummary,
)


@pytest.fixture
def unloaded_dill(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(DILL, "_dll", None)
    monkeypatch.setattr(DILL, "_dll_path", None)


def test_DeviceSummary_initialisation() -> None:
    c_device_summary = _DeviceSummary()
    c_device_summary.name = b"MOZA R12 Base\x90"
    device_summary = DeviceSummary(data=c_device_summary)

    assert device_summary.name == "MOZA R12 Base"


def test_load_default(unloaded_dill: None) -> None:
    DILL.load()
    assert DILL._dll is not None
    assert os.path.basename(DILL._dll_path) == "dill2.dll"


def test_load_legacy(unloaded_dill: None) -> None:
    DILL.load(use_legacy=True)
    assert DILL._dll is not None
    assert os.path.basename(DILL._dll_path) == "dill.dll"


def test_load_same_library_twice(unloaded_dill: None) -> None:
    DILL.load()
    dll = DILL._dll
    DILL.load()
    assert DILL._dll is dll


def test_load_different_library_after_load(unloaded_dill: None) -> None:
    DILL.load()
    with pytest.raises(DILLError):
        DILL.load(use_legacy=True)
