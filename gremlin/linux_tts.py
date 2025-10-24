# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2025 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Linux-native text-to-speech using espeak-ng or festival.

Replaces the Windows-specific SAPI TTS system.
"""

import logging
import subprocess
import shutil
from typing import Optional

from . import event_handler, util


class TextToSpeech:
    """Linux text-to-speech using espeak-ng or festival.
    
    Tries to use espeak-ng first (modern, better quality), 
    falls back to espeak, then festival.
    """

    def __init__(self):
        """Creates a new instance and detects available TTS backend."""
        self._logger = logging.getLogger("system")
        self._backend = self._detect_backend()
        self._volume = 100  # 0-100
        self._rate = 0      # -10 to 10 (espeak: 80-450 wpm, default ~175)
        
        if self._backend is None:
            self._logger.warning(
                "No TTS backend found. Install espeak-ng or festival:\n"
                "  Ubuntu/Debian: sudo apt install espeak-ng\n"
                "  Fedora: sudo dnf install espeak-ng\n"
                "  Arch: sudo pacman -S espeak-ng"
            )
        else:
            self._logger.info(f"TTS backend: {self._backend}")
            # Test TTS
            self.speak("")

    def _detect_backend(self) -> Optional[str]:
        """Detect which TTS backend is available.
        
        Returns:
            'espeak-ng', 'espeak', 'festival', or None
        """
        for backend in ['espeak-ng', 'espeak', 'festival']:
            if shutil.which(backend):
                return backend
        return None

    def speak(self, text: str) -> None:
        """Speaks the given text asynchronously.

        The text is queued asynchronously so this method returns immediately.

        Args:
            text: the text to speak
        """
        if not text or self._backend is None:
            return
        
        try:
            if self._backend in ['espeak-ng', 'espeak']:
                self._speak_espeak(text)
            elif self._backend == 'festival':
                self._speak_festival(text)
        except Exception as e:
            self._logger.error(f"TTS encountered a problem: {e}")

    def _speak_espeak(self, text: str) -> None:
        """Speak using espeak or espeak-ng.
        
        Args:
            text: text to speak
        """
        # Convert rate from -10..10 to words per minute
        # Default espeak speed is ~175 wpm
        # Range: 80 (slowest) to 450 (fastest)
        wpm = int(175 + (self._rate * 27.5))  # -10 = 80wpm, +10 = 450wpm
        wpm = max(80, min(450, wpm))
        
        # Convert volume from 0-100 to 0-200 (espeak range)
        espeak_volume = int((self._volume / 100.0) * 200)
        
        # Run asynchronously (Popen instead of run)
        subprocess.Popen(
            [
                self._backend,
                f'-s{wpm}',        # Speed in words per minute
                f'-a{espeak_volume}',  # Amplitude (volume)
                text
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def _speak_festival(self, text: str) -> None:
        """Speak using festival.
        
        Args:
            text: text to speak
        """
        # Festival uses different parameters
        # Rate and volume control is more limited
        subprocess.Popen(
            ['festival', '--tts'],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True
        ).communicate(input=text)

    def set_volume(self, value: int) -> None:
        """Sets the volume anywhere between 0 and 100.

        Args:
            value: the new volume value (0-100)
        """
        self._volume = int(util.clamp(value, 0, 100))
        self._logger.debug(f"TTS volume set to {self._volume}")

    def set_rate(self, value: int) -> None:
        """Sets the speaking speed between -10 and 10.

        Negative values slow speech down while positive values speed it up.

        Args:
            value: the new speaking rate (-10 to 10)
        """
        self._rate = int(util.clamp(value, -10, 10))
        self._logger.debug(f"TTS rate set to {self._rate}")


def text_substitution(text: str) -> str:
    """Returns the provided text after running text substitution on it.

    Args:
        text: the text to substitute parts of
        
    Returns:
        Original text with parts substituted
    """
    eh = event_handler.EventHandler()
    text = text.replace("${current_mode}", eh.active_mode)
    return text
