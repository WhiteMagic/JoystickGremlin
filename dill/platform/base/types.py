# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Portable ctypes structure definitions shared across all DILL backends.

These types mirror the C structures exposed by the Windows dill.dll.
On Linux they are used by the evdev backend to produce compatible objects
that the rest of the codebase (GUID, DeviceSummary, InputEvent …) can
consume without any platform-specific branching.
"""

from __future__ import annotations

import ctypes
import sys

if sys.platform == "win32":
    import ctypes.wintypes as ctwt
else:
    class ctwt:  # type: ignore[no-redef]
        """Portable substitutes for Windows-only ctypes.wintypes constants."""

        LONG     = ctypes.c_int32
        DWORD    = ctypes.c_uint32
        MAX_PATH = 260


class _GUID(ctypes.Structure):
    """Mirrors the Windows GUID / DIDEVICEINSTANCE device identifier."""

    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_uint8 * 8),
    ]


class _AxisMap(ctypes.Structure):
    """Maps a sequential axis index to its DirectInput axis descriptor."""

    _fields_ = [
        ("linear_index", ctwt.DWORD),
        ("axis_index",   ctwt.DWORD),
    ]


class _DeviceSummary(ctypes.Structure):
    """Static description of a joystick device (mirrors C DeviceSummary)."""

    _fields_ = [
        ("device_guid",  _GUID),
        ("vendor_id",    ctwt.DWORD),
        ("product_id",   ctwt.DWORD),
        ("joystick_id",  ctwt.DWORD),
        ("name",         ctypes.c_char * ctwt.MAX_PATH),
        ("axis_count",   ctwt.DWORD),
        ("button_count", ctwt.DWORD),
        ("hat_count",    ctwt.DWORD),
        ("axis_map",     _AxisMap * 8),
    ]


class _JoystickInputData(ctypes.Structure):
    """A single joystick input event (mirrors C JoystickInputData)."""

    _fields_ = [
        ("device_guid", _GUID),
        ("input_type",  ctypes.c_uint8),
        ("input_index", ctypes.c_uint8),
        ("value",       ctwt.LONG),
    ]


# ctypes callback types used by the Windows DLL (and reused by Linux backend
# so the rest of the code never needs a platform branch).
C_EVENT_CALLBACK        = ctypes.CFUNCTYPE(None, _JoystickInputData)
C_DEVICE_CHANGE_CALLBACK = ctypes.CFUNCTYPE(None, _DeviceSummary, ctypes.c_uint8)
