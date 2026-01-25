# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

import ctypes
from ctypes import wintypes
import logging
from typing import List

import win32api
import win32con

from gremlin.error import KeyboardError


def _create_function(lib_name, fn_name, param_types, return_type):
    """Creates a handle to a dll library function.

    :param lib_name name of the library to retrieve a function handle from
    :param fn_name name of the function
    :param param_types input parameter types
    :param return_type return parameter type
    :return function handle
    """
    fn = getattr(ctypes.WinDLL(lib_name), fn_name)
    fn.argtypes = param_types
    fn.restype = return_type
    return fn


# https://msdn.microsoft.com/en-us/library/windows/desktop/ms646296(v=vs.85).aspx
_get_keyboard_layout = _create_function(
    "user32",
    "GetKeyboardLayout",
    [wintypes.DWORD],
    wintypes.HKL
)

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms646299(v=vs.85).aspx
_get_keyboard_state = _create_function(
    "user32",
    "GetKeyboardState",
    [ctypes.POINTER(ctypes.c_char)],
    wintypes.BOOL
)

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms646307(v=vs.85).aspx
_map_virtual_key_ex = _create_function(
    "user32",
    "MapVirtualKeyExW",
    [ctypes.c_uint, ctypes.c_uint, wintypes.HKL],
    ctypes.c_uint
)

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms646322(v=vs.85).aspx
_to_unicode_ex = _create_function(
    "user32",
    "ToUnicodeEx",
    [
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_char),
        ctypes.POINTER(ctypes.c_wchar),
        ctypes.c_int,
        ctypes.c_uint,
        ctypes.c_void_p
    ],
    ctypes.c_int
)

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms646332(v=vs.85).aspx
_vk_key_scan_ex = _create_function(
    "user32",
    "VkKeyScanExW",
    [ctypes.c_wchar, wintypes.HKL],
    ctypes.c_short
)


class Key:

    """Represents a single key on the keyboard together with its
    different representations.
    """

    def __init__(self, name, scan_code, is_extended, virtual_code):
        """Creates a new Key instance.

        :param name the name used to refer to this key
        :param scan_code the scan code set 1 value corresponding
            to this key
        :param is_extended boolean indicating if the key is an
            extended scan code or not
        :param virtual_code the virtual key code assigned to this
            key by windows
        """
        self._name = name
        self._scan_code = scan_code
        self._is_extended = is_extended
        self._virtual_code = virtual_code
        self._lookup_name = None

    @property
    def name(self):
        return self._name

    @property
    def scan_code(self):
        return self._scan_code

    @property
    def is_extended(self):
        return self._is_extended

    @property
    def virtual_code(self):
        return self._virtual_code

    @property
    def lookup_name(self):
        if self._lookup_name is not None:
            return self._lookup_name
        else:
            return self._name

    @lookup_name.setter
    def lookup_name(self, name):
        if self._lookup_name is not None:
            raise KeyboardError("Setting lookup name repeatedly")
        self._lookup_name = name

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        if self._is_extended:
            return (0x0E << 8) + self._scan_code
        else:
            return self._scan_code


def _scan_code_to_virtual_code(scan_code, is_extended):
    """Returns the virtual code corresponding to the given scan code.

    :param scan_code scan code value to translate
    :param is_extended whether or not the scan code is extended
    :return virtual code corresponding to the given scan code
    """
    value = scan_code
    if is_extended:
        value = 0xe0 << 8 | scan_code

    virtual_code = _map_virtual_key_ex(value, 3, _get_keyboard_layout(0))
    return virtual_code


def _virtual_input_to_unicode(virtual_code):
    """Returns the unicode character corresponding to a given virtual code.

    :param virtual_code virtual code for which to return a unicode character
    :return unicode character corresponding to the given virtual code
    """
    keyboard_layout = _get_keyboard_layout(0)
    output_buffer = ctypes.create_unicode_buffer(8)
    state_buffer = ctypes.create_string_buffer(256)

    # Translate three times to get around dead keys showing up in funny ways
    # as the translation takes them into account for future keys
    state = _to_unicode_ex(
        virtual_code,
        0x00,
        state_buffer,
        output_buffer,
        8,
        0,
        keyboard_layout
    )
    state = _to_unicode_ex(
        virtual_code,
        0x00,
        state_buffer,
        output_buffer,
        8,
        0,
        keyboard_layout
    )
    state = _to_unicode_ex(
        virtual_code,
        0x00,
        state_buffer,
        output_buffer,
        8,
        0,
        keyboard_layout
    )

    if state == 0:
        logging.getLogger("system").error(
            "No translation for key {} available".format(hex(virtual_code))
        )
        return str(hex(virtual_code))
    return output_buffer.value.upper()


def _unicode_to_key(character):
    """Returns a Key instance corresponding to the given character.

    :param character the character for which to generate a Key instance
    :return Key instance for the given character, or None if an error occurred
    """
    if len(character) != 1:
        return None

    virtual_code = _vk_key_scan_ex(character, _get_keyboard_layout(0)) & 0x00FF
    if virtual_code == 0xFF:
        return None

    code_value = _map_virtual_key_ex(virtual_code, 4, _get_keyboard_layout(0))
    scan_code = code_value & 0xFF
    is_extended = False
    if code_value << 8 & 0xE0 or code_value << 8 & 0xE1:
        is_extended = True
    return Key(character, scan_code, is_extended, virtual_code)


def send_key_down(key):
    """Sends the KEYDOWN event for a single key.

    :param key the key for which to send the KEYDOWN event
    """
    flags = win32con.KEYEVENTF_EXTENDEDKEY if key.is_extended else 0
    win32api.keybd_event(key.virtual_code, key.scan_code, flags, 0)


def send_key_up(key):
    """Sends the KEYUP event for a single key.

    :param key the key for which to send the KEYUP event
    """
    flags = win32con.KEYEVENTF_EXTENDEDKEY if key.is_extended else 0
    flags |= win32con.KEYEVENTF_KEYUP
    win32api.keybd_event(key.virtual_code, key.scan_code, flags, 0)


def key_from_name(name):
    """Returns the key corresponding to the provided name.

    If no key exists with the provided name None is returned.

    :param name the name of the key to return
    :return Key instance or None
    """
    global g_scan_code_to_key, g_name_to_key

    # Attempt to located the key in our database and return it if successful
    key_name = name.lower().replace(" ", "")
    key = g_name_to_key.get(key_name, None)
    if key is not None:
        return key

    # Attempt to create the key to store and return if successful
    key = _unicode_to_key(name)
    if key is None:
        logging.getLogger("system").warning(
            "Invalid key name specified \"{}\"".format(name)
        )
        raise KeyboardError(f"Invalid key specified: {name}")
    else:
        g_scan_code_to_key[(key.scan_code, key.is_extended)] = key
        g_name_to_key[key_name] = key
        return key


def key_from_code(scan_code: int, is_extended: bool) -> Key:
    """Returns the key corresponding to the provided scan code.

    If no key exists with the provided scan code None is returned.

    Params:
        scan_code the scan code of the desired key
        is_extended flag indicating if the key is extended

    Returns:
        Key instance or None
    """
    global g_scan_code_to_key, g_name_to_key

    # Attempt to located the key in our database and return it if successful
    key = g_scan_code_to_key.get((scan_code, is_extended), None)
    if key is not None:
        return key

    # Attempt to create the key to store and return if successful
    virtual_code = _scan_code_to_virtual_code(scan_code, is_extended)
    name = _virtual_input_to_unicode(virtual_code)

    if virtual_code == 0xFF or name is None:
        logging.getLogger("system").warning(
            "Invalid scan code specified ({}, {})".format(
                scan_code, is_extended
            )
        )
        raise KeyboardError(
            f"Invalid scan code specified ({scan_code}, {is_extended})"
        )
    else:
        key = Key(name, scan_code, is_extended, virtual_code)
        g_scan_code_to_key[(scan_code, is_extended)] = key
        g_name_to_key[name.lower()] = key
        return key


def modifier_keys() -> List[Key]:
    """Returns a list containing all modifier keys.

    Returns:
        List with key instances corresponding to modifier keys.
    """
    return [
        g_name_to_key["leftshift"],
        g_name_to_key["leftcontrol"],
        g_name_to_key["leftalt"],
        g_name_to_key["rightshift"],
        g_name_to_key["rightshift2"],
        g_name_to_key["rightcontrol"],
        g_name_to_key["rightalt"],
    ]


# Storage for the various keys, prepopulated with non alphabetical keys
g_scan_code_to_key = {}

g_name_to_key = {
    # Function keys
    "f1": Key("F1", 0x3b, False, win32con.VK_F1),
    "f2": Key("F2", 0x3c, False, win32con.VK_F2),
    "f3": Key("F3", 0x3d, False, win32con.VK_F3),
    "f4": Key("F4", 0x3e, False, win32con.VK_F4),
    "f5": Key("F5", 0x3f, False, win32con.VK_F5),
    "f6": Key("F6", 0x40, False, win32con.VK_F6),
    "f7": Key("F7", 0x41, False, win32con.VK_F7),
    "f8": Key("F8", 0x42, False, win32con.VK_F8),
    "f9": Key("F9", 0x43, False, win32con.VK_F9),
    "f10": Key("F10", 0x44, False, win32con.VK_F10),
    "f11": Key("F11", 0x57, False, win32con.VK_F11),
    "f12": Key("F12", 0x58, False, win32con.VK_F12),
    # Control keys
    "printscreen": Key("Print Screen", 0x37, True, win32con.VK_PRINT),
    "scrolllock": Key("Scroll Lock", 0x46, False, win32con.VK_SCROLL),
    "pause": Key("Pause", 0x45, False, win32con.VK_PAUSE),
    # 6 control block
    "insert": Key("Insert", 0x52, True, win32con.VK_INSERT),
    "home": Key("Home", 0x47, True, win32con.VK_HOME),
    "pageup": Key("PageUp", 0x49, True, win32con.VK_PRIOR),
    "delete": Key("Delete", 0x53, True, win32con.VK_DELETE),
    "end": Key("End", 0x4f, True, win32con.VK_END),
    "pagedown": Key("PageDown", 0x51, True, win32con.VK_NEXT),
    # Arrow keys
    "up": Key("Up", 0x48, True, win32con.VK_UP),
    "left": Key("Left", 0x4b, True, win32con.VK_LEFT),
    "down": Key("Down", 0x50, True, win32con.VK_DOWN),
    "right": Key("Right", 0x4d, True, win32con.VK_RIGHT),
    # Numpad
    "numlock": Key("NumLock", 0x45, True, win32con.VK_NUMLOCK),
    "npdivide": Key("Numpad /", 0x35, True, win32con.VK_DIVIDE),
    "npmultiply": Key("Numpad *", 0x37, False, win32con.VK_MULTIPLY),
    "npminus": Key("Numpad -", 0x4a, False, win32con.VK_SUBTRACT),
    "npplus": Key("Numpad +", 0x4e, False, win32con.VK_ADD),
    "npenter": Key("Numpad Enter", 0x1c, True, win32con.VK_SEPARATOR),
    "npdelete": Key("Numpad Delete", 0x53, False, win32con.VK_DECIMAL),
    "np0": Key("Numpad 0", 0x52, False, win32con.VK_NUMPAD0),
    "np1": Key("Numpad 1", 0x4f, False, win32con.VK_NUMPAD1),
    "np2": Key("Numpad 2", 0x50, False, win32con.VK_NUMPAD2),
    "np3": Key("Numpad 3", 0x51, False, win32con.VK_NUMPAD3),
    "np4": Key("Numpad 4", 0x4b, False, win32con.VK_NUMPAD4),
    "np5": Key("Numpad 5", 0x4c, False, win32con.VK_NUMPAD5),
    "np6": Key("Numpad 6", 0x4d, False, win32con.VK_NUMPAD6),
    "np7": Key("Numpad 7", 0x47, False, win32con.VK_NUMPAD7),
    "np8": Key("Numpad 8", 0x48, False, win32con.VK_NUMPAD8),
    "np9": Key("Numpad 9", 0x49, False, win32con.VK_NUMPAD9),
    # Misc keys
    "backspace": Key("Backspace", 0x0e, False, win32con.VK_BACK),
    "space": Key("Space", 0x39, False, win32con.VK_SPACE),
    "tab": Key("Tab", 0x0f, False, win32con.VK_TAB),
    "capslock": Key("CapsLock", 0x3a, False, win32con.VK_CAPITAL),
    "leftshift": Key("Left Shift", 0x2a, False, win32con.VK_LSHIFT),
    "leftcontrol": Key("Left Control", 0x1d, False, win32con.VK_LCONTROL),
    "leftwin": Key("Left Win", 0x5b, True, win32con.VK_LWIN),
    "leftalt": Key("Left Alt", 0x38, False, win32con.VK_LMENU),
    # Right shift key appears to exist in both extended and
    # non-extended version
    "rightshift": Key("Right Shift", 0x36, False, win32con.VK_RSHIFT),
    "rightshift2": Key("Right Shift", 0x36, True, win32con.VK_RSHIFT),
    "rightcontrol": Key("Right Control", 0x1d, True, win32con.VK_RCONTROL),
    "rightwin": Key("Right Win", 0x5c, True, win32con.VK_RWIN),
    "rightalt": Key("Right Alt", 0x38, True, win32con.VK_RMENU),
    "apps": Key("Apps", 0x5d, True, win32con.VK_APPS),
    "enter": Key("Enter", 0x1c, False, win32con.VK_RETURN),
    "esc": Key("Esc", 0x01, False, win32con.VK_ESCAPE),
    # Various odd keys
    "noname": Key("Noname", 0xfc, False, win32con.VK_NONAME),
    "eraseeof": Key("EraseEof", 0xf9, False, win32con.VK_EREOF),
    "help": Key("Help", 0x2f, False, win32con.VK_HELP),
    "zoom": Key("Zoom", 0xfb, False, win32con.VK_ZOOM),
    # Expanded function keys
    "f13": Key("F13", 0x7c, False, win32con.VK_F13),
    "f14": Key("F14", 0x7d, False, win32con.VK_F14),
    "f15": Key("F15", 0x7e, False, win32con.VK_F15),
    "f16": Key("F16", 0x7f, False, win32con.VK_F16),
    "f17": Key("F17", 0x80, False, win32con.VK_F17),
    "f18": Key("F18", 0x81, False, win32con.VK_F18),
    "f19": Key("F19", 0x82, False, win32con.VK_F19),
    "f20": Key("F20", 0x83, False, win32con.VK_F20),
    "f21": Key("F21", 0x84, False, win32con.VK_F21),
    "f22": Key("F22", 0x85, False, win32con.VK_F22),
    "f23": Key("F23", 0x86, False, win32con.VK_F23),
    "f24": Key("F24", 0x87, False, win32con.VK_F24),
}


# Populate the scan code based lookup table
for name_, key_ in g_name_to_key.items():
    assert isinstance(key_, Key)
    key_.lookup_name = name_
    g_scan_code_to_key[(key_.scan_code, key_.is_extended)] = key_
