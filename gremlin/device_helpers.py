# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from gremlin import common
from gremlin.types import (
    HatDirection,
    InputType,
)

if TYPE_CHECKING:
    from gremlin import event_handler


class JoystickInputSignificant(metaclass=common.SingletonMetaclass):
    """Checks whether or not joystick inputs are significant."""

    def __init__(self) -> None:
        """Initializes the instance."""
        self._event_registry = {}
        self._mre_registry = {}
        self._time_registry = {}

    def should_process(self, event: event_handler.Event) -> bool:
        """Returns whether or not a particular event is significant enough to
        process.

        Args:
            event: the event to check for significance

        Returns:
            True if the event should be processed, False otherwise
        """
        self._mre_registry[event] = event

        match event.event_type:
            case InputType.JoystickAxis:
                return self._process_axis(event)
            case InputType.JoystickButton:
                return self._process_button(event)
            case InputType.JoystickHat:
                return self._process_hat(event)
            case _:
                logging.getLogger("system").warning("Event with unknown type received")
                return False

    def last_event(self, event: event_handler.Event) -> event_handler.Event:
        """Returns the most recent event of this type.

        Args:
            event: the type of event for which to return the most recent one

        Returns:
            Latest event instance corresponding to the specified event
        """
        return self._mre_registry[event]

    def reset(self) -> None:
        """Resets the detector to a clean state for subsequent uses."""
        self._event_registry = {}
        self._mre_registry = {}
        self._time_registry = {}

    def _process_axis(self, event: event_handler.Event) -> bool:
        """Process an axis event.

        Args:
            event: the axis event to process

        Returns:
            True if it should be processed, False otherwise
        """
        if event in self._event_registry:
            # Reset everything if we have no recent data.
            if self._time_registry[event] + 5.0 < time.time():
                self._event_registry[event] = event
                self._time_registry[event] = time.time()
                return False
            # Update state.
            else:
                self._time_registry[event] = time.time()
                if abs(self._event_registry[event].value - event.value) > 0.33:
                    self._event_registry[event] = event
                    self._time_registry[event] = time.time()
                    return True
                else:
                    return False
        else:
            self._event_registry[event] = event
            self._time_registry[event] = time.time()
            return False

    def _process_button(self, event: event_handler.Event) -> bool:
        """Process a button event.

        Args:
            event: the button event to process

        Returns:
            True if it should be processed, False otherwise
        """
        return True

    def _process_hat(self, event: event_handler.Event) -> bool:
        """Process a hat event.

        Args:
            event: the hat event to process

        Returns:
            True if it should be processed, False otherwise
        """
        return event.value != HatDirection.Center


class AxisChangeSignificanceTracker:
    def __init__(
        self,
        initial_value: float,
        minimum_change: float,
        minimum_time_interval: float,
        record_crossings: bool,
    ) -> None:
        self._last_time = time.monotonic_ns()
        self._last_value = initial_value
        self._minimum_change = minimum_change
        self._minimum_time_interval = minimum_time_interval * 1e9
        self._record_crossings = record_crossings

    def is_significant_change(self, new_value: float) -> bool:
        time_now = time.monotonic_ns()
        # Precompute values used to determine if a significant change is present.
        time_delta = time_now - self._last_time
        value_delta = abs(new_value - self._last_value)
        zero_crossed = (new_value > 0) != (self._last_value > 0)
        extrema_reached = abs(self._last_value) != 1.0 and abs(new_value) == 1.0

        if self._record_crossings and (zero_crossed or extrema_reached):
            self._last_time = time_now
            self._last_value = new_value
            return True

        if (
            time_delta >= self._minimum_time_interval
            and value_delta >= self._minimum_change
        ):
            self._last_time = time_now
            self._last_value = new_value
            return True

        return False
