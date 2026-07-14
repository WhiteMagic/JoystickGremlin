# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import threading
import time

import win32gui
import win32process
from PySide6 import QtCore


class ProcessMonitor(QtCore.QObject):
    """Monitors the currently active window process.

    This class continuously monitors the active window and whenever
    it changes the path to the executable is retrieved and signaled
    to the rest of the system using Qt's signal / slot mechanism.
    """

    # Signal emitted when the active window changes
    process_changed = QtCore.Signal(str)

    # Definition of the flags for limited information queries
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    # kernel32.dll library handle
    kernel32 = ctypes.windll.kernel32

    def __init__(self) -> None:
        """Creates a new instance."""
        QtCore.QObject.__init__(self)
        self._buffer = ctypes.create_string_buffer(1024)
        self._buffer_size = ctypes.wintypes.DWORD(1024)
        self._current_path = ""
        self._current_pid = -1
        self.running = False
        self._update_thread = None

    def start(self) -> None:
        """Starts monitoring the current process."""
        if not self.running:
            self.running = True
            self._update_thread = threading.Thread(target=self._update)
            self._update_thread.start()

    def stop(self) -> None:
        """Stops monitoring the current process."""
        self.running = False
        if self._update_thread is not None:
            self._update_thread.join()

    def _update(self) -> None:
        """Monitors the active process for changes."""
        while self.running:
            _, pid = win32process.GetWindowThreadProcessId(
                win32gui.GetForegroundWindow()
            )

            if pid != self._current_pid:
                self._current_pid = pid
                handle = ProcessMonitor.kernel32.OpenProcess(
                    ProcessMonitor.PROCESS_QUERY_LIMITED_INFORMATION, False, pid
                )

                self._buffer_size = ctypes.wintypes.DWORD(1024)
                ProcessMonitor.kernel32.QueryFullProcessImageNameA(
                    handle, 0, self._buffer, ctypes.byref(self._buffer_size)
                )
                ProcessMonitor.kernel32.CloseHandle(handle)

                self._current_path = os.path.normpath(
                    str(self._buffer.value)[2:-1]
                ).replace("\\", "/")
                self.process_changed.emit(self.current_path)

            time.sleep(1.0)

    @property
    def current_path(self) -> str:
        """Returns the path to the currently active executable.

        Returns:
            The path to the currently active executable
        """
        return self._current_path


def list_current_processes() -> list[str]:
    """Returns a list of executable paths to currently active processes.

    Returns:
       The list of active process executable paths
    """
    from win32com.client import GetObject

    wmi = GetObject("winmgmts:")
    processes = wmi.InstancesOf("Win32_Process")
    process_list = []
    for entry in processes:
        executable = entry.Properties_("ExecutablePath").Value
        if executable is not None:
            process_list.append(os.path.normpath(executable).replace("\\", "/"))
    return sorted(set(process_list))
