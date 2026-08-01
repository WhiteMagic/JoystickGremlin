# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pytest

from gremlin.spline import MAX_HANDLE_SLOPE, CubicBezierSpline


def cbs(
    t: float,
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
) -> tuple[float, float]:
    t2 = t * t
    t3 = t2 * t
    mt = 1 - t
    mt2 = mt * mt
    mt3 = mt2 * mt

    def compute(w0: float, w1: float, w2: float, w3: float) -> float:
        return w0 * mt3 + 3 * w1 * mt2 * t + 3 * w2 * mt * t2 + w3 * t3

    x = compute(p0[0], p1[0], p2[0], p3[0])
    y = compute(p0[1], p1[1], p2[1], p3[1])
    return x, y


def test_cubic_bezier_spline_default() -> None:

    checks = [
        # Control points
        ((-1.0, -1.0), -1.0),
        ((1.0, 1.0), 1.0),
        # Interpolation
        ((-0.5, -0.5), -0.5),
        ((0.0, 0.0), 0.0),
        ((0.25, 0.25), 0.25),
        # Out of bounds
        ((-1.5, -1.5), -1.0),
        ((1.5, 1.5), 1.0),
    ]

    # Default initialization
    s = CubicBezierSpline()
    for c in checks:
        assert s(c[0][0]) == c[1]

    # Manual initialization of default values
    s = CubicBezierSpline([(-1, -1), (-0.95, -0.95), (0.95, 0.95), (1, 1)])
    for c in checks:
        assert s(c[0][0]) == c[1]


def test_cubic_bezier_spline_handle_geometry() -> None:
    s = CubicBezierSpline()
    s.add_control_point(0.0, -0.2)

    # Handles are free by default, retaining the previous behavior.
    assert [cp.symmetric_handles for cp in s.control_points()] == [False] * 3

    # Slope and length survive a round trip, with the left handle pointing at
    # smaller and the right handle at larger x values.
    for slope, length in [(0.5, 0.3), (2.0, 0.1), (0.0, 0.25), (-1.5, 0.4)]:
        for side in ["left", "right"]:
            s.set_handle_geometry(1, side, slope, length)
            assert s.handle_geometry(1, side) == pytest.approx((slope, length))
            dx = s.handle(1, side).x - s.control_points()[1].center.x
            assert (dx < 0) if side == "left" else (dx > 0)

    # An end point only has the one handle, the missing one is a no-op.
    assert s.handle(0, "left") is None
    assert s.handle_geometry(0, "left") == (0.0, 0.0)
    s.set_handle_geometry(0, "left", 1.0, 0.5)
    assert s.handle_geometry(0, "left") == (0.0, 0.0)

    # A vertical handle has no finite slope, but must not blow up either.
    cp = s.control_points()[1]
    cp.handle_right.x = cp.center.x
    cp.handle_right.y = cp.center.y + 0.1
    slope, length = s.handle_geometry(1, "right")
    assert slope == MAX_HANDLE_SLOPE
    assert length == pytest.approx(0.1)


def test_cubic_bezier_spline_symmetric_handles() -> None:
    s = CubicBezierSpline()
    s.add_control_point(0.0, -0.2)
    s.set_handle_geometry(1, "right", 0.4, 0.2)
    s.set_symmetric_handles(1, True)

    cp = s.control_points()[1]
    assert cp.symmetric_handles
    assert s.handle_geometry(1, "left") == pytest.approx((0.4, 0.2))

    # Moving one handle drags the other one along.
    s.set_handle_geometry(1, "left", 0.8, 0.35)
    assert s.handle_geometry(1, "right") == pytest.approx((0.8, 0.35))
    assert cp.handle_right.x == pytest.approx(2 * cp.center.x - cp.handle_left.x)
    assert cp.handle_right.y == pytest.approx(2 * cp.center.y - cp.handle_left.y)

    # The curve now leaves the control point at the same slope on both sides.
    delta = 0.002
    incoming = (s(cp.center.x) - s(cp.center.x - delta)) / delta
    outgoing = (s(cp.center.x + delta) - s(cp.center.x)) / delta
    assert incoming == pytest.approx(outgoing, abs=0.05)
    assert incoming == pytest.approx(0.8, abs=0.05)

    # Symmetry is retained when the control point itself is moved.
    for point in [cp.center, cp.handle_left, cp.handle_right]:
        point.x += 0.25
        point.y += 0.1
    s.fit()
    assert s.handle_geometry(1, "left") == pytest.approx((0.8, 0.35))
    assert s.handle_geometry(1, "right") == pytest.approx((0.8, 0.35))

    # Turning symmetry off leaves the handles where they are.
    before = (s.handle_geometry(1, "left"), s.handle_geometry(1, "right"))
    s.set_symmetric_handles(1, False)
    assert not s.control_points()[1].symmetric_handles
    assert (s.handle_geometry(1, "left"), s.handle_geometry(1, "right")) == before


def test_cubic_bezier_spline_curve() -> None:
    cps = [(-1, -1), (-1, 1), (-1, 1), (1, 1)]
    s = CubicBezierSpline(cps)

    assert s(-1.0) == -1.0
    assert s(1.0) == 1.0
    r = cbs(0.5, *cps)
    assert s(r[0]) == r[1]
    r = cbs(0.91, *cps)
    assert s(r[0]) == r[1]
