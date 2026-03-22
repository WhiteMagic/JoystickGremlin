# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Abstract base class that all DILL platform backends must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from dill.platform.base.types import _GUID, _DeviceSummary


class AbstractDillBackend(ABC):
    """Contract for DILL platform backends.

    Each backend is responsible for:
    - enumerating connected joystick devices,
    - delivering input events and device-change notifications via callbacks,
    - answering synchronous state queries (axis / button / hat).

    The return types of get_device_information_by_* are _DeviceSummary ctypes
    instances (from dill.platform.base.types).  Callers (DILL class) wrap them
    in the higher-level DeviceSummary Python class.
    """

    @abstractmethod
    def init(self) -> None:
        """Start the backend (enumerate devices, launch event loops)."""

    @abstractmethod
    def set_input_event_callback(self, callback: Callable) -> None:
        """Register *callback* to be called on every joystick input event.

        On Windows the callback is a ctypes CFUNCTYPE wrapper; on Linux it is
        a plain Python callable — backends handle the difference internally.
        """

    @abstractmethod
    def set_device_change_callback(self, callback: Callable) -> None:
        """Register *callback* to be called when a device is added/removed."""

    @abstractmethod
    def get_device_count(self) -> int:
        """Return the number of currently connected joystick devices."""

    @abstractmethod
    def get_device_information_by_index(self, index: int) -> _DeviceSummary:
        """Return a _DeviceSummary for the device at *index*."""

    @abstractmethod
    def get_device_information_by_guid(self, guid: _GUID) -> _DeviceSummary:
        """Return a _DeviceSummary for the device identified by *guid*."""

    @abstractmethod
    def get_axis(self, guid: _GUID, index: int) -> int:
        """Return the current axis value in DirectInput range [-32768, 32767]."""

    @abstractmethod
    def get_button(self, guid: _GUID, index: int) -> bool:
        """Return True if the 1-based *index* button is currently pressed."""

    @abstractmethod
    def get_hat(self, guid: _GUID, index: int) -> int:
        """Return the hat value (DirectInput hundredths-of-degrees, -1 = centred)."""

    @abstractmethod
    def device_exists(self, guid: _GUID) -> bool:
        """Return True if the device identified by *guid* is connected."""
