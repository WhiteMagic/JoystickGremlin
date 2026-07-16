# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")


from gremlin.spline import CubicBezierSpline


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


def test_cubic_bezier_spline_curve() -> None:
    cps = [(-1, -1), (-1, 1), (-1, 1), (1, 1)]
    s = CubicBezierSpline(cps)

    assert s(-1.0) == -1.0
    assert s(1.0) == 1.0
    r = cbs(0.5, *cps)
    assert s(r[0]) == r[1]
    r = cbs(0.91, *cps)
    assert s(r[0]) == r[1]
