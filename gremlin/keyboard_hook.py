# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2017 Lionel Ott
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

import gremlin
import gremlin.common


class KeyEvent(object):

    """Structure containing details about a key event."""

    def __init__(self, scan_code, is_extended, is_pressed, is_injected):
        """Creates a new instance with the given data.

        :param scan_code the scan code of the key this event is for
        :param is_extended flag indicating if the scan code is extended
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
        return "({:d} {:d}) {} {}".format(
                self._scan_code,
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


@gremlin.common.SingletonDecorator
class KeyboardHook(object):

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
        if n_code >= 0:
            # Event types which specify a key press event
            key_press_types = [0x0100, 0x0104]

            # Extract data from the message
            scan_code = l_param[1]
            is_extended = l_param[2] is not None and bool(l_param[2] & 0x0001)
            is_pressed = w_param in key_press_types
            is_injected = l_param[2] is not None and bool(l_param[2] & 0x0010)

            # Create the event and pass it to all all registered callbacks
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
