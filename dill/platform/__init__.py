# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Platform abstraction layer for the DILL joystick-input backend.

Structure mirrors gremlin/platform/:

    dill/platform/
    ├── base/
    │   ├── types.py     – portable ctypes structure definitions
    │   └── backend.py   – AbstractDillBackend ABC
    ├── windows/
    │   └── backend.py   – WindowsDillBackend  (wraps dill.dll via ctypes)
    └── linux/
        └── backend.py   – LinuxDillBackend    (evdev)
"""
