# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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


import copy
import ctypes
import ctypes.wintypes as ctwt
from enum import Enum
import os
import time


class DILLError(Exception):

    """Exception raised when an error occurs within the DILL module."""

    def __init__(self, value):
        super().__init__(value)


class _GUID(ctypes.Structure):

    """Strcture mapping C information into a set of Python readable values."""

    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_uint8 * 8)
    ]


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


class _JoystickInputData(ctypes.Structure):

    """Mapping for the JoystickInputData C structure."""

    _fields_ = [
        ("device_guid", _GUID),
        ("input_type", ctypes.c_uint8),
        ("input_index", ctypes.c_uint8),
        ("value", ctwt.LONG)
    ]


class _AxisMap(ctypes.Structure):

    """Mapping for the AxisMap C structure."""

    _fields_ = [
        ("linear_index", ctwt.DWORD),
        ("axis_index", ctwt.DWORD)
    ]


class _DeviceSummary(ctypes.Structure):

    """Mapping for the DeviceSummary C structure."""

    _fields_ = [
        ("device_guid", _GUID),
        ("vendor_id", ctwt.DWORD),
        ("product_id", ctwt.DWORD),
        ("joystick_id", ctwt.DWORD),
        ("name", ctypes.c_char * ctwt.MAX_PATH),
        ("axis_count", ctwt.DWORD),
        ("button_count", ctwt.DWORD),
        ("hat_count", ctwt.DWORD),
        ("axis_map", _AxisMap * 8)
    ]


class GUID:

    """Python GUID class."""

    def __init__(self, guid):
        """Creates a new instance.

        Parameters
        ==========
        guid : _GUID
            Mapping of a C struct representing a device GUID
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

    @property
    def ctypes(self):
        """Returns the object mapping the C structure.

        Returns
        =======
        _GUID
            Mapping of a C GUID structure
        """
        return self._ctypes_guid

    def __str__(self):
        """Returns a string representation of the GUID.

        Returns
        =======
        str
            GUID string representation in hexadecimal
        """
        return "{{{:08X}-{:04X}-{:04X}-{:04X}-{:012X}}}".format(
            self.guid[0],
            self.guid[1],
            self.guid[2],
            self.guid[3],
            self.guid[4]
        )

    def __eq__(self, other):
        """Returns whether or not two GUID instances are identical.

        Parameters
        ==========
        other : GUID
            Instance with which to perform the equality comparison

        Returns
        =======
        bool
            True if the two GUIDs are equal, False otherwise
        """
        return hash(self) == hash(other)

    def __lt__(self, other):
        """Returns the result of the < operator.

        Parameters
        ==========
        other : GUID
            Instance with which to perform the equality comparison

        Returns
        =======
        bool
            True if this instance is < other, False otherwise
        """
        return str(self) < str(other)

    def __hash__(self):
        """Returns the hash of this GUID.

        Returns
        =======
        int
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


GUID_Keyboard = GUID(_GUID_SysKeyboard)
GUID_Virtual = GUID(_GUID_Virtual)
GUID_Invalid = GUID(_GUID_Invalid)


class InputType(Enum):

    """Enumeration of valid input types that can be reported."""

    Axis = 1,
    Button = 2,
    Hat = 3

    @staticmethod
    def from_ctype(value):
        """Returns the enum type corresponding to the provided value.

        Parameters
        ==========
        value : int
            The integer value representing the input type according to DILL

        Returns
        =======
        InputType
            Enum value representing the correct InputType
        """
        if value == 1:
            return InputType.Axis
        elif value == 2:
            return InputType.Button
        elif value == 3:
            return InputType.Hat
        else:
            raise DILLError("Invalid input type value {:d}".format(value))


class DeviceActionType(Enum):

    """Represents the state change of a device."""

    Connected = 1
    Disconnected = 2

    @staticmethod
    def from_ctype(value):
        """Returns the enum type corresponding to the provided value.

        Parameters
        ==========
        value : int
            The integer value representing the action type according to DILL

        Returns
        =======
        DeviceActionType
            Enum value representing the correct DeviceAction
        """
        if value == 1:
            return DeviceActionType.Connected
        elif value == 2:
            return DeviceActionType.Disconnected
        else:
            raise DILLError("Invalid device action type {:d}".format)


class InputEvent:

    """Holds information about a single event.

    An event is an axis, button, or hat changing its state. The type of
    input, the index, and the new value as well as device GUID are reported.
    """

    def __init__(self, data):
        """Creates a new instance.

        Parameters
        ==========
        data : _JoystickInputData
            The data received from DILL and to be held by this isntance
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

    def __init__(self, data):
        """Creates a new instance.

        Parameters
        ==========
        data : _AxisMap
            The data received from DILL and to be held by this instance
        """
        self.linear_index = data.linear_index
        self.axis_index = data.axis_index


class DeviceSummary:

    """Holds information about a single device.

    This summary holds static information about a single device's layout.
    """

    def __init__(self, data):
        """Creates a new instance.

        Parameters
        ==========
        data : _DeviceSummary
            The data received from DILL and to be held by this instance
        """
        self.device_guid = GUID(data.device_guid)
        self.vendor_id = data.vendor_id
        self.product_id = data.product_id
        self.joystick_id = data.joystick_id
        self.name = data.name.decode("utf-8")
        self.axis_count = data.axis_count
        self.button_count = data.button_count
        self.hat_count = data.hat_count
        self.axis_map = []
        for i in range(8):
            self.axis_map.append(AxisMap(data.axis_map[i]))
        self.vjoy_id = -1

    @property
    def is_virtual(self):
        """Returns if a device is virtual.

        Returns
        =======
        bool
            True if the device is a virtual vJoy device, False otherwise
        """
        return self.vendor_id == 0x1234 and self.product_id == 0xBEAD

    def set_vjoy_id(self, vjoy_id):
        """Sets the vJoy id for this device summary.

        Settings the vJoy device id is necessary, as DILL cannot know these
        ids, and as such this has to be entered when DirectInput devices and
        vJoy devices are linked.

        Parameters
        ==========
        vjoy_id : int
            Index of the vJoy device corresponding to this DirectInput device
        """
        assert self.is_virtual is True
        self.vjoy_id = vjoy_id


C_EVENT_CALLBACK = ctypes.CFUNCTYPE(None, _JoystickInputData)
C_DEVICE_CHANGE_CALLBACK = ctypes.CFUNCTYPE(None, _DeviceSummary, ctypes.c_uint8)

_dll_path = os.path.join(os.path.dirname(__file__), "dill.dll")
_di_listener_dll = ctypes.cdll.LoadLibrary(_dll_path)

_di_listener_dll.get_device_information_by_index.argtypes = [ctypes.c_uint]
_di_listener_dll.get_device_information_by_index.restype = _DeviceSummary


class DILL:

    """Exposes functions of the DILL library in an easy to use manner."""

    # Attempt to find the correct location of the dll for development
    # and installed use cases.
    _dev_path = os.path.join(os.path.dirname(__file__), "dill.dll")
    if os.path.isfile("dill.dll"):
        _dll_path = "dill.dll"
    elif os.path.isfile(_dev_path):
        _dll_path = _dev_path
    else:
        raise DILLError("Unable to locate di_listener dll")

    _dll = ctypes.cdll.LoadLibrary(_dll_path)

    # Storage for the callback functions
    device_change_callback_fn = None
    input_event_callback_fn = None

    # Declare argument and return types for all the functions
    # exposed by the dll
    api_functions = {
        "init": {
            "arguments": [],
            "returns": None
        },
        "set_input_event_callback": {
            "arguments": [C_EVENT_CALLBACK],
            "returns": None
        },
        "set_device_change_callback": {
            "arguments": [C_DEVICE_CHANGE_CALLBACK],
            "returns": None
        },
        "get_device_information_by_index": {
            "arguments": [ctypes.c_uint],
            "returns": _DeviceSummary
        },
        "get_device_information_by_guid": {
            "arguments": [_GUID],
            "returns": _DeviceSummary
        },
        "get_device_count": {
            "arguments": [],
            "returns": ctypes.c_uint
        },
        "device_exists": {
            "arguments": [_GUID],
            "returns": ctypes.c_bool
        },
        "get_axis": {
            "arguments": [_GUID, ctwt.DWORD],
            "returns": ctwt.LONG
        },
        "get_button": {
            "arguments": [_GUID, ctwt.DWORD],
            "returns": ctypes.c_bool
        },
        "get_hat": {
            "arguments": [_GUID, ctwt.DWORD],
            "returns": ctwt.LONG
        }
    }

    @staticmethod
    def init():
        """Initializes the DILL library.

        This has to be called before any other DILL interactions can take place.
        """
        DILL._dll.init()

    @staticmethod
    def set_input_event_callback(callback):
        """Sets the callback function to use for input events.

        The provided callback function will be executed whenever an event
        occurs by the DILL library providing and InputEvent object to said
        callback.

        Parameters
        ==========
        callback : callable
            Function to execute when an event occurs.
        """
        DILL.input_event_callback_fn = C_EVENT_CALLBACK(callback)
        DILL._dll.set_input_event_callback(
            DILL.input_event_callback_fn
        )

    @staticmethod
    def set_device_change_callback(callback):
        """Sets the callback function to use for device change events.

        The provided function will be executed whenever the status of a
        device changes, providing a DeviceSummary object to the callback.

        Parameters
        ==========
        callback : callable
            Function to execute when an event occurs.
        """
        DILL.device_change_callback_fn = \
            C_DEVICE_CHANGE_CALLBACK(callback)
        DILL._dll.set_device_change_callback(
            DILL.device_change_callback_fn
        )

    @staticmethod
    def get_device_count():
        """Returns the number of connected devices.

        Return
        ======
        int
            The number of devices connected.
        """
        return DILL._dll.get_device_count()

    @staticmethod
    def get_device_information_by_index(index):
        """Returns device information for the given index.

        Parameters
        ==========
        index : int
            The index of the device for which to return information.

        Return
        ======
        DeviceSummary
            Structure containing detailed information about the desired device.
        """
        return DeviceSummary(
            DILL._dll.get_device_information_by_index(index)
        )

    @staticmethod
    def get_device_information_by_guid(guid):
        """Returns device information for the given GUID.

        Parameters
        ==========
        guid : GUID
            The GUID of the device for which to return information.

        Return
        ======
        DeviceSummary
            Structure containing detailed information about the desired device.
        """
        return DeviceSummary(
            DILL._dll.get_device_information_by_guid(guid.ctypes)
        )

    @staticmethod
    def get_axis(guid, index):
        """Returns the state of the specified axis for a specific device.

        Parameters
        ==========
        guid : GUID
            GUID of the device of interest.
        index : int
            Index of the axis to return the value of.

        Return
        ======
        float
            Current value of the specific axis for the desired device.
        """
        return DILL._dll.get_axis(guid.ctypes, index)

    @staticmethod
    def get_button(guid, index):
        """Returns the state of the specified button for a specific device.

        Parameters
        ==========
        guid : GUID
            GUID of the device of interest.
        index : int
            Index of the button to return the value of.

        Return
        ======
        bool
            Current value of the specific button for the desired device.
        """
        return DILL._dll.get_button(guid.ctypes, index)

    @staticmethod
    def get_hat(guid, index):
        """Returns the state of the specified hat for a specific device.

        Parameters
        ==========
        guid : GUID
            GUID of the device of interest.
        index : int
            Index of the hat to return the value of.

        Return
        ======
        int
            Current value of the specific hat for the desired device.
        """
        return DILL._dll.get_hat(guid.ctypes, index)

    @staticmethod
    def get_device_name(guid):
        """Returns the name of the device specified by the provided GUID.

        Parameters
        ==========
        guid : GUID
            GUID of the device of which to return the name

        Return
        ======
        str
            Name of the specified device.
        """
        info = DeviceSummary(
            DILL._dll.get_device_information_by_guid(guid.ctypes)
        )
        return info.name

    @staticmethod
    def device_exists(guid):
        """Returns whether or not a specific device is connected.

        Parameters
        ==========
        guid : GUID
            GUID of the device to check whether or not it is connected

        Return
        ======
        bool
            True if the device is connected, False otherwise.
        """
        return DILL._dll.device_exists(guid.ctypes)

    @staticmethod
    def initialize():
        """Initializes the functions as class methods."""
        for fn_name, params in DILL.api_functions.items():
            dll_fn = getattr(DILL._dll, fn_name)
            if "arguments" in params:
                dll_fn.argtypes = params["arguments"]
            if "returns" in params:
                dll_fn.restype = params["returns"]


# Initialize the class
DILL.initialize()
