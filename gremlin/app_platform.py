# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Platform-selecting shim for application-level configuration.

Exposes a single module-level instance `app_backend` that callers use
without needing to know which platform they are running on.
"""

import sys

if sys.platform == "win32":
    from gremlin.platform.windows.app import AppBackend
elif sys.platform.startswith("linux"):
    from gremlin.platform.linux.app import AppBackend
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")

app_backend: AppBackend = AppBackend()
