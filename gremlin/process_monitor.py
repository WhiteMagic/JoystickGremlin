# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Cross-platform process monitoring.

The OS-specific queries are delegated to the platform backend selected at
import time; the QObject machinery (thread, signal) is shared by all platforms.
"""

from __future__ import annotations

import sys
import time
import threading

from PySide6 import QtCore

if sys.platform == "win32":
    from gremlin.platform.windows.process_monitor import ProcessBackend
elif sys.platform.startswith("linux"):
    from gremlin.platform.linux.process_monitor import ProcessBackend
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")

_process_backend = ProcessBackend()


class ProcessMonitor(QtCore.QObject):

    """Monitors the currently active window process."""

    process_changed = QtCore.Signal(str)

    def __init__(self) -> None:
        QtCore.QObject.__init__(self)
        self._current_path = ""
        self.running = False
        self._update_thread: threading.Thread | None = None

    def start(self) -> None:
        if not self.running:
            self.running = True
            self._update_thread = threading.Thread(target=self._update)
            self._update_thread.start()

    def stop(self) -> None:
        self.running = False
        if self._update_thread is not None:
            self._update_thread.join()

    def _update(self) -> None:
        while self.running:
            path = _process_backend.get_active_process_path()
            if path is not None and path != self._current_path:
                self._current_path = path
                self.process_changed.emit(self._current_path)
            time.sleep(1.0)

    @property
    def current_path(self) -> str:
        return self._current_path


def list_current_processes() -> list[str]:
    """Returns a sorted list of executable paths of currently running processes."""
    return _process_backend.list_process_paths()
