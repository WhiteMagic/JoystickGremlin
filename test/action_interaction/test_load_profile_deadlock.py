# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import threading
import time
import uuid

import pytest
import pytestqt.qtbot
from PySide6 import QtCore

from action_plugins import load_profile
from action_plugins.double_tap import (
    DoubleTapData,
    DoubleTapFunctor,
)
from gremlin.base_classes import (
    Value,
    teardown_functor_tree,
)
from gremlin.types import (
    Event,
    InputType,
)


class FakeBackend(QtCore.QObject):
    """Tears the functor down on a profile load, mirroring whatCodeRunner.stop does."""

    def __init__(self, functor: DoubleTapFunctor) -> None:
        super().__init__()
        self._functor = functor
        self.loaded = False

    @QtCore.Slot(str)
    def loadProfile(self, fpath: str) -> None:
        # Lets the Double Tap timer expire and wait on the FSM lock.
        time.sleep(self._functor.data.threshold * 3)
        teardown_functor_tree(self._functor)
        self.loaded = True

    @QtCore.Slot(str)
    def loadProfileAndActivate(self, fpath: str) -> None:
        self.loadProfile(fpath)

    def activate_gremlin(self, activate: bool) -> None:
        pass


def test_load_profile_in_double_tap_does_not_deadlock(
    qtbot: pytestqt.qtbot.QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = DoubleTapData()
    data.threshold = 0.1
    data.double_actions = [load_profile.LoadProfileData()]
    functor = DoubleTapFunctor(data)
    fake_backend = FakeBackend(functor)
    monkeypatch.setattr(load_profile.backend, "Backend", lambda: fake_backend)

    def double_tap() -> None:
        for pressed in (True, False, True):
            event = Event(
                InputType.JoystickButton,
                1,
                uuid.UUID(int=0),
                "Default",
                is_pressed=pressed,
            )
            functor(event, Value(pressed))

    # Daemon so a deadlocked timer thread, which inherits it, can't block exit.
    worker = threading.Thread(target=double_tap, daemon=True)
    worker.start()
    worker.join(2.0)

    assert not worker.is_alive(), "Load Profile inside a Double Tap deadlocked"
    qtbot.waitUntil(lambda: fake_backend.loaded, timeout=2000)
