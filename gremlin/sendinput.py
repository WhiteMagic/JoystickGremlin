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


import ctypes
import ctypes.wintypes
import math
import threading
import time

from gremlin.common import MouseButton, SingletonDecorator


"""Defines flags used when specifying MOUSEINPUT structures.

https://msdn.microsoft.com/en-us/library/ms646273(v=VS.85).aspx
"""
WHEEL_DELTA = 120
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_HWHEEL = 0x01000
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100


"""Defines data structure type for INPUT structures.

https://msdn.microsoft.com/en-us/library/ms646270(v=vs.85).aspx
"""
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1


@SingletonDecorator
class MouseController:

    """Centralizes sending mouse events in a organized manner."""

    def __init__(self):
        """Creates a new instance."""
        self._direction = 0
        self._min_velocity = 0
        self._max_velocity = 0
        self._time_to_max = 0.0
        self._dx = 0
        self._dy = 0

        self._last_start_time = time.time()

        self._delta_x = 0
        self._delta_y = 0
        self._dx_time_inc = 0
        self._dy_time_inc = 0
        self._next_dx_update = 0
        self._next_dy_update = 0

        self._is_running = False
        self._thread = threading.Thread(target=self._control_loop)

    def set_accelerated_motion(self, direction, min_speed, max_speed, time_to_max):
        self._direction = direction
        self._min_velocity = min_speed
        self._max_velocity = max_speed
        self._time_to_max = time_to_max

    # @property
    # def dx(self):
    #     return self._delta_x
    #
    # @dx.setter
    # def dx(self, value):
    #     self._delta_x = value
    #     self._min_velocity = 0
    #     self._max_velocity = 0
    #     self._time_to_max = 0
    #     self._last_start_time = time.time()
    #     self._delta_x = math.ceil(abs(value) / 100.0)
    #     if self._delta_x == 0:
    #         self._dx_time_inc = 0.01
    #     else:
    #         self._dx_time_inc = 1.0 / (abs(value) / self._delta_x)
    #         self._delta_x = int(math.copysign(self._delta_x, value))
    #
    # @property
    # def dy(self):
    #     return self._delta_y
    #
    # @dy.setter
    # def dy(self, value):
    #     self._last_start_time = time.time()
    #     self._delta_y = math.ceil(abs(value) / 100.0)
    #     if self._delta_y == 0:
    #         self._dy_time_inc = 0.01
    #     else:
    #         self._dy_time_inc = 1.0 / (abs(value) / self._delta_y)
    #         self._delta_y = int(math.copysign(self._delta_y, value))

    @property
    def min_velocity(self):
        return self._min_velocity

    @min_velocity.setter
    def min_velocity(self, value):
        self._min_velocity = int(value)

    @property
    def max_velocity(self):
        return self._max_velocity

    @max_velocity.setter
    def max_velocity(self, value):
        self._max_velocity = int(value)

    @property
    def time_to_max(self):
        return self._time_to_max

    @time_to_max.setter
    def time_to_max(self, value):
        self._time_to_max = float(value)

    def start(self):
        """Starts the thread that will send motions when required."""
        self._last_start_time = time.time()
        if not self._is_running:
            self._thread = threading.Thread(target=self._control_loop)
            self._thread.start()

    def stop(self):
        """Stops the thread that sends motion events."""
        if self._thread.is_alive():
            self._is_running = False
            self._thread.join()

    def _control_loop(self):
        """Loop responsible for creating and sending mouse motion events."""
        self._is_running = True

        while self._is_running:
            # Only send motion events if they are non zero
            if self._delta_x == 0 and self._delta_y == 0 and self._acceleration == 0:
                time.sleep(0.01)
                continue

            delta_x = 0
            delta_y = 0

            cur_time = time.time()
            delta_t2 = (cur_time - self._last_start_time) ** 2
            if self._next_dx_update < cur_time:
                delta_x = min(
                    abs(self._delta_x) + 0.5 * self._acceleration * delta_t2,
                    self.max_speed
                )
                self._next_dx_update += self._dx_time_inc
                if self._next_dx_update < cur_time:
                    self._next_dx_update = cur_time + self._dx_time_inc
            if self._next_dy_update < cur_time:
                delta_y = min(
                    abs(self._delta_y) + 0.5 * self._acceleration * delta_t2,
                    self.max_speed
                )
                self._next_dy_update += self._dy_time_inc
                if self._next_dy_update < cur_time:
                    self._next_dy_update = cur_time + self._dy_time_inc

            #print(delta_x, self._next_dx_update, cur_time)

            # Send mouse motion event and then sleep
            if delta_x != 0 or delta_y != 0:
                mouse_relative_motion(
                    int(math.copysign(delta_x, self._delta_x)),
                    int(math.copysign(delta_y, self._delta_y))
                )

                # print(delta_x, delta_y)

            time.sleep(0.01)


class _MOUSEINPUT(ctypes.Structure):

    """Defines the MOUSEINPUT structure.

    https://msdn.microsoft.com/en-us/library/ms646273(v=VS.85).aspx
    """

    _fields_ = (
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG)),
    )


class _KEYBDINPUT(ctypes.Structure):

    """Defines the KEYBDINPUT structure.

    https://msdn.microsoft.com/en-us/library/ms646271(v=vs.85).aspx
    """

    _fields_ = (
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("wExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
    )


class _INPUTunion(ctypes.Union):

    """Defines the INPUT union type.

    https://msdn.microsoft.com/en-us/library/ms646270(v=vs.85).aspx
    """

    _fields_ = (
        ("mi", _MOUSEINPUT),
        ("ki", _KEYBDINPUT)
    )


class _INPUT(ctypes.Structure):

    """Defines the INPUT structure.

    https://msdn.microsoft.com/en-us/library/ms646270(v=vs.85).aspx
    """

    _fields_ = (
        ("type", ctypes.wintypes.DWORD),
        ("union", _INPUTunion)
    )


def mouse_relative_motion(dx, dy):
    _send_input(
        _mouse_input(MOUSEEVENTF_MOVE, dx, dy)
    )


def mouse_press(button):
    if button == MouseButton.Left:
        _send_input(_mouse_input(MOUSEEVENTF_LEFTDOWN))
    elif button == MouseButton.Right:
        _send_input(_mouse_input(MOUSEEVENTF_RIGHTDOWN))
    elif button == MouseButton.Middle:
        _send_input(_mouse_input(MOUSEEVENTF_MIDDLEDOWN))
    elif button == MouseButton.Back:
        _send_input(_mouse_input(MOUSEEVENTF_XDOWN, data=XBUTTON1))
    elif button == MouseButton.Forward:
        _send_input(_mouse_input(MOUSEEVENTF_XDOWN, data=XBUTTON2))


def mouse_release(button):
    if button == MouseButton.Left:
        _send_input(_mouse_input(MOUSEEVENTF_LEFTUP))
    elif button == MouseButton.Right:
        _send_input(_mouse_input(MOUSEEVENTF_RIGHTUP))
    elif button == MouseButton.Middle:
        _send_input(_mouse_input(MOUSEEVENTF_MIDDLEUP))
    elif button == MouseButton.Back:
        _send_input(_mouse_input(MOUSEEVENTF_XUP, data=XBUTTON1))
    elif button == MouseButton.Forward:
        _send_input(_mouse_input(MOUSEEVENTF_XUP, data=XBUTTON2))


def mouse_wheel(motion):
    _send_input(_mouse_input(MOUSEEVENTF_WHEEL, data=-motion*WHEEL_DELTA))


def _mouse_input(flags, dx=0, dy=0, data=0):
    return _INPUT(
        INPUT_MOUSE,
        _INPUTunion(mi=_MOUSEINPUT(dx, dy, data, flags, 0, None))
    )


def _send_input(*inputs):
    nInputs = len(inputs)
    LPINPUT = _INPUT * nInputs
    pInputs = LPINPUT(*inputs)
    cbSize = ctypes.c_int(ctypes.sizeof(_INPUT))

    return ctypes.windll.user32.SendInput(nInputs, pInputs, cbSize)
