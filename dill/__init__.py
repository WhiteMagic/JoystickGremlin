# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import copy
from enum import Enum
import sys
from typing import Callable
import uuid

from gremlin.app_platform import app_backend as _app_backend

# Import the portable ctypes struct definitions from the PAL base layer.
# They are defined once here so that WindowsDillBackend and LinuxDillBackend
# can both produce _DeviceSummary / _JoystickInputData instances that are
# the *same Python class* — crucial for isinstance() and ctypes field access.
from dill.platform.base.types import (
    _GUID,
    _AxisMap,
    _DeviceSummary,
    _JoystickInputData,
    ctwt,           # noqa: F401 — re-exported public API
    C_EVENT_CALLBACK,           # noqa: F401 — re-exported public API
    C_DEVICE_CHANGE_CALLBACK,   # noqa: F401 — re-exported public API
)
from dill.platform.base.backend import AbstractDillBackend


class DILLError(Exception):

    """Exception raised when an error occurs within the DILL module."""

    def __init__(self, value: str) -> None:
        """Creates a new error instance with the given message.

        Args:
            value: the error message to use
        """
        super().__init__(value)


def _attempt_decoding_device_name(data: bytes) -> str:
    """Attempts to decode the device name using the system's ANSI code page.

    Should errors occur during decoding, the errors are ignored and the
    undecodable bytes are simply dropped.

    Args:
        data: The raw bytes representing the device name.

    Returns:
        The decoded device name.
    """
    return data.decode(_app_backend.ansi_code_page(), errors="ignore")


_GUID_SysKeyboard = _GUID()
_GUID_SysKeyboard.Data1 = 0x6F1D2B61
_GUID_SysKeyboard.Data2 = 0xD5A0
_GUID_SysKeyboard.Data3 = 0x11CF
_GUID_SysKeyboard.Data4[0] = 0xBF
_GUID_SysKeyboard.Data4[1] = 0xC7
_GUID_SysKeyboard.Data4[2] = 0x44
_GUID_SysKeyboard.Data4[3] = 0x45
_GUID_SysKeyboard.Data4[4] = 0x53
_GUID_SysKeyboard.Data4[5] = 0x54
_GUID_SysKeyboard.Data4[6] = 0x00
_GUID_SysKeyboard.Data4[7] = 0x00

_GUID_Virtual = _GUID()
_GUID_Virtual.Data1 = 0x89d5e905
_GUID_Virtual.Data2 = 0x1e26
_GUID_Virtual.Data3 = 0x4c52
_GUID_Virtual.Data4[0] = 0xad
_GUID_Virtual.Data4[1] = 0x46
_GUID_Virtual.Data4[2] = 0x7b
_GUID_Virtual.Data4[3] = 0xcc
_GUID_Virtual.Data4[4] = 0x06
_GUID_Virtual.Data4[5] = 0xdf
_GUID_Virtual.Data4[6] = 0x4c
_GUID_Virtual.Data4[7] = 0x20

_GUID_LogicalDevice = _GUID()
_GUID_LogicalDevice.Data1 = 0xF0AF472F
_GUID_LogicalDevice.Data2 = 0x8E17
_GUID_LogicalDevice.Data3 = 0x493B
_GUID_LogicalDevice.Data4[0] = 0xA1
_GUID_LogicalDevice.Data4[1] = 0xEB
_GUID_LogicalDevice.Data4[2] = 0x73
_GUID_LogicalDevice.Data4[3] = 0x33
_GUID_LogicalDevice.Data4[4] = 0xEE
_GUID_LogicalDevice.Data4[5] = 0x85
_GUID_LogicalDevice.Data4[6] = 0x43
_GUID_LogicalDevice.Data4[7] = 0xF2

_GUID_Invalid = _GUID()
_GUID_Invalid.Data1 = 0x00000000
_GUID_Invalid.Data2 = 0x0000
_GUID_Invalid.Data3 = 0x0000
_GUID_Invalid.Data4[0] = 0x00
_GUID_Invalid.Data4[1] = 0x00
_GUID_Invalid.Data4[2] = 0x00
_GUID_Invalid.Data4[3] = 0x00
_GUID_Invalid.Data4[4] = 0x00
_GUID_Invalid.Data4[5] = 0x00
_GUID_Invalid.Data4[6] = 0x00
_GUID_Invalid.Data4[7] = 0x00


class GUID:

    """Python GUID class."""

    def __init__(self, guid: _GUID) -> None:
        """Creates a new instance.

        Args:
            guid: Mapping of a C struct representing a device GUID
        """
        assert isinstance(guid, _GUID)
        self._ctypes_guid = copy.deepcopy(guid)
        self.guid = (
            guid.Data1,
            guid.Data2,
            guid.Data3,
            (guid.Data4[0] << 8) + guid.Data4[1],
            (guid.Data4[2] << 40) + (guid.Data4[3] << 32) +
            (guid.Data4[4] << 24) + (guid.Data4[5] << 16) +
            (guid.Data4[6] << 8) + guid.Data4[7]
        )

    @staticmethod
    def from_str(value: str) -> GUID:
        """Reads a string GUID representation into the internal data format.

        This transforms a GUID of the form {B4CA5720-11D0-11E9-8002-444553540000}
        into the underlying raw and exposed objects used within DILL.

        Args:
            value: the string representation of the GUID

        Returns:
            GUID object representing the provided value
        """
        return GUID.from_uuid(uuid.UUID(value))

    @staticmethod
    def from_uuid(value: uuid.UUID) -> GUID:
        """Converts a unique identifier from the UUID type to the GUID type.

        Args:
            value: unique identifier to be converted

        Returns:
            Unique identifier in GUID format
        """
        try:
            raw_guid = _GUID()
            raw_guid.Data1 = int.from_bytes(value.bytes[0:4], "big")
            raw_guid.Data2 = int.from_bytes(value.bytes[4:6], "big")
            raw_guid.Data3 = int.from_bytes(value.bytes[6:8], "big")
            for i in range(8):
                raw_guid.Data4[i] = value.bytes[8 + i]

            return GUID(raw_guid)
        except (ValueError, AttributeError) as _:
            raise DILLError(f"Failed parsing GUID from value '{value}'")

    @property
    def ctypes(self) -> _GUID:
        """Returns the object mapping the C structure.

        Returns:
            Mapping of a C GUID structure
        """
        return self._ctypes_guid

    @property
    def uuid(self) -> uuid.UUID:
        """Returns a UUID representation of this GUID.

        Returns:
            UUID object representation of this GUID instance.
        """
        return uuid.UUID(str(self))

    def __str__(self) -> str:
        """Returns a string representation of the GUID.

        Returns:
            GUID string representation in hexadecimal
        """
        return "{:08X}-{:04X}-{:04X}-{:04X}-{:012X}".format(
            self.guid[0],
            self.guid[1],
            self.guid[2],
            self.guid[3],
            self.guid[4]
        )

    def __eq__(self, other: GUID) -> bool:
        """Returns whether or not two GUID instances are identical.

        Args:
            other: Instance with which to perform the equality comparison

        Returns:
            True if the two GUIDs are equal, False otherwise
        """
        return hash(self) == hash(other)

    def __lt__(self, other: GUID) -> bool:
        """Returns the result of the < operator.

        Args:
            other: Instance with which to perform the equality comparison

        Returns:
            True if this instance is < other, False otherwise
        """
        return str(self) < str(other)

    def __hash__(self) -> int:
        """Returns the hash of this GUID.

        Returns:
            The has computed from this GUID
        """
        return hash((
            self._ctypes_guid.Data1,
            self._ctypes_guid.Data2,
            self._ctypes_guid.Data3,
            self._ctypes_guid.Data4[0],
            self._ctypes_guid.Data4[1],
            self._ctypes_guid.Data4[2],
            self._ctypes_guid.Data4[3],
            self._ctypes_guid.Data4[4],
            self._ctypes_guid.Data4[5],
            self._ctypes_guid.Data4[6],
            self._ctypes_guid.Data4[7]
        ))


# Expose set of pre-defined GUID instances
GUID_Keyboard = GUID(_GUID_SysKeyboard)
UUID_Keyboard = GUID_Keyboard.uuid
GUID_Virtual = GUID(_GUID_Virtual)
UUID_Virtual = GUID_Virtual.uuid
GUID_LogicalDevice = GUID(_GUID_LogicalDevice)
UUID_LogicalDevice = GUID_LogicalDevice.uuid
GUID_Invalid = GUID(_GUID_Invalid)
UUID_Invalid = GUID_Invalid.uuid


class InputType(Enum):

    """Enumeration of valid input types that can be reported."""

    Axis = 1,
    Button = 2,
    Hat = 3

    @staticmethod
    def from_ctype(value: int) -> InputType:
        """Returns the enum type corresponding to the provided value.

        Args:
            value: int value representing the input type according to DILL

        Returns:
            Enum value representing the correct InputType
        """
        if value == 1:
            return InputType.Axis
        elif value == 2:
            return InputType.Button
        elif value == 3:
            return InputType.Hat
        else:
            raise DILLError(f"Invalid input type value {value}")


class DeviceActionType(Enum):

    """Represents the state change of a device."""

    Connected = 1
    Disconnected = 2

    @staticmethod
    def from_ctype(value: int) -> DeviceActionType:
        """Returns the enum type corresponding to the provided value.

        Args:
            value: int value representing the action type according to DILL

        Returns:
            Enum value representing the correct DeviceAction
        """
        if value == 1:
            return DeviceActionType.Connected
        elif value == 2:
            return DeviceActionType.Disconnected
        else:
            raise DILLError(f"Invalid device action type {value}")


class InputEvent:

    """Holds information about a single event.

    An event is an axis, button, or hat changing its state. The type of
    input, the index, and the new value as well as device GUID are reported.
    """

    def __init__(self, data: _JoystickInputData) -> None:
        """Creates a new instance.

        Args:
            data: data received from DILL and to be held by this instance
        """
        self.device_guid = GUID(data.device_guid)
        self.input_type = InputType.from_ctype(data.input_type)
        self.input_index = int(data.input_index)
        self.value = int(data.value)


class AxisMap:

    """Holds information about a single axis map entry.

    An AxisMap holds a mapping from an axis' sequential index to the actual
    descriptive DirectInput axis index.
    """

    def __init__(self, data: _AxisMap) -> None:
        """Creates a new instance.

        Args:
            data: data received from DILL and to be held by this instance
        """
        self.linear_index = data.linear_index
        self.axis_index = data.axis_index


class DeviceSummary:

    """Holds information about a single device.

    This summary holds static information about a single device's layout.
    """

    def __init__(self, data: _DeviceSummary) -> None:
        """Creates a new instance.

        Args:
            data: data received from DILL and to be held by this instance
        """
        self.device_guid = GUID(data.device_guid)
        self.vendor_id = data.vendor_id
        self.product_id = data.product_id
        self.joystick_id = data.joystick_id
        # The name of devices is encoded based on the system's local code page.
        # Thus we attempt to decode them, but failures simply result in
        # dropped characters.
        self.name = _attempt_decoding_device_name(data.name)
        self.axis_count = data.axis_count
        self.button_count = data.button_count
        self.hat_count = data.hat_count
        self.axis_map = []
        for i in range(8):
            self.axis_map.append(AxisMap(data.axis_map[i]))
        self.axis_lookup = {}
        for entry in self.axis_map:
            self.axis_lookup[entry.axis_index] = entry.linear_index
        self.vjoy_id = -1

    @property
    def is_virtual(self) -> bool:
        """Returns if a device is virtual.

        Returns:
            True if the device is a virtual vJoy device, False otherwise
        """
        return self.vendor_id == 0x1234 and self.product_id == 0xBEAD

    def set_vjoy_id(self, vjoy_id: int) -> None:
        """Sets the vJoy id for this device summary.

        Settings the vJoy device id is necessary, as DILL cannot know these
        ids, and as such this has to be entered when DirectInput devices and
        vJoy devices are linked.

        Args:
            vjoy_id: index of the vJoy device corresponding to this
                DirectInput device
        """
        assert self.is_virtual is True
        self.vjoy_id = vjoy_id


# ---------------------------------------------------------------------------
# Platform backend selection
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    from dill.platform.windows.backend import WindowsDillBackend
    _dill_backend: AbstractDillBackend = WindowsDillBackend()
elif sys.platform.startswith("linux"):
    from dill.platform.linux.backend import LinuxDillBackend
    _dill_backend: AbstractDillBackend = LinuxDillBackend()
else:
    raise DILLError(f"Unsupported platform: {sys.platform}")


# ---------------------------------------------------------------------------
# Public API — thin wrapper that delegates to the platform backend
# ---------------------------------------------------------------------------

class DILL:

    """Exposes joystick-device functions via a platform-appropriate backend."""

    _dill_initialized = False

    @staticmethod
    def init() -> None:
        """Initializes the DILL backend.

        This has to be called before any other DILL interactions can take place.
        """
        if not DILL._dill_initialized:
            _dill_backend.init()
            DILL._dill_initialized = True

    @staticmethod
    def set_input_event_callback(callback: Callable[[InputEvent], None]) -> None:
        """Sets the callback function to use for input events.

        The provided callback function will be executed whenever an event
        occurs by the DILL library providing and InputEvent object to said
        callback.

        Args:
            callback: function to execute when an event occurs
        """
        _dill_backend.set_input_event_callback(callback)

    @staticmethod
    def set_device_change_callback(
            callback: Callable[[DeviceSummary], None]
    ) -> None:
        """Sets the callback function to use for device change events.

        The provided function will be executed whenever the status of a
        device changes, providing a DeviceSummary object to the callback.

        Args:
            callback: function to execute when an event occurs
        """
        _dill_backend.set_device_change_callback(callback)

    @staticmethod
    def get_device_count() -> int:
        """Returns the number of connected devices.

        Returns:
            The number of devices connected
        """
        return _dill_backend.get_device_count()

    @staticmethod
    def get_device_information_by_index(index: int) -> DeviceSummary:
        """Returns device information for the given index.

        Args:
            index: index of the device for which to return information

        Returns:
            Structure containing detailed information about the desired device
        """
        return DeviceSummary(_dill_backend.get_device_information_by_index(index))

    @staticmethod
    def get_device_information_by_guid(guid: GUID) -> DeviceSummary:
        """Returns device information for the given GUID.

        Args:
            guid: GUID of the device for which to return information

        Returns:
            Structure containing detailed information about the desired device
        """
        return DeviceSummary(
            _dill_backend.get_device_information_by_guid(guid.ctypes)
        )

    @staticmethod
    def get_axis(guid: GUID, index: int) -> int:
        """Returns the state of the specified axis for a specific device.

        Args:
            guid: GUID of the device of interest
            index: Index of the axis to return the value of

        Returns:
            Current value of the specific axis for the desired device
        """
        return _dill_backend.get_axis(guid.ctypes, index)

    @staticmethod
    def get_button(guid: GUID, index: int) -> bool:
        """Returns the state of the specified button for a specific device.

        Args:
            guid: GUID of the device of interest
            index: Index of the button to return the value of

        Returns:
            Current value of the specific button for the desired device
        """
        return _dill_backend.get_button(guid.ctypes, index)

    @staticmethod
    def get_hat(guid: GUID, index: int) -> int:
        """Returns the state of the specified hat for a specific device.

        Args:
            guid: GUID of the device of interest
            index: Index of the hat to return the value of

        Returns:
            Current value of the specific hat for the desired device
        """
        return _dill_backend.get_hat(guid.ctypes, index)

    @staticmethod
    def get_device_name(guid: GUID) -> str:
        """Returns the name of the device specified by the provided GUID.

        Args:
            guid: GUID of the device of which to return the name

        Returns:
            Name of the specified device
        """
        return DeviceSummary(
            _dill_backend.get_device_information_by_guid(guid.ctypes)
        ).name

    @staticmethod
    def device_exists(guid: GUID) -> bool:
        """Returns whether or not a specific device is connected.

        Args:
            guid: GUID of the device to check whether or not it is connected

        Returns:
            True if the device is connected, False otherwise
        """
        return _dill_backend.device_exists(guid.ctypes)
