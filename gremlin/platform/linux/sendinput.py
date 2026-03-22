# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Linux mouse injection — evdev.UInput-based.

Vector2, MotionType, MouseMotion, FixedMouseMotion, AcceleratedMouseMotion are
pure Python and fully functional on all platforms.
"""

from __future__ import annotations

import enum
import math
import threading
import time
from typing import TYPE_CHECKING

import evdev
from evdev import ecodes

from gremlin.common import SingletonDecorator
from gremlin.types import MouseButton

if TYPE_CHECKING:
    from gremlin.event_handler import Event


# ---------------------------------------------------------------------------
# Singleton UInput mouse device (lazy)
# ---------------------------------------------------------------------------

_ui_mouse: evdev.UInput | None = None


def _get_mouse() -> evdev.UInput:
    global _ui_mouse
    if _ui_mouse is None:
        _ui_mouse = evdev.UInput(
            events={
                ecodes.EV_KEY: [
                    ecodes.BTN_LEFT,
                    ecodes.BTN_RIGHT,
                    ecodes.BTN_MIDDLE,
                    ecodes.BTN_SIDE,
                    ecodes.BTN_EXTRA,
                ],
                ecodes.EV_REL: [
                    ecodes.REL_X,
                    ecodes.REL_Y,
                    ecodes.REL_WHEEL,
                ],
            },
            name="JoystickGremlin Mouse",
        )
    return _ui_mouse


# MouseButton → evdev button code
_BUTTON_TO_EVDEV: dict[MouseButton, int] = {
    MouseButton.Left:    ecodes.BTN_LEFT,
    MouseButton.Right:   ecodes.BTN_RIGHT,
    MouseButton.Middle:  ecodes.BTN_MIDDLE,
    MouseButton.Forward: ecodes.BTN_EXTRA,
    MouseButton.Back:    ecodes.BTN_SIDE,
}


# ---------------------------------------------------------------------------
# Pure-Python helpers (identical on all platforms)
# ---------------------------------------------------------------------------

class Vector2:

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @classmethod
    def from_angle(cls, angle: float) -> Vector2:
        angle_rad = math.radians(angle)
        return Vector2(math.cos(angle_rad), math.sin(angle_rad))

    def normalize(self) -> Vector2:
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
    Fixed = 1,
    Accelerated = 2


class MouseMotion:

    delta_t = 0.01

    def __init__(self, dx: float = 0, dy: float = 0):
        self.dx = dx
        self.dy = dy
        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)
        self._dx_timestamp = 0
        self._dy_timestamp = 0

    def __call__(self) -> tuple[int, int]:
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
        delta = 0.0 if abs(delta) < 1e-6 else delta
        tick_value = math.ceil(abs(delta) / 100.0)
        if tick_value == 0:
            tick_time = MouseMotion.delta_t
        else:
            tick_time = 1.0 / (abs(delta) / tick_value)
            tick_value = int(math.copysign(tick_value, delta))
        return tick_value, tick_time


class FixedMouseMotion(MouseMotion):

    def __init__(self, dx: float, dy: float):
        super().__init__(dx, dy)

    def set_dx(self, value: float) -> None:
        self.dx = value
        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)

    def set_dy(self, value: float) -> None:
        self.dy = value
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)


class AcceleratedMouseMotion(MouseMotion):

    def __init__(
            self,
            direction: Vector2,
            min_speed: float,
            max_speed: float,
            time_to_max_speed: float
    ):
        super().__init__()
        self.direction = direction
        self.min_velocity = min_speed
        self.max_velocity = max_speed
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
        self.direction = direction
        self.dx = self.direction.x * self.current_velocity
        self.dy = self.direction.y * self.current_velocity
        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)

    def __call__(self) -> tuple[float, float]:
        dx, dy = super().__call__()
        self.current_velocity = min(
            self.max_velocity,
            self.current_velocity + self.acceleration * MouseMotion.delta_t
        )
        self.dx = self.direction.x * self.current_velocity
        self.dy = self.direction.y * self.current_velocity
        self._tick_dx_value, self._tick_dx_time = self._compute_values(self.dx)
        self._tick_dy_value, self._tick_dy_time = self._compute_values(self.dy)
        return dx, dy


# ---------------------------------------------------------------------------
# MouseController (drives continuous motion via a background thread)
# ---------------------------------------------------------------------------

@SingletonDecorator
class MouseController:

    def __init__(self):
        self._motion_type = MotionType.Fixed
        self._delta_generator = FixedMouseMotion(0, 0)
        self._motion_commands = {}
        self._is_running = False
        self._thread = threading.Thread(target=self._control_loop)

    def set_absolute_motion(self, dx: int | None = None, dy: int | None = None) -> None:
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
        direction -= 90
        if self._motion_type == MotionType.Accelerated:
            self._motion_commands[event] = Vector2.from_angle(direction)
            self._delta_generator.set_direction(self._compute_direction())
        else:
            self._motion_type = MotionType.Accelerated
            self._motion_commands = {event: Vector2.from_angle(direction)}
            self._delta_generator = AcceleratedMouseMotion(
                self._compute_direction(), min_speed, max_speed, time_to_max_speed
            )

    def remove_accelerated_motion(self, event: Event) -> None:
        if event in self._motion_commands:
            del self._motion_commands[event]
            if len(self._motion_commands) == 0:
                self.set_absolute_motion(0, 0)
            else:
                self._delta_generator.set_direction(self._compute_direction())

    def start(self) -> None:
        if not self._is_running:
            self._thread = threading.Thread(target=self._control_loop)
            self._thread.start()

    def stop(self) -> None:
        if self._thread.is_alive():
            self._is_running = False
            self._thread.join()

    def _control_loop(self) -> None:
        self._is_running = True
        while self._is_running:
            dx, dy = self._delta_generator()
            if dx != 0 or dy != 0:
                mouse_relative_motion(int(dx), int(dy))
            time.sleep(0.01)

    def _compute_direction(self) -> Vector2:
        sum_vec = Vector2(0, 0)
        for v in self._motion_commands.values():
            sum_vec += v
        return sum_vec.normalize()


# ---------------------------------------------------------------------------
# Mouse injection functions
# ---------------------------------------------------------------------------

def mouse_relative_motion(dx: int, dy: int) -> None:
    ui = _get_mouse()
    if dx != 0:
        ui.write(ecodes.EV_REL, ecodes.REL_X, dx)
    if dy != 0:
        ui.write(ecodes.EV_REL, ecodes.REL_Y, dy)
    ui.syn()


def mouse_press(button: MouseButton) -> None:
    evdev_btn = _BUTTON_TO_EVDEV.get(button)
    if evdev_btn is None:
        return
    ui = _get_mouse()
    ui.write(ecodes.EV_KEY, evdev_btn, 1)
    ui.syn()


def mouse_release(button: MouseButton) -> None:
    evdev_btn = _BUTTON_TO_EVDEV.get(button)
    if evdev_btn is None:
        return
    ui = _get_mouse()
    ui.write(ecodes.EV_KEY, evdev_btn, 0)
    ui.syn()


def mouse_wheel(motion: int) -> None:
    ui = _get_mouse()
    ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, motion)
    ui.syn()
