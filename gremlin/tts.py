# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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
This module provides convenient access to the Microsoft SAPI text
to speech system.
"""

import logging
import win32com.client

from . import event_handler, util


class TextToSpeech:

    def __init__(self):
        """Creates a new instance."""
        self._speaker = win32com.client.Dispatch("SAPI.SpVoice")
        self.speak("")

    def speak(self, text):
        """Queues the given text to be spoken by SAPI using the async flag.

        Since the text is queued asynchronously this method returns
        immediately.

        :param text the text to speak
        """
        try:
            self._speaker.Speak(text, 1)
        except Exception as e:
            logging.getLogger("system").error(
                "TTS encountered a problem: {}".format(e)
            )

    def set_volume(self, value):
        """Sets the volume anywhere between 0 and 100.

        :param value the new volume value
        """
        self._speaker.Volume = int(util.clamp(value, 0, 100))

    def set_rate(self, value):
        """Sets the speaking speed between -10 and 10.

        Negative values slow speech down while positive values speed
        it up.

        :param value the new speaking rate
        """
        self._speaker.Rate = int(util.clamp(value, -10, 10))


def text_substitution(text):
    """Returns the provided text after running text substitution on it.

    :param text the text to substitute parts of
    :return original text with parts substituted
    """
    eh = event_handler.EventHandler()
    text = text.replace("${current_mode}", eh.active_mode)
    return text
