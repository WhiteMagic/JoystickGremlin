# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from gremlin.types import ValueRange


def test_initial_state() -> None:
    r = ValueRange(1, 5)
    assert r._low == 1
    assert r._high == 5
    assert r.value == 1
    assert isinstance(r.value, int)
    assert isinstance(r._low, int)
    assert isinstance(r._high, int)

    r = ValueRange(1.5, 3.2)
    assert r._low == 1.5
    assert r._high == 3.2
    assert r.value == 1.5
    assert isinstance(r.value, float)
    assert isinstance(r._low, float)
    assert isinstance(r._high, float)

    r = ValueRange(10, 2)
    assert r._low == 2
    assert r._high == 10
    assert r.value == 2

    r = ValueRange(7, 7)
    assert r._low == 7
    assert r._high == 7
    assert r.value == 7

    r = ValueRange(0, 10)
    r.value = 5
    assert r.value == 5


def test_set_values() -> None:
    r = ValueRange(0, 10)
    r.value = 5
    assert r.value == 5
    r.value = 11
    assert r.value == 10
    r.value = -1
    assert r.value == 0


def test_type_adherance() -> None:
    r = ValueRange(1, 2)
    assert isinstance(r.value, int)
    assert isinstance(r._low, int)
    assert isinstance(r._high, int)

    r = ValueRange(1.1, 2.2)
    assert isinstance(r.value, float)
    assert isinstance(r._low, float)
    assert isinstance(r._high, float)
