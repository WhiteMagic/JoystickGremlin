# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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

import abc
from typing import List, Tuple, Optional

from gremlin import util
from gremlin.types import Point2D


# Typing alias
type CoordinateList = List[Tuple[float, float]]


class AbstractCurve(abc.ABC):

    """Base class for all curves, providing a common interface."""

    def __init__(self, points: Optional[CoordinateList]=None):
        self._is_symmetric = False
        self._process_points(
            points if points is not None else self._default_points()
        )
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
    def control_points(self) -> List[Point2D | CubicBezierSpline.ControlPoint]:
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
            points[len(points)-idx-1].x = -x
            points[len(points)-idx-1].y = -y
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

    def __init__(self, points: Optional[CoordinateList]=None):
        """Creates a piece wise linear curve.

        Args:
            points: collection of (x, y) coordinates defining the curve
        """
        super().__init__(points)
        self.fit()

    def control_points(self) -> List[Point2D]:
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
            p2 = self.points[-i-1]

            p2.x = -p1.x
            p2.y = -p1.y

        if count % 2 != 0:
            self.points[int(count / 2)] = Point2D(0.0, 0.0)

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

    def __init__(self, points: Optional[CoordinateList]=None):
        """Creates a new CubicSpline object.

        Args:
            points: the set of (x, y) control points
        """
        super().__init__(points)

    def control_points(self) -> List[Point2D]:
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
            p2 = self.points[-i-1]

            p2.x = -p1.x
            p2.y = -p1.y

        if count % 2 != 0:
            self.points[int(count / 2)] = Point2D(0.0, 0.0)

    def fit(self) -> None:
        """Computes the second derivatives for the control points."""
        self.points = sorted(self.points, key=lambda pt: pt.x)
        n = len(self.points) - 1

        if n < 2:
            return
            # raise error.GremlinError(
            #     f"CubicSpline requires at least two control points "
            # )

        eps = 0.000001
        h = [0.0] * n
        b = [0.0] * n
        u = [0.0] * n
        v = [0.0] * n

        for i in range(n):
            h[i] = self.points[i+1].x - self.points[i].x
            b[i] = (self.points[i+1].y - self.points[i].y) / (h[i]+eps)

        u[1] = 2 * (h[0] + h[1])
        v[1] = 6 * (b[1] - b[0])
        for i in range(2, n):
            u[i] = 2 * (h[i] + h[i-1]) - h[i-1]**2 / (u[i-1] + eps)
            v[i] = 6 * (b[i] - b[i-1]) - (h[i-1] * v[i-1]) / (u[i-1] + eps)

        self.z[n] = 0.0
        for i in range(n-1, 0, -1):
            self.z[i] = (v[i] - h[i] * self.z[i+1]) / (u[i] + eps)
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
        n = len(self.points)
        i = 0
        for i in range(n-1):
            if self.points[i].x <= x <= self.points[i+1].x:
                break

        h = self.points[i+1].x - self.points[i].x + 0.00001
        tmp = (self.z[i] / 2.0) + (x - self.points[i].x) * \
            (self.z[i+1] - self.z[i]) / (6 * h)
        tmp = -(h/6.0) * (self.z[i+1] + 2 * self.z[i]) + \
            (self.points[i+1].y - self.points[i].y) / h + (x - self.points[i].x) * tmp

        return self.points[i].y + (x - self.points[i].x) * tmp


class CubicBezierSpline(AbstractCurve):

    """Implementation of a cubic Bezier spline."""

    class ControlPoint:

        def __init__(
                self,
                center: Optional[Point2D]=None,
                handle_left: Optional[Point2D]=None,
                handle_right: Optional[Point2D]=None
        ):
            self.center = center
            self.handle_left = handle_left
            self.handle_right = handle_right

    def __init__(self, points: Optional[CoordinateList]=None):
        """Creates a new CubicBezierSpline object.

        Args:
            points: the set of (x, y) knots and corresponding control points
        """
        self._control_points = []
        self._lookup = []
        super().__init__(points)

    def control_points(self) -> List[ControlPoint]:
        return self._control_points

    def add_control_point(self, x: float, y: float) -> None:
        x = util.clamp_analog_axis(x)
        y = util.clamp_analog_axis(y)
        self._control_points.append(CubicBezierSpline.ControlPoint(
            Point2D(x, y),
            Point2D(x-0.05, y),
            Point2D(x+0.05, y)
        ))
        if self._is_symmetric:
            self._control_points.append(CubicBezierSpline.ControlPoint(
                Point2D(-x, -y),
                Point2D(-x-0.05, -y),
                Point2D(-x+0.05, -y)
            ))
        self.fit()

    def invert(self) -> None:
        for cp in self._control_points:
            cp.center.y *= -1
            if cp.handle_left is not None:
                cp.handle_left.y *= -1
            if cp.handle_right is not None:
                cp.handle_right.y *= -1
        self.fit()

    def fit(self):
        self._control_points = [
            cp for cp in sorted(self._control_points, key=lambda cp: cp.center.x)
        ]
        self._generate_lookup()

    def _enforce_symmetry(self) -> None:
        count = len(self._control_points)
        for i in range(int(count / 2.0)):
            cp1 = self._control_points[i]
            cp2 = self._control_points[-i - 1]

            # cp1 is the reference point for the state to mirror
            cp2.center = Point2D(-cp1.center.x, -cp1.center.y)

            # Update handles

            # if cp1.handle_right and cp1.handle_left:
            #     cp2.handle_left = cp2.center - (cp1.handle_right - cp1.center)
            #     cp2.handle_right = cp2.center - (cp1.handle_left - cp1.center)
            # if len(cp1.handles) == 2:
            #     cp2.handles[0] = cp2.center - (cp1.handles[1] - cp1.center)
            #     cp2.handles[1] = cp2.center - (cp1.handles[0] - cp1.center)
            # elif len(cp1.handles) == 1:
            #     cp2.handles[0] = cp2.center - (cp1.handles[0] - cp1.center)
            if cp1.handle_left is not None:
                cp2.handle_right = cp2.center - (cp1.handle_left - cp1.center)
            if cp1.handle_right is not None:
                cp2.handle_left = cp2.center - (cp1.handle_right - cp1.center)

        if count % 2 != 0:
            self._control_points[int(count / 2)].center = Point2D(0.0, 0.0)

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
            self._control_points.append(CubicBezierSpline.ControlPoint(
                center=points[i],
                handle_left=points[i - 1],
                handle_right=points[i + 1]
            ))
        self._control_points.append(
            CubicBezierSpline.ControlPoint(points[-1], handle_left=points[-2])
        )

    def _generate_lookup(self) -> None:
        """Generates the lookup table mapping x to t values."""
        # Iterate over all spline segments that form the curve
        self._lookup = []
        for cp1, cp2 in zip(self._control_points[:-1], self._control_points[1:]):
            # Grab the knots and their in between control points
            points = [
                cp1.center,
                cp1.handle_right,
                cp2.handle_left,
                cp2.center
            ]

            # Compute the t -> coordinate mappings
            step_size = 0.01
            self._lookup.append([])
            for i in range(0, 101):
                t = i * step_size
                self._lookup[-1].append((t, self._value_at_t(points, t)))

    def _value_at_t(self, points: List[Point2D], t: float) -> Point2D:
        """Returns the Point2D for the spline at time t.

        Args:
            points: the control points defining the spline
            t: the time-like point

        Returns:
            x and y coordinate corresponding to the given time point as Point2D
        """
        t2 = t ** 2
        t3 = t ** 3
        mt = 1 - t
        mt2 = mt ** 2
        mt3 = mt ** 3

        return Point2D(
            points[0].x * mt3
                + 3 * points[1].x * mt2 * t
                + 3 * points[2].x * mt * t2
                + points[3].x * t3,
            points[0].y * mt3
                + 3 * points[1].y * mt2 * t
                + 3 * points[2].y * mt * t2
                + points[3].y * t3
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
            # segment_count = int((len(self.points) - 4) / 3) + 1
            # Find segment corresponding to the x value
            index = 0
            for cp1, cp2 in zip(self._control_points[:-1], self._control_points[1:]):
                if cp1.center.x <= x <= cp2.center.x:
                    break
                index += 1
            # for i in range(len(self.control_points) - 1):
            #     if self.control_points[i].center.x <= x self.con
            #     if self.points[offset].x <= x <= self.points[offset+3].x:
            #         index = i
            #         break

        # Linearly interpolate the lookup table data
        interval = [0, len(self._lookup[index])]
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

        low = self._lookup[index][interval[0]][1]
        high = self._lookup[index][interval[1]][1]

        return low.y + (x - low.x) * ((high.y - low.y) / (high.x - low.x))
