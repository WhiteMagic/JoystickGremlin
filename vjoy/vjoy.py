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

import ctypes
import enum
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import os

from vjoy.vjoy_interface import VJoyState, VJoyInterface

from gremlin.error import VJoyError
from gremlin.types import AxisNames
import gremlin.spline


def _error_string(vid: int, iid: int, value: Any) -> str:
    """Creates an error string for the given inputs.

    Args:
        vid: vjoy device id
        iid: input id
        value: input value

    Returns:
        string representing the error
    """
    return "vjoy: {} input: {} value: {}".format(vid, iid, value)


class AxisCode(enum.Enum):

    """Enumeration of the valid axis names."""

    X = 0x30
    Y = 0x31
    Z = 0x32
    RX = 0x33
    RY = 0x34
    RZ = 0x35
    SL0 = 0x36
    SL1 = 0x37


class HatType(enum.Enum):

    """Valid hat types."""

    Discrete = 0
    Continuous = 1


def device_available(vjoy_id: int) -> bool:
    """Returns whether a device is available, i.e. can be acquired.

    Args:
        vjoy_id: id of the vjoy device to check

    Returns:
        True if the device is available, False otherwise
    """
    dev_free = VJoyInterface.GetVJDStatus(vjoy_id) == VJoyState.Free.value
    dev_acquire = VJoyInterface.AcquireVJD(vjoy_id)
    VJoyInterface.RelinquishVJD(vjoy_id)

    return dev_free & dev_acquire


def device_exists(vjoy_id: int) -> bool:
    """Returns whether a device exists.

    A device that exists may be acquired by a different process and thus not
    usable by Gremlin.

    Args:
        vjoy_id: id of the vjoy device to check

    Returns:
        True if the device exists, False otherwise
    """
    state = VJoyInterface.GetVJDStatus(vjoy_id)
    return state not in [VJoyState.Missing.value, VJoyState.Unknown.value]


def axis_count(vjoy_id: int) -> int:
    """Returns the number of axes of the given vJoy device.

    Args:
        vjoy_id: id of the vjoy device

    Returns:
        The number of axes available on a device
    """
    count = 0
    for axis in AxisCode:
        if VJoyInterface.GetVJDAxisExist(vjoy_id, axis.value) > 0:
            count += 1
    return count


def button_count(vjoy_id: int) -> int:
    """Returns the number of buttons of the given vJoy device.

    Args:
        vjoy_id: id of the vjoy device

    Returns:
        The number of buttons available on a device
    """
    return VJoyInterface.GetVJDButtonNumber(vjoy_id)


def hat_count(vjoy_id: int) -> int:
    """Returns the number of hats of the given vJoy device.

    Args:
        vjoy_id: id of the vjoy device

    Returns:
        The number of hats available on a device
    """
    return VJoyInterface.GetVJDContPovNumber(vjoy_id)


def hat_configuration_valid(vjoy_id: int) -> bool:
    """Returns if the hats are configured properly.

    In order for hats to work properly they have to be set as continous and
    not discrete.

    Args:
        vjoy_id: index of the vJoy device to query

    Returns:
        True if the hats are configured properly, False otherwise
    """
    continuous_count = VJoyInterface.GetVJDContPovNumber(vjoy_id)
    discrete_count = VJoyInterface.GetVJDDiscPovNumber(vjoy_id)

    return continuous_count >= discrete_count


class Axis:

    """Represents an analog axis in vJoy, allows setting the value
    of the axis."""

    def __init__(self, vjoy_dev: VJoy, axis_id: int) -> None:
        """Creates a new object.

        Args:
            vjoy_dev: the vJoy device this axis belongs to
            axis_id: the id of the axis this object controls
        """
        self.vjoy_dev = vjoy_dev
        self.vjoy_id = vjoy_dev.vjoy_id
        self.axis_id = axis_id
        self._value = 0.0

        # Retrieve axis minimum and maximum values
        tmp = ctypes.c_ulong()
        VJoyInterface.GetVJDAxisMin(
            self.vjoy_id,
            self.axis_id,
            ctypes.byref(tmp)
        )
        self._min_value = tmp.value
        VJoyInterface.GetVJDAxisMax(
            self.vjoy_id,
            self.axis_id,
            ctypes.byref(tmp)
        )
        self._max_value = tmp.value
        self._half_range = int(self._max_value / 2)

        self._deadzone_fn = lambda x: deadzone(x, -1.0, -0.0, 0.0, 1.0)
        self._response_curve_fn = lambda x: x

        # If this is not the case our value setter needs to change
        if self._min_value != 0:
            raise VJoyError("vJoy axis minimum value is not 0  - {}".format(
                    _error_string(self.vjoy_id, self.axis_id, self._min_value)
            ))

    def set_response_curve(
            self,
            spline_type: str,
            control_points: List[Tuple[float, float]]
    ) -> None:
        """Sets the response curve to use for the axis.

        Args:
            spline_type: the type of spline to use
            control_points: the control points defining the spline
        """
        if spline_type == "cubic-spline":
            self._response_curve_fn = gremlin.spline.CubicSpline(control_points)
        elif spline_type == "cubic-bezier-spline":
            self._response_curve_fn = \
                gremlin.spline.CubicBezierSpline(control_points)
        else:
            logging.getLogger("system").error("Invalid spline type specified")
            self._response_curve_fn = lambda x: x

    def set_deadzone(
            self,
            low: float,
            center_low: float,
            center_high: float,
            high: float
    ) -> None:
        """Sets the deadzone for the axis.

        Args:
            low: low deadzone limit
            center_low: lower center deadzone limit
            center_high: upper center deadzone limit
            high: high deadzone limit
        """
        self._deadzone_fn = lambda x: deadzone(
            x, low, center_low, center_high, high
        )

    @property
    def value(self) -> float:
        """Returns the axis position as a value between [-1, 1]"

        Returns:
            position of the axis as a value between [-1, 1]
        """
        self.vjoy_dev.used()
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        """Sets the position of the axis based on a value between [-1, 1].

        Args:
            value: the position of the axis in the range [-1, 1]
        """
        self.vjoy_dev.ensure_ownership()

        # Log an error on invalid data but continue processing by clamping
        # the values in the next step
        if 1.0 - abs(value) < -0.001:
            logging.getLogger("system").warning(
                "Wrong data type provided, has to be float in [-1, 1],"
                " provided value was {:.2f}".format(value)
            )

        # Normalize value to [-1, 1] and apply response curve and deadzone
        # settings
        self._value = self._response_curve_fn(
            self._deadzone_fn(min(1.0, max(-1.0, value)))
        )

        if not VJoyInterface.SetAxis(
                int(self._half_range + self._half_range * self._value),
                self.vjoy_id,
                self.axis_id
        ):
            raise VJoyError(
                "Failed setting axis value - {}".format(
                    _error_string(self.vjoy_id, self.axis_id, self._value)
                )
            )
        self.vjoy_dev.used()

    def set_absolute_value(self, value: float) -> None:
        """Sets the position of the axis based on a value between [-1, 1].

        In comparison to the value setter this function bypasses the
        deadzone and response curve settings.

        Args:
            value: the position of the axis in the range [-1, 1]
        """
        # Log an error on invalid data but continue processing by clamping
        # the values in the next step
        if 1.0 - abs(value) < -0.001:
            logging.getLogger("system").warning(
                "Wrong data type provided, has to be float in [-1, 1],"
                " provided value was {:.2f}".format(value)
            )

        # Normalize value to [-1, 1] and apply response curve and deadzone
        # settings
        self._value = value

        if not VJoyInterface.SetAxis(
                int(self._half_range + self._half_range * self._value),
                self.vjoy_id,
                self.axis_id
        ):
            raise VJoyError(
                "Failed setting axis value - {}".format(
                    _error_string(self.vjoy_id, self.axis_id, self._value)
                )
            )
        self.vjoy_dev.used()


class Button:

    """Represents a button in vJoy, allows pressing and releasing it."""

    def __init__(self, vjoy_dev: VJoy, button_id: int) -> None:
        """Creates a new object.

        Args:
            vjoy_dev: the vJoy device this button belongs to
            button_id: the id of the button this object controls
        """
        self.vjoy_dev = vjoy_dev
        self.vjoy_id = vjoy_dev.vjoy_id
        self.button_id = button_id
        self._is_pressed = False

    @property
    def is_pressed(self) -> bool:
        """Returns whether the button is pressed.

        Returns:
            True if the button is pressed, False otherwise
        """
        self.vjoy_dev.used()
        return self._is_pressed

    @is_pressed.setter
    def is_pressed(self, is_pressed: bool) -> None:
        """Sets the state of the button.

        Args:
            is_pressed: True if the button is pressed, False otherwise
        """
        assert(isinstance(is_pressed, bool))
        self.vjoy_dev.ensure_ownership()
        self._is_pressed = is_pressed
        if not VJoyInterface.SetBtn(
                self._is_pressed,
                self.vjoy_id,
                self.button_id
        ):
            raise VJoyError(
                "Failed setting button value - {}".format(
                    _error_string(self.vjoy_id, self.button_id, self._is_pressed)
                )
            )
        self.vjoy_dev.used()


class Hat:

    """Represents a discrete hat in vJoy, allows setting the direction
    of the hat."""

    # Discrete directions, mapping (x, y) coordinates to vJoy values
    to_discrete_direction = {
        (0, 1): 0,
        (1, 0): 1,
        (0, -1): 2,
        (-1, 0): 3,
        (0, 0): -1
    }

    # Continuous directions, mapping 8-way *(x, y) coordinates to vJoy values
    to_continuous_direction = {
        (0, 0): -1,
        (0, 1): 0,
        (1, 1): 4500,
        (1, 0): 9000,
        (1, -1): 13500,
        (0, -1): 18000,
        (-1, -1): 22500,
        (-1, 0): 27000,
        (-1, 1): 31500
    }

    def __init__(self, vjoy_dev: VJoy, hat_id: int, hat_type: HatType) -> None:
        """Creates a new object.

        Args:
            vjoy_dev: the vJoy device this hat belongs to
            hat_id: the id of the hat this object controls
            hat_type: the type of hat being used, discrete or continuous
        """
        self.vjoy_dev = vjoy_dev
        self.vjoy_id = vjoy_dev.vjoy_id
        self.hat_id = hat_id
        self._direction = (0, 0)
        self.hat_type = hat_type

    @property
    def direction(self) -> Tuple[int, int]:
        """Returns the current direction of the hat.

        Returns:
            current direction of the hat encoded as a tuple (x, y)
        """
        self.vjoy_dev.used()
        return self._direction

    @direction.setter
    def direction(self, direction: Tuple[int, int]) -> None:
        """Sets the direction of the hat.

        Args:
            direction the new direction of the hat
        """
        self.vjoy_dev.ensure_ownership()

        if self.hat_type == HatType.Discrete:
            self._set_discrete_direction(direction)
        elif self.hat_type == HatType.Continuous:
            self._set_continuous_direction(direction)
        else:
            raise VJoyError("Invalid hat type specified - {}".format(
                _error_string(self.vjoy_id, self.axis_id, self.direction)
            ))
        self.vjoy_dev.used()

    def _set_discrete_direction(self, direction: Tuple[int, int]) -> None:
        """Sets the direction of a discrete hat.

        Args:
            direction: the direction of the hat
        """
        if direction not in Hat.to_discrete_direction:
            raise VJoyError(
                "Invalid direction specified - {}".format(
                    _error_string(self.vjoy_id, self.axis_id, self._direction)
                )
            )

        self._direction = direction
        if not VJoyInterface.SetDiscPov(
                Hat.to_discrete_direction[direction],
                self.vjoy_id,
                self.hat_id
        ):
            raise VJoyError(
                "Failed to set hat direction - {}".format(
                    _error_string(self.vjoy_id, self.axis_id, self._direction)
                )
            )

    def _set_continuous_direction(self, direction: Tuple[int, int]) -> None:
        """Sets the direction of a continuous hat.

        Args:
            direction: the direction of the hat motion
        """
        if direction not in Hat.to_continuous_direction:
            raise VJoyError(
                "Invalid direction specified - {}".format(
                    _error_string(self.vjoy_id, self.hat_id, direction)
                )
            )

        self._direction = direction
        if not VJoyInterface.SetContPov(
                Hat.to_continuous_direction[direction],
                self.vjoy_id,
                self.hat_id
        ):
            raise VJoyError(
                "Failed to set hat direction - {}".format(
                    _error_string(self.vjoy_id, self.hat_id, self._direction)
                )
            )


class VJoy:

    """Represents a vJoy device present in the system."""

    # Duration of inactivity after which the keep alive routine is run
    keep_alive_timeout = 60

    # Axis name mapping
    axis_equivalence = {
        AxisCode.X: 1,
        AxisCode.Y: 2,
        AxisCode.Z: 3,
        AxisCode.RX: 4,
        AxisCode.RY: 5,
        AxisCode.RZ: 6,
        AxisCode.SL0: 7,
        AxisCode.SL1: 8
    }

    def __init__(self, vjoy_id: int) -> None:
        """Creates a new object.

        Args:
            vjoy_id: id of the vJoy device to initialize.
        """
        self.vjoy_id = None

        if not VJoyInterface.vJoyEnabled():
            logging.getLogger("system").error("vJoy is not currently running")
            raise VJoyError("vJoy is not currently running")
        if VJoyInterface.GetvJoyVersion() < 0x218:
            logging.getLogger("system").error(
                "Running incompatible vJoy version, 2.1.8 or higher required"
            )
            raise VJoyError("Running incompatible vJoy version, 2.1.8 or higher required")
        elif VJoyInterface.GetVJDStatus(vjoy_id) != VJoyState.Free.value:
            logging.getLogger("system").error(
                "Requested vJoy device is not available - vid: {}".format(vjoy_id)
            )
            raise VJoyError(
                "Requested vJoy device is not available - vid: {}".format(vjoy_id)
            )
        elif not VJoyInterface.AcquireVJD(vjoy_id):
            logging.getLogger("system").error(
                "Failed to acquire the vJoy device - vid: {}".format(vjoy_id)
            )
            raise VJoyError(
                "Failed to acquire the vJoy device - vid: {}".format(vjoy_id)
            )

        self.vjoy_id = vjoy_id
        self.pid = os.getpid()

        # Initialize all controls
        self._axis_lookup = {}
        self._axis_names = {}
        self._axis = self._init_axes()
        self._button = self._init_buttons()
        self._hat = self._init_hats()

        # Timestamp of the last time the device was used
        self._last_active = time.time()
        self._keep_alive_timer = threading.Timer(
            VJoy.keep_alive_timeout,
            self._keep_alive
        )
        self._keep_alive_timer.start()

        # Reset all controls
        self.reset()

    def ensure_ownership(self) -> None:
        """Ensure this device is still owned by the process.

        This object can only be constructed if it successfully acquires the
        vjoy device and destroys itself when relinquishing control. Therefore,
        it cannot ever not own the vJoy device.

        Under certain circumstances the vJoy devices are reset (issue #129).
        By checking for ownership and reacquiring if needed this can be solved.
        """
        if self.vjoy_id is None:
            return

        if self.pid != VJoyInterface.GetOwnerPid(self.vjoy_id):
            if not VJoyInterface.AcquireVJD(self.vjoy_id):
                logging.getLogger("system").error(
                    "Failed to re-acquire the vJoy device - vid: {}".format(
                        self.vjoy_id
                ))
                raise VJoyError(
                    "Failed to re-acquire the vJoy device - vid: {}".format(
                        self.vjoy_id
                ))

    def is_owned(self) -> bool:
        """Returns True if the vJoy device is owned by the current process.

        Returns:
            True if the current process owns this vJoy device, False othwerwise
        """
        if self.vjoy_id is not None:
            return self.pid == VJoyInterface.GetOwnerPid(self.vjoy_id)
        else:
            return False

    @property
    def axis_count(self) -> int:
        """Returns the number of axes present in this device.

        Returns:
            number of axes on this device
        """
        return int(len(self._axis))

    @property
    def button_count(self) -> int:
        """Returns the number of buttons present in this device.

        Returns:
            number of buttons on this device
        """
        return len(self._button)

    @property
    def hat_count(self) -> int:
        """Returns the number of hats present in this device.

        Returns:
            number of hats on this device
        """
        return len(self._hat)

    def axis_name(
            self,
            axis_id: Optional[int]=None,
            linear_index: Optional[int]=None
    ) -> str:
        """Returns the textual name of the requested axis.

        As there are two ways to refer to an axis, absolute in terms of the
        AxisName enum and relative, i.e. number based on the total number of
        axes present. This method deals with both methods and the user
        needs to request the correct one.

        Args:
            axis_id: absolute index of the axis whose name to return
            linear_index: relative index of the axis whose name to return

        Returns:
            name of the provided axis
        """
        if axis_id is not None:
            axis_id = VJoy.axis_equivalence.get(axis_id, axis_id)
            if not self.is_axis_valid(axis_id=axis_id):
                raise VJoyError(
                    "Invalid axis index requested - {}".format(
                        _error_string(self.vjoy_id, axis_id, "")
                    )
                )
            return self._axis_names[axis_id]
        elif linear_index is not None:
            if not self.is_axis_valid(linear_index=linear_index):
                raise VJoyError(
                    "Invalid linear index for axis lookup provided - {}".format(
                        _error_string(self.vjoy_id, linear_index, "")
                    )
                )
            return self._axis_names[self._axis_lookup[linear_index]]
        else:
            raise VJoyError("No vjoy_id or linear_index provided")

    def axis_id(self, linear_index: int) -> int:
        """Returns the absolute axis id corresponding to the relative one.

        Args:
            linear_index: the relative index of the desired axis

        Returns:
            absolute id of the axis
        """
        if not self.is_axis_valid(linear_index=linear_index):
            raise VJoyError(
                "Invalid linear index for axis lookup provided - {}".format(
                    _error_string(self.vjoy_id, linear_index, "")
                )
            )

        return self._axis_lookup[linear_index]

    def axis(
            self,
            axis_id: Optional[int]=None,
            linear_index: Optional[int]=None
    ) -> Axis:
        """Returns the axis object associated with the provided index.

        Args:
            axis_id: actual id of the axis which may not be contiguous
            linear_index: linear index of the axis independent of true ids

        Returns:
            Axis object corresponding to the provided index
        """
        if axis_id is not None:
            axis_id = VJoy.axis_equivalence.get(axis_id, axis_id)
            if not self.is_axis_valid(axis_id=axis_id):
                raise VJoyError(
                    "Invalid axis index requested - {}".format(
                        _error_string(self.vjoy_id, axis_id, "")
                    )
                )
            return self._axis[axis_id]
        elif linear_index is not None:
            if not self.is_axis_valid(linear_index=linear_index):
                raise VJoyError(
                    "Invalid linear index for axis lookup provided - {}".format(
                        _error_string(self.vjoy_id, linear_index, "")
                    )
                )
            return self._axis[self._axis_lookup[linear_index]]
        else:
            raise VJoyError("No vjoy_id or linear_index provided")

    def button(self, index: int) -> Button:
        """Returns the axis object associated with the provided index.

        Args:
            index: the index of the button to return

        Returns:
            Button object corresponding to the provided index
        """
        if index not in self._button:
            raise VJoyError(
                "Invalid button index requested - {}".format(
                    _error_string(self.vjoy_id, index, "")
                )
            )
        return self._button[index]

    def hat(self, index: int) -> Hat:
        """Returns the hat object associated with the provided index.

        Args:
            index: the index of the hat to return

        Returns:
            Hat object corresponding to the provided index
        """
        if index not in self._hat:
            raise VJoyError(
                "Invalid hat index requested - {}".format(
                    _error_string(self.vjoy_id, index, "")
                )
            )
        return self._hat[index]

    def is_axis_valid(
            self,
            axis_id: Optional[int]=None,
            linear_index: Optional[int]=None
    ) -> bool:
        """Returns whether an axis is valid.

        Args:
            axis_id: actual id of the axis which may not be contiguous
            linear_index: linear index of the axis independent of true ids

        Returns:
            True if the axis is valid, False otherwise
        """
        if axis_id is not None:
            return axis_id in self._axis
        elif linear_index is not None:
            return linear_index in self._axis_lookup
        else:
            raise VJoyError("No vjoy_id or linear_index provided")

    def is_button_valid(self, index: int) -> bool:
        """Returns whether the provided button index is valid.

        Args:
            index: button index to check

        Returns:
            True if the button is valid, False otherwise
        """
        return index in self._button

    def is_hat_valid(self, index: int) -> bool:
        """Returns whether the provided hat index is valid.

        Args:
            index: hat index to check

        Returns:
            True if the hat is valid, False otherwise
        """
        return index in self._hat

    def reset(self) -> None:
        """Resets the state of all inputs to their default state."""
        # Obtain the current state of all inputs
        axis_states = {}
        button_states = {}
        hat_states = {}

        for i, axis in self._axis.items():
            axis_states[i] = axis.value
        for i, button in self._button.items():
            button_states[i] = button.is_pressed
        for i, hat in self._hat.items():
            hat_states[i] = hat.direction

        # Perform reset using default vJoy functionality
        success = VJoyInterface.ResetVJD(self.vjoy_id)

        # Restore input states based on what we recorded
        if success:
            for i in self._axis:
                self._axis[i].set_absolute_value(axis_states[i])
            for i in self._button:
                self._button[i].is_pressed = button_states[i]
            for i in self._hat:
                self._hat[i].direction = hat_states[i]
        else:
            logging.getLogger("system").info(
                "Could not reset vJoy device, are we using it?"
            )

    def used(self) -> None:
        """Updates the timestamp of the last time the device has been used."""
        self._last_active = time.time()

    def invalidate(self) -> None:
        """Releases all resources claimed by this instance.

        Releases the lock on the vjoy device instance as well as terminating
        the keep alive timer.
        """
        if self.vjoy_id:
            self.reset()
            VJoyInterface.RelinquishVJD(self.vjoy_id)
            self.vjoy_id = None
            self._keep_alive_timer.cancel()

    def _keep_alive(self) -> None:
        """Timer callback ensuring the vJoy device stays active.

        If the device hasn't been used in the last 60 seconds the device will
        be reset to ensure it doesn't time out.
        """
        if self._last_active + VJoy.keep_alive_timeout < time.time():
            self.reset()
        self._keep_alive_timer = threading.Timer(
            VJoy.keep_alive_timeout,
            self._keep_alive
        )
        self._keep_alive_timer.start()

    def _init_axes(self) -> Dict[int, Axis]:
        """Retrieves all axes present on the vJoy device and creates their
        control objects.

        Returns:
            dictionary of Axis objects
        """
        axes = {}
        for i, axis in enumerate(AxisCode):
            if VJoyInterface.GetVJDAxisExist(self.vjoy_id, axis.value) > 0:
                axes[i+1] = Axis(self, axis.value)
                self._axis_names[i+1] = AxisNames.to_string(AxisNames(i + 1))
                self._axis_lookup[len(self._axis_names)] = i+1
                self._axis_lookup[axis] = i+1
        return axes

    def _init_buttons(self) -> Dict[int, Button]:
        """Retrieves all buttons present on the vJoy device and creates their
        control objects.

        Returns:
            dictionary of Button objects
        """
        buttons = {}
        for btn_id in range(1, VJoyInterface.GetVJDButtonNumber(self.vjoy_id)+1):
            buttons[btn_id] = Button(self, btn_id)
        return buttons

    def _init_hats(self) -> Dict[int, Hat]:
        """Retrieves all hats present on the vJoy device and creates their
        control objects.

        A single device can either have continuous or discrete hats, but
        not both at the same time.

        Returns:
            dictionary of Hat objects
        """
        hats = {}
        # We can't use discrete hats as such their existence is considered
        # an error
        if VJoyInterface.GetVJDDiscPovNumber(self.vjoy_id) > 0:
            error_msg = "vJoy is configured incorrectly. \n\n" \
                    "Please ensure hats are configured as 'Continuous' " \
                    "rather then '4 Directions'."
            logging.getLogger("system").error(error_msg)
            raise VJoyError(error_msg)
        # for hat_id in range(1, VJoyInterface.GetVJDDiscPovNumber(self.vjoy_id)+1):
        #     hats[hat_id] = Hat(self, hat_id, HatType.Discrete)
        for hat_id in range(1, VJoyInterface.GetVJDContPovNumber(self.vjoy_id)+1):
            hats[hat_id] = Hat(self, hat_id, HatType.Continuous)
        return hats

    def __str__(self) -> str:
        """Print information about the vJoy device we're holding.

        Returns:
            string representation of the vJoy device information
        """
        return "vJoyId={0:d} axis={1:d} buttons={2:d} hats={3:d}".format(
            self.vjoy_id,
            len(self._axis),
            len(self._button),
            len(self._hat)
        )


class VJoyProxy:

    """Manages the usage of vJoy and allows shared access all callbacks."""

    vjoy_devices = {}

    def __getitem__(self, index):
        """Returns the requested vJoy instance.

        Args:
            index: index of the vjoy device to return

        Returns:
            VJoy instance corresponding to the given id
        """
        if index in VJoyProxy.vjoy_devices:
            return VJoyProxy.vjoy_devices[index]
        else:
            if not isinstance(index, int):
                raise VJoyError("Integer ID for vjoy device ID expected")

            try:
                device = VJoy(index)
                VJoyProxy.vjoy_devices[index] = device
                return device
            except VJoyError as e:
                logging.getLogger("system").error(
                    f"Failed accessing vJoy id={index}, error is: {e}"
                )
                raise e

    @classmethod
    def reset(cls):
        """Relinquishes control over all held VJoy devices."""
        for device in VJoyProxy.vjoy_devices.values():
            device.invalidate()
        VJoyProxy.vjoy_devices = {}


def deadzone(
        value: float,
        low: float,
        low_center: float,
        high_center: float,
        high: float
) -> float:
    """Returns the mapped value taking the provided deadzone into
    account.

    The following relationship between the limits has to hold.
    -1 <= low < low_center <= 0 <= high_center < high <= 1

    Args:
        value: the raw input value
        low: low deadzone limit
        low_center: lower center deadzone limit
        high_center: upper center deadzone limit
        high: high deadzone limit

    Returns:
        Value clamped and interpolated based on the deadzone settings
    """
    if value >= 0:
        return min(1.0, max(0.0, (value - high_center) / abs(high - high_center)))
    else:
        return max(-1.0, min(0.0, (value - low_center) / abs(low - low_center)))