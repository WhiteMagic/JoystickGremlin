# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pytest

from gremlin import fsm


def test_simple() -> None:
    def f1() -> int:
        return 1

    def f2() -> int:
        return 2

    def f3() -> int:
        return 3

    states = ["1", "2", "3"]
    actions = ["switch"]
    transitions = {
        ("1", "switch"): fsm.Transition([f1], "2"),
        ("2", "switch"): fsm.Transition([f2], "3"),
        ("3", "switch"): fsm.Transition([f3], "1"),
    }

    sm = fsm.FiniteStateMachine("1", states, actions, transitions)

    assert sm.current_state == "1"
    assert sm.perform("switch")[0] == 1
    assert sm.current_state == "2"
    assert sm.perform("switch")[0] == 2
    assert sm.current_state == "3"
    assert sm.perform("switch")[0] == 3
    assert sm.current_state == "1"


def test_multi() -> None:
    # 1 - 2 - 4
    #   \   /
    #     3

    def add(a: int, b: int) -> int:
        return a + b

    def sub(a: int, b: int) -> int:
        return a - b

    def mul(a: int, b: int) -> int:
        return a * b

    states = ["1", "2", "3", "4"]
    actions = ["add", "mul", "sub"]
    transitions = {
        ("1", "add"): fsm.Transition([add, mul], "2"),
        ("1", "sub"): fsm.Transition([sub, mul], "3"),
        ("3", "add"): fsm.Transition([add], "4"),
        ("2", "add"): fsm.Transition([add], "4"),
        ("4", "sub"): fsm.Transition([sub], "1"),
    }

    sm = fsm.FiniteStateMachine("1", states, actions, transitions)

    assert sm.current_state == "1"
    assert sm.perform("add", 2, 3) == [5, 6]
    assert sm.current_state == "2"
    assert sm.perform("add", 5, 1) == [6]
    assert sm.current_state == "4"
    assert sm.perform("sub", 5, 5) == [0]
    assert sm.current_state == "1"
    assert sm.perform("sub", 10, 3) == [7, 30]
    assert sm.current_state == "3"


def test_perform_invalid_transition_raises() -> None:
    states = ["1", "2"]
    actions = ["switch"]
    transitions = {
        ("1", "switch"): fsm.Transition([lambda: None], "2"),
    }

    sm = fsm.FiniteStateMachine("1", states, actions, transitions)

    assert sm.perform("switch") == [None]
    assert sm.current_state == "2"

    # No transition exists from state "2", so this raises and leaves the
    # state unchanged.
    with pytest.raises(AssertionError):
        sm.perform("switch")
    assert sm.current_state == "2"


def test_try_perform() -> None:
    states = ["1", "2"]
    actions = ["switch"]
    transitions = {
        ("1", "switch"): fsm.Transition([lambda: "ok"], "2"),
    }

    sm = fsm.FiniteStateMachine("1", states, actions, transitions)

    assert sm.try_perform("switch") == ["ok"]
    assert sm.current_state == "2"

    # No transition exists from state "2", try_perform reports this via
    # None instead of raising and leaves the state unchanged.
    assert sm.try_perform("switch") is None
    assert sm.current_state == "2"
