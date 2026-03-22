# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

# Windows implementation – moved from gremlin/windows_event_hook.py (content unchanged).

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import threading
from typing import Callable

from gremlin.common import SingletonMetaclass
from gremlin.types import MouseButton

user32 = ctypes.WinDLL("user32")


g_keyboard_callbacks = []
g_mouse_callbacks = []


HOOKPROC = ctypes.WINFUNCTYPE(
    wintypes.LPARAM,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM
)

user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.SetWindowsHookExW.argtypes = (
    ctypes.c_int,
    HOOKPROC,
    wintypes.HINSTANCE,
    wintypes.DWORD
)

user32.CallNextHookEx.restype = wintypes.LPARAM
user32.CallNextHookEx.argtypes = (
    wintypes.HHOOK,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM
)

user32.GetMessageW.argtypes = (
    wintypes.LPMSG,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT
)

user32.TranslateMessage.argtypes = (wintypes.LPMSG,)
user32.DispatchMessageW.argtypes = (wintypes.LPMSG,)

HC_ACTION       = 0
WH_KEYBOARD_LL  = 13
WH_MOUSE_LL     = 14

WM_QUIT         = 0x0012
WM_MOUSEMOVE    = 0x0200
WM_LBUTTONDOWN  = 0x0201
WM_LBUTTONUP    = 0x0202
WM_RBUTTONDOWN  = 0x0204
WM_RBUTTONUP    = 0x0205
WM_MBUTTONDOWN  = 0x0207
WM_MBUTTONUP    = 0x0208
WM_MOUSEWHEEL   = 0x020A
WM_XBUTTONDOWN  = 0x020B
WM_XBUTTONUP    = 0x020C
WM_MOUSEHWHEEL  = 0x020E


class KBDLLHOOKSTRUCT(ctypes.Structure):

    _fields_ = (
        ("vkCode",      wintypes.DWORD),
        ("scanCode",    wintypes.DWORD),
        ("flags",       wintypes.DWORD),
        ("time",        wintypes.DWORD),
        ("dwExtraInfo", wintypes.WPARAM)
    )
LPKBDLLHOOKSTRUCT = ctypes.POINTER(KBDLLHOOKSTRUCT)


class MSLLHOOKSTRUCT(ctypes.Structure):

    _fields_ = (
        ("pt",          wintypes.POINT),
        ("mouseData",   wintypes.DWORD),
        ("flags",       wintypes.DWORD),
        ("time",        wintypes.DWORD),
        ("dwExtraInfo", wintypes.WPARAM)
    )
LPMSLLHOOKSTRUCT = ctypes.POINTER(MSLLHOOKSTRUCT)


@HOOKPROC
def process_keyboard_event(n_code, w_param, l_param):
    msg = ctypes.cast(l_param, LPKBDLLHOOKSTRUCT)[0]

    if n_code >= 0 and msg.scanCode:
        scan_code = msg.scanCode & 0xFF
        is_extended = msg.flags is not None and bool(msg.flags & 0x0001)
        is_pressed = w_param in [0x0100, 0x0104]
        is_injected = msg.flags is not None and bool(msg.flags & 0x0010)

        if msg.scanCode != 541:
            evt = KeyEvent(scan_code, is_extended, is_pressed, is_injected)
            for cb in g_keyboard_callbacks:
                cb(evt)

    return user32.CallNextHookEx(None, n_code, w_param, l_param)


@HOOKPROC
def process_mouse_event(n_code, w_param, l_param):
    if n_code == HC_ACTION and w_param != WM_MOUSEMOVE:
        msg = ctypes.cast(l_param, LPMSLLHOOKSTRUCT)[0]

        button_id = None
        is_pressed = True
        if w_param in [WM_LBUTTONDOWN, WM_LBUTTONUP]:
            button_id = MouseButton.Left
            is_pressed = w_param == WM_LBUTTONDOWN
        elif w_param in [WM_RBUTTONDOWN, WM_RBUTTONUP]:
            button_id = MouseButton.Right
            is_pressed = w_param == WM_RBUTTONDOWN
        elif w_param in [WM_MBUTTONDOWN, WM_MBUTTONUP]:
            button_id = MouseButton.Middle
            is_pressed = w_param == WM_MBUTTONDOWN
        elif w_param in [WM_XBUTTONDOWN, WM_XBUTTONUP]:
            if msg.mouseData & (0x0001 << 16):
                button_id = MouseButton.Back
            elif msg.mouseData & (0x0002 << 16):
                button_id = MouseButton.Forward
            is_pressed = w_param == WM_XBUTTONDOWN
        elif w_param == WM_MOUSEWHEEL:
            if (msg.mouseData >> 16) == 120:
                button_id = MouseButton.WheelUp
            elif (msg.mouseData >> 16) == 65416:
                button_id = MouseButton.WheelDown

        evt = MouseEvent(button_id, is_pressed, False)
        for cb in g_mouse_callbacks:
            cb(evt)

    return user32.CallNextHookEx(None, n_code, w_param, l_param)


@dataclass
class KeyEvent:

    """Structure containing details about a key event."""

    scan_code : int
    is_extended : bool
    is_pressed : bool
    is_injected : bool

    def __str__(self) -> str:
        up_or_down = "down" if self.is_pressed else "up"
        injected_str = "injected" if self.is_injected else ""
        return f"({hex(self.scan_code)} {self.is_extended}) " \
               f"{up_or_down}, {injected_str}"


@dataclass
class MouseEvent:

    """Structure containing information about a mouse event."""

    button_id : MouseButton
    is_pressed : bool
    is_injected : bool


class KeyboardHook(metaclass=SingletonMetaclass):

    def __init__(self) -> None:
        self._running = False
        self._listen_thread = threading.Thread(target=self._listen)

    def register(self, callback: Callable[[KeyEvent], None]) -> None:
        global g_keyboard_callbacks
        g_keyboard_callbacks.append(callback)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._listen_thread.start()

    def stop(self) -> None:
        if self._running:
            self._running = False
            user32.PostThreadMessageW(self._listen_thread.ident, WM_QUIT, 0, 0)
            self._listen_thread.join()
            self._listen_thread = threading.Thread(target=self._listen)

    def _listen(self) -> None:
        hook_id = user32.SetWindowsHookExW(WH_KEYBOARD_LL, process_keyboard_event, None, 0)

        msg = wintypes.MSG()
        while self._running:
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if not result:
                break
            if result == -1:
                raise ctypes.WinError(ctypes.get_last_error())
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        try:
            user32.UnhookWindowsHookEx(hook_id)
        except Exception:
            pass


class MouseHook(metaclass=SingletonMetaclass):

    def __init__(self) -> None:
        self._running = False
        self._listen_thread = threading.Thread(target=self._listen)

    def register(self, callback: Callable[[MouseEvent], None]) -> None:
        global g_mouse_callbacks
        g_mouse_callbacks.append(callback)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._listen_thread.start()

    def stop(self) -> None:
        if self._running:
            self._running = False
            user32.PostThreadMessageW(self._listen_thread.ident, WM_QUIT, 0, 0)
            self._listen_thread.join()
            self._listen_thread = threading.Thread(target=self._listen)

    def _listen(self) -> None:
        hook_id = user32.SetWindowsHookExW(WH_MOUSE_LL, process_mouse_event, None, 0)

        msg = wintypes.MSG()
        while self._running:
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if not result:
                break
            if result == -1:
                raise ctypes.WinError(ctypes.get_last_error())
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnhookWindowsHookEx(hook_id)
