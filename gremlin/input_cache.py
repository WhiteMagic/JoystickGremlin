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

from typing import Dict, List
import uuid

from PySide6 import QtCore

from dill import DILL, GUID, UUID_LogicalDevice
from gremlin.common import SingletonDecorator
from gremlin import error, keyboard, logical_device, types


class JoystickWrapper:

    """Wraps joysticks and presents an API similar to vjoy."""

    class Input:

        """Represents a joystick input."""

        def __init__(self, joystick_guid: uuid.UUID, index: int) -> None:
            """Creates a new instance.

            Args:
                joystick_guid: unique id of the device instance
                index: index of the input
            """
            self._joystick_guid = joystick_guid
            self._index = index
            self._value = None

        def update(self, value: float | bool | types.HatDirection) -> None:
            """Updates the cached state of the specific input.

            Args:
                value: new value of the input
            """
            self._value = value

    class Axis(Input):

        """Represents a single axis of a joystick."""

        def __init__(self, joystick_guid: uuid.UUID, index: int) -> None:
            super().__init__(joystick_guid, index)

            self._value = 0.0

        @property
        def value(self) -> float:
            # FIXME: This bypasses calibration and any other possible
            #        mappings we might do in the future
            # return DILL.get_axis(self._joystick_guid, self._index) / float(32768)
            return self._value if self._value else 0.0

    class Button(Input):

        """Represents a single button of a joystick."""

        def __init__(self, joystick_guid: uuid.UUID, index: int) -> None:
            super().__init__(joystick_guid, index)

            self._value = False

        @property
        def is_pressed(self) -> bool:
            return self._value

    class Hat(Input):

        """Represents a single hat of a joystick,"""

        def __init__(self, joystick_guid: uuid.UUID, index: int) -> None:
            super().__init__(joystick_guid, index)

            self._value = types.HatDirection.Center.value

        @property
        def direction(self) -> tuple[int, int]:
            return self._value

    def __init__(self, device_guid: uuid.UUID) -> None:
        """Creates a new wrapper object for the given joystick.

        Args:
            device_guid: unique id of the joystick instance to wrap
        """
        self._device_guid = device_guid
        self._dill_guid = GUID.from_uuid(device_guid)
        if DILL.device_exists(self._dill_guid) is False:
            raise error.GremlinError(
                f"No device with the provided GUID '{device_guid}' exist"
            )

        self._info = DILL.get_device_information_by_guid(self._dill_guid)
        self._axis = self._init_axes()
        self._buttons = self._init_buttons()
        self._hats = self._init_hats()

    @property
    def device_guid(self) -> uuid.UUID:
        """Returns the unique ID of the joystick.

        Returns:
            Unique identifier of the joystick
        """
        return self._device_guid

    @property
    def name(self) -> str:
        """Returns the name of the joystick.

        Returns:
            Name of the joystick
        """
        return self._info.name

    def is_axis_valid(self, axis_index: int) -> bool:
        """Returns whether the specified axis exists for this device.

        Iterates over all known axes of this device and checks if one maps
        onto the named axis value.

        Args:
            axis_index: index of the axis in the AxisNames enum

        Returns:
            True the specified axis exists, False otherwise
        """
        for i in range(self._info.axis_count):
            if self._info.axis_map[i].axis_index == axis_index:
                return True
        return False

    def axis_reverse_lookup(self, axis_index: int) -> int:
        """Returns the linear index corresponding to the given axis index.

        Args:
            axis_index: index of the axis adhering to the AxisNames enum order

        Returns:
            linear index corresponding to the given axis index
        """
        for i in range(self._info.axis_count):
            if self._info.axis_map[i].axis_index == axis_index:
                return i + 1
        raise error.GremlinError(
            f"Axis reverse lookup failed for axis index {axis_index}"
        )

    def axis(self, index: int) -> Axis:
        """Returns the axis for the given index.

        The index is 1 based, i.e. the first axis starts with index 1.

        Args:
            index: index of the axis to return

        Returns:
            Axis instance corresponding to the given index
        """
        if index not in self._axis:
            raise error.GremlinError(
                f"Invalid axis {index} specified for device {self._device_guid}"
            )
        return self._axis[index]

    def button(self, index: int) -> Button:
        """Returns the Button instance for the given index.

        The index is 1 based, i.e. the first button starts with index 1.

        Args:
            index: index of the button to return

        Returns:
            Button instance corresponding to the given index
        """
        if not (0 < index < len(self._buttons)):
            raise error.GremlinError(
                f"Invalid button {index} specified for device {self._device_guid}"
            )
        return self._buttons[index]

    def hat(self, index: int) -> Hat:
        """Returns the Hat instance for the given index.

        The index is 1 based, i.e. the first hat starts with index 1.

        Args:
            index: index of the hat to return

        Returns:
            Hat instance corresponding to given index
        """
        if not (0 < index < len(self._hats)):
            raise error.GremlinError(
                f"Invalid hat {index} specified for device {self._device_guid}"
            )
        return self._hats[index]

    @property
    def axis_count(self) -> int:
        """Returns the number of axes of the joystick.

        Returns:
            Number of axes
        """
        return self._info.axis_count

    @property
    def button_count(self) -> int:
        """Returns the number of buttons on the joystick.

        Returns:
            Number of buttons
        """
        return self._info.button_count

    @property
    def hat_count(self) -> int:
        """Returns the number of hats on the joystick.

        Returns:
            Number of hats
        """
        return self._info.hat_count

    def _init_axes(self) -> Dict[int, JoystickWrapper.Axis]:
        """Initializes the axes of the joystick.

        Returns:
            dictionary of JoystickWrapper.Axis objects with their axis index
            as key rather than the axis number
        """
        axes = {}
        for i in range(self._info.axis_count):
            aid = self._info.axis_map[i].axis_index
            axes[aid] = JoystickWrapper.Axis(self._device_guid, aid)
        return axes

    def _init_buttons(self) -> List[JoystickWrapper.Button]:
        """Initializes the buttons of the joystick.

        Returns:
            list of JoystickWrapper.Button objects
        """
        buttons = [None,]
        for i in range(self._info.button_count):
            buttons.append(JoystickWrapper.Button(self._device_guid, i+1))
        return buttons

    def _init_hats(self) -> List[JoystickWrapper.Hat]:
        """Initializes the hats of the joystick.

        Returns:
            list of JoystickWrapper.Hat objects
        """
        hats = [None,]
        for i in range(self._info.hat_count):
            hats.append(JoystickWrapper.Hat(self._device_guid, i+1))
        return hats


@SingletonDecorator
class Joystick:

    """Allows read access to joystick state information."""

    # Dictionary of initialized joystick devices
    devices = {}

    def __getitem__(
        self,
        device_guid: uuid.UUID
    ) -> logical_device.LogicalDevice | JoystickWrapper:
        """Returns the requested joystick instance.

        If the joystick instance exists it is returned directly, otherwise
        it is first created and then returned.

        Args:
            device_guid: unique identifier of the joystick device

        Returns:
            The corresponding joystick device.
        """
        if device_guid not in self.devices:
            # Handle the intermediate output device first
            if device_guid == UUID_LogicalDevice:
                self.devices[device_guid] = logical_device.LogicalDevice()
            else:
                # If the device exists add process it and add it, otherwise
                # throw an exception
                if DILL.device_exists(GUID.from_uuid(device_guid)):
                    self.devices[device_guid] = JoystickWrapper(device_guid)
                else:
                    raise error.GremlinError(
                        f"No device with guid '{device_guid}' exists"
                    )

        return self.devices[device_guid]


@SingletonDecorator
class Keyboard:

    """Provides access to the keyboard state."""

    def __init__(self) -> None:
        """Initialises a new object."""
        self._keyboard_state = {}

    def update(self, key: keyboard.Key, is_pressed: bool) -> None:
        """Updates the state of a key.

        Args:
            key: input being changed
            is_pressed: whether the key is pressed
        """
        self._keyboard_state[key] = is_pressed

    def is_pressed(self, key: keyboard.Key | str) -> bool:
        """Returns whether or not the key is pressed.

        Args:
            key: input whose state to return

        Returns:
            True if the key is pressed, False otherwise
        """
        if isinstance(key, str):
            key = keyboard.key_from_name(key)
        return self._keyboard_state.get(key, False)
