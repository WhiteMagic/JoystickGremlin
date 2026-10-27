# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

from unittest import mock

from PySide6 import QtCore

from gremlin import event_handler
from gremlin.ui.util import InputListenerModel


def _keyboard_receivers() -> int:
    return event_handler.EventListener().receivers(
        QtCore.SIGNAL("keyboard_event(PyObject)")
    )


def test_disable_disconnects_listeners() -> None:
    baseline = _keyboard_receivers()
    listener = InputListenerModel()

    listener.enabled = True
    assert _keyboard_receivers() == baseline + 1

    listener.enabled = False
    assert _keyboard_receivers() == baseline


def test_disable_stops_abort_timer() -> None:
    listener = InputListenerModel()
    listener._abort_timer = mock.create_autospec(QtCore.QTimer, instance=True)
    listener.enabled = True

    listener.enabled = False

    listener._abort_timer.stop.assert_called_once()
