# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Platform abstraction layer (PAL) for JoystickGremlin.

This package provides platform-specific implementations for:
- Keyboard/mouse injection (sendinput, keyboard)
- Global keyboard/mouse event hooks (event_hook)
- Active process monitoring (process_monitor)
- Text-to-speech (tts)

The sub-packages `windows` and `linux` contain the concrete implementations.
Individual gremlin modules act as thin shims that re-export the correct
implementation based on `sys.platform` at import time.
"""
