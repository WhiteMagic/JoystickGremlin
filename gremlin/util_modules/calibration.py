# -*- coding: utf-8; -*-

"""Axis calibration and deadzone utilities.

This module contains utilities for axis calibration, deadzone handling,
and axis value transformation. Extracted from gremlin.util.

Functions:
- create_calibration_function() - Creates calibration function for axes
- with_center_calibration() - Calibrates normal axes with center point
- no_center_calibration() - Calibrates slider-type axes without center
"""

from typing import Callable

__all__ = [
    "create_calibration_function",
    "with_center_calibration",
    "no_center_calibration",
]


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamps a value to the given range.

    Args:
        value: value to clamp
        min_value: minimum allowed value
        max_value: maximum allowed value

    Returns:
        Clamped value within [min_value, max_value]
    """
    return max(min_value, min(max_value, value))


def with_center_calibration(
        value: int,
        low: int,
        centerLow: int,
        centerHigh: int,
        high: int
) -> float:
    """Returns the calibrated value for a normal style axis.

    Args:
        value: the raw value to process
        low: the minimum value of the axis
        centerLow: the center low value of the axis
        centerHigh: the center high value of the axis
        high: the maximum value of the axis

    Returns:
        the calibrated value in [-1, 1] corresponding to the provided raw value
    """
    clamped = int(clamp(value, low, high))
    if clamped < centerLow:
        return (clamped - centerLow) / float(centerLow - low)
    elif centerLow <= clamped <= centerHigh:
        return 0.0
    else:
        return (clamped - centerHigh) / float(high - centerHigh)


def no_center_calibration(value: int, minimum: int, maximum: int) -> float:
    """Returns the calibrated value for a slider type axis.

    Args:
        value: the raw value to process
        minimum: the minimum value of the axis
        maximum: the maximum value of the axis

    Returns:
        the calibrated value in [-1, 1] corresponding to the provided raw value
    """
    clamped = int(clamp(value, minimum, maximum))
    return (clamped - minimum) / float(maximum - minimum) * 2.0 - 1.0


def create_calibration_function(
        low: int,
        centerLow: int,
        centerHigh: int,
        high: int,
        has_center: bool
) -> Callable[[int], float]:
    """Returns a calibration function appropriate for the provided data.

    Args:
        low: the lower bound of the calibration function
        centerLow: the lower value around the center of the calibration function
        centerHigh: the upper value around the center of the calibration function
        high: the upper bound of the calibration function
        has_center: True if the calibration is for an axis with a center

    Returns:
        function which returns a value in [-1, 1] corresponding
        to the provided raw input value
    """
    if has_center:
        return lambda x: with_center_calibration(x, low, centerLow, centerHigh, high)
    else:
        return lambda x: no_center_calibration(x, low, high)
