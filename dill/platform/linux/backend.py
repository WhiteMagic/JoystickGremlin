# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Linux DILL backend — evdev-based joystick enumeration and event delivery."""

from __future__ import annotations

import ctypes
import logging
import threading
import time
import uuid as _uuid_mod
from typing import Callable, Optional

import evdev
from evdev import ecodes

from dill.platform.base.backend import AbstractDillBackend
from dill.platform.base.types import (
    _GUID,
    _AxisMap,
    _DeviceSummary,
    _JoystickInputData,
    ctwt,
)

_log = logging.getLogger("system")

# ---------------------------------------------------------------------------
# Axis mapping: evdev ABS_* code → DirectInput 1-based axis index
# ---------------------------------------------------------------------------

_ABS_TO_DI: dict[int, int] = {
    ecodes.ABS_X:        1,
    ecodes.ABS_Y:        2,
    ecodes.ABS_Z:        3,
    ecodes.ABS_RX:       4,
    ecodes.ABS_RY:       5,
    ecodes.ABS_RZ:       6,
    ecodes.ABS_THROTTLE: 7,
    ecodes.ABS_RUDDER:   8,
}

_DI_TO_ABS: dict[int, int] = {v: k for k, v in _ABS_TO_DI.items()}

# Hat axis pairs (X code, Y code) indexed 0-3
_HAT_AXES = [
    (ecodes.ABS_HAT0X, ecodes.ABS_HAT0Y),
    (ecodes.ABS_HAT1X, ecodes.ABS_HAT1Y),
    (ecodes.ABS_HAT2X, ecodes.ABS_HAT2Y),
    (ecodes.ABS_HAT3X, ecodes.ABS_HAT3Y),
]
_HAT_CODES = {code for pair in _HAT_AXES for code in pair}

# evdev (x, y) → DirectInput hat value (hundredths of degrees, -1 = centred)
_XY_TO_DI_HAT: dict[tuple[int, int], int] = {
    ( 0,  0): -1,
    ( 0, -1): 0,
    ( 1, -1): 4500,
    ( 1,  0): 9000,
    ( 1,  1): 13500,
    ( 0,  1): 18000,
    (-1,  1): 22500,
    (-1,  0): 27000,
    (-1, -1): 31500,
}

# UUID namespace for stable device identifiers
_DILL_NS = _uuid_mod.UUID("e4e7f789-e4e7-e4e7-e4e7-e4e7f7890000")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VJOY_VENDOR  = 0x1234
_VJOY_PRODUCT = 0xBEAD


def _device_uuid(dev: evdev.InputDevice) -> _uuid_mod.UUID:
    """Return a stable UUID derived from vendor:product and a unique identifier.

    For real physical devices dev.phys is a stable hardware path such as
    "usb-0000:00:14.0-1/input0" and is used directly.

    For virtual UInput devices (our vjoy devices) evdev always sets
    dev.phys to the same fixed string ("py-evdev-uinput"), so it cannot
    serve as a discriminant. We detect these by VID/PID and use dev.name
    instead (e.g. "JoystickGremlin vJoy 1") which is unique per device.
    """
    if dev.info.vendor == _VJOY_VENDOR and dev.info.product == _VJOY_PRODUCT:
        unique = dev.name
    else:
        unique = dev.phys or dev.path
    key = f"{dev.info.vendor:04x}:{dev.info.product:04x}:{unique}"
    return _uuid_mod.uuid5(_DILL_NS, key)


_JOYSTICK_BTN_MIN = ecodes.BTN_JOYSTICK  # 0x120 — excludes mouse buttons (0x110-0x11F)


def _is_joystick(dev: evdev.InputDevice) -> bool:
    """Return True if the device looks like a joystick or gamepad.

    Two conditions must both hold:
    1. The device exposes at least one joystick/throttle/rudder ABS axis
       (or a hat axis pair), so that pure mice (ABS_X/Y only) are excluded.
    2. The device has at least one button in the BTN_JOYSTICK / BTN_GAMEPAD
       range (0x120+), so that keyboards and mice are excluded.
    """
    caps = dev.capabilities()
    abs_codes = {code for code, _ in caps.get(ecodes.EV_ABS, [])}
    if not (abs_codes & (_ABS_TO_DI.keys() | _HAT_CODES)):
        return False
    keys = set(caps.get(ecodes.EV_KEY, []))
    return bool(keys.intersection(range(_JOYSTICK_BTN_MIN, ecodes.KEY_MAX + 1)))


def _uuid_to_guid(u: _uuid_mod.UUID) -> _GUID:
    """Convert a Python UUID to a _GUID ctypes struct."""
    b = u.bytes
    g = _GUID()
    g.Data1 = int.from_bytes(b[0:4], "big")
    g.Data2 = int.from_bytes(b[4:6], "big")
    g.Data3 = int.from_bytes(b[6:8], "big")
    for i in range(8):
        g.Data4[i] = b[8 + i]
    return g


def _guid_to_uuid(guid: _GUID) -> _uuid_mod.UUID:
    """Convert a _GUID ctypes struct back to a Python UUID."""
    b = (
        guid.Data1.to_bytes(4, "big")
        + guid.Data2.to_bytes(2, "big")
        + guid.Data3.to_bytes(2, "big")
        + bytes(guid.Data4)
    )
    return _uuid_mod.UUID(bytes=b)


def _scale_axis(value: int, min_val: int, max_val: int) -> int:
    """Normalize an evdev absolute value to DirectInput range [-32768, 32767]."""
    if max_val == min_val:
        return 0
    return round((value - min_val) / (max_val - min_val) * 65535) - 32768


# ---------------------------------------------------------------------------
# Per-device state
# ---------------------------------------------------------------------------

class _DeviceState:
    """Tracks mutable state for one evdev joystick device."""

    def __init__(self, dev: evdev.InputDevice, uid: _uuid_mod.UUID) -> None:
        self.dev = dev
        self.uid = uid
        self.guid = _uuid_to_guid(uid)
        caps = dev.capabilities()

        # Sorted list of joystick button codes (→ 1-based DI index)
        all_keys = caps.get(ecodes.EV_KEY, [])
        self.button_codes: list[int] = sorted(
            c for c in all_keys if c >= ecodes.BTN_MISC
        )

        # Sorted list of non-hat absolute axis codes present on the device
        abs_pairs = caps.get(ecodes.EV_ABS, [])
        self.axis_codes: list[int] = sorted(
            code for code, _ in abs_pairs
            if code in _ABS_TO_DI
        )

        # Hat state per hat index: {hat_idx: [x, y]}
        self.hat_state: dict[int, list[int]] = {
            i: [0, 0] for i in range(len(_HAT_AXES))
            if _HAT_AXES[i][0] in {code for code, _ in abs_pairs}
        }

    def build_summary(self) -> _DeviceSummary:
        """Return a populated _DeviceSummary ctypes struct for this device."""
        s = _DeviceSummary()
        s.device_guid = self.guid
        s.vendor_id   = self.dev.info.vendor
        s.product_id  = self.dev.info.product
        s.joystick_id = 0

        name_bytes = self.dev.name.encode("utf-8", errors="ignore")
        s.name = name_bytes[: ctwt.MAX_PATH - 1]

        s.axis_count   = len(self.axis_codes)
        s.button_count = len(self.button_codes)
        s.hat_count    = len(self.hat_state)

        for i, code in enumerate(self.axis_codes[:8]):
            s.axis_map[i].linear_index = i
            s.axis_map[i].axis_index   = _ABS_TO_DI[code]

        return s

    def di_hat_value(self, hat_idx: int) -> int:
        xy = self.hat_state.get(hat_idx, [0, 0])
        return _XY_TO_DI_HAT.get(tuple(xy), -1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

class LinuxDillBackend(AbstractDillBackend):
    """evdev-based joystick backend for Linux."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._devices: dict[_uuid_mod.UUID, _DeviceState] = {}
        self._input_callback: Optional[Callable] = None
        self._device_callback: Optional[Callable] = None
        self._running = False

    # ------------------------------------------------------------------
    # AbstractDillBackend — lifecycle
    # ------------------------------------------------------------------

    def init(self) -> None:
        """Enumerate devices and start event / hotplug threads."""
        self._running = True
        self._enumerate_devices()
        threading.Thread(
            target=self._hotplug_loop, daemon=True, name="dill-hotplug"
        ).start()

    # ------------------------------------------------------------------
    # AbstractDillBackend — callbacks
    # ------------------------------------------------------------------

    def set_input_event_callback(self, callback: Callable) -> None:
        self._input_callback = callback

    def set_device_change_callback(self, callback: Callable) -> None:
        self._device_callback = callback

    # ------------------------------------------------------------------
    # AbstractDillBackend — queries
    # ------------------------------------------------------------------

    def get_device_count(self) -> int:
        with self._lock:
            return len(self._devices)

    def get_device_information_by_index(self, index: int) -> _DeviceSummary:
        with self._lock:
            states = list(self._devices.values())
        if index < len(states):
            return states[index].build_summary()
        return _DeviceSummary()

    def get_device_information_by_guid(self, guid: _GUID) -> _DeviceSummary:
        uid = _guid_to_uuid(guid)
        with self._lock:
            state = self._devices.get(uid)
        return state.build_summary() if state else _DeviceSummary()

    def get_axis(self, guid: _GUID, index: int) -> int:
        uid = _guid_to_uuid(guid)
        with self._lock:
            state = self._devices.get(uid)
        if state is None:
            return 0
        abs_code = _DI_TO_ABS.get(index)
        if abs_code is None or abs_code not in state.axis_codes:
            return 0
        try:
            info = state.dev.absinfo(abs_code)
            return _scale_axis(info.value, info.min, info.max)
        except Exception:
            return 0

    def get_button(self, guid: _GUID, index: int) -> bool:
        uid = _guid_to_uuid(guid)
        with self._lock:
            state = self._devices.get(uid)
        if state is None:
            return False
        idx = index - 1  # convert 1-based to 0-based
        if idx < 0 or idx >= len(state.button_codes):
            return False
        try:
            return state.button_codes[idx] in state.dev.active_keys()
        except Exception:
            return False

    def get_hat(self, guid: _GUID, index: int) -> int:
        uid = _guid_to_uuid(guid)
        with self._lock:
            state = self._devices.get(uid)
        if state is None:
            return -1
        return state.di_hat_value(index - 1)  # 1-based → 0-based

    def device_exists(self, guid: _GUID) -> bool:
        uid = _guid_to_uuid(guid)
        with self._lock:
            return uid in self._devices

    # ------------------------------------------------------------------
    # Device enumeration
    # ------------------------------------------------------------------

    def _enumerate_devices(self) -> None:
        for path in evdev.list_devices():
            self._try_add_device(path)

    def _try_add_device(self, path: str) -> Optional[_DeviceState]:
        try:
            dev = evdev.InputDevice(path)
            if not _is_joystick(dev):
                return None
            uid = _device_uuid(dev)
            with self._lock:
                if uid in self._devices:
                    return None
                state = _DeviceState(dev, uid)
                self._devices[uid] = state
            _log.debug("DILL Linux: added %s (%s)", dev.name, path)
            threading.Thread(
                target=self._read_loop,
                args=(uid,),
                daemon=True,
                name=f"dill-{dev.name}",
            ).start()
            return state
        except Exception as exc:
            _log.debug("DILL Linux: cannot open %s: %s", path, exc)
            return None

    # ------------------------------------------------------------------
    # Event loop (one thread per device)
    # ------------------------------------------------------------------

    def _read_loop(self, uid: _uuid_mod.UUID) -> None:
        with self._lock:
            state = self._devices.get(uid)
        if state is None:
            return

        try:
            for ev in state.dev.read_loop():
                if not self._running:
                    break
                if ev.type == ecodes.EV_ABS:
                    self._dispatch_abs(state, ev)
                elif ev.type == ecodes.EV_KEY:
                    self._dispatch_key(state, ev)
        except OSError:
            _log.debug("DILL Linux: device disconnected: %s", state.dev.name)
        finally:
            self._remove_device(uid)

    # ------------------------------------------------------------------
    # Event dispatch helpers
    # ------------------------------------------------------------------

    def _dispatch_abs(self, state: _DeviceState, ev: evdev.InputEvent) -> None:
        # Hat axis — update state and dispatch a hat event
        for hat_idx, (hx, hy) in enumerate(_HAT_AXES):
            if ev.code == hx:
                state.hat_state[hat_idx][0] = ev.value
                self._dispatch_hat(state, hat_idx)
                return
            if ev.code == hy:
                state.hat_state[hat_idx][1] = ev.value
                self._dispatch_hat(state, hat_idx)
                return

        # Regular axis
        di_index = _ABS_TO_DI.get(ev.code)
        if di_index is None or self._input_callback is None:
            return

        try:
            info = state.dev.absinfo(ev.code)
        except Exception:
            return

        data = _JoystickInputData()
        data.device_guid  = state.guid
        data.input_type   = 1  # Axis
        data.input_index  = di_index
        data.value        = _scale_axis(ev.value, info.min, info.max)
        self._input_callback(data)

    def _dispatch_key(self, state: _DeviceState, ev: evdev.InputEvent) -> None:
        if self._input_callback is None:
            return
        if ev.code not in state.button_codes:
            return
        btn_index = state.button_codes.index(ev.code) + 1  # 1-based
        data = _JoystickInputData()
        data.device_guid  = state.guid
        data.input_type   = 2  # Button
        data.input_index  = btn_index
        data.value        = ev.value  # 1 = pressed, 0 = released
        self._input_callback(data)

    def _dispatch_hat(self, state: _DeviceState, hat_idx: int) -> None:
        if self._input_callback is None:
            return
        data = _JoystickInputData()
        data.device_guid  = state.guid
        data.input_type   = 3  # Hat
        data.input_index  = hat_idx + 1  # 1-based
        data.value        = state.di_hat_value(hat_idx)
        self._input_callback(data)

    # ------------------------------------------------------------------
    # Device removal
    # ------------------------------------------------------------------

    def _remove_device(self, uid: _uuid_mod.UUID) -> None:
        with self._lock:
            state = self._devices.pop(uid, None)
        if state is None:
            return
        _log.debug("DILL Linux: removed %s", state.dev.name)
        if self._device_callback is not None:
            summary = state.build_summary()
            self._device_callback(summary, ctypes.c_uint8(2))  # Disconnected

    # ------------------------------------------------------------------
    # Hotplug monitor (polls /dev/input every second)
    # ------------------------------------------------------------------

    def _hotplug_loop(self) -> None:
        with self._lock:
            seen = set(self._devices.keys())

        while self._running:
            time.sleep(1.0)
            current_paths = evdev.list_devices()

            # Determine which UUIDs are currently present
            current: dict[_uuid_mod.UUID, str] = {}
            for path in current_paths:
                try:
                    dev = evdev.InputDevice(path)
                    if _is_joystick(dev):
                        current[_device_uuid(dev)] = path
                except Exception:
                    pass

            with self._lock:
                known = set(self._devices.keys())

            # New devices
            for uid, path in current.items():
                if uid not in known:
                    state = self._try_add_device(path)
                    if state and self._device_callback is not None:
                        self._device_callback(
                            state.build_summary(), ctypes.c_uint8(1)  # Connected
                        )
                    seen.add(uid)

            # The read_loop threads detect disconnections via OSError and call
            # _remove_device, so no explicit removal is needed here.
            seen = set(current.keys())
