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


import ctypes
import ctypes.wintypes as ctwt
from enum import Enum
import os
import time


class _GUID(ctypes.Structure):

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

    _fields_ = [
        ("device_guid", _GUID),
        ("input_type", ctypes.c_uint8),
        ("input_index", ctypes.c_uint8),
        ("value", ctwt.LONG)
    ]


class _AxisMap(ctypes.Structure):

    _fields_ = [
        ("linear_index", ctwt.DWORD),
        ("axis_index", ctwt.DWORD)
    ]


class _DeviceSummary(ctypes.Structure):

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

    def __init__(self, guid):
        assert isinstance(guid, _GUID)
        self._ctypes_guid = guid
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
        return self._ctypes_guid

    def __str__(self):
        return "{{{:X}-{:X}-{:X}-{:X}-{:X}}}".format(
            self.guid[0],
            self.guid[1],
            self.guid[2],
            self.guid[3],
            self.guid[4]
        )

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
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

    Axis = 1,
    Button = 2,
    Hat = 3

    @staticmethod
    def from_ctype(value):
        if value == 1:
            return InputType.Axis
        elif value == 2:
            return InputType.Button
        elif value == 3:
            return InputType.Hat
        else:
            raise "Invalid input type value {:d}".format(value)


class DeviceActionType(Enum):

    Connected = 1
    Disconnected = 2

    @staticmethod
    def from_ctype(value):
        if value == 1:
            return DeviceActionType.Connected
        elif value == 2:
            return DeviceActionType.Disconnected
        else:
            raise "Invalid device action type {:d}".format


class InputEvent:

    def __init__(self, data):
        self.device_guid = GUID(data.device_guid)
        self.input_type = InputType.from_ctype(data.input_type)
        self.input_index = int(data.input_index)
        self.value = int(data.value)


class AxisMap:

    def __init__(self, data):
        self.linear_index = data.linear_index
        self.axis_index = data.axis_index


class DeviceSummary:

    def __init__(self, data):
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
        return self.vendor_id == 0x1234 and self.product_id == 0xBEAD

    def set_vjoy_id(self, vjoy_id):
        assert self.is_virtual is True
        self.vjoy_id = vjoy_id


C_EVENT_CALLBACK = ctypes.CFUNCTYPE(None, _JoystickInputData)
C_DEVICE_CHANGE_CALLBACK = ctypes.CFUNCTYPE(None, _DeviceSummary, ctypes.c_uint8)

_dll_path = os.path.join(os.path.dirname(__file__), "di_listener.dll")
_di_listener_dll = ctypes.cdll.LoadLibrary(_dll_path)

_di_listener_dll.get_device_information_by_index.argtypes = [ctypes.c_uint]
_di_listener_dll.get_device_information_by_index.restype = _DeviceSummary


class DILL:

    # Attempt to find the correct location of the dll for development
    # and installed use cases.
    _dev_path = os.path.join(os.path.dirname(__file__), "di_listener.dll")
    if os.path.isfile("di_listener.dll"):
        _dll_path = "di_listener.dll"
    elif os.path.isfile(_dev_path):
        _dll_path = _dev_path
    else:
        raise "Unable to locate di_listener dll"

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
            "returns": ctwt.LONG
        },
        "get_hat": {
            "arguments": [_GUID, ctwt.DWORD],
            "returns": ctwt.LONG
        }
    }

    @staticmethod
    def init():
        DILL._dll.init()

    @staticmethod
    def set_input_event_callback(callback):
        DILL.input_event_callback_fn = C_EVENT_CALLBACK(callback)
        DILL._dll.set_input_event_callback(
            DILL.input_event_callback_fn
        )

    @staticmethod
    def set_device_change_callback(callback):
        DILL.device_change_callback_fn = \
            C_DEVICE_CHANGE_CALLBACK(callback)
        DILL._dll.set_device_change_callback(
            DILL.device_change_callback_fn
        )

    @staticmethod
    def get_device_count():
        return DILL._dll.get_device_count()

    @staticmethod
    def get_device_information_by_index(index):
        return DeviceSummary(
            DILL._dll.get_device_information_by_index(index)
        )

    @staticmethod
    def get_device_information_by_guid(guid):
        return DeviceSummary(
            DILL._dll.get_device_information_by_guid(guid.ctypes)
        )

    @staticmethod
    def get_axis(guid, index):
        return DILL._dll.get_axis(guid.ctypes, index)

    @staticmethod
    def get_button(guid, index):
        return DILL._dll.get_button(guid.ctypes, index)

    @staticmethod
    def get_hat(guid, index):
        return DILL._dll.get_hat(guid.ctypes, index)

    @staticmethod
    def get_device_name(guid):
        info = DeviceSummary(
            DILL._dll.get_device_information_by_guid(guid.ctypes)
        )
        return info.name

    @staticmethod
    def device_exists(guid):
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


if __name__ == "__main__":

    guid_list = []

    def event_callback(_event):
        event = InputEvent(_event)
        print("{} {} {} {}".format(
            event.device_guid,
            event.input_type.name,
            event.input_index,
            event.value
        ))


    def device_change_callback(_info, _action):
        info = DeviceSummary(_info)
        action = DeviceActionType.from_ctype(_action)
        if info.device_guid not in guid_list:
            print("Adding device")
            guid_list.append(info.device_guid)

        if info.name == b'T.16000M':
            for gid in guid_list:
                print(hash(gid) == hash(info.device_guid))

        print(action)
        if action == DeviceActionType.Connected:
            print(
                info.name,
                info.axis_count,
                info.button_count,
                info.hat_count
            )
            for i in range(info.axis_count):
                print("> {} {}".format(
                    info.axis_map[i].linear_index,
                    info.axis_map[i].axis_index
                ))


    # event_cb_fun = C_EVENT_CALLBACK(event_callback)
    #device_change_cb_fun = C_DEVICE_CHANGE_CALLBACK(device_change_callback)
    #
    # dev_path = os.path.join(os.path.dirname(__file__), "di_listener.dll")
    #
    # dll = ctypes.cdll.LoadLibrary(dev_path)
    #
    # dll.set_input_event_callback(event_cb_fun)
    # dll.set_device_change_callback(device_change_cb_fun)
    # dll.init()

    DILL.set_device_change_callback(device_change_callback)
    DILL.set_input_event_callback(event_callback)
    DILL.init()

    for i in range(DILL.get_device_count()):
        info = DILL.get_device_information_by_index(i)
        print(
            info.name,
            info.axis_count,
            info.button_count,
            info.hat_count
        )

    while True:
        # for i in range(DILL.get_device_count()):
        #     info = DILL.get_device_information_by_index(i)
        #     print(DILL.get_axis(info.device_guid, 1))
        time.sleep(0.1)
