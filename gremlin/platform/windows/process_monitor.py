# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Windows implementation of the process-detection backend."""

import ctypes
import ctypes.wintypes
import os

import win32gui
import win32process

from gremlin.platform.base import AbstractProcessBackend


class ProcessBackend(AbstractProcessBackend):

    """Windows implementation using win32gui/win32process and kernel32."""

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    kernel32 = ctypes.windll.kernel32

    def __init__(self) -> None:
        self._buffer = ctypes.create_string_buffer(1024)
        self._buffer_size = ctypes.wintypes.DWORD(1024)
        self._cached_pid: int = -1
        self._cached_path: str = ""

    def get_active_process_path(self) -> str | None:
        """Return the path of the foreground process.

        The expensive kernel32 lookup is skipped when the foreground PID
        has not changed since the last call (cached result is returned instead).
        """
        _, pid = win32process.GetWindowThreadProcessId(
            win32gui.GetForegroundWindow()
        )

        if pid == self._cached_pid:
            return self._cached_path if self._cached_path else None

        self._cached_pid = pid
        handle = ProcessBackend.kernel32.OpenProcess(
            ProcessBackend.PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid
        )

        self._buffer_size = ctypes.wintypes.DWORD(1024)
        ProcessBackend.kernel32.QueryFullProcessImageNameA(
            handle,
            0,
            self._buffer,
            ctypes.byref(self._buffer_size)
        )
        ProcessBackend.kernel32.CloseHandle(handle)

        raw = str(self._buffer.value)[2:-1]
        if not raw:
            self._cached_path = ""
            return None
        self._cached_path = os.path.normpath(raw).replace("\\", "/")
        return self._cached_path

    def list_process_paths(self) -> list[str]:
        """Return a sorted, deduplicated list of all running executable paths."""
        from win32com.client import GetObject
        wmi = GetObject('winmgmts:')
        processes = wmi.InstancesOf("Win32_Process")
        process_list = []
        for entry in processes:
            executable = entry.Properties_("ExecutablePath").Value
            if executable is not None:
                process_list.append(os.path.normpath(executable).replace("\\", "/"))
        return sorted(set(process_list))
