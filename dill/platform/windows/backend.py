# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Windows DILL backend — wraps dill.dll via ctypes."""

from __future__ import annotations

import ctypes
import os
import sys
from typing import Callable

from dill.platform.base.backend import AbstractDillBackend
from dill.platform.base.types import (
    _GUID,
    _DeviceSummary,
    _JoystickInputData,
    C_EVENT_CALLBACK,
    C_DEVICE_CHANGE_CALLBACK,
    ctwt,
)


class WindowsDillBackend(AbstractDillBackend):
    """Delegates every call to the native dill.dll DirectInput wrapper."""

    def __init__(self) -> None:
        self._dll = self._load_dll()
        self._initialized = False
        # ctypes callback objects must be kept alive as long as the DLL uses
        # them — storing them here prevents premature garbage collection.
        self._event_fn = None
        self._device_fn = None

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_dll() -> ctypes.CDLL:
        """Locate dill.dll and load it, configuring all exported functions."""
        dev_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "dill.dll")
        )
        if os.path.isfile("dill.dll"):
            dll_path = "dill.dll"
        elif "_MEIPASS" in sys.__dict__:
            dll_path = os.path.join(sys._MEIPASS, "dill.dll")
        elif os.path.isfile(dev_path):
            dll_path = dev_path
        else:
            raise RuntimeError("Unable to locate dill.dll library")

        dll = ctypes.cdll.LoadLibrary(dll_path)
        WindowsDillBackend._configure(dll)
        return dll

    @staticmethod
    def _configure(dll: ctypes.CDLL) -> None:
        """Set argtypes / restype for every exported function."""
        dll.init.argtypes = []
        dll.init.restype = None

        dll.set_input_event_callback.argtypes = [C_EVENT_CALLBACK]
        dll.set_input_event_callback.restype = None

        dll.set_device_change_callback.argtypes = [C_DEVICE_CHANGE_CALLBACK]
        dll.set_device_change_callback.restype = None

        dll.get_device_information_by_index.argtypes = [ctypes.c_uint]
        dll.get_device_information_by_index.restype = _DeviceSummary

        dll.get_device_information_by_guid.argtypes = [_GUID]
        dll.get_device_information_by_guid.restype = _DeviceSummary

        dll.get_device_count.argtypes = []
        dll.get_device_count.restype = ctypes.c_uint

        dll.device_exists.argtypes = [_GUID]
        dll.device_exists.restype = ctypes.c_bool

        dll.get_axis.argtypes = [_GUID, ctwt.DWORD]
        dll.get_axis.restype = ctwt.LONG

        dll.get_button.argtypes = [_GUID, ctwt.DWORD]
        dll.get_button.restype = ctypes.c_bool

        dll.get_hat.argtypes = [_GUID, ctwt.DWORD]
        dll.get_hat.restype = ctwt.LONG

    # ------------------------------------------------------------------
    # AbstractDillBackend implementation
    # ------------------------------------------------------------------

    def init(self) -> None:
        if not self._initialized:
            self._dll.init()
            self._initialized = True

    def set_input_event_callback(self, callback: Callable) -> None:
        self._event_fn = C_EVENT_CALLBACK(callback)
        self._dll.set_input_event_callback(self._event_fn)

    def set_device_change_callback(self, callback: Callable) -> None:
        self._device_fn = C_DEVICE_CHANGE_CALLBACK(callback)
        self._dll.set_device_change_callback(self._device_fn)

    def get_device_count(self) -> int:
        return self._dll.get_device_count()

    def get_device_information_by_index(self, index: int) -> _DeviceSummary:
        return self._dll.get_device_information_by_index(index)

    def get_device_information_by_guid(self, guid: _GUID) -> _DeviceSummary:
        return self._dll.get_device_information_by_guid(guid)

    def get_axis(self, guid: _GUID, index: int) -> int:
        return self._dll.get_axis(guid, index)

    def get_button(self, guid: _GUID, index: int) -> bool:
        return self._dll.get_button(guid, index)

    def get_hat(self, guid: _GUID, index: int) -> int:
        return self._dll.get_hat(guid, index)

    def device_exists(self, guid: _GUID) -> bool:
        return self._dll.device_exists(guid)
