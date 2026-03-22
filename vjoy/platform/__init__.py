# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Platform abstraction layer for the vjoy virtual joystick output backend.

    vjoy/platform/
    ├── base/
    │   └── backend.py   – AbstractVJoyBackend ABC
    ├── windows/
    │   └── backend.py   – WindowsVJoyBackend  (wraps vJoyInterface.dll)
    └── linux/
        └── backend.py   – LinuxVJoyBackend    (evdev.UInput)
"""
