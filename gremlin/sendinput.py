# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Platform-selecting shim for mouse injection.

On Windows: delegates to gremlin.platform.windows.sendinput (full implementation).
On Linux:   delegates to gremlin.platform.linux.sendinput (stub implementation).
"""

import sys

if sys.platform == "win32":
    from gremlin.platform.windows.sendinput import (  # noqa: F401
        MouseController,
        Vector2,
        MotionType,
        MouseMotion,
        FixedMouseMotion,
        AcceleratedMouseMotion,
        mouse_relative_motion,
        mouse_press,
        mouse_release,
        mouse_wheel,
    )
elif sys.platform.startswith("linux"):
    from gremlin.platform.linux.sendinput import (  # noqa: F401
        MouseController,
        Vector2,
        MotionType,
        MouseMotion,
        FixedMouseMotion,
        AcceleratedMouseMotion,
        mouse_relative_motion,
        mouse_press,
        mouse_release,
        mouse_wheel,
    )
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")
