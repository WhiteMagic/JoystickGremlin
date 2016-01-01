# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ctypes
import ctypes.wintypes
import os
import time
import threading

from PyQt5 import QtCore

import win32gui
import win32process


class ProcessMonitor(QtCore.QObject):

    """Monitors the currently active window process.

    This class continuously monitors the active window and whenever
    it changes the path to the executable is retrieved and signaled
    to the rest of the system using Qt's signal / slot mechanism.
    """

    # Signal emitted when the active window changes
    process_changed = QtCore.pyqtSignal(str)

    # Definition of the flags for limited information queries
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    # kernel32.dll library handle
    kernel32 = ctypes.windll.kernel32

    def __init__(self):
        """Creates a new instance."""
        QtCore.QObject.__init__(self)
        self._buffer = ctypes.create_string_buffer(1024)
        self._buffer_size = ctypes.wintypes.DWORD(1024)
        self._current_path = ""
        self._current_pid = -1
        self.running = False
        self._update_thread = None

    def start(self):
        """Starts monitoring the current process."""
        if not self.running:
            self.running = True
            self._update_thread = threading.Thread(
                target=self._update
            )
            self._update_thread.start()

    def stop(self):
        """Stops monitorung the current process."""
        self.running = False
        if self._update_thread is not None:
            self._update_thread.join()

    def _update(self):
        """Monitors the active process for changes."""
        while self.running:
            _, pid = win32process.GetWindowThreadProcessId(
                win32gui.GetForegroundWindow()
            )

            if pid != self._current_pid:
                self._current_pid = pid
                handle = ProcessMonitor.kernel32.OpenProcess(
                    ProcessMonitor.PROCESS_QUERY_LIMITED_INFORMATION,
                    False,
                    pid
                )

                self._buffer_size = ctypes.wintypes.DWORD(1024)
                ProcessMonitor.kernel32.QueryFullProcessImageNameA(
                    handle,
                    0,
                    self._buffer,
                    ctypes.byref(self._buffer_size)
                )
                ProcessMonitor.kernel32.CloseHandle(handle)

                self._current_path = os.path.normpath(
                    str(self._buffer.value)[2:-1]
                ).replace("\\", "/")
                self.process_changed.emit(self.current_path)

            time.sleep(1.0)

    @property
    def current_path(self):
        """Returns the path to the currently active executable.

        :return path to the currently active executable
        """
        return self._current_path