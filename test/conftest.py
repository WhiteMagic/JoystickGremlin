# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib
import tempfile

# Mock before any imports happen
from unittest.mock import Mock

import pytest

import gremlin.util

gremlin.util.userprofile_path = Mock(return_value=tempfile.mkdtemp())

import gremlin.event_handler
import gremlin.ui.backend
import joystick_gremlin


@pytest.fixture(scope="session")
def qapp_cls() -> type[joystick_gremlin.JoystickGremlinApp]:
    return joystick_gremlin.JoystickGremlinApp


@pytest.fixture(scope="session", autouse=True)
def _terminate_event_listener_and_monitor(
    request: pytest.FixtureRequest,
) -> None:
    """Terminates session-wide singletons once, after the entire run."""

    # EventListener/Backend set up their DILL callback and process-monitor
    # thread once per session with nothing to restart them; must not
    # terminate them mid-session, only here. Skip ones this session never
    # created; Backend cannot be constructed without an engine.
    def _finalize() -> None:
        if gremlin.event_handler.EventListener.instance is not None:
            gremlin.event_handler.EventListener.instance.terminate()
        if gremlin.ui.backend.Backend.instance is not None:
            gremlin.ui.backend.Backend.instance.process_monitor.stop()

    request.addfinalizer(_finalize)


@pytest.fixture(scope="session")
def test_root_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent
