# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Platform-selecting shim for text-to-speech.

On Windows: delegates to gremlin.platform.windows.tts (SAPI implementation).
On Linux:   delegates to gremlin.platform.linux.tts (stub implementation).
"""

import sys

if sys.platform == "win32":
    from gremlin.platform.windows.tts import (  # noqa: F401
        TextToSpeech,
        text_substitution,
    )
elif sys.platform.startswith("linux"):
    from gremlin.platform.linux.tts import (  # noqa: F401
        TextToSpeech,
        text_substitution,
    )
else:
    raise ImportError(f"Unsupported platform: {sys.platform}")
