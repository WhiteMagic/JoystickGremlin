# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
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


import collections
from collections.abc import Callable
import functools
import logging
import time
import uuid

from PySide6 import QtCore

import gremlin.common
import gremlin.keyboard

from gremlin import common, event_handler, mode_manager
from gremlin.types import InputType
from vjoy.vjoy import VJoyProxy


ButtonReleaseEntry = collections.namedtuple(
    "Entry", ["callback", "event", "mode"]
)


@common.SingletonDecorator
class ButtonReleaseActions(QtCore.QObject):

    """Ensures a desired action is run when a button is released."""

    def __init__(self):
        """Initializes the instance."""
        QtCore.QObject.__init__(self)

        self._registry = {}
        self._ignore_registry = {}
        el = event_handler.EventListener()
        el.joystick_event.connect(self._input_event_cb)
        el.keyboard_event.connect(self._input_event_cb)
        el.virtual_event.connect(self._input_event_cb)
        mm = mode_manager.ModeManager()
        self._current_mode = mm.current.name
        mm.mode_changed.connect(self._mode_changed_cb)

    def register_callback(
        self,
        callback: Callable[[], None],
        physical_event: event_handler.Event
    ) -> None:
        """Registers a callback with the system.

        Args:
            callback: the function to run when the corresponding button is
                released
            physical_event: the physical event of the button being pressed
        """
        release_evt = physical_event.clone()
        release_evt.is_pressed = False

        if release_evt not in self._registry:
            self._registry[release_evt] = []
        # Do not record the mode since we may want to run the release action
        # independent of a mode
        self._registry[release_evt].append(
            ButtonReleaseEntry(callback, release_evt, None)
        )

    def register_button_release(
        self,
        vjoy_input: tuple[int, int],
        physical_event: event_handler.Event,
        activate_on: bool
    ) -> None:
        """Registers a physical and vjoy button pair for tracking.

        This method ensures that a vjoy button is pressed/released when the
        specified physical event occurs next. This is useful for cases where
        an action was triggered in a different mode or using a different
        condition.

        Args:
            vjoy_input: the vjoy button to release, represented as
                (vjoy_device_id, vjoy_button_id)
            physical_event: the button event when release should
                trigger the release of the vjoy button
            activate_on: button state on which to trigger the automatic
                release
        """
        if (physical_event, vjoy_input) in self._ignore_registry:
            logging.getLogger("system").warning(
                f"Not registering button release event for "
                f"{physical_event} to {vjoy_input}"
            )
            return

        release_evt = physical_event.clone()
        release_evt.is_pressed = activate_on

        if release_evt not in self._ignore_registry:
            self._ignore_registry[release_evt] = []
        # Record current mode so we only release if we've changed mode
        self._ignore_registry[release_evt].append(ButtonReleaseEntry(
            lambda: self._release_callback_prototype(vjoy_input),
            release_evt,
            self._current_mode
        ))

    def ignore_button_release(
            self,
            vjoy_input: tuple[int, int],
            physical_event: event_handler.Event
    ) -> None:
        """Ignores physical and vjoy button pair tracking requests.

        This prevents calls to register_button_callback from being honored
        in cases where some action wants to disable this feature.

        Args:
            vjoy_input: the vjoy button to release, represented as
                (vjoy_device_id, vjoy_button_id)
            physical_event: the button event when release should
                trigger the release of the vjoy button
        """
        key = (physical_event, vjoy_input)
        self._ignore_registry[key] = True

    def reset(self) -> None:
        """Wipes the registry database."""
        self._registry = {}
        self._ignore_registry = {}

    def _release_callback_prototype(self, vjoy_input: tuple[int, int]) -> None:
        """Prototype of a button release callback, used with lambdas.

        Args:
            vjoy_input: the vjoy input data to use in the release
        """
        vjoy = VJoyProxy()
        # Check if the button is valid otherwise we cause Gremlin to crash
        if vjoy[vjoy_input[0]].is_button_valid(vjoy_input[1]):
            vjoy[vjoy_input[0]].button(vjoy_input[1]).is_pressed = False
        else:
            logging.getLogger("system").warning(
                f"Attempted to use non existent button: " +
                f"vJoy {vjoy_input[0]:d} button {vjoy_input[1]:d}"
            )

    def _input_event_cb(self, event: event_handler.Event) -> None:
        """Runs callbacks associated with the given event.

        Args:
            event: the event to process
        """
        #if evt in [e for e in self._registry if e.is_pressed != evt.is_pressed]:
        if event in self._registry:
            new_list = []
            for entry in self._registry[event]:
                if entry.event.is_pressed == event.is_pressed:
                    entry.callback()
                else:
                    new_list.append(entry)
            self._registry[event] = new_list

    def _mode_changed_cb(self, mode: str) -> None:
        """Updates the current mode variable.

        Args:
            mode: name of the now active mode
        """
        self._current_mode = mode


@common.SingletonDecorator
class JoystickInputSignificant:

    """Checks whether or not joystick inputs are significant."""

    def __init__(self):
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

        if event.event_type == InputType.JoystickAxis:
            return self._process_axis(event)
        elif event.event_type == InputType.JoystickButton:
            return self._process_button(event)
        elif event.event_type == InputType.JoystickHat:
            return self._process_hat(event)
        else:
            logging.getLogger("system").warning(
                "Event with unknown type received"
            )
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
            # Reset everything if we have no recent data
            if self._time_registry[event] + 5.0 < time.time():
                self._event_registry[event] = event
                self._time_registry[event] = time.time()
                return False
            # Update state
            else:
                self._time_registry[event] = time.time()
                if abs(self._event_registry[event].value - event.value) > 0.25:
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
        return event.value != (0, 0)


# def select_first_valid_vjoy_input(
#         valid_types: list[InputType]
# ) -> dict[str, Any]|None:
#     """Returns the first valid vjoy input.
#
#     Args:
#         valid_types: List of InputType values that are valid type to be returned
#
#     Returns:
#         Dictionary containing the information about the selected vJoy input
#     """
#     for dev in vjoy_devices():
#         if InputType.JoystickAxis in valid_types and dev.axis_count > 0:
#             return {
#                 "device_id": dev.vjoy_id,
#                 "input_type": InputType.JoystickAxis,
#                 "input_id": dev.axis_map[0].axis_index
#             }
#         elif InputType.JoystickButton in valid_types and dev.button_count > 0:
#             return {
#                 "device_id": dev.vjoy_id,
#                 "input_type": InputType.JoystickButton,
#                 "input_id": 1
#             }
#         elif InputType.JoystickHat in valid_types and dev.hat_count > 0:
#             return {
#                 "device_id": dev.vjoy_id,
#                 "input_type": InputType.JoystickHat,
#                 "input_id": 1
#             }
#     return None


# def linear_axis_index(axis_map, axis_index):
#     """Returns the linear index for an axis based on the axis index.
#
#     Parameters
#     ==========
#     axis_map : dill.AxisMap
#         AxisMap instance which contains the mapping between linear and
#         axis indices
#     axis_index : int
#         Index of the axis for which to return the linear index
#
#     Return
#     ======
#     int
#         Linear axis index
#     """
#     for entry in axis_map:
#         if entry.axis_index == axis_index:
#             return entry.linear_index
#     raise error.GremlinError("Linear axis lookup failed")
