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

import functools
import logging
import time
from threading import Thread

import win32con
import win32api

from gremlin.error import KeyboardError


# Default delay between subsequent message dispatch. This is to to get
# around some games not picking up messages if they are sent in too
# quick a succession.
default_delay = 0.05


def _run_macro(sequence):
    """Executes the provided macro.

    :param sequence the sequence of commands to execute
    """
    for item in sequence:
        if isinstance(item, Macro.KeyAction):
            if item.is_pressed:
                _send_key_down(item.key)
            else:
                _send_key_up(item.key)
        elif isinstance(item, Macro.Pause):
            time.sleep(item.duration)
        else:
            raise KeyboardError("Invalid item in the sequence {}".format(
                type(item))
            )
        time.sleep(default_delay)


def _send_key_down(key):
    """Sends the KEYDOWN event for a single key.

    :param key the key for which to send the KEYDOWN event
    """
    flags = win32con.KEYEVENTF_EXTENDEDKEY if key.is_extended else 0
    win32api.keybd_event(key.virtual_key, key.scan_code, flags, 0)


def _send_key_up(key):
    """Sends the KEYUP event for a single key.

    :param key the key for which to send the KEYUP event
    """
    flags = win32con.KEYEVENTF_EXTENDEDKEY if key.is_extended else 0
    flags |= win32con.KEYEVENTF_KEYUP
    win32api.keybd_event(key.virtual_key, key.scan_code, flags, 0)


class Macro(object):

    """Represents a macro which can be executed."""

    def __init__(self):
        """Creates a new macro instance."""
        self._sequence = []

    def run(self):
        """Executes the macro in a separate thread."""
        Thread(target=functools.partial(_run_macro, self._sequence)).start()

    def pause(self, duration):
        """Adds a pause of the given duration to the macro.

        :param duration the duration of the pause in seconds
        """
        self._sequence.append(Macro.Pause(duration))

    def press(self, key):
        """Presses the specified key down.

        :param key the key to press
        """
        self.action(key, True)

    def release(self, key):
        """Releases the specified key.

        :param key the key to release
        """
        self.action(key, False)

    def tap(self, key):
        """Taps the specified key.

        :param key the key to tap
        """
        self.action(key, True)
        self.action(key, False)

    def action(self, key, is_pressed):
        """Adds the specified action to the sequence.

        :param key the key involved in the action
        :param is_pressed boolean indicating if the key is pressed
            (True) or released (False)
        """
        if isinstance(key, str):
            key = key_from_name(key)
        elif isinstance(key, Keys.Key):
            pass
        else:
            raise KeyboardError("Invalid key specified")

        self._sequence.append(Macro.KeyAction(key, is_pressed))

    class KeyAction(object):

        """Key to press or release by a macro."""

        def __init__(self, key, is_pressed):
            """Creates a new Key object for use in a macro.

            :param key the key to use in the action
            :param is_pressed True if the key should be pressed, False
                otherwise
            """
            if not isinstance(key, Keys.Key):
                raise KeyboardError("Invalid Key instance provided")
            self.key = key
            self.is_pressed = is_pressed

    class Pause(object):

        """Represents the pause in a macro between pressed."""

        def __init__(self, duration):
            """Creates a new Pause object for use in a macro.

            :param duration the duration in seconds of the pause
            """
            self.duration = duration


class Keys(object):

    class Key(object):

        """Represents a single key on the keyboard together with its
        different representations.
        """

        def __init__(self, name, scan_code, is_extended, virtual_key):
            """Creates a new Key instance.

            :param name the name used to refer to this key
            :param scan_code the scan code set 1 value corresponding
                to this key
            :param is_extended boolean indicating if the key is an
                extended scan code or not
            :param virtual_key the virtual key code assigned to this
                key by windows
            """
            self._name = name
            self._scan_code = scan_code
            self._is_extended = is_extended
            self._virtual_key = virtual_key

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
        def virtual_key(self):
            return self._virtual_key

        def __eq__(self, other):
            return hash(self) == hash(other)

        def __ne__(self, other):
            return not (self == other)

        def __hash__(self):
            if self._is_extended:
                return (0x0E << 8) + self._scan_code
            else:
                return self._scan_code

    # Definition of all the available keys
    A = Key("A", 0x1e, False, 0x41)
    B = Key("B", 0x30, False, 0x42)
    C = Key("C", 0x2e, False, 0x43)
    D = Key("D", 0x20, False, 0x44)
    E = Key("E", 0x12, False, 0x45)
    F = Key("F", 0x21, False, 0x46)
    G = Key("G", 0x22, False, 0x47)
    H = Key("H", 0x23, False, 0x48)
    I = Key("I", 0x17, False, 0x49)
    J = Key("J", 0x24, False, 0x4a)
    K = Key("K", 0x25, False, 0x4b)
    L = Key("L", 0x26, False, 0x4c)
    M = Key("M", 0x32, False, 0x4d)
    N = Key("N", 0x31, False, 0x4e)
    O = Key("O", 0x18, False, 0x4f)
    P = Key("P", 0x19, False, 0x50)
    Q = Key("Q", 0x10, False, 0x51)
    R = Key("R", 0x13, False, 0x52)
    S = Key("S", 0x1f, False, 0x53)
    T = Key("T", 0x14, False, 0x54)
    U = Key("U", 0x16, False, 0x55)
    V = Key("V", 0x2f, False, 0x56)
    W = Key("W", 0x11, False, 0x57)
    X = Key("X", 0x2d, False, 0x58)
    Y = Key("Y", 0x15, False, 0x59)
    Z = Key("Z", 0x2c, False, 0x5a)

    Num0 = Key("0", 0x0b, False, 0x30)
    Num1 = Key("1", 0x02, False, 0x31)
    Num2 = Key("2", 0x03, False, 0x32)
    Num3 = Key("3", 0x04, False, 0x33)
    Num4 = Key("4", 0x05, False, 0x34)
    Num5 = Key("5", 0x06, False, 0x35)
    Num6 = Key("6", 0x07, False, 0x36)
    Num7 = Key("7", 0x08, False, 0x37)
    Num8 = Key("8", 0x09, False, 0x38)
    Num9 = Key("9", 0x0a, False, 0x39)

    F1 = Key("F1", 0x3b, False, win32con.VK_F1)
    F2 = Key("F2", 0x3c, False, win32con.VK_F2)
    F3 = Key("F3", 0x3d, False, win32con.VK_F3)
    F4 = Key("F4", 0x3e, False, win32con.VK_F4)
    F5 = Key("F5", 0x3f, False, win32con.VK_F5)
    F6 = Key("F6", 0x40, False, win32con.VK_F6)
    F7 = Key("F7", 0x41, False, win32con.VK_F7)
    F8 = Key("F8", 0x42, False, win32con.VK_F8)
    F9 = Key("F9", 0x43, False, win32con.VK_F9)
    F10 = Key("F10", 0x44, False, win32con.VK_F10)
    F11 = Key("F11", 0x57, False, win32con.VK_F11)
    F12 = Key("F12", 0x58, False, win32con.VK_F12)

    # PrntScrn
    # ScrollLock
    # Pause

    Insert = Key("Insert", 0x52, True, win32con.VK_INSERT)
    Home = Key("Home", 0x47, True, win32con.VK_HOME)
    PageUp = Key("PageUp", 0x49, True, win32con.VK_PRIOR)
    Delete = Key("Delete", 0x53, True, win32con.VK_DELETE)
    End = Key("End", 0x4f, True, win32con.VK_END)
    PageDown = Key("PageDown", 0x51, True, win32con.VK_NEXT)

    UpArrow = Key("Up", 0x48, True, win32con.VK_UP)
    LeftArrow = Key("Left", 0x4b, True, win32con.VK_LEFT)
    DownArrow = Key("Down", 0x50, True, win32con.VK_DOWN)
    RightArrow = Key("Right", 0x4d, True, win32con.VK_RIGHT)

    NumLock = Key("NumLock", 0x45, False, win32con.VK_NUMLOCK)
    KPDivide = Key("KPDivide", 0x35, True, win32con.VK_DIVIDE)
    KPMultiply = Key("KPMultiply", 0x37, False, win32con.VK_MULTIPLY)
    KPMinus = Key("KPMinus", 0x4a, False, win32con.VK_SUBTRACT)
    KPPlus = Key("KPPlus", 0x4e, False, win32con.VK_ADD)
    KPEnter = Key("KPEnter", 0x1c, True, win32con.VK_SEPARATOR)
    KPDelete = Key("KPDelete", 0x53, False, win32con.VK_DECIMAL)
    KP0 = Key("KP0", 0x52, False, win32con.VK_NUMPAD0)
    KP1 = Key("KP1", 0x4f, False, win32con.VK_NUMPAD1)
    KP2 = Key("KP2", 0x50, False, win32con.VK_NUMPAD2)
    KP3 = Key("KP3", 0x51, False, win32con.VK_NUMPAD3)
    KP4 = Key("KP4", 0x4b, False, win32con.VK_NUMPAD4)
    KP5 = Key("KP5", 0x4c, False, win32con.VK_NUMPAD5)
    KP6 = Key("KP6", 0x4d, False, win32con.VK_NUMPAD6)
    KP7 = Key("KP7", 0x47, False, win32con.VK_NUMPAD7)
    KP8 = Key("KP8", 0x48, False, win32con.VK_NUMPAD8)
    KP9 = Key("KP9", 0x49, False, win32con.VK_NUMPAD9)

    Tilde = Key("~", 0x29, False, 0xC0)
    Minus = Key("-", 0x0c, False, 0XBD)
    Equal = Key("=", 0x0d, False, 0xBB)
    Backslash = Key("\\", 0x2b, False, 0xDC)
    Backspace = Key("Backspace", 0x0e, False, win32con.VK_BACK)
    Space = Key("Space", 0x39, False, win32con.VK_SPACE)
    Tab = Key("Tab", 0x0f, False, win32con.VK_TAB)
    CapsLock = Key("CapsLock", 0x3a, False, win32con.VK_CAPITAL)
    LShift = Key("LShift", 0x2a, False, win32con.VK_LSHIFT)
    LControl = Key("LControl", 0x1d, False, win32con.VK_LCONTROL)
    LWin = Key("LWin", 0x5b, True, win32con.VK_LWIN)
    LAlt = Key("LAlt", 0x38, False, win32con.VK_LMENU)
    # Right shift key appears to exist in both extended and
    # non-extended version
    RShift = Key("RShift", 0x36, False, win32con.VK_RSHIFT)
    RShift2 = Key("RShift", 0x36, True, win32con.VK_RSHIFT)
    RControl = Key("RControl", 0x1d, True, win32con.VK_RCONTROL)
    RWin = Key("RWin", 0x5c, True, win32con.VK_RWIN)
    RAlt = Key("RAlt", 0x38, True, win32con.VK_RMENU)
    Apps = Key("Apps", 0x5d, True, win32con.VK_APPS)
    Enter = Key("Enter", 0x1c, False, win32con.VK_RETURN)
    Esc = Key("Esc", 0x01, False, win32con.VK_ESCAPE)
    LBracket = Key("[", 0x1a, False, 0xDB)
    RBracket = Key("]", 0x1b, False, 0xDD)
    Semicolon = Key(";", 0x27, False, 0xBA)
    Apostrophe = Key("'", 0x28, False, 0xDE)
    Comma = Key(",", 0x33, False, 0xBC)
    Period = Key(".", 0x34, False, 0xBE)
    Slash = Key("/", 0x35, False, 0xBF)


def key_from_name(name):
    """Returns the key corresponding to the provided name.

    If no key exists with the provided name None is returned.

    :param name the name of the key to return
    :return Key instance or None
    """
    key = name_to_key.get(name, None)
    if key is None:
        logging.warning("Invalid key name specified \"{}\"".format(name))
    return key


def key_from_code(scan_code, is_extended):
    """Returns the key corresponding to the provided scan code.

    If no key exists with the provided scan code None is returned.

    :param scan_code the scan code of the desired key
    :param is_extended flag indicating if the key is extended
    :return Key instance or None
    """
    key = code_to_key.get((scan_code, is_extended), None)
    if key is None:
        logging.warning("Invalid scan code specified ({}, {})".format(
            scan_code, is_extended
        ))
    return key


# Populate the lookup tables
code_to_key = {}
name_to_key = {}
for key_object in Keys.__dict__.values():
    if isinstance(key_object, Keys.Key):
        code_to_key[(key_object.scan_code, key_object.is_extended)] = key_object
        name_to_key[key_object.name] = key_object
