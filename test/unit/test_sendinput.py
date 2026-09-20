# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import math
import uuid
from collections.abc import Iterator
from unittest import mock

import pytest

from gremlin.sendinput import (
    _MAX_TICKS_BEHIND,
    MotionKey,
    MouseMotionManager,
    Vector2,
    _compute_temporal_integration_data,
)

_TICK = 0.01


def _key(identifier: int = 0) -> MotionKey:
    """Returns a motion key that is unique for the given identifier."""
    return (uuid.UUID(int=identifier), mock.MagicMock())


def _travel(
    manager: MouseMotionManager, duration: float, delta_t: float = _TICK
) -> tuple[int, int]:
    """Returns the total motion generated over the given duration."""
    total_x = 0
    total_y = 0
    for _ in range(round(duration / delta_t)):
        delta_x, delta_y = manager._step(delta_t)
        total_x += delta_x
        total_y += delta_y
    return total_x, total_y


@pytest.fixture(autouse=True)
def manager() -> Iterator[MouseMotionManager]:
    """Provides a motion manager isolated from other tests.

    The manager is a process wide singleton, so its state has to be dropped
    around every test.
    """
    instance = MouseMotionManager()
    instance.reset()
    yield instance
    instance.reset()


@pytest.mark.parametrize(
    ("degree", "expected"),
    [
        (0.0, (0.0, -1.0)),
        (90.0, (1.0, 0.0)),
        (180.0, (0.0, 1.0)),
        (270.0, (-1.0, 0.0)),
        (45.0, (0.70710678, -0.70710678)),
    ],
)
def test_from_compass_direction(degree: float, expected: tuple[float, float]) -> None:
    vector = Vector2.from_compass_direction(degree)

    assert vector.x == pytest.approx(expected[0], abs=1e-6)
    assert vector.y == pytest.approx(expected[1], abs=1e-6)


def test_sub_pixel_velocity_accumulates(manager: MouseMotionManager) -> None:
    """Speeds below one pixel per tick must still move the cursor."""
    manager.set_velocity(_key(), Vector2(5.0, 0.0))

    steps = [manager._step(_TICK)[0] for _ in range(200)]

    assert sum(steps) == pytest.approx(10, abs=1)
    assert max(abs(step) for step in steps) <= 1


def test_sources_sum(manager: MouseMotionManager) -> None:
    manager.set_accelerated_motion(_key(1), Vector2(0.0, -1.0), 100.0, 100.0, 0.0)
    manager.set_accelerated_motion(_key(2), Vector2(1.0, 0.0), 100.0, 100.0, 0.0)

    delta_x, delta_y = _travel(manager, 1.0)

    assert math.hypot(delta_x, delta_y) == pytest.approx(141, abs=2)


def test_updating_one_source_leaves_the_other_intact(
    manager: MouseMotionManager,
) -> None:
    horizontal_key = _key(1)
    manager.set_velocity(horizontal_key, Vector2(100.0, 0.0))
    manager.set_velocity(_key(2), Vector2(0.0, 200.0))

    manager.set_velocity(horizontal_key, Vector2(50.0, 0.0))

    delta_x, delta_y = _travel(manager, 1.0)
    assert delta_x == pytest.approx(50, abs=1)
    assert delta_y == pytest.approx(200, abs=1)


def test_zero_velocity_removes_source(manager: MouseMotionManager) -> None:
    key = _key()
    manager.set_velocity(key, Vector2(100.0, 0.0))
    manager.set_velocity(key, Vector2(0.0, 0.0))

    assert manager._sources == {}


def test_clear_only_removes_the_given_source(manager: MouseMotionManager) -> None:
    constant_key = _key(1)
    manager.set_velocity(constant_key, Vector2(100.0, 0.0))
    manager.set_accelerated_motion(_key(2), Vector2(0.0, -1.0), 100.0, 100.0, 0.0)

    manager.clear(constant_key)

    delta_x, delta_y = _travel(manager, 1.0)
    assert delta_x == 0
    assert delta_y < 0


def test_last_clear_zeroes_residual_and_idles(manager: MouseMotionManager) -> None:
    key = _key()
    manager.set_velocity(key, Vector2(137.0, 0.0))
    manager._step(_TICK)
    assert manager._has_sources.is_set()
    assert manager._residual.x != 0.0

    manager.clear(key)

    assert manager._residual.x == 0.0
    assert not manager._has_sources.is_set()


def test_ramp_reaches_maximum_speed(manager: MouseMotionManager) -> None:
    manager.set_accelerated_motion(_key(), Vector2(1.0, 0.0), 0.0, 100.0, 1.0)

    first_second = _travel(manager, 1.0)[0]
    second_second = _travel(manager, 1.0)[0]

    assert first_second == pytest.approx(50, abs=3)
    assert second_second == pytest.approx(100, abs=3)


def test_redirect_preserves_ramped_speed(manager: MouseMotionManager) -> None:
    key = _key()
    manager.set_accelerated_motion(key, Vector2(0.0, -1.0), 0.0, 1000.0, 1.0)
    _travel(manager, 0.5)
    speed_before = manager._sources[key].velocity(0.0).magnitude()

    manager.set_accelerated_motion(key, Vector2(1.0, 0.0), 0.0, 1000.0, 1.0)

    source = manager._sources[key]
    assert source.velocity(0.0).magnitude() == pytest.approx(speed_before)
    assert source.velocity(0.0).x > 0


def test_start_drops_state_and_reads_update_rate(manager: MouseMotionManager) -> None:
    manager.set_velocity(_key(), Vector2(100.0, 0.0))

    with (
        mock.patch("threading.Thread"),
        mock.patch("gremlin.sendinput.Configuration") as configuration,
    ):
        configuration.return_value.value.return_value = 200
        manager.start()

    assert manager._sources == {}
    assert manager._tick_interval == pytest.approx(1.0 / 200)


def test_compute_temporal_integration_data_normal_tick() -> None:
    delta_t, next_tick = _compute_temporal_integration_data(1.01, 1.0, 1.01, _TICK)

    assert delta_t == pytest.approx(0.01)
    assert next_tick == pytest.approx(1.02)


def test_compute_temporal_integration_data_clamps_and_resyncs_after_stall() -> None:
    delta_t, next_tick = _compute_temporal_integration_data(5.0, 1.0, 1.01, _TICK)

    assert delta_t == pytest.approx(_MAX_TICKS_BEHIND * _TICK)
    assert next_tick == pytest.approx(5.0)
