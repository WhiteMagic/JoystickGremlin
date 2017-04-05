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


class CubicSpline(object):

    """Creates a new cubic spline based interpolation.
    
    The methods requires a set of control points which are used to
    create a C2 spline which passes through all of them.
    """

    def __init__(self, points):
        """Creates a new CubicSpline object.

        :param points the set of (x, y) control points
        """
        # Order the points by increasing x coordinate to guarantee proper
        # functioning of the spline code
        ordered_points = sorted(points, key=lambda x: x[0])

        self.x = [v[0] for v in ordered_points]
        self.y = [v[1] for v in ordered_points]
        self.z = [0] * len(points)

        self._fit()

    def _fit(self):
        """Computes the second derivatives for the control points."""
        n = len(self.x)-1

        if n < 2:
            return

        h = [0] * n
        b = [0] * n
        u = [0] * n
        v = [0] * n

        for i in range(n):
            h[i] = self.x[i+1] - self.x[i]
            b[i] = (self.y[i+1] - self.y[i]) / h[i]

        u[1] = 2 * (h[0] + h[1])
        v[1] = 6 * (b[1] - b[0])
        for i in range(2, n):
            u[i] = 2 * (h[i] + h[i-1]) - h[i-1]**2 / u[i-1]
            v[i] = 6 * (b[i] - b[i-1]) - (h[i-1] * v[i-1]) / u[i-1]

        self.z[n] = 0.0
        for i in range(n-1, 0, -1):
            self.z[i] = (v[i] - h[i] * self.z[i+1]) / u[i]
        self.z[0] = 0.0

    def __call__(self, x):
        """Returns the function value at the desired position.

        :param x the location at which to evaluate the function
        :return function value at the provided position
        """
        n = len(self.x)

        i = 0
        for i in range(n-1):
            if self.x[i] <= x <= self.x[i+1]:
                break

        h = self.x[i+1] - self.x[i]
        tmp = (self.z[i] / 2.0) + (x - self.x[i]) * \
            (self.z[i+1] - self.z[i]) / (6 * h)
        tmp = -(h/6.0) * (self.z[i+1] + 2 * self.z[i]) + \
            (self.y[i+1] - self.y[i]) / h + (x - self.x[i]) * tmp

        return self.y[i] + (x - self.x[i]) * tmp


class CubicBezierSpline(object):

    """Implementation of cubic Bezier splines."""

    def __init__(self, points):
        """Creates a new CubicBezierSpline object.

        :param points the set of (x, y) knots and control points
        """
        self.x = [v[0] for v in points]
        self.y = [v[1] for v in points]

        self.knots = [pt for pt in points[::3]]

    def __call__(self, x):
        """Returns the function value at the desired position.

        :param x the location at which to evaluate the function
        :return function value at the provided position
        """
        if self.knots[0][0] > x:
            index = 0
            t = 0
        elif self.knots[-1][0] <= x:
            index = len(self.knots)-2
            t = 1
        else:
            index = len(self.knots)-1
            for i, pt in enumerate(self.knots[::-1]):
                if x >= pt[0]:
                    break
                index -= 1
            t = (x - self.knots[index][0]) / \
                (self.knots[index+1][0] - self.knots[index][0])

        offset = index * 3
        return (1-t)**3 * self.y[offset] \
            + 3*(1-t)**2 * t * self.y[offset+1] \
            + 3*(1-t) * t**2 * self.y[offset+2] \
            + t**3 * self.y[offset+3]
