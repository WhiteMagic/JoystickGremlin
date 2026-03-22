# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Windows vjoy backend — wraps vJoyInterface.dll via ctypes."""

from __future__ import annotations

import ctypes
import os
import sys

from gremlin.error import GremlinError
from vjoy.platform.base.backend import AbstractVJoyBackend


class WindowsVJoyBackend(AbstractVJoyBackend):
    """Wraps vJoyInterface.dll via ctypes for Windows."""

    def __init__(self) -> None:
        self._dll = self._load_dll()
        self._configure(self._dll)

    # ------------------------------------------------------------------
    # DLL loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_dll() -> ctypes.CDLL:
        dev_path = os.path.join(os.path.dirname(__file__), "..", "..", "vJoyInterface.dll")
        if os.path.isfile("vJoyInterface.dll"):
            dll_path = "vJoyInterface.dll"
        elif "_MEIPASS" in sys.__dict__:
            dll_path = os.path.join(sys._MEIPASS, "vJoyInterface.dll")  # type: ignore[attr-defined]
        elif os.path.isfile(dev_path):
            dll_path = dev_path
        else:
            raise GremlinError("Unable to locate vjoy dll")
        return ctypes.cdll.LoadLibrary(dll_path)

    @staticmethod
    def _configure(dll: ctypes.CDLL) -> None:
        """Set argtypes / restype for every DLL function."""
        # General vJoy information
        dll.GetvJoyVersion.argtypes = []
        dll.GetvJoyVersion.restype  = ctypes.c_short

        dll.vJoyEnabled.argtypes = []
        dll.vJoyEnabled.restype  = ctypes.c_bool

        dll.GetvJoyProductString.argtypes = []
        dll.GetvJoyProductString.restype  = ctypes.c_wchar_p

        dll.GetvJoyManufacturerString.argtypes = []
        dll.GetvJoyManufacturerString.restype  = ctypes.c_wchar_p

        dll.GetvJoySerialNumberString.argtypes = []
        dll.GetvJoySerialNumberString.restype  = ctypes.c_wchar_p

        # Device properties
        dll.GetVJDButtonNumber.argtypes = [ctypes.c_uint]
        dll.GetVJDButtonNumber.restype  = ctypes.c_int

        dll.GetVJDDiscPovNumber.argtypes = [ctypes.c_uint]
        dll.GetVJDDiscPovNumber.restype  = ctypes.c_int

        dll.GetVJDContPovNumber.argtypes = [ctypes.c_uint]
        dll.GetVJDContPovNumber.restype  = ctypes.c_int

        # API claims bool but is actually int — see upstream bug report
        dll.GetVJDAxisExist.argtypes = [ctypes.c_uint, ctypes.c_uint]
        dll.GetVJDAxisExist.restype  = ctypes.c_int

        dll.GetVJDAxisMax.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
        dll.GetVJDAxisMax.restype  = ctypes.c_bool

        dll.GetVJDAxisMin.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
        dll.GetVJDAxisMin.restype  = ctypes.c_bool

        # Device management
        dll.GetOwnerPid.argtypes = [ctypes.c_uint]
        dll.GetOwnerPid.restype  = ctypes.c_int

        dll.AcquireVJD.argtypes = [ctypes.c_uint]
        dll.AcquireVJD.restype  = ctypes.c_bool

        dll.RelinquishVJD.argtypes = [ctypes.c_uint]
        dll.RelinquishVJD.restype  = None

        dll.UpdateVJD.argtypes = [ctypes.c_uint, ctypes.c_void_p]
        dll.UpdateVJD.restype  = ctypes.c_bool

        dll.GetVJDStatus.argtypes = [ctypes.c_uint]
        dll.GetVJDStatus.restype  = ctypes.c_int

        # Reset functions
        dll.ResetVJD.argtypes = [ctypes.c_uint]
        dll.ResetVJD.restype  = ctypes.c_bool

        dll.ResetAll.argtypes = []
        dll.ResetAll.restype  = None

        dll.ResetButtons.argtypes = [ctypes.c_uint]
        dll.ResetButtons.restype  = ctypes.c_bool

        dll.ResetPovs.argtypes = [ctypes.c_uint]
        dll.ResetPovs.restype  = ctypes.c_bool

        # Set values
        dll.SetAxis.argtypes = [ctypes.c_long, ctypes.c_uint, ctypes.c_uint]
        dll.SetAxis.restype  = ctypes.c_bool

        dll.SetBtn.argtypes = [ctypes.c_bool, ctypes.c_uint, ctypes.c_ubyte]
        dll.SetBtn.restype  = ctypes.c_bool

        dll.SetDiscPov.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_ubyte]
        dll.SetDiscPov.restype  = ctypes.c_bool

        dll.SetContPov.argtypes = [ctypes.c_ulong, ctypes.c_uint, ctypes.c_ubyte]
        dll.SetContPov.restype  = ctypes.c_bool

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — driver info
    # ------------------------------------------------------------------

    def vjoy_enabled(self) -> bool:
        return self._dll.vJoyEnabled()

    def get_version(self) -> int:
        return self._dll.GetvJoyVersion()

    def get_product_string(self) -> str:
        return self._dll.GetvJoyProductString()

    def get_manufacturer_string(self) -> str:
        return self._dll.GetvJoyManufacturerString()

    def get_serial_number_string(self) -> str:
        return self._dll.GetvJoySerialNumberString()

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — device status
    # ------------------------------------------------------------------

    def get_vjd_status(self, vjoy_id: int) -> int:
        return self._dll.GetVJDStatus(vjoy_id)

    def get_owner_pid(self, vjoy_id: int) -> int:
        return self._dll.GetOwnerPid(vjoy_id)

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — device acquisition
    # ------------------------------------------------------------------

    def acquire_vjd(self, vjoy_id: int) -> bool:
        return self._dll.AcquireVJD(vjoy_id)

    def relinquish_vjd(self, vjoy_id: int) -> None:
        self._dll.RelinquishVJD(vjoy_id)

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — device capabilities
    # ------------------------------------------------------------------

    def get_vjd_button_number(self, vjoy_id: int) -> int:
        return self._dll.GetVJDButtonNumber(vjoy_id)

    def get_vjd_disc_pov_number(self, vjoy_id: int) -> int:
        return self._dll.GetVJDDiscPovNumber(vjoy_id)

    def get_vjd_cont_pov_number(self, vjoy_id: int) -> int:
        return self._dll.GetVJDContPovNumber(vjoy_id)

    def get_vjd_axis_exist(self, vjoy_id: int, axis_id: int) -> int:
        return self._dll.GetVJDAxisExist(vjoy_id, axis_id)

    def get_vjd_axis_max(self, vjoy_id: int, axis_id: int) -> int:
        tmp = ctypes.c_long()
        self._dll.GetVJDAxisMax(vjoy_id, axis_id, ctypes.byref(tmp))
        return tmp.value

    def get_vjd_axis_min(self, vjoy_id: int, axis_id: int) -> int:
        tmp = ctypes.c_long()
        self._dll.GetVJDAxisMin(vjoy_id, axis_id, ctypes.byref(tmp))
        return tmp.value

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — reset
    # ------------------------------------------------------------------

    def reset_vjd(self, vjoy_id: int) -> bool:
        return self._dll.ResetVJD(vjoy_id)

    def reset_all(self) -> None:
        self._dll.ResetAll()

    def reset_buttons(self, vjoy_id: int) -> bool:
        return self._dll.ResetButtons(vjoy_id)

    def reset_povs(self, vjoy_id: int) -> bool:
        return self._dll.ResetPovs(vjoy_id)

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — set values
    # ------------------------------------------------------------------

    def set_axis(self, value: int, vjoy_id: int, axis_id: int) -> bool:
        return self._dll.SetAxis(value, vjoy_id, axis_id)

    def set_btn(self, pressed: bool, vjoy_id: int, btn_id: int) -> bool:
        return self._dll.SetBtn(pressed, vjoy_id, btn_id)

    def set_disc_pov(self, direction: int, vjoy_id: int, hat_id: int) -> bool:
        return self._dll.SetDiscPov(direction, vjoy_id, hat_id)

    def set_cont_pov(self, degrees: int, vjoy_id: int, hat_id: int) -> bool:
        return self._dll.SetContPov(degrees, vjoy_id, hat_id)
