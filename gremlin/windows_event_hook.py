# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2018 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import atexit
import ctypes
from ctypes import wintypes
import threading
import time

import gremlin.common


class KeyEvent:

    """Structure containing details about a key event."""

    def __init__(self, scan_code, is_extended, is_pressed, is_injected):
        """Creates a new instance with the given data.

        :param scan_code the hardware scan code of this event
        :param is_extended whether or not the scan code is an extended one
        :param is_pressed flag indicating if the key is pressed
        :param is_injected flag indicating if the event has been injected
        """
        self._scan_code = scan_code
        self._is_extended = is_extended
        self._is_pressed = is_pressed
        self._is_injected = is_injected

    def __str__(self):
        """Returns a string representation of the event.

        :return string representation of the event
        """
        return "({} {}) {}, {}".format(
            hex(self._scan_code),
            self._is_extended,
            "down" if self._is_pressed else "up",
            "injected" if self.is_injected else ""
        )

    @property
    def scan_code(self):
        return self._scan_code

    @property
    def is_extended(self):
        return self._is_extended

    @property
    def is_pressed(self):
        return self._is_pressed

    @property
    def is_injected(self):
        return self._is_injected


class MouseEvent:

    """Structure containing information about a mouse event."""

    def __init__(self, button_id, is_pressed, is_injected):
        self._button_id = button_id
        self._is_pressed = is_pressed
        self._is_injected = is_injected

    @property
    def button_id(self):
        return self._button_id

    @property
    def is_pressed(self):
        return self._is_pressed

    @property
    def is_injected(self):
        return self._is_injected


@gremlin.common.SingletonDecorator
class KeyboardHook:

    """Hooks into the event stream and grabs keyboard related events
    and passes them on to registered callback functions.

    The following pages are references to the various functions used:
    [1] SetWindowsHookEx
        https://msdn.microsoft.com/en-us/library/windows/desktop/ms644990(v=vs.85).aspx
    [2] LowLevelKeyboardProc
        https://msdn.microsoft.com/en-us/library/windows/desktop/ms644985(v=vs.85).aspx
    [3] KBDLLHOOKSTRUCT
        https://msdn.microsoft.com/en-us/library/windows/desktop/ms644967(v=vs.85).aspx
    """

    # Event types which specify a key press event
    key_press_types = [0x0100, 0x0104]

    def __init__(self):
        self._hook_id = None
        self._callbacks = []
        self._running = False
        self._listen_thread = threading.Thread(target=self._listen)

    def register(self, callback):
        """Registers a new message callback.

        :param callback the new callback to register
        """
        self._callbacks.append(callback)

    def start(self):
        """Starts the hook if it is not yet running."""
        if self._running:
            return
        self._running = True
        self._listen_thread.start()

    def stop(self):
        """Stops the hook from running."""
        if self._running:
            self._running = False
            self._listen_thread.join()
            # Recreate thread so we can launch it again
            self._listen_thread = threading.Thread(target=self._listen)

    def _process_event(self, n_code, w_param, l_param):
        """Process a single event.

        :param n_code code detailing how to process the event
        :param w_param message type identifier
        :param l_param message content
        """
        # Only handle events we're supposed to, see
        # https://msdn.microsoft.com/en-us/library/windows/desktop/ms644985(v=vs.85).aspx
        if n_code >= 0 and l_param[1]:
            # Extract data from the message
            scan_code = l_param[1] & 0xFF
            is_extended = l_param[2] is not None and bool(l_param[2] & 0x0001)
            is_pressed = w_param in self.key_press_types
            is_injected = l_param[2] is not None and bool(l_param[2] & 0x0010)

            # A scan code of 541 indicates AltGr being pressed. AltGr is sent
            # as a combination of RAlt + RCtrl to the system and as such
            # generates two key events, one for RAlt and one for RCtrl. The
            # RCtrl one is being modified due to RAlt being pressed.
            #
            # In this application we want the RAlt key press and ignore the
            # RCtrl key press.

            # Create the event and pass it to all all registered callbacks
            if l_param[1] != 541:
                evt = KeyEvent(scan_code, is_extended, is_pressed, is_injected)
                for cb in self._callbacks:
                    cb(evt)

        # Pass the event on to the next callback in the chain
        return ctypes.windll.user32.CallNextHookEx(
                self.hook_id,
                n_code,
                w_param,
                l_param
        )

    def _listen(self):
        """Configures the hook and starts listening."""
        # Hook callback function factory
        hook_factory = ctypes.CFUNCTYPE(
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_void_p)
        )
        keyboard_hook = hook_factory(self._process_event)

        # Hook our callback into the system
        ctypes.windll.kernel32.GetModuleHandleW.restype = \
            ctypes.wintypes.HMODULE
        ctypes.windll.kernel32.GetModuleHandleW.argtypes = \
            [ctypes.wintypes.LPCWSTR]
        self.hook_id = ctypes.windll.user32.SetWindowsHookExA(
                0x00D,
                keyboard_hook,
                ctypes.windll.kernel32.GetModuleHandleW(None),
                0
        )

        # Ensure proper cleanup on termination
        atexit.register(
                ctypes.windll.user32.UnhookWindowsHookEx, self.hook_id
        )

        while self._running:
            ctypes.windll.user32.PeekMessageW(None, 0, 0, 0, 1)
            time.sleep(0.001)


@gremlin.common.SingletonDecorator
class MousedHook:

    """Hooks into the event stream and grabs mouse related events
    and passes them on to registered callback functions.

    The following pages are references to the various functions used:
    [1] SetWindowsHookEx
        https://msdn.microsoft.com/en-us/library/windows/desktop/ms644990(v=vs.85).aspx
    [2] LowLevelMouseProc
        https://msdn.microsoft.com/de-de/library/windows/desktop/ms644986(v=vs.85).aspx
    [3] KBDLLHOOKSTRUCT
        https://msdn.microsoft.com/en-us/library/windows/desktop/ms644967(v=vs.85).aspx
    """

    WM_MOUSEMOVE = 0x0200
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_MBUTTONDOWN = 0x0207
    WM_MBUTTONUP = 0x0208
    WM_MOUSEWHEEL = 0x020A
    WM_XBUTTONDOWN = 0x020B
    WM_XBUTTONUP = 0x020C
    WM_MOUSEHWHEEL = 0x020E

    def __init__(self):
        self._hook_id = None
        self._callbacks = []
        self._running = False
        self._listen_thread = threading.Thread(target=self._listen)

    def register(self, callback):
        """Registers a new message callback.

        :param callback the new callback to register
        """
        self._callbacks.append(callback)

    def start(self):
        """Starts the hook if it is not yet running."""
        if self._running:
            return
        self._running = True
        self._listen_thread.start()

    def stop(self):
        """Stops the hook from running."""
        if self._running:
            self._running = False
            self._listen_thread.join()
            # Recreate thread so we can launch it again
            self._listen_thread = threading.Thread(target=self._listen)

    def _process_event(self, n_code, w_param, l_param):
        """Process a single event.

        :param n_code code detailing how to process the event
        :param w_param message type identifier
        :param l_param message content
        """
        # Only handle events we're supposed to, see
        # https://msdn.microsoft.com/en-us/library/windows/desktop/ms644985(v=vs.85).aspx
        if n_code == 0 and w_param != self.WM_MOUSEMOVE:
            button_id = None
            is_pressed = True
            if w_param in [self.WM_LBUTTONDOWN, self.WM_LBUTTONUP]:
                button_id = gremlin.common.MouseButton.Left
                is_pressed = w_param == self.WM_LBUTTONDOWN
            elif w_param in [self.WM_RBUTTONDOWN, self.WM_RBUTTONUP]:
                button_id = gremlin.common.MouseButton.Right
                is_pressed = w_param == self.WM_RBUTTONDOWN
            elif w_param in [self.WM_MBUTTONDOWN, self.WM_MBUTTONUP]:
                button_id = gremlin.common.MouseButton.Middle
                is_pressed = w_param == self.WM_MBUTTONDOWN
            elif w_param in [self.WM_XBUTTONDOWN, self.WM_XBUTTONUP]:
                if l_param[2] & (0x0001 << 16):
                    button_id = gremlin.common.MouseButton.Back
                elif l_param[2] & (0x0002 << 16):
                    button_id = gremlin.common.MouseButton.Forward
                is_pressed = w_param == self.WM_XBUTTONDOWN
            elif w_param == self.WM_MOUSEWHEEL:
                if (l_param[2] >> 16) == 120:
                    button_id = gremlin.common.MouseButton.WheelUp
                elif (l_param[2] >> 16) == 65416:
                    button_id = gremlin.common.MouseButton.WheelDown
            else:
                print(w_param)

            # print(button_id)
            evt = MouseEvent(button_id, is_pressed, False)
            for cb in self._callbacks:
                cb(evt)

            # Extract data from the message
            # print(n_code, w_param)
            # if l_param[2] is not None:
            #     # print(l_param[0], l_param[1], bin(l_param[2]))
            #     print(w_param, l_param[2] & (0x0001 << 16))
            #     #
            #     #  1 0000 0000 0000 0000
            #     # 10 0000 0000 0000 0000

        # Pass the event on to the next callback in the chain
        return ctypes.windll.user32.CallNextHookEx(
                self.hook_id,
                n_code,
                w_param,
                l_param
        )

    def _listen(self):
        """Configures the hook and starts listening."""
        # Hook callback function factory
        hook_factory = ctypes.CFUNCTYPE(
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_void_p)
        )
        mouse_hook = hook_factory(self._process_event)

        # Hook our callback into the system
        ctypes.windll.kernel32.GetModuleHandleW.restype = \
            ctypes.wintypes.HMODULE
        ctypes.windll.kernel32.GetModuleHandleW.argtypes = \
            [ctypes.wintypes.LPCWSTR]
        self.hook_id = ctypes.windll.user32.SetWindowsHookExA(
                0x00E,
                mouse_hook,
                ctypes.windll.kernel32.GetModuleHandleW(None),
                0
        )

        # Ensure proper cleanup on termination
        atexit.register(
            ctypes.windll.user32.UnhookWindowsHookEx, self.hook_id
        )

        while self._running:
            ctypes.windll.user32.PeekMessageW(None, 0, 0, 0, 1)
            time.sleep(0.001)
