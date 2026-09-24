# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import abc
import ctypes
import ctypes.wintypes
import logging
import math
import threading
import time
import uuid
from typing import TYPE_CHECKING

from gremlin.common import SingletonMetaclass
from gremlin.config import Configuration
from gremlin.types import MouseButton

if TYPE_CHECKING:
    from gremlin.event_handler import Event


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


# Cap on how many update steps can be compensated in a single update.
_MAX_TICKS_BEHIND = 5

# Identifies a single mouse motion contribution, by the action id and triggering event.
type MotionKey = tuple[uuid.UUID, Event]


class Vector2:
    def __init__(self, x: float, y: float) -> None:
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

    @classmethod
    def from_compass_direction(cls, degree: float) -> Vector2:
        """Converts a compass heading into a screen space direction.

        Args:
            degree: heading in degree, 0 being north and 90 being east

        Returns:
            Unit vector along the heading, with y growing downwards
        """
        return cls.from_angle(degree - 90.0)

    def magnitude(self) -> float:
        """Returns the length of this vector.

        Returns:
            Euclidean length of the vector
        """
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self) -> Vector2:
        """Returns a unit vector representation of the instance's direction.

        Returns:
            Unit length vector with the same direction
        """
        magnitude = self.magnitude()
        if magnitude < 0.00001:
            return Vector2(0, 0)
        return Vector2(self.x / magnitude, self.y / magnitude)

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2:
        return Vector2(self.x * scalar, self.y * scalar)

    def __str__(self) -> str:
        return f"[{self.x}, {self.y}]"


class MotionSource(abc.ABC):
    """Base class of all mouse motion contributions."""

    @abc.abstractmethod
    def velocity(self, delta_t: float) -> Vector2:
        """Returns the velocity valid for the next delta_t seconds.

        Advances any internal state by delta_t.

        Args:
            delta_t: duration in seconds the returned velocity applies to

        Returns:
            Velocity in pixels per second
        """


class ConstantVelocity(MotionSource):
    """Velocity dictated directly by the driving input, e.g. an axis."""

    def __init__(self, velocity: Vector2) -> None:
        """Creates a new instance.

        Args:
            velocity: velocity in pixels per second
        """
        self._velocity = velocity

    def set_velocity(self, velocity: Vector2) -> None:
        """Updates the velocity of this contribution.

        Args:
            velocity: new velocity in pixels per second
        """
        self._velocity = velocity

    def velocity(self, delta_t: float) -> Vector2:
        return self._velocity


class IncreasingVelocity(MotionSource):
    """Velocity ramping from min_speed up to max_speed along a direction."""

    def __init__(
        self,
        direction: Vector2,
        min_speed: float,
        max_speed: float,
        time_to_max_speed: float,
    ) -> None:
        """Creates a new instance.

        Args:
            direction: the direction of motion as a 2d vector
            min_speed: minimum speed in pixels per second
            max_speed: maximum speed in pixels per second
            time_to_max_speed: time to reach max_speed
        """
        self._direction = direction
        if max_speed < min_speed:
            min_speed, max_speed = max_speed, min_speed
        self._max_speed = max_speed
        self._speed = min_speed

        # Prevent numerical issues due to excessively small time_to_max_speed.
        if time_to_max_speed < 0.01:
            self._acceleration = 1e6
        else:
            self._acceleration = (max_speed - min_speed) / time_to_max_speed

    def set_direction(self, direction: Vector2) -> None:
        """Sets the direction of travel, retaining the speed reached so far.

        Args:
            direction: new direction of travel
        """
        self._direction = direction

    def velocity(self, delta_t: float) -> Vector2:
        # Return the velocity for this step, then increase velocity based on the
        # acceleration.
        current_velocity = self._direction * self._speed
        self._speed = min(self._max_speed, self._speed + self._acceleration * delta_t)
        return current_velocity


def _compute_temporal_integration_data(
    now: float, last_time: float, next_tick: float, interval: float
) -> tuple[float, float]:
    """Returns the integration step and the time of the next tick.

    Stalls are prevented from teleporting the cursor by clamping the amount of time
    that can be integrated and by resetting the next tick deadline.

    Args:
        now: current time
        last_time: time at which the previous step was performed
        next_tick: time the current tick was scheduled for
        interval: duration between two ticks

    Returns:
        Duration to integrate over and the time of the next tick
    """
    delta_t = min(now - last_time, _MAX_TICKS_BEHIND * interval)
    return delta_t, max(next_tick + interval, now)


class MouseMotionManager(metaclass=SingletonMetaclass):
    """Combines all mouse motion contributions into a single cursor motion.

    Every contribution, from different inputs, is registered under a key and provides
    velocity data which is summed up on each tick.
    """

    def __init__(self) -> None:
        """Creates a new instance."""
        self._lock = threading.Lock()
        self._sources: dict[MotionKey, MotionSource] = {}
        self._residual = Vector2(0.0, 0.0)
        self._has_sources = threading.Event()
        self._tick_interval = 0.01

        self._is_running = False
        self._thread: threading.Thread | None = None

    def set_velocity(self, key: MotionKey, velocity: Vector2) -> None:
        """Sets a directly driven motion contribution.

        A velocity of zero removes the contribution, which keeps the registry clean of
        stale entries.

        Args:
            key: identifier of the contribution
            velocity: velocity in pixels per second
        """
        if velocity.magnitude() < 1e-6:
            self.clear(key)
            return

        with self._lock:
            self._sources[key] = ConstantVelocity(velocity)
            self._has_sources.set()

    def set_accelerated_motion(
        self,
        key: MotionKey,
        direction: Vector2,
        min_speed: float,
        max_speed: float,
        time_to_max_speed: float,
    ) -> None:
        """Creates or redirects an accelerating motion contribution.

        An existing contribution retains the speed it has ramped up to and only changes
        direction.

        Args:
            key: identifier of the contribution
            direction: direction of travel as a 2d vector
            min_speed: minimum speed in pixels per second
            max_speed: maximum speed in pixels per second
            time_to_max_speed: time to reach max_speed
        """
        with self._lock:
            source = self._sources.get(key)
            if isinstance(source, IncreasingVelocity):
                source.set_direction(direction)
            else:
                self._sources[key] = IncreasingVelocity(
                    direction, min_speed, max_speed, time_to_max_speed
                )
            self._has_sources.set()

    def clear(self, key: MotionKey) -> None:
        """Removes the motion contribution of the given key.

        Args:
            key: identifier of the contribution to remove
        """
        with self._lock:
            self._sources.pop(key, None)
            if not self._sources:
                self._go_idle()

    def reset(self) -> None:
        """Drops all motion contributions."""
        with self._lock:
            self._sources.clear()
            self._go_idle()

    def start(self) -> None:
        """Starts the thread that will send motions at regular intervals when set."""
        if self._thread is not None and self._thread.is_alive():
            logging.getLogger("system").warning(
                "MouseMotionManager already running, ignoring start request."
            )
            return

        self.reset()
        self._tick_interval = 1.0 / max(
            1, Configuration().value("action", "map-to-mouse", "update-rate")
        )
        self._is_running = True
        self._thread = threading.Thread(target=self._control_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the thread that sends motion events."""
        self._is_running = False
        # Wake an idle loop so that it can observe the flag.
        self._has_sources.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()
        self._thread = None
        self.reset()

    def _go_idle(self) -> None:
        """Suspends motion generation, discarding the sub pixel remainder.

        The caller is assumed to hold the lock.
        """
        self._residual = Vector2(0.0, 0.0)
        self._has_sources.clear()

    def _step(self, delta_t: float) -> tuple[int, int]:
        """Returns the cursor motion accumulated over the given duration.

        Args:
            delta_t: duration in seconds to integrate the contributions over

        Returns:
            Whole pixel motion along the x and y axis
        """
        total = Vector2(0.0, 0.0)
        with self._lock:
            for source in self._sources.values():
                total += source.velocity(delta_t)

            self._residual += total * delta_t
            fraction_x, pixels_x = math.modf(self._residual.x)
            fraction_y, pixels_y = math.modf(self._residual.y)
            self._residual = Vector2(fraction_x, fraction_y)

        return int(pixels_x), int(pixels_y)

    def _control_loop(self) -> None:
        """Loop responsible for creating and sending mouse motion events."""
        last_time = next_tick = time.perf_counter()

        while self._is_running:
            # Wait for an event to wake up instead of spinning.
            if not self._has_sources.is_set():
                self._has_sources.wait()
                last_time = next_tick = time.perf_counter()
                continue

            now = time.perf_counter()
            delta_t, next_tick = _compute_temporal_integration_data(
                now, last_time, next_tick, self._tick_interval
            )
            last_time = now

            delta_x, delta_y = self._step(delta_t)
            if delta_x or delta_y:
                mouse_relative_motion(delta_x, delta_y)

            time.sleep(max(0.0, next_tick - time.perf_counter()))


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
        ("wExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG)),
    )


class _INPUTunion(ctypes.Union):
    """Defines the INPUT union type.

    https://msdn.microsoft.com/en-us/library/ms646270(v=vs.85).aspx
    """

    _fields_ = (("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT))


class _INPUT(ctypes.Structure):
    """Defines the INPUT structure.

    https://msdn.microsoft.com/en-us/library/ms646270(v=vs.85).aspx
    """

    _fields_ = (("type", ctypes.wintypes.DWORD), ("union", _INPUTunion))


def mouse_relative_motion(dx: int, dy: int) -> None:
    _send_input(_mouse_input(MOUSEEVENTF_MOVE, dx, dy))


def mouse_press(button: MouseButton) -> None:
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


def mouse_release(button: MouseButton) -> None:
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


def mouse_wheel(motion: int) -> None:
    _send_input(_mouse_input(MOUSEEVENTF_WHEEL, data=-motion * WHEEL_DELTA))


def _mouse_input(flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> _INPUT:
    return _INPUT(
        INPUT_MOUSE, _INPUTunion(mi=_MOUSEINPUT(dx, dy, data, flags, 0, None))
    )


def _send_input(*inputs: _INPUT) -> int:
    nInputs = len(inputs)
    LPINPUT = _INPUT * nInputs
    pInputs = LPINPUT(*inputs)
    cbSize = ctypes.c_int(ctypes.sizeof(_INPUT))

    return ctypes.windll.user32.SendInput(nInputs, pInputs, cbSize)
