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


import ctypes
import enum
import logging
import threading
import time

from vjoy.vjoy_interface import VJoyState, VJoyInterface
from gremlin.error import VJoyError
import gremlin.common
import gremlin.spline


class AxisName(enum.Enum):

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


class Axis:

    """Represents an analog axis in vJoy, allows setting the value
    of the axis."""

    def __init__(self, vjoy_dev, axis_id):
        """Creates a new object.

        :param vjoy_dev the vJoy device this axis belongs to
        :param axis_id the id of the axis this object controls
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
            raise VJoyError("vJoy axis minimum value is not 0")

    def set_response_curve(self, spline_type, control_points):
        """Sets the response curve to use for the axis.

        :param spline_type the type of spline to use
        :param control_points the control points defining the spline
        """
        if spline_type == "cubic-spline":
            self._response_curve_fn = gremlin.spline.CubicSpline(control_points)
        elif spline_type == "cubic-bezier-spline":
            self._response_curve_fn = \
                gremlin.spline.CubicBezierSpline(control_points)
        else:
            logging.getLogger("system").error("Invalid spline type specified")
            self._response_curve_fn = lambda x: x

    def set_deadzone(self, low, center_low, center_high, high):
        """Sets the deadzone for the axis.

        :param low low deadzone limit
        :param center_low lower center deadzone limit
        :param center_high upper center deadzone limit
        :param high high deadzone limit
        """
        self._deadzone_fn = lambda x: deadzone(
            x, low, center_low, center_high, high
        )

    @property
    def value(self):
        """Returns the axis position as a value between [-1, 1]"

        :return position of the axis as a value between [-1, 1]
        """
        self.vjoy_dev.used()
        return self._value

    @value.setter
    def value(self, value):
        """Sets the position of the axis based on a value between [-1, 1].

        :param value the position of the axis in the range [-1, 1]
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
        self._value = self._response_curve_fn(
            self._deadzone_fn(min(1.0, max(-1.0, value)))
        )

        if not VJoyInterface.SetAxis(
                int(self._half_range + self._half_range * self._value),
                self.vjoy_id,
                self.axis_id
        ):
            raise VJoyError("Failed setting axis value")
        self.vjoy_dev.used()

    def set_absolute_value(self, value):
        """Sets the position of the axis based on a value between [-1, 1].

        In comparison to the value setter this function bypasses the
        deadzone and response curve settings.

        :param value the position of the axis in the range [-1, 1]
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
            raise VJoyError("Failed setting axis value")
        self.vjoy_dev.used()


class Button:

    """Represents a button in vJoy, allows pressing and releasing it."""

    def __init__(self, vjoy_dev, button_id):
        """Creates a new object.

        :param vjoy_dev the vJoy device this button belongs to
        :param button_id the id of the button this object controls
        """
        self.vjoy_dev = vjoy_dev
        self.vjoy_id = vjoy_dev.vjoy_id
        self.button_id = button_id
        self._is_pressed = False

    @property
    def is_pressed(self):
        """Returns whether or not the button is pressed.

        :return True if the button is pressed, False otherwise
        """
        self.vjoy_dev.used()
        return self._is_pressed

    @is_pressed.setter
    def is_pressed(self, is_pressed):
        """Sets the state of the button.

        :param is_pressed True if the button is pressed, False otherwise
        """
        assert(isinstance(is_pressed, bool))
        self._is_pressed = is_pressed
        if not VJoyInterface.SetBtn(
                self._is_pressed,
                self.vjoy_id,
                self.button_id
        ):
            raise VJoyError("Failed updating button state")
        self.vjoy_dev.used()


class Hat:

    """Represents a discrete hat in vJoy, allows setting the direction
    of the hat."""

    # Recognized direction names
    to_discrete_direction = {
        (0, 1): 0,
        (1, 0): 1,
        (0, -1): 2,
        (-1, 0): 3,
        (0, 0): -1
    }

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

    def __init__(self, vjoy_dev, hat_id, hat_type):
        """Creates a new object.

        :param vjoy_dev the vJoy device this hat belongs to
        :param hat_id the id of the hat this object controls
        """
        self.vjoy_dev = vjoy_dev
        self.vjoy_id = vjoy_dev.vjoy_id
        self.hat_id = hat_id
        self._direction = (0, 0)
        self.hat_type = hat_type

    @property
    def direction(self):
        """Returns the current direction of the hat.

        :return current direction of the hat encoded as a tuple (x, y)
        """
        self.vjoy_dev.used()
        return self._direction

    @direction.setter
    def direction(self, direction):
        """Sets the direction of the hat.

        :param direction the new direction of the hat
        """
        if self.hat_type == HatType.Discrete:
            self._set_discrete_direction(direction)
        elif self.hat_type == HatType.Continuous:
            self._set_continuous_direction(direction)
        else:
            raise VJoyError("Invalid hat type specified")
        self.vjoy_dev.used()

    def _set_discrete_direction(self, direction):
        """Sets the direction of a discrete hat.

        :param direction the direction of the hat
        """
        if direction not in Hat.to_discrete_direction:
            raise VJoyError(
                "Invalid direction specified: {}".format(str(direction))
            )

        self._direction = direction
        if not VJoyInterface.SetDiscPov(
                Hat.to_discrete_direction[direction],
                self.vjoy_id,
                self.hat_id
        ):
            raise VJoyError("Failed to set hat direction")

    def _set_continuous_direction(self, direction):
        """Sets the direction of a continuous hat.

        :param direction the angle in degree of the hat
        """
        if direction not in Hat.to_continuous_direction:
            raise VJoyError(
                "Invalid direction specified: {}".format(str(direction))
            )

        self._direction = direction
        if not VJoyInterface.SetContPov(
                Hat.to_continuous_direction[direction],
                self.vjoy_id,
                self.hat_id
        ):
            raise VJoyError("Failed to set hat direction")


class VJoy:

    """Represents a vJoy device present in the system."""

    # Duration of inactivity after which the keep alive routine is run
    keep_alive_timeout = 60

    def __init__(self, vjoy_id):
        """Creates a new object.

        :param vjoy_id id of the vJoy device to initialize.
        """
        self.vjoy_id = None

        if not VJoyInterface.vJoyEnabled():
            logging.getLogger("system").error("vJoy is not currently running")
            raise VJoyError("vJoy is not currently running")
        if VJoyInterface.GetvJoyVersion() != 0x218:
            logging.getLogger("system").error(
                "Running incompatible vJoy version, 2.1.8 required"
            )
            raise VJoyError("Running incompatible vJoy version, 2.1.8 required")
        elif VJoyInterface.GetVJDStatus(vjoy_id) != VJoyState.Free.value:
            logging.getLogger("system").error(
                "Requested vJoy device is not available"
            )
            raise VJoyError("Requested vJoy device is not available")
        elif not VJoyInterface.AcquireVJD(vjoy_id):
            logging.getLogger("system").error(
                "Failed to acquire the vJoy device"
            )
            raise VJoyError("Failed to acquire the vJoy device")

        self.vjoy_id = vjoy_id

        # Initialize all controls
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

    @property
    def axis_count(self):
        return int(len(self._axis) / 2)

    @property
    def button_count(self):
        return len(self._button)

    @property
    def hat_count(self):
        return len(self._hat)

    def axis_name_by_index(self, index):
        """Returns the name of the axis based on linear enumeration.

        This will return the name of the axis by converting a simple counting
        index into the vJoy axis id / name combo.

        :param index index of the axis
        :return name of the axis
        """
        keys = sorted(self._axis_names.keys())
        return self._axis_names[keys[index]]

    def axis_name_by_id(self, index):
        return self._axis_names[index]

    def axis(self, index):
        """Returns the axis object associated with the provided index.

        :param index the index of the axis to return
        :return Axis object corresponding to the provided index
        """
        if index not in self._axis:
            raise VJoyError("Invalid axis index requested: {:d}".format(index))
        return self._axis[index]

    def button(self, index):
        """Returns the axis object associated with the provided index.

        :param index the index of the button to return
        :return Button object corresponding to the provided index
        """
        if index not in self._button:
            raise VJoyError("Invalid button index requested: {:d}".format(index))
        return self._button[index]

    def hat(self, index):
        """Returns the hat object associated with the provided index.

        :param index the index of the hat to return
        :return Hat object corresponding to the provided index
        """
        if index not in self._hat:
            raise VJoyError("Invalid hat index requested: {:d}".format(index))
        return self._hat[index]

    def is_axis_valid(self, index):
        """Returns whether or not an axis is valid.

        :param index the index of the axis to test
        :return True if the axis is valid, False otherwise
        """
        return index in self._axis

    def is_button_valid(self, index):
        """Returns whether or not the provided button index is valid.

        :param index button index to check
        :return True if the button is valid, False otherwise
        """
        return index in self._button

    def is_hat_valid(self, index):
        """Returns whether or not the provided hat index is valid.

        :param index hat index to check
        :return True if the hat is valid, False otherwise
        """
        return index in self._hat

    def reset(self):
        """Resets the state of all inputs to their default state."""
        # Obtain the current state of all inputs
        axis_states = {}
        button_states = {}
        hat_states = {}

        for axis_name in AxisName:
            if self.is_axis_valid(axis_name):
                axis_states[axis_name] = self._axis[axis_name].value
        for id, button in self._button.items():
            button_states[id] = button.is_pressed
        for id, hat in self._hat.items():
            hat_states[id] = hat.direction

        # Perform reset using default vJoy functionality
        VJoyInterface.ResetVJD(self.vjoy_id)

        # Restore input states based on what we recorded
        for axis_name, value in axis_states.items():
            self._axis[axis_name].set_absolute_value(value)
        for id in self._button:
            self._button[id].is_pressed = button_states[id]
        for id in self._hat:
            self._hat[id].direction = hat_states[id]

    def used(self):
        """Updates the timestamp of the last time the device has been used."""
        self._last_active = time.time()

    def invalidate(self):
        """Releases all resources claimed by this instance.

        Releases the lock on the vjoy device instance as well as terminating
        the keep alive timer.
        """
        if self.vjoy_id:
            self.reset()
            VJoyInterface.RelinquishVJD(self.vjoy_id)
            self.vjoy_id = None
            self._keep_alive_timer.cancel()

    def _keep_alive(self):
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

    def _init_axes(self):
        """Retrieves all axes present on the vJoy device and creates their
        control objects.

        :returns dictionary of Axis objects
        """
        axes = {}
        for i, axis in enumerate(AxisName):
            if VJoyInterface.GetVJDAxisExist(self.vjoy_id, axis.value) > 0:
                axes[axis] = Axis(self, axis.value)
                axes[i+1] = axes[axis]
                self._axis_names[i+1] = gremlin.common.vjoy_axis_names[i]
        return axes

    def _init_buttons(self):
        """Retrieves all buttons present on the vJoy device and creates their
        control objects.

        :returns list of Button objects
        """
        buttons = {}
        for btn_id in range(1, VJoyInterface.GetVJDButtonNumber(self.vjoy_id)+1):
            buttons[btn_id] = Button(self, btn_id)
        return buttons

    def _init_hats(self):
        """Retrieves all hats present on the vJoy device and creates their
        control objects.

        A single device can either have continuous or discrete hats, but
        not both at the same time.

        :returns list of Hat objects
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

    def __str__(self):
        """Print information about the vJoy device we're holding.

        :returns string representation of the vJoy device information
        """
        return "vJoyId={0:d} axis={1:d} buttons={2:d} hats={3:d}".format(
            self.vjoy_id,
            len(self.axis),
            len(self.button),
            len(self.hat)
        )


def deadzone(value, low, low_center, high_center, high):
    """Returns the mapped value taking the provided deadzone into
    account.

    The following relationship between the limits has to hold.
    -1 <= low < low_center <= 0 <= high_center < high <= 1

    :param value the raw input value
    :param low low deadzone limit
    :param low_center lower center deadzone limit
    :param high_center upper center deadzone limit
    :param high high deadzone limit
    :return corrected value
    """
    if value >= 0:
        return min(1, max(0, (value - high_center) / abs(high - high_center)))
    else:
        return max(-1, min(0, (value - low_center) / abs(low - low_center)))