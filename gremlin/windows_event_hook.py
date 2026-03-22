# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Platform-selecting shim for global keyboard/mouse event hooks.

On Windows: delegates to gremlin.platform.windows.event_hook (full implementation).
On Linux:   delegates to gremlin.platform.linux.event_hook (stub implementation).
"""

import sys

if sys.platform == "win32":
    from gremlin.platform.windows.event_hook import (  # noqa: F401
        KeyboardHook,
        MouseHook,
        KeyEvent,
        MouseEvent,
    )
elif sys.platform.startswith("linux"):
    from gremlin.platform.linux.event_hook import (  # noqa: F401
        KeyboardHook,
        MouseHook,
        KeyEvent,
        MouseEvent,
    )
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")
