# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Linux TTS backend — espeak-ng via subprocess.

text_substitution is pure Python and fully functional on all platforms.
"""

import logging
import shutil
import subprocess

from gremlin import event_handler, util

_log = logging.getLogger("system")

# Cached check: is espeak-ng available?
_ESPEAK = shutil.which("espeak-ng") or shutil.which("espeak")


class TextToSpeech:

    """Text-to-speech via espeak-ng (non-blocking)."""

    # espeak-ng amplitude: 0-200 (default 100) — map from SAPI 0-100
    # espeak-ng rate: words/min (default 160) — map from SAPI -10..10
    _DEFAULT_AMPLITUDE = 100
    _DEFAULT_RATE = 160

    def __init__(self):
        if _ESPEAK is None:
            _log.warning(
                "TTS: espeak-ng not found. "
                "Install it with: sudo dnf install espeak-ng"
            )
        self._amplitude = self._DEFAULT_AMPLITUDE
        self._rate = self._DEFAULT_RATE

    def speak(self, text: str) -> None:
        if not text or _ESPEAK is None:
            return
        try:
            subprocess.Popen(
                [_ESPEAK, "-a", str(self._amplitude), "-s", str(self._rate), text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            _log.error("TTS encountered a problem: %s", exc)

    def set_volume(self, value) -> None:
        """Set volume. SAPI range 0-100 → espeak-ng amplitude 0-200."""
        self._amplitude = int(util.clamp(value, 0, 100) * 2)

    def set_rate(self, value) -> None:
        """Set rate. SAPI range -10..10 → espeak-ng ~80..320 words/min."""
        # Linear map: -10→80, 0→160, 10→320
        clamped = util.clamp(value, -10, 10)
        self._rate = int(160 + clamped * 16)


def text_substitution(text: str) -> str:
    """Returns the provided text after running text substitution on it."""
    eh = event_handler.EventHandler()
    text = text.replace("${current_mode}", eh.active_mode)
    return text
