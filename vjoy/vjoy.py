# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
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
import threading
import time

from vjoy.vjoy_interface import VJoyState, VJoyInterface
from gremlin.error import VJoyError


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


class Axis(object):

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

        # If this is not the case our value setter needs to change
        assert(self._min_value == 0)

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
        if 1.0 - abs(value) < -0.001:
            raise VJoyError(
                "Wrong data type provided, has to be float in [-1, 1],"
                " provided value was {:.2f}".format(value)
            )
        self._value = min(1.0, max(-1.0, value))

        if not VJoyInterface.SetAxis(
                int(self._half_range + self._half_range * self._value),
                self.vjoy_id,
                self.axis_id
        ):
            raise VJoyError("Failed setting axis value")
        self.vjoy_dev.used()


class Button(object):

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


class Hat(object):

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


class VJoy(object):

    """Represents a vJoy device present in the system."""

    def __init__(self, vjoy_id):
        """Creates a new object.

        :param vjoy_id id of the vJoy device to initialize.
        """
        self.vjoy_id = None

        if not VJoyInterface.vJoyEnabled():
            raise VJoyError("vJoy is not currently running")
        elif VJoyInterface.GetVJDStatus(vjoy_id) != VJoyState.Free.value:
            raise VJoyError("Requested vJoy device is not available")
        elif not VJoyInterface.AcquireVJD(vjoy_id):
            raise VJoyError("Failed to acquire the vJoy device")

        self.vjoy_id = vjoy_id

        # Initialize all controls
        self._axis = self._init_axes()
        self._button = self._init_buttons()
        self._hat = self._init_hats()

        # Timestamp of the last time the device was used
        self._last_active = time.time()
        self._keep_alive_timer = threading.Timer(60.0, self._keep_alive)
        self._keep_alive_timer.start()

        # Reset all controls
        VJoyInterface.ResetVJD(self.vjoy_id)

    def axis(self, index):
        return self._axis[index]

    def button(self, index):
        return self._button[index]

    def hat(self, index):
        return self._hat[index]

    def reset(self):
        """Resets the state of all inputs to their default state."""
        VJoyInterface.ResetVJD(self.vjoy_id)

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
        if self._last_active + 60 < time.time():
            self.reset()
        self._keep_alive_timer = threading.Timer(60.0, self._keep_alive)
        self._keep_alive_timer.start()

    def _init_buttons(self):
        """Retrieves all buttons present on the vJoy device and creates their
        control objects.

        :returns list of Button objects
        """
        buttons = {}
        for btn_id in range(1, VJoyInterface.GetVJDButtonNumber(self.vjoy_id)+1):
            buttons[btn_id] = Button(self, btn_id)
        return buttons

    def _init_axes(self):
        """Retrieves all axes present on the vJoy device and creates their
        control objects.

        :returns dictionary of Axis objects
        """
        axes = {}
        for i, axis in enumerate(AxisName):
            if VJoyInterface.GetVJDAxisExist(self.vjoy_id, axis.value):
                axes[axis] = Axis(self, axis.value)
                axes[i+1] = Axis(self, axis.value)
        return axes

    def _init_hats(self):
        """Retrieves all hats present on the vJoy device and creates their
        control objects.

        A single device can either have continuous or discrete hats, but
        not both at the same time.

        :returns list of Hat objects
        """
        hats = {}
        for hat_id in range(1, VJoyInterface.GetVJDDiscPovNumber(self.vjoy_id)+1):
            hats[hat_id] = Hat(self, hat_id, HatType.Discrete)
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
