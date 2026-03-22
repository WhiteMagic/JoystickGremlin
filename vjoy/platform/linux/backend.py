# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Linux vjoy backend — evdev.UInput-based virtual joystick output."""

from __future__ import annotations

import logging
import os
import threading

import evdev
from evdev import AbsInfo, ecodes

from vjoy.platform.base.backend import AbstractVJoyBackend

_log = logging.getLogger("system")

# ---------------------------------------------------------------------------
# VJoyState raw values (mirrors VJoyState enum in vjoy_interface.py)
# Duplicated here to avoid a circular import (vjoy_interface imports us).
# ---------------------------------------------------------------------------

_STATE_FREE    = 1
_STATE_MISSING = 3

# ---------------------------------------------------------------------------
# Axis mapping: AxisCode HID usage (0x30-0x37) → evdev ABS code
# Matches the inverse of _ABS_TO_DI in dill/platform/linux/backend.py
# ---------------------------------------------------------------------------

_HID_TO_ABS: dict[int, int] = {
    0x30: ecodes.ABS_X,
    0x31: ecodes.ABS_Y,
    0x32: ecodes.ABS_Z,
    0x33: ecodes.ABS_RX,
    0x34: ecodes.ABS_RY,
    0x35: ecodes.ABS_RZ,
    0x36: ecodes.ABS_THROTTLE,
    0x37: ecodes.ABS_RUDDER,
}

_SUPPORTED_AXIS_IDS = frozenset(_HID_TO_ABS.keys())

# ---------------------------------------------------------------------------
# Hat mapping: DirectInput hundredths-of-degrees → (x, y) for ABS_HATnX/Y
# Inverse of _XY_TO_DI_HAT in dill/platform/linux/backend.py
# ---------------------------------------------------------------------------

_DI_HAT_TO_XY: dict[int, tuple[int, int]] = {
    -1:    ( 0,  0),   # center
     0:    ( 0, -1),   # N
     4500: ( 1, -1),   # NE
     9000: ( 1,  0),   # E
    13500: ( 1,  1),   # SE
    18000: ( 0,  1),   # S
    22500: (-1,  1),   # SW
    27000: (-1,  0),   # W
    31500: (-1, -1),   # NW
}

# Discrete POV direction → (x, y)  (0=N, 1=E, 2=S, 3=W, -1=center)
_DISC_TO_XY: dict[int, tuple[int, int]] = {
    -1: ( 0,  0),
     0: ( 0, -1),
     1: ( 1,  0),
     2: ( 0,  1),
     3: (-1,  0),
}

# Hat pairs (X code, Y code) indexed 0-3
_HAT_AXES = [
    (ecodes.ABS_HAT0X, ecodes.ABS_HAT0Y),
    (ecodes.ABS_HAT1X, ecodes.ABS_HAT1Y),
    (ecodes.ABS_HAT2X, ecodes.ABS_HAT2Y),
    (ecodes.ABS_HAT3X, ecodes.ABS_HAT3Y),
]

# Fixed capabilities per virtual device.
# Each vjoy device gets _BUTTON_BASE + vjoy_id buttons so that
# device_initialization can distinguish identical-capability devices via the
# (axis_count, button_count, hat_count) hash it uses for DILL/vjoy matching.
# Example: vjoy 1 → 33 buttons, vjoy 2 → 34, …
_VJOY_VENDOR  = 0x1234
_VJOY_PRODUCT = 0xBEAD
_BUTTON_BASE  = 32
_HAT_COUNT    = 4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _button_count(vjoy_id: int) -> int:
    """Return the number of buttons for *vjoy_id*.

    Each device gets _BUTTON_BASE + vjoy_id buttons so the
    (axis_count, button_count, hat_count) hash used by device_initialization
    is unique per device, allowing correct DILL/vjoy matching.
    """
    return _BUTTON_BASE + vjoy_id


def _make_uinput(vjoy_id: int) -> evdev.UInput:
    """Create and return a UInput virtual joystick device for *vjoy_id*."""
    axis_range = AbsInfo(value=0, min=-32768, max=32767, fuzz=0, flat=0, resolution=0)
    hat_range  = AbsInfo(value=0, min=-1,     max=1,     fuzz=0, flat=0, resolution=0)

    abs_capabilities = [
        (ecodes.ABS_X,        axis_range),
        (ecodes.ABS_Y,        axis_range),
        (ecodes.ABS_Z,        axis_range),
        (ecodes.ABS_RX,       axis_range),
        (ecodes.ABS_RY,       axis_range),
        (ecodes.ABS_RZ,       axis_range),
        (ecodes.ABS_THROTTLE, axis_range),
        (ecodes.ABS_RUDDER,   axis_range),
        (ecodes.ABS_HAT0X,    hat_range),
        (ecodes.ABS_HAT0Y,    hat_range),
        (ecodes.ABS_HAT1X,    hat_range),
        (ecodes.ABS_HAT1Y,    hat_range),
        (ecodes.ABS_HAT2X,    hat_range),
        (ecodes.ABS_HAT2Y,    hat_range),
        (ecodes.ABS_HAT3X,    hat_range),
        (ecodes.ABS_HAT3Y,    hat_range),
    ]

    key_capabilities = [ecodes.BTN_JOYSTICK + i for i in range(_button_count(vjoy_id))]

    return evdev.UInput(
        events={
            ecodes.EV_ABS: abs_capabilities,
            ecodes.EV_KEY: key_capabilities,
        },
        name=f"JoystickGremlin vJoy {vjoy_id}",
        # Match the vJoy Windows driver VID/PID so that dill.DeviceSummary.is_virtual
        # returns True and device_initialization can pair DILL and vjoy devices.
        vendor=_VJOY_VENDOR,
        product=_VJOY_PRODUCT,
    )


# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

class LinuxVJoyBackend(AbstractVJoyBackend):
    """evdev.UInput-based virtual joystick backend for Linux."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._devices: dict[int, evdev.UInput] = {}
        self._pre_create_devices()

    def _pre_create_devices(self) -> None:
        """Pre-create the configured number of virtual joystick devices.

        The count is read from AppBackend.vjoy_device_count (default 4).
        Pre-created devices return _STATE_OWNED so device_exists() sees them
        immediately without waiting for an explicit acquire_vjd() call.
        """
        from gremlin.app_platform import app_backend
        count = getattr(app_backend, "vjoy_device_count", 4)
        for vjoy_id in range(1, count + 1):
            try:
                self._devices[vjoy_id] = _make_uinput(vjoy_id)
                _log.debug(
                    "LinuxVJoyBackend: pre-created UInput for vjoy %d", vjoy_id
                )
            except Exception as exc:
                _log.error(
                    "LinuxVJoyBackend: failed to pre-create UInput for vjoy %d: %s",
                    vjoy_id, exc,
                )

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — driver info
    # ------------------------------------------------------------------

    def vjoy_enabled(self) -> bool:
        return os.access("/dev/uinput", os.W_OK)

    def get_version(self) -> int:
        return 0x218  # satisfies the >= 2.1.8 check in vjoy.py

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — device status
    # ------------------------------------------------------------------

    def get_vjd_status(self, vjoy_id: int) -> int:
        with self._lock:
            if vjoy_id in self._devices:
                # Report Free so that VJoy.__init__ can proceed to AcquireVJD.
                # The UInput device already exists at OS level; from vjoy.py's
                # perspective it is "free to be acquired" until VJoy() is
                # constructed for it.
                return _STATE_FREE
            return _STATE_MISSING

    def get_owner_pid(self, vjoy_id: int) -> int:
        with self._lock:
            return os.getpid() if vjoy_id in self._devices else -1

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — device acquisition
    # ------------------------------------------------------------------

    def acquire_vjd(self, vjoy_id: int) -> bool:
        with self._lock:
            if vjoy_id in self._devices:
                # Already pre-created or previously acquired — report success.
                return True
            try:
                self._devices[vjoy_id] = _make_uinput(vjoy_id)
                _log.debug("LinuxVJoyBackend: created UInput for vjoy %d", vjoy_id)
                return True
            except Exception as exc:
                _log.error(
                    "LinuxVJoyBackend: failed to create UInput for vjoy %d: %s",
                    vjoy_id, exc,
                )
                return False

    def relinquish_vjd(self, vjoy_id: int) -> None:
        # On Linux the UInput device must stay alive for the full application
        # lifetime: closing it would destroy it at OS level (unlike the Windows
        # vJoy driver, which persists independently).  Releasing ownership is a
        # logical no-op; the device will be cleaned up when the process exits.
        _log.debug("LinuxVJoyBackend: relinquish_vjd(%d) — no-op on Linux", vjoy_id)

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — device capabilities
    # ------------------------------------------------------------------

    def get_vjd_button_number(self, vjoy_id: int) -> int:
        return _button_count(vjoy_id)

    def get_vjd_disc_pov_number(self, vjoy_id: int) -> int:
        # Return 0 so vjoy.py treats all hats as Continuous (correct for UInput)
        return 0

    def get_vjd_cont_pov_number(self, vjoy_id: int) -> int:
        return _HAT_COUNT

    def get_vjd_axis_exist(self, vjoy_id: int, axis_id: int) -> int:
        return 1 if axis_id in _SUPPORTED_AXIS_IDS else 0

    def get_vjd_axis_max(self, vjoy_id: int, axis_id: int) -> int:
        return 32767

    def get_vjd_axis_min(self, vjoy_id: int, axis_id: int) -> int:
        return -32768

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — reset
    # ------------------------------------------------------------------

    def reset_vjd(self, vjoy_id: int) -> bool:
        with self._lock:
            ui = self._devices.get(vjoy_id)
        if ui is None:
            return False
        try:
            for abs_code in [
                ecodes.ABS_X, ecodes.ABS_Y, ecodes.ABS_Z,
                ecodes.ABS_RX, ecodes.ABS_RY, ecodes.ABS_RZ,
                ecodes.ABS_THROTTLE, ecodes.ABS_RUDDER,
            ]:
                ui.write(ecodes.EV_ABS, abs_code, 0)
            for i in range(_button_count(vjoy_id)):
                ui.write(ecodes.EV_KEY, ecodes.BTN_JOYSTICK + i, 0)
            for ax_code, ay_code in _HAT_AXES:
                ui.write(ecodes.EV_ABS, ax_code, 0)
                ui.write(ecodes.EV_ABS, ay_code, 0)
            ui.syn()
            return True
        except Exception as exc:
            _log.error("LinuxVJoyBackend: reset_vjd(%d) failed: %s", vjoy_id, exc)
            return False

    def reset_all(self) -> None:
        with self._lock:
            ids = list(self._devices.keys())
        for vjoy_id in ids:
            self.reset_vjd(vjoy_id)

    def reset_buttons(self, vjoy_id: int) -> bool:
        with self._lock:
            ui = self._devices.get(vjoy_id)
        if ui is None:
            return False
        try:
            for i in range(_button_count(vjoy_id)):
                ui.write(ecodes.EV_KEY, ecodes.BTN_JOYSTICK + i, 0)
            ui.syn()
            return True
        except Exception as exc:
            _log.error("LinuxVJoyBackend: reset_buttons(%d) failed: %s", vjoy_id, exc)
            return False

    def reset_povs(self, vjoy_id: int) -> bool:
        with self._lock:
            ui = self._devices.get(vjoy_id)
        if ui is None:
            return False
        try:
            for ax_code, ay_code in _HAT_AXES:
                ui.write(ecodes.EV_ABS, ax_code, 0)
                ui.write(ecodes.EV_ABS, ay_code, 0)
            ui.syn()
            return True
        except Exception as exc:
            _log.error("LinuxVJoyBackend: reset_povs(%d) failed: %s", vjoy_id, exc)
            return False

    # ------------------------------------------------------------------
    # AbstractVJoyBackend — set values
    # ------------------------------------------------------------------

    def set_axis(self, value: int, vjoy_id: int, axis_id: int) -> bool:
        abs_code = _HID_TO_ABS.get(axis_id)
        if abs_code is None:
            return False
        with self._lock:
            ui = self._devices.get(vjoy_id)
        if ui is None:
            return False
        try:
            ui.write(ecodes.EV_ABS, abs_code, value)
            ui.syn()
            return True
        except Exception as exc:
            _log.error("LinuxVJoyBackend: set_axis(%d) failed: %s", vjoy_id, exc)
            return False

    def set_btn(self, pressed: bool, vjoy_id: int, btn_id: int) -> bool:
        key_code = ecodes.BTN_JOYSTICK + btn_id - 1  # btn_id is 1-based
        with self._lock:
            ui = self._devices.get(vjoy_id)
        if ui is None:
            return False
        try:
            ui.write(ecodes.EV_KEY, key_code, 1 if pressed else 0)
            ui.syn()
            return True
        except Exception as exc:
            _log.error("LinuxVJoyBackend: set_btn(%d) failed: %s", vjoy_id, exc)
            return False

    def set_cont_pov(self, degrees: int, vjoy_id: int, hat_id: int) -> bool:
        xy = _DI_HAT_TO_XY.get(degrees)
        if xy is None:
            return False
        hat_idx = hat_id - 1  # hat_id is 1-based
        if hat_idx < 0 or hat_idx >= len(_HAT_AXES):
            return False
        ax_code, ay_code = _HAT_AXES[hat_idx]
        with self._lock:
            ui = self._devices.get(vjoy_id)
        if ui is None:
            return False
        try:
            ui.write(ecodes.EV_ABS, ax_code, xy[0])
            ui.write(ecodes.EV_ABS, ay_code, xy[1])
            ui.syn()
            return True
        except Exception as exc:
            _log.error("LinuxVJoyBackend: set_cont_pov(%d) failed: %s", vjoy_id, exc)
            return False

    def set_disc_pov(self, direction: int, vjoy_id: int, hat_id: int) -> bool:
        xy = _DISC_TO_XY.get(direction)
        if xy is None:
            return False
        hat_idx = hat_id - 1  # hat_id is 1-based
        if hat_idx < 0 or hat_idx >= len(_HAT_AXES):
            return False
        ax_code, ay_code = _HAT_AXES[hat_idx]
        with self._lock:
            ui = self._devices.get(vjoy_id)
        if ui is None:
            return False
        try:
            ui.write(ecodes.EV_ABS, ax_code, xy[0])
            ui.write(ecodes.EV_ABS, ay_code, xy[1])
            ui.syn()
            return True
        except Exception as exc:
            _log.error("LinuxVJoyBackend: set_disc_pov(%d) failed: %s", vjoy_id, exc)
            return False
