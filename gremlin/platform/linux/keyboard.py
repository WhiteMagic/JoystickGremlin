# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Linux keyboard implementation — evdev.UInput-based key injection."""

from __future__ import annotations

import logging
from typing import List

import evdev
from evdev import ecodes

from gremlin.error import KeyboardError

_log = logging.getLogger("system")

# ---------------------------------------------------------------------------
# Singleton UInput keyboard device (lazy)
# ---------------------------------------------------------------------------

_ui_keyboard: evdev.UInput | None = None


def _get_keyboard() -> evdev.UInput:
    global _ui_keyboard
    if _ui_keyboard is None:
        # Declare all standard keys so any key can be injected
        keys = list(range(1, 249))
        _ui_keyboard = evdev.UInput(
            events={ecodes.EV_KEY: keys},
            name="JoystickGremlin Keyboard",
        )
    return _ui_keyboard


# ---------------------------------------------------------------------------
# Key class (identical interface to Windows version)
# ---------------------------------------------------------------------------

class Key:

    """Represents a single key on the keyboard.

    On Linux, scan_code stores the evdev keycode (which happens to match
    Windows Set-1 scan codes for non-extended keys).
    """

    def __init__(self, name, scan_code, is_extended, virtual_code):
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
        return self._scan_code


# ---------------------------------------------------------------------------
# Key injection
# ---------------------------------------------------------------------------

def send_key_down(key: Key) -> None:
    ui = _get_keyboard()
    ui.write(ecodes.EV_KEY, key.scan_code, 1)
    ui.syn()


def send_key_up(key: Key) -> None:
    ui = _get_keyboard()
    ui.write(ecodes.EV_KEY, key.scan_code, 0)
    ui.syn()


# ---------------------------------------------------------------------------
# Extended-key translation: Windows Set-1 scan code → evdev keycode
#
# Non-extended keys: evdev keycode == Windows Set-1 scan code (identical).
# Extended keys (0xE0 prefix in hardware): different evdev codes.
# ---------------------------------------------------------------------------

_WIN_EXTENDED_TO_EVDEV: dict[int, int] = {
    0x37: ecodes.KEY_SYSRQ,       # Print Screen
    0x52: ecodes.KEY_INSERT,
    0x47: ecodes.KEY_HOME,
    0x49: ecodes.KEY_PAGEUP,
    0x53: ecodes.KEY_DELETE,
    0x4f: ecodes.KEY_END,
    0x51: ecodes.KEY_PAGEDOWN,
    0x48: ecodes.KEY_UP,
    0x4b: ecodes.KEY_LEFT,
    0x50: ecodes.KEY_DOWN,
    0x4d: ecodes.KEY_RIGHT,
    0x45: ecodes.KEY_NUMLOCK,
    0x35: ecodes.KEY_KPSLASH,
    0x1c: ecodes.KEY_KPENTER,
    0x1d: ecodes.KEY_RIGHTCTRL,
    0x38: ecodes.KEY_RIGHTALT,
    0x5b: ecodes.KEY_LEFTMETA,
    0x5c: ecodes.KEY_RIGHTMETA,
    0x5d: ecodes.KEY_COMPOSE,
}


def key_from_name(name: str) -> Key:
    key_name = name.lower().replace(" ", "")
    key = g_name_to_key.get(key_name)
    if key is not None:
        return key
    raise KeyboardError(f"Invalid key specified: {name}")


def key_from_code(scan_code: int, is_extended: bool) -> Key:
    if is_extended:
        evdev_code = _WIN_EXTENDED_TO_EVDEV.get(scan_code, scan_code)
    else:
        evdev_code = scan_code  # identical for non-extended keys

    key = g_evdev_to_key.get(evdev_code)
    if key is not None:
        return key

    # Unknown code — create a placeholder so profiles survive round-trips
    _log.warning(
        "key_from_code: unknown code (%d, %s), creating placeholder",
        scan_code, is_extended,
    )
    placeholder = Key(f"key_{evdev_code}", evdev_code, is_extended, 0)
    g_evdev_to_key[evdev_code] = placeholder
    return placeholder


def modifier_keys() -> List[Key]:
    return [
        g_name_to_key["leftshift"],
        g_name_to_key["leftcontrol"],
        g_name_to_key["leftalt"],
        g_name_to_key["rightshift"],
        g_name_to_key["rightcontrol"],
        g_name_to_key["rightalt"],
    ]


# ---------------------------------------------------------------------------
# Key tables
# Scan codes stored here are evdev keycodes.
# For non-extended keys they happen to equal Windows Set-1 scan codes.
# ---------------------------------------------------------------------------

g_name_to_key: dict[str, Key] = {
    # --- Function keys ---
    "f1":  Key("F1",  ecodes.KEY_F1,  False, 0),
    "f2":  Key("F2",  ecodes.KEY_F2,  False, 0),
    "f3":  Key("F3",  ecodes.KEY_F3,  False, 0),
    "f4":  Key("F4",  ecodes.KEY_F4,  False, 0),
    "f5":  Key("F5",  ecodes.KEY_F5,  False, 0),
    "f6":  Key("F6",  ecodes.KEY_F6,  False, 0),
    "f7":  Key("F7",  ecodes.KEY_F7,  False, 0),
    "f8":  Key("F8",  ecodes.KEY_F8,  False, 0),
    "f9":  Key("F9",  ecodes.KEY_F9,  False, 0),
    "f10": Key("F10", ecodes.KEY_F10, False, 0),
    "f11": Key("F11", ecodes.KEY_F11, False, 0),
    "f12": Key("F12", ecodes.KEY_F12, False, 0),
    "f13": Key("F13", ecodes.KEY_F13, False, 0),
    "f14": Key("F14", ecodes.KEY_F14, False, 0),
    "f15": Key("F15", ecodes.KEY_F15, False, 0),
    "f16": Key("F16", ecodes.KEY_F16, False, 0),
    "f17": Key("F17", ecodes.KEY_F17, False, 0),
    "f18": Key("F18", ecodes.KEY_F18, False, 0),
    "f19": Key("F19", ecodes.KEY_F19, False, 0),
    "f20": Key("F20", ecodes.KEY_F20, False, 0),
    "f21": Key("F21", ecodes.KEY_F21, False, 0),
    "f22": Key("F22", ecodes.KEY_F22, False, 0),
    "f23": Key("F23", ecodes.KEY_F23, False, 0),
    "f24": Key("F24", ecodes.KEY_F24, False, 0),
    # --- Letters ---
    "a": Key("A", ecodes.KEY_A, False, 0),
    "b": Key("B", ecodes.KEY_B, False, 0),
    "c": Key("C", ecodes.KEY_C, False, 0),
    "d": Key("D", ecodes.KEY_D, False, 0),
    "e": Key("E", ecodes.KEY_E, False, 0),
    "f": Key("F", ecodes.KEY_F, False, 0),
    "g": Key("G", ecodes.KEY_G, False, 0),
    "h": Key("H", ecodes.KEY_H, False, 0),
    "i": Key("I", ecodes.KEY_I, False, 0),
    "j": Key("J", ecodes.KEY_J, False, 0),
    "k": Key("K", ecodes.KEY_K, False, 0),
    "l": Key("L", ecodes.KEY_L, False, 0),
    "m": Key("M", ecodes.KEY_M, False, 0),
    "n": Key("N", ecodes.KEY_N, False, 0),
    "o": Key("O", ecodes.KEY_O, False, 0),
    "p": Key("P", ecodes.KEY_P, False, 0),
    "q": Key("Q", ecodes.KEY_Q, False, 0),
    "r": Key("R", ecodes.KEY_R, False, 0),
    "s": Key("S", ecodes.KEY_S, False, 0),
    "t": Key("T", ecodes.KEY_T, False, 0),
    "u": Key("U", ecodes.KEY_U, False, 0),
    "v": Key("V", ecodes.KEY_V, False, 0),
    "w": Key("W", ecodes.KEY_W, False, 0),
    "x": Key("X", ecodes.KEY_X, False, 0),
    "y": Key("Y", ecodes.KEY_Y, False, 0),
    "z": Key("Z", ecodes.KEY_Z, False, 0),
    # --- Digits ---
    "0": Key("0", ecodes.KEY_0, False, 0),
    "1": Key("1", ecodes.KEY_1, False, 0),
    "2": Key("2", ecodes.KEY_2, False, 0),
    "3": Key("3", ecodes.KEY_3, False, 0),
    "4": Key("4", ecodes.KEY_4, False, 0),
    "5": Key("5", ecodes.KEY_5, False, 0),
    "6": Key("6", ecodes.KEY_6, False, 0),
    "7": Key("7", ecodes.KEY_7, False, 0),
    "8": Key("8", ecodes.KEY_8, False, 0),
    "9": Key("9", ecodes.KEY_9, False, 0),
    # --- Navigation / control block ---
    "printscreen": Key("Print Screen", ecodes.KEY_SYSRQ,    True,  0),
    "scrolllock":  Key("Scroll Lock",  ecodes.KEY_SCROLLLOCK, False, 0),
    "pause":       Key("Pause",        ecodes.KEY_PAUSE,    False, 0),
    "insert":      Key("Insert",       ecodes.KEY_INSERT,   True,  0),
    "home":        Key("Home",         ecodes.KEY_HOME,     True,  0),
    "pageup":      Key("PageUp",       ecodes.KEY_PAGEUP,   True,  0),
    "delete":      Key("Delete",       ecodes.KEY_DELETE,   True,  0),
    "end":         Key("End",          ecodes.KEY_END,      True,  0),
    "pagedown":    Key("PageDown",     ecodes.KEY_PAGEDOWN, True,  0),
    # --- Arrow keys ---
    "up":    Key("Up",    ecodes.KEY_UP,    True, 0),
    "left":  Key("Left",  ecodes.KEY_LEFT,  True, 0),
    "down":  Key("Down",  ecodes.KEY_DOWN,  True, 0),
    "right": Key("Right", ecodes.KEY_RIGHT, True, 0),
    # --- Numpad ---
    "numlock":    Key("NumLock",      ecodes.KEY_NUMLOCK,  True,  0),
    "npdivide":   Key("Numpad /",     ecodes.KEY_KPSLASH,  True,  0),
    "npmultiply": Key("Numpad *",     ecodes.KEY_KPASTERISK, False, 0),
    "npminus":    Key("Numpad -",     ecodes.KEY_KPMINUS,  False, 0),
    "npplus":     Key("Numpad +",     ecodes.KEY_KPPLUS,   False, 0),
    "npenter":    Key("Numpad Enter", ecodes.KEY_KPENTER,  True,  0),
    "npdelete":   Key("Numpad Delete", ecodes.KEY_KPDOT,   False, 0),
    "np0": Key("Numpad 0", ecodes.KEY_KP0, False, 0),
    "np1": Key("Numpad 1", ecodes.KEY_KP1, False, 0),
    "np2": Key("Numpad 2", ecodes.KEY_KP2, False, 0),
    "np3": Key("Numpad 3", ecodes.KEY_KP3, False, 0),
    "np4": Key("Numpad 4", ecodes.KEY_KP4, False, 0),
    "np5": Key("Numpad 5", ecodes.KEY_KP5, False, 0),
    "np6": Key("Numpad 6", ecodes.KEY_KP6, False, 0),
    "np7": Key("Numpad 7", ecodes.KEY_KP7, False, 0),
    "np8": Key("Numpad 8", ecodes.KEY_KP8, False, 0),
    "np9": Key("Numpad 9", ecodes.KEY_KP9, False, 0),
    # --- Misc ---
    "backspace":    Key("Backspace",    ecodes.KEY_BACKSPACE,  False, 0),
    "space":        Key("Space",        ecodes.KEY_SPACE,      False, 0),
    "tab":          Key("Tab",          ecodes.KEY_TAB,        False, 0),
    "capslock":     Key("CapsLock",     ecodes.KEY_CAPSLOCK,   False, 0),
    "leftshift":    Key("Left Shift",   ecodes.KEY_LEFTSHIFT,  False, 0),
    "leftcontrol":  Key("Left Control", ecodes.KEY_LEFTCTRL,   False, 0),
    "leftwin":      Key("Left Win",     ecodes.KEY_LEFTMETA,   True,  0),
    "leftalt":      Key("Left Alt",     ecodes.KEY_LEFTALT,    False, 0),
    "rightshift":   Key("Right Shift",  ecodes.KEY_RIGHTSHIFT, False, 0),
    "rightshift2":  Key("Right Shift",  ecodes.KEY_RIGHTSHIFT, True,  0),
    "rightcontrol": Key("Right Control", ecodes.KEY_RIGHTCTRL, True,  0),
    "rightwin":     Key("Right Win",    ecodes.KEY_RIGHTMETA,  True,  0),
    "rightalt":     Key("Right Alt",    ecodes.KEY_RIGHTALT,   True,  0),
    "apps":         Key("Apps",         ecodes.KEY_COMPOSE,    True,  0),
    "enter":        Key("Enter",        ecodes.KEY_ENTER,      False, 0),
    "esc":          Key("Esc",          ecodes.KEY_ESC,        False, 0),
    # --- Punctuation / symbols ---
    "minus":        Key("-",  ecodes.KEY_MINUS,      False, 0),
    "equal":        Key("=",  ecodes.KEY_EQUAL,      False, 0),
    "leftbrace":    Key("[",  ecodes.KEY_LEFTBRACE,  False, 0),
    "rightbrace":   Key("]",  ecodes.KEY_RIGHTBRACE, False, 0),
    "backslash":    Key("\\", ecodes.KEY_BACKSLASH,  False, 0),
    "semicolon":    Key(";",  ecodes.KEY_SEMICOLON,  False, 0),
    "apostrophe":   Key("'",  ecodes.KEY_APOSTROPHE, False, 0),
    "grave":        Key("`",  ecodes.KEY_GRAVE,      False, 0),
    "comma":        Key(",",  ecodes.KEY_COMMA,      False, 0),
    "dot":          Key(".",  ecodes.KEY_DOT,        False, 0),
    "slash":        Key("/",  ecodes.KEY_SLASH,      False, 0),
}

# Reverse lookup: evdev keycode → Key
g_evdev_to_key: dict[int, Key] = {
    key.scan_code: key for key in g_name_to_key.values()
}

# Alias expected by gremlin/keyboard.py
g_scan_code_to_key = g_evdev_to_key

# Set lookup_name on all pre-populated keys
for _lname, _key in g_name_to_key.items():
    try:
        _key.lookup_name = _lname
    except KeyboardError:
        pass  # rightshift2 shares an evdev code with rightshift — skip duplicate
