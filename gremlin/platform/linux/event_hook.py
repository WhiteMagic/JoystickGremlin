# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Linux keyboard/mouse event hooks — evdev-based global input monitoring."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Callable

import evdev
from evdev import ecodes

from gremlin.common import SingletonMetaclass
from gremlin.types import MouseButton

_log = logging.getLogger("system")

# ---------------------------------------------------------------------------
# Extended-key set: evdev keycodes that map to Windows extended keys.
# Used to populate is_extended in KeyEvent so key_from_code() works correctly.
# ---------------------------------------------------------------------------

_EVDEV_EXTENDED: frozenset[int] = frozenset([
    ecodes.KEY_SYSRQ,
    ecodes.KEY_INSERT,    ecodes.KEY_DELETE,
    ecodes.KEY_HOME,      ecodes.KEY_END,
    ecodes.KEY_PAGEUP,    ecodes.KEY_PAGEDOWN,
    ecodes.KEY_UP,        ecodes.KEY_DOWN,
    ecodes.KEY_LEFT,      ecodes.KEY_RIGHT,
    ecodes.KEY_NUMLOCK,   ecodes.KEY_KPSLASH,  ecodes.KEY_KPENTER,
    ecodes.KEY_RIGHTCTRL, ecodes.KEY_RIGHTALT,
    ecodes.KEY_LEFTMETA,  ecodes.KEY_RIGHTMETA, ecodes.KEY_COMPOSE,
])

# BTN_* evdev codes → MouseButton enum
_EVDEV_TO_MOUSE_BUTTON: dict[int, MouseButton] = {
    ecodes.BTN_LEFT:   MouseButton.Left,
    ecodes.BTN_RIGHT:  MouseButton.Right,
    ecodes.BTN_MIDDLE: MouseButton.Middle,
    ecodes.BTN_EXTRA:  MouseButton.Forward,
    ecodes.BTN_SIDE:   MouseButton.Back,
}


# ---------------------------------------------------------------------------
# Event dataclasses (identical interface to Windows version)
# ---------------------------------------------------------------------------

@dataclass
class KeyEvent:

    """Structure containing details about a key event."""

    scan_code: int
    is_extended: bool
    is_pressed: bool
    is_injected: bool

    def __str__(self) -> str:
        up_or_down = "down" if self.is_pressed else "up"
        injected_str = "injected" if self.is_injected else ""
        return f"({hex(self.scan_code)} {self.is_extended}) {up_or_down}, {injected_str}"


@dataclass
class MouseEvent:

    """Structure containing information about a mouse event."""

    button_id: MouseButton
    is_pressed: bool
    is_injected: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_our_device(dev: evdev.InputDevice) -> bool:
    """Return True if this device was created by JoystickGremlin."""
    return dev.name.startswith("JoystickGremlin")


def _is_keyboard(dev: evdev.InputDevice) -> bool:
    """Return True if the device looks like a real keyboard."""
    caps = dev.capabilities()
    keys = set(caps.get(ecodes.EV_KEY, []))
    return ecodes.KEY_A in keys and ecodes.KEY_SPACE in keys


def _is_mouse(dev: evdev.InputDevice) -> bool:
    """Return True if the device looks like a real mouse."""
    caps = dev.capabilities()
    keys = set(caps.get(ecodes.EV_KEY, []))
    rels = set(caps.get(ecodes.EV_REL, []))
    return ecodes.BTN_LEFT in keys and ecodes.REL_X in rels


# ---------------------------------------------------------------------------
# KeyboardHook
# ---------------------------------------------------------------------------

class KeyboardHook(metaclass=SingletonMetaclass):

    """Monitors all physical keyboard devices and fires registered callbacks."""

    def __init__(self) -> None:
        self._running = False
        self._callbacks: list[Callable[[KeyEvent], None]] = []
        self._threads: list[threading.Thread] = []

    def register(self, callback: Callable[[KeyEvent], None]) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                if _is_keyboard(dev) and not _is_our_device(dev):
                    t = threading.Thread(
                        target=self._read_loop,
                        args=(dev,),
                        daemon=True,
                        name=f"kb-hook-{dev.name[:20]}",
                    )
                    t.start()
                    self._threads.append(t)
                    _log.debug("KeyboardHook: listening on %s (%s)", dev.name, path)
            except Exception as exc:
                _log.debug("KeyboardHook: cannot open %s: %s", path, exc)

    def stop(self) -> None:
        self._running = False

    def _read_loop(self, dev: evdev.InputDevice) -> None:
        try:
            for ev in dev.read_loop():
                if not self._running:
                    break
                if ev.type != ecodes.EV_KEY:
                    continue
                if ev.value not in (0, 1):   # ignore key-repeat (value == 2)
                    continue
                event = KeyEvent(
                    scan_code=ev.code,
                    is_extended=ev.code in _EVDEV_EXTENDED,
                    is_pressed=(ev.value == 1),
                    is_injected=False,
                )
                for cb in self._callbacks:
                    try:
                        cb(event)
                    except Exception:
                        pass
        except OSError:
            _log.debug("KeyboardHook: device disconnected: %s", dev.name)


# ---------------------------------------------------------------------------
# MouseHook
# ---------------------------------------------------------------------------

class MouseHook(metaclass=SingletonMetaclass):

    """Monitors all physical mouse devices and fires registered callbacks."""

    def __init__(self) -> None:
        self._running = False
        self._callbacks: list[Callable[[MouseEvent], None]] = []
        self._threads: list[threading.Thread] = []

    def register(self, callback: Callable[[MouseEvent], None]) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                if _is_mouse(dev) and not _is_our_device(dev):
                    t = threading.Thread(
                        target=self._read_loop,
                        args=(dev,),
                        daemon=True,
                        name=f"mouse-hook-{dev.name[:20]}",
                    )
                    t.start()
                    self._threads.append(t)
                    _log.debug("MouseHook: listening on %s (%s)", dev.name, path)
            except Exception as exc:
                _log.debug("MouseHook: cannot open %s: %s", path, exc)

    def stop(self) -> None:
        self._running = False

    def _read_loop(self, dev: evdev.InputDevice) -> None:
        try:
            for ev in dev.read_loop():
                if not self._running:
                    break
                if ev.type != ecodes.EV_KEY:
                    continue
                button = _EVDEV_TO_MOUSE_BUTTON.get(ev.code)
                if button is None:
                    continue
                event = MouseEvent(
                    button_id=button,
                    is_pressed=(ev.value == 1),
                    is_injected=False,
                )
                for cb in self._callbacks:
                    try:
                        cb(event)
                    except Exception:
                        pass
        except OSError:
            _log.debug("MouseHook: device disconnected: %s", dev.name)
