# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

from collections.abc import Iterator

import pytest

import gremlin.shared_state
from gremlin.config import Configuration
from gremlin.event_helpers import ModeChangeActions
from gremlin.mode_manager import (
    Mode,
    ModeManager,
)
from gremlin.profile import Profile


@pytest.fixture
def registry() -> Iterator[ModeChangeActions]:
    """Provides a mode change registry isolated from other tests.

    Both the registry and the mode manager are process wide singletons, so their state
    has to be dropped around every test.
    """
    gremlin.shared_state.current_profile = Profile()
    Configuration().set("global", "behavior", "refresh-axis-on-mode-change", False)

    manager = ModeManager()
    manager.reset()

    instance = ModeChangeActions()
    instance.reset()

    yield instance

    instance.reset()


def _switch_to(name: str) -> None:
    """Makes the named mode active, publishing the change."""
    ModeManager().switch_to(Mode(name, ModeManager().current.name))


def test_register_replaces_existing_entry(registry: ModeChangeActions) -> None:
    calls = []

    registry.register("key", lambda old, new: calls.append("first") or True)
    registry.register("key", lambda old, new: calls.append("second") or True)
    _switch_to("A")

    assert calls == ["second"]


def test_callback_removed_when_executed(registry: ModeChangeActions) -> None:
    calls = []

    registry.register("key", lambda old, new: calls.append(new.name) or True)
    _switch_to("A")
    _switch_to("B")

    assert calls == ["A"]


def test_callback_kept_when_not_executed(registry: ModeChangeActions) -> None:
    calls = []

    registry.register("key", lambda old, new: calls.append(new.name) or False)
    _switch_to("A")
    _switch_to("B")

    assert calls == ["A", "B"]


def test_unregister_removes_entry(registry: ModeChangeActions) -> None:
    calls = []

    registry.register("key", lambda old, new: calls.append(new.name) or False)
    registry.unregister("key")
    registry.unregister("never registered")
    _switch_to("A")

    assert calls == []


def test_reset_clears_registry(registry: ModeChangeActions) -> None:
    calls = []

    registry.register("first", lambda old, new: calls.append("first") or False)
    registry.register("second", lambda old, new: calls.append("second") or False)
    registry.reset()
    _switch_to("A")

    assert calls == []


def test_exception_in_callback_drops_callback(
    registry: ModeChangeActions,
) -> None:
    calls = []

    def raising_callback(old: Mode, new: Mode) -> bool:
        calls.append("raising")
        raise RuntimeError("callback failure")

    registry.register("raising", raising_callback)
    registry.register("sane", lambda old, new: calls.append("sane") or False)
    _switch_to("A")
    _switch_to("B")

    assert calls == ["raising", "sane", "sane"]


def test_callbacks_receive_both_modes(registry: ModeChangeActions) -> None:
    calls = []

    registry.register("key", lambda old, new: calls.append((old.name, new.name)))
    _switch_to("A")
    _switch_to("B")

    assert calls == [("Default", "A"), ("A", "B")]


def test_registry_may_be_modified_while_firing(registry: ModeChangeActions) -> None:
    calls = []

    def adding_callback(old: Mode, new: Mode) -> bool:
        calls.append("adding")
        registry.register("added", lambda old, new: calls.append("added") or False)
        registry.unregister("doomed")
        return True

    registry.register("adding", adding_callback)
    registry.register("doomed", lambda old, new: calls.append("doomed") or False)
    _switch_to("A")

    # The entry added during the pass only runs on the next mode change, the one
    # removed during it never runs.
    assert calls == ["adding"]

    _switch_to("B")
    assert calls == ["adding", "added"]
