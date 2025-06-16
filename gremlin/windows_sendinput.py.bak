# -*- coding: utf-8; -*-

# Copyright (C) 2017 Lionel Ott
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


from __future__ import annotations

import ctypes
import ctypes.wintypes
import enum
import math
import threading
import time

from gremlin.common import SingletonDecorator
from gremlin.event_handler import Event
from gremlin.types import MouseButton


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


class Vector2:

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @classmethod
    def from_angle(cls, angle: float) -> Vector2:
        """Converts an angle in degree into a 2D vector.

        Args:
            angle: angular direction in degree

        Returns:
            2D vector representing the direction
        """
        angle_rad = math.radians(angle)
        return Vector2(math.cos(angle_rad), math.sin(angle_rad))

    def normalize(self) -> Vector2:
        """Returns a unit vector representation of the instance's direction.

        Returns:
            Unit length vector with the same direction
        """
        magnitude = math.sqrt(self.x ** 2 + self.y ** 2)
        if magnitude < 0.00001:
            return Vector2(0, 0)
        return Vector2(self.x / magnitude, self.y / magnitude)

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def __str__(self) -> str:
        return f"[{self.x}, {self.y}]"


class MotionType(enum.Enum):

    """Mouse motion types available."""

    Fixed = 1,
    Accelerated = 2


class MouseMotion:

    """Base class of all mouse motion behaviors."""

    # Time step between calls
    delta_t = 0.01

    def __init__(self, dx: float=0, dy: float=0):
        """Creates a new instance.

        Args:
            dx: motion along the x-axis in pixels per second
            dy: motion along the y-axis in pixels per second
        """
        self.dx = dx
        self.dy = dy

        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)

        self._dx_timestamp = 0
        self._dy_timestamp = 0

    def __call__(self) -> tuple[int, int]:
        """Returns the change in x and y for this point in time.

        Returns:
            The change in (dx, dy) for this time point
        """
        if self._tick_dx_value == 0 and self._tick_dy_value == 0:
            return 0, 0

        delta_x = 0
        delta_y = 0

        cur_time = time.time()
        if self._dx_timestamp < cur_time:
            delta_x = self._tick_dx_value
            self._dx_timestamp = cur_time + self._tick_dx_time
        if self._dy_timestamp < cur_time:
            delta_y = self._tick_dy_value
            self._dy_timestamp = cur_time + self._tick_dy_time

        return delta_x, delta_y

    def _compute_values(self, delta: float) -> tuple[int, float]:
        """Computes discretization values to send integer motions.

        Args:
            delta: the amount of change in pixels per second to discretize for

        Returns:
            Discretization information in terms of cursor movement amount
            and movement interval
        """
        delta = 0.0 if abs(delta) < 1e-6 else delta
        tick_value = math.ceil(abs(delta) / 100.0)
        if tick_value == 0:
            tick_time = MouseMotion.delta_t
        else:
            tick_time = 1.0 / (abs(delta) / tick_value)
            tick_value = int(math.copysign(tick_value, delta))

        return tick_value, tick_time


class FixedMouseMotion(MouseMotion):

    """Motion generation with fixed speed."""

    def __init__(self, dx: float, dy: float):
        """Creates a new instance.

        Args:
            dx: motion along the x-axis in pixels per second
            dy: motion along the y-axis in pixels per second
        """
        super().__init__(dx, dy)

    def set_dx(self, value: float) -> None:
        """Updates the x velocity.

        Args:
            value: speed in pixels per second along the x-axis
        """
        self.dx = value
        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)

    def set_dy(self, value: float) -> None:
        """Updates the y velocity.

        Args:
            value speed in pixels per second along the y-axis
        """
        self.dy = value
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)


class AcceleratedMouseMotion(MouseMotion):

    """Motion generation with acceleration over time."""

    def __init__(
            self,
            direction: Vector2,
            min_speed: float,
            max_speed: float,
            time_to_max_speed: float
    ):
        """Creates a new instance.

        Args:
            direction: the direction of motion as a 2d vector
            min_speed: minimum speed in pixels per second
            max_speed: maximum speed in pixels per second
            time_to_max_speed: time to reach max_speed
        """
        super().__init__()

        self.direction = direction
        self.min_velocity = min_speed
        self.max_velocity = max_speed

        # Make sure we don't get numerical issues with acceleration computation
        if time_to_max_speed < 0.001:
            self.acceleration = 1e6
        else:
            self.acceleration = (max_speed - min_speed) / time_to_max_speed

        self.current_velocity = self.min_velocity
        self.dx = self.direction.x * self.current_velocity
        self.dy = self.direction.y * self.current_velocity
        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)

    def set_direction(self, direction: Vector2) -> None:
        """Sets the direction for which to emit position changes.

        Args:
            direction: new direction of travel
        """
        self.direction = direction# - 90
        self.dx = self.direction.x * self.current_velocity
        self.dy = self.direction.y * self.current_velocity
        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)


    def __call__(self) -> tuple[float, float]:
        """Returns the change in x and y for this point in time.

        Returns:
            The change in (dx, dy) for this time point
        """
        # Get values to return using current integration step values
        dx, dy = super().__call__()

        # Apply acceleration to obtain next integration step values
        self.current_velocity = min(
            self.max_velocity,
            self.current_velocity + self.acceleration * MouseMotion.delta_t
        )
        self.dx = self.direction.x * self.current_velocity
        self.dy = self.direction.y * self.current_velocity
        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)

        # Return cached values
        return dx, dy


@SingletonDecorator
class MouseController:

    """Centralizes sending mouse events in an organized manner."""

    def __init__(self):
        """Creates a new instance."""
        self._motion_type = MotionType.Fixed
        self._delta_generator = FixedMouseMotion(0, 0)
        self._motion_commands = {}

        self._is_running = False
        self._thread = threading.Thread(target=self._control_loop)

    def set_absolute_motion(
            self,
            dx: int|None=None,
            dy: int|None=None
    ) -> None:
        """Configures a motion using absolute velocities.

        If dx / dy are set to None their values will not be updated.

        Args:
            dx: velocity along the x-axis in pixels per second
            dy: velocity along the y-axis in pixels per second
        """
        if self._motion_type == MotionType.Fixed:
            if dx is not None:
                self._delta_generator.set_dx(dx)
            if dy is not None:
                self._delta_generator.set_dy(dy)
        else:
            self._motion_type = MotionType.Fixed
            self._delta_generator = FixedMouseMotion(
                dx if dx is not None else 0,
                dy if dy is not None else 0
            )

    def add_accelerated_motion(
            self,
            direction: int,
            min_speed: int,
            max_speed: int,
            time_to_max_speed: float,
            event: Event
    ) -> None:
        """Configures a motion using acceleration.

        Args:
            direction: the direction of motion in degree
            min_speed: minimum speed in pixels per second
            max_speed: maximum speed in pixels per second
            time_to_max_speed: time to reach max_speed
            event: the source event of the given accelerated motion
        """
        # Rotate by 90 deggree to line up with X, Y coordinates
        direction -= 90
        if self._motion_type == MotionType.Accelerated:
            self._motion_commands[event] = Vector2.from_angle(direction)
            self._delta_generator.set_direction(self._compute_direction())
        else:
            self._motion_type = MotionType.Accelerated
            self._motion_commands = {
                event: Vector2.from_angle(direction)
            }
            self._delta_generator = AcceleratedMouseMotion(
                self._compute_direction(),
                min_speed,
                max_speed,
                time_to_max_speed
            )

    def remove_accelerated_motion(self, event: Event) -> None:
        """Removes the motion information associated with a given event.

        Args:
            event: Event identifying the direction to remove
        """
        if event in self._motion_commands:
            del self._motion_commands[event]
            if len(self._motion_commands) == 0:
                self.set_absolute_motion(0, 0)
            else:
                self._delta_generator.set_direction(self._compute_direction())

    def start(self) -> None:
        """Starts the thread that will send motions when required."""
        if not self._is_running:
            self._thread = threading.Thread(target=self._control_loop)
            self._thread.start()

    def stop(self) -> None:
        """Stops the thread that sends motion events."""
        if self._thread.is_alive():
            self._is_running = False
            self._thread.join()

    def _control_loop(self) -> None:
        """Loop responsible for creating and sending mouse motion events."""
        self._is_running = True

        while self._is_running:
            dx, dy = self._delta_generator()
            if dx != 0 or dy != 0:
                mouse_relative_motion(int(dx), int(dy))
            time.sleep(0.01)

    def _compute_direction(self) -> Vector2:
        """Computes the average direction of all the motion commands.

        Returns:
            Average motion vector derived from the list of directions
        """
        sum_vec = Vector2(0, 0)
        for v in self._motion_commands.values():
            sum_vec += v
        return sum_vec.normalize()


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


def mouse_relative_motion(dx: int, dy: int):
    _send_input(
        _mouse_input(MOUSEEVENTF_MOVE, dx, dy)
    )


def mouse_press(button: MouseButton):
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


def mouse_release(button: MouseButton):
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


def mouse_wheel(motion: int):
    _send_input(_mouse_input(MOUSEEVENTF_WHEEL, data=-motion*WHEEL_DELTA))


def _mouse_input(flags, dx: int=0, dy: int=0, data: int=0):
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
