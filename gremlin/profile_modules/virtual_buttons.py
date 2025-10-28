# -*- coding: utf-8; -*-

"""Virtual button abstractions for profile system.

This module contains abstract and concrete virtual button classes
that allow axis and hat inputs to be treated as buttons.

Extracted from gremlin.profile for better organization.
"""

from abc import ABCMeta, abstractmethod
from typing import Optional

from gremlin.types import AxisButtonDirection, HatDirection


class AbstractVirtualButton(metaclass=ABCMeta):
    """Base class for all virtual button types.
    
    Virtual buttons allow non-button inputs (axes, hats) to be
    treated as buttons by defining activation conditions.
    """

    @abstractmethod
    def is_pressed(self, value) -> bool:
        """Returns whether the button is pressed given the input value.

        Args:
            value: the input value to process

        Returns:
            True if the button is pressed, False otherwise
        """
        pass


class VirtualAxisButton(AbstractVirtualButton):
    """Represents a single button on an axis.

    An axis can have two buttons, one for each half of the axis
    or a single button representing the entire axis.
    """

    def __init__(
            self,
            lower_limit: float,
            upper_limit: float,
            direction: AxisButtonDirection
    ):
        """Creates a new instance.

        Args:
            lower_limit: lower activation threshold
            upper_limit: upper activation threshold
            direction: activation direction (above/below/anywhere)
        """
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.direction = direction

    def is_pressed(self, value: float) -> bool:
        """Returns whether the button is pressed given the axis value.

        Args:
            value: axis value to check

        Returns:
            True if the button is pressed, False otherwise
        """
        is_active = self.lower_limit <= value <= self.upper_limit
        return is_active


class VirtualHatButton(AbstractVirtualButton):
    """Represents a single button on a hat.

    Each hat has 8 possible directions which can be mapped as
    individual buttons.
    """

    def __init__(self, direction: HatDirection):
        """Creates a new instance.

        Args:
            direction: hat direction that activates this button
        """
        self.direction = direction

    def is_pressed(self, value: HatDirection) -> bool:
        """Returns whether the button is pressed given the hat value.

        Args:
            value: hat direction value

        Returns:
            True if the button is pressed, False otherwise
        """
        return self.direction == value
