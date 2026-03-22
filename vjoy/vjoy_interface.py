# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

import enum
import sys

from gremlin.error import GremlinError
from vjoy.platform.base.backend import AbstractVJoyBackend


class VJoyState(enum.Enum):

    """Enumeration of the possible VJoy device states."""

    Owned = 0       # The device is owned by the current application
    Free = 1        # The device is not owned by any application
    Bust = 2        # The device is owned by another application
    Missing = 3     # The device is not present
    Unknown = 4     # Unknown type of error


# ---------------------------------------------------------------------------
# Platform backend selection
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    from vjoy.platform.windows.backend import WindowsVJoyBackend
    _vjoy_backend: AbstractVJoyBackend = WindowsVJoyBackend()
elif sys.platform.startswith("linux"):
    from vjoy.platform.linux.backend import LinuxVJoyBackend
    _vjoy_backend: AbstractVJoyBackend = LinuxVJoyBackend()
else:
    raise GremlinError(f"Unsupported platform: {sys.platform}")


# ---------------------------------------------------------------------------
# Facade — preserves the VJoyInterface.Xxx() call sites in vjoy.py unchanged
# ---------------------------------------------------------------------------

class VJoyInterface:

    """Thin facade that delegates all vJoy operations to the platform backend."""

    @staticmethod
    def vJoyEnabled() -> bool:
        return _vjoy_backend.vjoy_enabled()

    @staticmethod
    def GetvJoyVersion() -> int:
        return _vjoy_backend.get_version()

    @staticmethod
    def GetvJoyProductString() -> str:
        return _vjoy_backend.get_product_string()

    @staticmethod
    def GetvJoyManufacturerString() -> str:
        return _vjoy_backend.get_manufacturer_string()

    @staticmethod
    def GetvJoySerialNumberString() -> str:
        return _vjoy_backend.get_serial_number_string()

    @staticmethod
    def GetVJDStatus(vjoy_id: int) -> int:
        return _vjoy_backend.get_vjd_status(vjoy_id)

    @staticmethod
    def GetOwnerPid(vjoy_id: int) -> int:
        return _vjoy_backend.get_owner_pid(vjoy_id)

    @staticmethod
    def AcquireVJD(vjoy_id: int) -> bool:
        return _vjoy_backend.acquire_vjd(vjoy_id)

    @staticmethod
    def RelinquishVJD(vjoy_id: int) -> None:
        _vjoy_backend.relinquish_vjd(vjoy_id)

    @staticmethod
    def GetVJDButtonNumber(vjoy_id: int) -> int:
        return _vjoy_backend.get_vjd_button_number(vjoy_id)

    @staticmethod
    def GetVJDDiscPovNumber(vjoy_id: int) -> int:
        return _vjoy_backend.get_vjd_disc_pov_number(vjoy_id)

    @staticmethod
    def GetVJDContPovNumber(vjoy_id: int) -> int:
        return _vjoy_backend.get_vjd_cont_pov_number(vjoy_id)

    @staticmethod
    def GetVJDAxisExist(vjoy_id: int, axis_id: int) -> int:
        return _vjoy_backend.get_vjd_axis_exist(vjoy_id, axis_id)

    @staticmethod
    def GetVJDAxisMax(vjoy_id: int, axis_id: int) -> int:
        return _vjoy_backend.get_vjd_axis_max(vjoy_id, axis_id)

    @staticmethod
    def GetVJDAxisMin(vjoy_id: int, axis_id: int) -> int:
        return _vjoy_backend.get_vjd_axis_min(vjoy_id, axis_id)

    @staticmethod
    def ResetVJD(vjoy_id: int) -> bool:
        return _vjoy_backend.reset_vjd(vjoy_id)

    @staticmethod
    def ResetAll() -> None:
        _vjoy_backend.reset_all()

    @staticmethod
    def ResetButtons(vjoy_id: int) -> bool:
        return _vjoy_backend.reset_buttons(vjoy_id)

    @staticmethod
    def ResetPovs(vjoy_id: int) -> bool:
        return _vjoy_backend.reset_povs(vjoy_id)

    @staticmethod
    def SetAxis(value: int, vjoy_id: int, axis_id: int) -> bool:
        return _vjoy_backend.set_axis(value, vjoy_id, axis_id)

    @staticmethod
    def SetBtn(pressed: bool, vjoy_id: int, btn_id: int) -> bool:
        return _vjoy_backend.set_btn(pressed, vjoy_id, btn_id)

    @staticmethod
    def SetDiscPov(direction: int, vjoy_id: int, hat_id: int) -> bool:
        return _vjoy_backend.set_disc_pov(direction, vjoy_id, hat_id)

    @staticmethod
    def SetContPov(degrees: int, vjoy_id: int, hat_id: int) -> bool:
        return _vjoy_backend.set_cont_pov(degrees, vjoy_id, hat_id)
