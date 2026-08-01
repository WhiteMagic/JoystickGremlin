# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import abc
import math

from gremlin import util
from gremlin.types import Point2D

# Typing alias
type CoordinateList = list[tuple[float, float]]

# Slope reported for a handle that is (near) vertical. Such a handle is a
# degenerate configuration for a response curve, but it has to map onto a
# finite number for the UI to be able to display it.
MAX_HANDLE_SLOPE = 1000.0


class AbstractCurve(abc.ABC):
    """Base class for all curves, providing a common interface."""

    def __init__(self, points: CoordinateList | None = None) -> None:
        self._is_symmetric = False
        self._process_points(points if points is not None else self._default_points())
        self.fit()

    @property
    def is_symmetric(self) -> bool:
        return self._is_symmetric

    @is_symmetric.setter
    def is_symmetric(self, value: bool) -> None:
        if value != self._is_symmetric:
            self._is_symmetric = value
            if value:
                self._enforce_symmetry()
            self.fit()

    @abc.abstractmethod
    def control_points(self) -> list[Point2D | CubicBezierSpline.ControlPoint]:
        """Returns the list of all control points.

        Returns:
            List of all control points.
        """
        pass

    @abc.abstractmethod
    def add_control_point(self, x: float, y: float) -> None:
        """Adds a new control point to the curve.

        This also takes care of adding additional points if the curve is in
        the symmetric mode.

        Args:
            x: x-coordinate of the control point (will be clamped).
            y: y-coordinate of the control point (will be clamped).
        """
        pass

    def remove_control_point(self, index: int) -> None:
        """Removes an existing control point from the curve.

        Args:
            index: index of the control point to remove
        """
        points = self.control_points()
        # Removing of edge points or invalid indices is not permitted.
        if not (0 < index < len(points) - 1):
            return

        if self.is_symmetric:
            # Cannot remove the center point in symmetric mode.
            if math.floor(len(points) / 2) == index:
                return
            else:
                # Obtain indices to remove and order them.
                idx1 = index
                idx2 = len(points) - index - 1
                if idx1 > idx2:
                    idx1, idx2 = idx2, idx1
                # Remove points in order and account for the index shift.
                del points[idx1]
                del points[idx2 - 1]
        else:
            del points[index]
        self.fit()

    def set_control_point(self, x: float, y: float, idx: int) -> None:
        """Sets a new position for an existing control point.

        Args:
            x: x-coordinate of the control point (will be clamped).
            y: y-coordinate of the control point (will be clamped).
            idx: index of the control point to set
        """
        x = util.clamp_analog_axis(x)
        y = util.clamp_analog_axis(y)
        points = self.control_points()
        points[idx].x = x
        points[idx].y = y
        if self.is_symmetric:
            len_points = len(points)
            assert len_points % 2, "Symmetric curves must have odd number of points"
            points[len_points - idx - 1].x = -x
            points[len_points - idx - 1].y = -y
        self.fit()

    @abc.abstractmethod
    def invert(self) -> None:
        """Inverts the curve along the y axis."""
        pass

    @abc.abstractmethod
    def fit(self) -> None:
        """Computes internal representation required for proper curve
        computation."""
        pass

    @abc.abstractmethod
    def _enforce_symmetry(self) -> None:
        """Updates the curve definition such that it is symmetric around
        the center."""
        pass

    @abc.abstractmethod
    def _default_points(self) -> CoordinateList:
        """Returns a default set of points for the curve.

        Returns:
            List of default control point coordinates
        """
        pass

    @abc.abstractmethod
    def _process_points(self, points: CoordinateList) -> None:
        """Generates the required data structure for the curve."""
        pass

    @abc.abstractmethod
    def __call__(self, x: float) -> float:
        """Evaluates the curve at the given location.

        Args:
            x: location at which to evaluate the curve

        Returns:
            Function value of the curve at the given location
        """
        pass


class PiecewiseLinear(AbstractCurve):
    def __init__(self, points: CoordinateList | None = None) -> None:
        """Creates a piece wise linear curve.

        Args:
            points: collection of (x, y) coordinates defining the curve
        """
        super().__init__(points)
        self.fit()

    def control_points(self) -> list[Point2D]:
        return self.points

    def add_control_point(self, x: float, y: float) -> None:
        x = util.clamp_analog_axis(x)
        y = util.clamp_analog_axis(y)
        self.points.append(Point2D(x, y))
        if self.is_symmetric:
            self.points.append(Point2D(-x, -y))
        self.points = sorted(self.points, key=lambda pt: pt.x)

    def invert(self) -> None:
        for pt in self.points:
            pt.y *= -1

    def fit(self) -> None:
        self.points = sorted(self.points, key=lambda pt: pt.x)

    def _enforce_symmetry(self) -> None:
        count = len(self.points)

        for i in range(int(count / 2.0)):
            p1 = self.points[i]
            p2 = self.points[-i - 1]

            p2.x = -p1.x
            p2.y = -p1.y

        if count % 2:  # Odd number of points.
            self.points[int(count / 2)] = Point2D(0.0, 0.0)
        else:
            self.points.insert(int(count / 2), Point2D(0.0, 0.0))

    def _default_points(self) -> CoordinateList:
        return [(-1.0, -1.0), (1.0, 1.0)]

    def _process_points(self, points: CoordinateList) -> None:
        self.points = [
            Point2D(pt[0], pt[1]) for pt in sorted(points, key=lambda pt: pt[0])
        ]

    def __call__(self, x: float) -> float:
        """Returns the linearly interpolated value for the given position.

        Args:
            x the location at which to evaluate the spline

        Returns:
            linearly interpolated value for the provided position
        """
        x = util.clamp(x, -1.0, 1.0)

        if x <= self.points[0].x:
            return self.points[0].y
        elif x >= self.points[-1].x:
            return self.points[-1].y
        else:
            for i in range(len(self.points) - 1):
                a = self.points[i]
                b = self.points[i + 1]
                if a.x <= x < b.x:
                    return a.y + (b.y - a.y) * (x - a.x) / (b.x - a.x)


class CubicSpline(AbstractCurve):
    """Defines a cubic spline for interpolation.

    The spline requires a set of control points which are used to
    create a C2 spline which passes through all of them.
    """

    def __init__(self, points: CoordinateList | None = None) -> None:
        """Creates a new CubicSpline object.

        Args:
            points: the set of (x, y) control points
        """
        super().__init__(points)

    def control_points(self) -> list[Point2D]:
        return self.points

    def add_control_point(self, x: float, y: float) -> None:
        x = util.clamp_analog_axis(x)
        y = util.clamp_analog_axis(y)
        self.points.append(Point2D(x, y))
        self.z.append(0.0)
        if self._is_symmetric:
            self.points.append(Point2D(-x, -y))
            self.z.append(0.0)
        self.fit()

    def invert(self) -> None:
        for pt in self.points:
            pt.y *= -1
        self.fit()

    def _enforce_symmetry(self) -> None:
        count = len(self.points)
        for i in range(int(count / 2.0)):
            p1 = self.points[i]
            p2 = self.points[-i - 1]

            p2.x = -p1.x
            p2.y = -p1.y

        if count % 2:  # Odd number of points.
            self.points[int(count / 2)] = Point2D(0.0, 0.0)
        else:
            self.points.insert(int(count / 2), Point2D(0.0, 0.0))
            self.z.insert(int(count / 2), 0.0)

    def fit(self) -> None:
        """Computes the second derivatives for the control points."""
        self.points = sorted(self.points, key=lambda pt: pt.x)
        self.z = [0.0] * len(self.points)
        n = len(self.points) - 1

        if n < 2:
            return

        eps = 0.000001
        h = [0.0] * n
        b = [0.0] * n
        u = [0.0] * n
        v = [0.0] * n

        for i in range(n):
            h[i] = self.points[i + 1].x - self.points[i].x
            b[i] = (self.points[i + 1].y - self.points[i].y) / (h[i] + eps)

        u[1] = 2 * (h[0] + h[1])
        v[1] = 6 * (b[1] - b[0])
        for i in range(2, n):
            u[i] = 2 * (h[i] + h[i - 1]) - h[i - 1] ** 2 / (u[i - 1] + eps)
            v[i] = 6 * (b[i] - b[i - 1]) - (h[i - 1] * v[i - 1]) / (u[i - 1] + eps)

        self.z[n] = 0.0
        for i in range(n - 1, 0, -1):
            self.z[i] = (v[i] - h[i] * self.z[i + 1]) / (u[i] + eps)
        self.z[0] = 0.0

    def _default_points(self) -> CoordinateList:
        return [(-1.0, -1.0), (1.0, 1.0)]

    def _process_points(self, points: CoordinateList) -> None:
        # Order the points by increasing x coordinate to guarantee proper
        # functioning of the spline code
        self.points = [
            Point2D(pt[0], pt[1]) for pt in sorted(points, key=lambda pt: pt[0])
        ]
        self.z = [0.0] * len(self.points)

    def __call__(self, x: float) -> float:
        """Returns the spline interpolate value at the desired position.

        Args:
            x the location at which to evaluate the spline

        Returns:
            function value at the provided position
        """
        x = util.clamp(x, -1.0, 1.0)

        n = len(self.points)
        i = 0
        for i in range(n - 1):
            if self.points[i].x <= x <= self.points[i + 1].x:
                break

        h = self.points[i + 1].x - self.points[i].x + 0.00001
        tmp = (self.z[i] / 2.0) + (x - self.points[i].x) * (
            self.z[i + 1] - self.z[i]
        ) / (6 * h)
        tmp = (
            -(h / 6.0) * (self.z[i + 1] + 2 * self.z[i])
            + (self.points[i + 1].y - self.points[i].y) / h
            + (x - self.points[i].x) * tmp
        )

        # User generic clamp to avoid function call overhead in this call which
        # is time sensitive.
        return util.clamp(self.points[i].y + (x - self.points[i].x) * tmp, -1.0, 1.0)


class CubicBezierSpline(AbstractCurve):
    """Implementation of a cubic Bezier spline."""

    class ControlPoint:
        def __init__(
            self,
            center: Point2D | None = None,
            handle_left: Point2D | None = None,
            handle_right: Point2D | None = None,
            symmetric_handles: bool = False,
        ) -> None:
            self.center = center
            self.handle_left = handle_left
            self.handle_right = handle_right
            # When set, the two handles are kept as mirror images of each
            # other, which makes the curve leave the control point with the
            # same slope on both sides.
            self.symmetric_handles = symmetric_handles

    def __init__(self, points: CoordinateList | None = None) -> None:
        """Creates a new CubicBezierSpline object.

        Args:
            points: the set of (x, y) knots and corresponding control points
        """
        self._control_points = []
        self._lookup = []
        super().__init__(points)

    def control_points(self) -> list[ControlPoint]:
        return self._control_points

    def handle(self, index: int, side: str) -> Point2D | None:
        """Returns the requested handle of a control point.

        Args:
            index: index of the control point owning the handle
            side: "left" or "right" handle of the control point

        Returns:
            The requested handle or None if it does not exist
        """
        cp = self._control_points[index]
        return cp.handle_left if side == "left" else cp.handle_right

    def handle_geometry(self, index: int, side: str) -> tuple[float, float]:
        """Returns slope and length of a control point's handle.

        The slope is the gradient of the curve as it leaves the control point
        in the direction of the handle, the length determines how far the
        curve follows that slope before bending towards its neighbor.

        Args:
            index: index of the control point owning the handle
            side: "left" or "right" handle of the control point

        Returns:
            Slope and length of the handle, (0, 0) if it does not exist
        """
        cp = self._control_points[index]
        handle = self.handle(index, side)
        if handle is None:
            return (0.0, 0.0)

        dx = handle.x - cp.center.x
        dy = handle.y - cp.center.y
        length = math.hypot(dx, dy)
        if abs(dx) < 1e-9:
            slope = math.copysign(MAX_HANDLE_SLOPE, dy) if dy != 0 else 0.0
        else:
            slope = util.clamp(dy / dx, -MAX_HANDLE_SLOPE, MAX_HANDLE_SLOPE)
        return (slope, length)

    def set_handle_geometry(
        self, index: int, side: str, slope: float, length: float
    ) -> None:
        """Positions a control point's handle via slope and length.

        The left handle always extends towards smaller x values and the right
        one towards larger ones, so a positive slope describes a rising curve
        on both sides.

        Args:
            index: index of the control point owning the handle
            side: "left" or "right" handle of the control point
            slope: gradient with which the curve leaves the control point
            length: distance of the handle from the control point
        """
        cp = self._control_points[index]
        handle = self.handle(index, side)
        if handle is None:
            return

        slope = util.clamp(slope, -MAX_HANDLE_SLOPE, MAX_HANDLE_SLOPE)
        length = max(0.0, length)
        dx = (-1.0 if side == "left" else 1.0) * length / math.sqrt(1 + slope**2)
        handle.x = cp.center.x + dx
        handle.y = cp.center.y + slope * dx
        self.enforce_handle_symmetry(index, side)
        self.fit()

    def set_symmetric_handles(
        self, index: int, is_symmetric: bool, side: str = "right"
    ) -> None:
        """Enables or disables handle symmetry for a single control point.

        Args:
            index: index of the control point to modify
            is_symmetric: whether the handles are to mirror each other
            side: handle to use as the reference when enabling symmetry
        """
        cp = self._control_points[index]
        cp.symmetric_handles = is_symmetric
        if self._is_symmetric:
            self._control_points[
                len(self._control_points) - index - 1
            ].symmetric_handles = is_symmetric
        if is_symmetric:
            self.enforce_handle_symmetry(index, side)
        self.fit()

    def enforce_handle_symmetry(self, index: int, side: str) -> None:
        """Mirrors a handle onto the opposite one of the same control point.

        Does nothing unless the control point has handle symmetry enabled and
        possesses both handles.

        Args:
            index: index of the control point to update
            side: handle to use as the reference for the mirroring
        """
        cp = self._control_points[index]
        if not cp.symmetric_handles:
            return

        source = self.handle(index, side)
        target = self.handle(index, "right" if side == "left" else "left")
        if source is None or target is None:
            return
        target.x = 2 * cp.center.x - source.x
        target.y = 2 * cp.center.y - source.y

    def add_control_point(self, x: float, y: float) -> None:
        x = util.clamp_analog_axis(x)
        y = util.clamp_analog_axis(y)
        self._control_points.append(
            CubicBezierSpline.ControlPoint(
                Point2D(x, y), Point2D(x - 0.05, y), Point2D(x + 0.05, y)
            )
        )
        if self._is_symmetric:
            self._control_points.append(
                CubicBezierSpline.ControlPoint(
                    Point2D(-x, -y), Point2D(-x - 0.05, -y), Point2D(-x + 0.05, -y)
                )
            )
        self.fit()

    def invert(self) -> None:
        for cp in self._control_points:
            cp.center.y *= -1
            if cp.handle_left is not None:
                cp.handle_left.y *= -1
            if cp.handle_right is not None:
                cp.handle_right.y *= -1
        self.fit()

    def fit(self) -> None:
        self._control_points = [
            cp for cp in sorted(self._control_points, key=lambda cp: cp.center.x)
        ]
        self._generate_lookup()

    def _enforce_symmetry(self) -> None:
        count = len(self._control_points)
        for i in range(int(count / 2.0)):
            cp1 = self._control_points[i]
            cp2 = self._control_points[-i - 1]

            # cp1 is the reference point for the state to mirror.
            cp2.center = Point2D(-cp1.center.x, -cp1.center.y)
            cp2.symmetric_handles = cp1.symmetric_handles

            # Update handles
            if cp1.handle_left is not None:
                cp2.handle_right = cp2.center - (cp1.handle_left - cp1.center)
            if cp1.handle_right is not None:
                cp2.handle_left = cp2.center - (cp1.handle_right - cp1.center)

        # Already have a point to use as the center.
        if count % 2:
            point = self._control_points[int(count / 2)]
            point.center = Point2D(0.0, 0.0)
            point.handle_left.x = -point.handle_right.x
            point.handle_left.y = -point.handle_right.y
        else:
            self._control_points.insert(
                int(count / 2),
                CubicBezierSpline.ControlPoint(
                    Point2D(0, 0), Point2D(-0.05, 0), Point2D(+0.05, 0)
                ),
            )

    def _default_points(self) -> CoordinateList:
        return [(-1.0, -1.0), (-0.95, -0.95), (0.95, 0.95), (1.0, 1.0)]

    def _process_points(self, coords: CoordinateList) -> None:
        points = [Point2D(pt[0], pt[1]) for pt in coords]

        # Generate list of control point structures
        self._control_points = []
        self._control_points.append(
            CubicBezierSpline.ControlPoint(points[0], handle_right=points[1])
        )
        for i in range(3, len(points) - 2, 3):
            self._control_points.append(
                CubicBezierSpline.ControlPoint(
                    center=points[i],
                    handle_left=points[i - 1],
                    handle_right=points[i + 1],
                )
            )
        self._control_points.append(
            CubicBezierSpline.ControlPoint(points[-1], handle_left=points[-2])
        )

    def _generate_lookup(self) -> None:
        """Generates the lookup table mapping x to t values."""
        # Iterate over all spline segments that form the curve
        self._lookup = []
        for cp1, cp2 in zip(self._control_points[:-1], self._control_points[1:]):
            # Grab the knots and their in between control points
            points = [cp1.center, cp1.handle_right, cp2.handle_left, cp2.center]

            # Compute the t -> coordinate mappings
            step_size = 0.01
            self._lookup.append([])
            for i in range(0, 101):
                t = i * step_size
                self._lookup[-1].append((t, self._value_at_t(points, t)))

    def _value_at_t(self, points: list[Point2D], t: float) -> Point2D:
        """Returns the Point2D for the spline at time t.

        Args:
            points: the control points defining the spline
            t: the time-like point

        Returns:
            x and y coordinate corresponding to the given time point as Point2D
        """
        t2 = t**2
        t3 = t**3
        mt = 1 - t
        mt2 = mt**2
        mt3 = mt**3

        return Point2D(
            points[0].x * mt3
            + 3 * points[1].x * mt2 * t
            + 3 * points[2].x * mt * t2
            + points[3].x * t3,
            points[0].y * mt3
            + 3 * points[1].y * mt2 * t
            + 3 * points[2].y * mt * t2
            + points[3].y * t3,
        )

    def __call__(self, x: float) -> float:
        """Returns the function value at the desired position.

        Args:
            x: the location at which to evaluate the function

        Returns:
            Function value at the provided position
        """
        # Ensure we have a valid value for x
        x = util.clamp(x, -1.0, 1.0)

        # Determine spline group to use
        index = 0
        if self._control_points[0].center.x > x:
            index = 0
        elif self._control_points[-1].center.x < x:
            index = len(self._lookup) - 1
        else:
            # Find segment corresponding to the x value
            index = 0
            for cp1, cp2 in zip(self._control_points[:-1], self._control_points[1:]):
                if cp1.center.x <= x <= cp2.center.x:
                    break
                index += 1

        # Linearly interpolate the lookup table data
        interval = [0, len(self._lookup[index]) - 1]
        searching = True
        while searching:
            distance = interval[1] - interval[0]
            if distance == 1:
                searching = False
                break
            # Binary search to find the correct lookup entries to interpolate
            center_index = interval[0] + int(distance / 2.0)
            if self._lookup[index][center_index][1].x < x:
                interval[0] = center_index
            else:
                interval[1] = center_index

        # Safeguard against out of bounds results.
        if interval[0] < 0:
            interval = [0, 1]
        elif interval[1] >= len(self._lookup[index]):
            interval = [len(self._lookup[index]) - 2, len(self._lookup[index]) - 1]

        low = self._lookup[index][interval[0]][1]
        high = self._lookup[index][interval[1]][1]

        # Use generic clamp to avoid function call overhead in this call which
        # is time sensitive.
        return util.clamp(
            low.y + (x - low.x) * ((high.y - low.y) / (high.x - low.x)), -1.0, 1.0
        )
