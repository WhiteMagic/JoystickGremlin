# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Platform-selecting shim for keyboard operations.

On Windows: delegates to gremlin.platform.windows.keyboard (full implementation).
On Linux:   delegates to gremlin.platform.linux.keyboard (stub implementation).
"""

import sys

if sys.platform == "win32":
    from gremlin.platform.windows.keyboard import (  # noqa: F401
        Key,
        send_key_down,
        send_key_up,
        key_from_name,
        key_from_code,
        modifier_keys,
        g_scan_code_to_key,
        g_name_to_key,
    )
elif sys.platform.startswith("linux"):
    from gremlin.platform.linux.keyboard import (  # noqa: F401
        Key,
        send_key_down,
        send_key_up,
        key_from_name,
        key_from_code,
        modifier_keys,
        g_scan_code_to_key,
        g_name_to_key,
    )
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")
