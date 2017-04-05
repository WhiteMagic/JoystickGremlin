# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2017 Lionel Ott
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

"""Collection of actions that allow controlling JoystickGremlin."""

import gremlin.event_handler


class ModeList(object):

    """Represents a list of modes to cycle through."""

    def __init__(self, modes):
        """Creates a new instance with the provided modes.

        :param modes list of mode names to cycle through
        """
        self._modes = modes
        self._current_index = 0

    def next(self):
        """Returns the next mode in the sequence.

        :return name of the next mode in sequence
        """
        self._current_index = (self._current_index + 1) % len(self._modes)
        return self._modes[self._current_index]


def switch_mode(mode):
    """Switches the currently active mode to the one provided.

    :param mode the mode to switch to
    """
    gremlin.event_handler.EventHandler().change_mode(mode)


def switch_to_previous_mode():
    """Switches to the previously active mode."""
    eh = gremlin.event_handler.EventHandler()
    eh.change_mode(eh.previous_mode)


def cycle_modes(mode_list):
    """Cycles to the next mode in the provided mode list.

    If the currently active mode is not in the provided list of modes
    the first mode in the list is activated.

    :param mode_list list of mode names to cycle through
    """
    gremlin.event_handler.EventHandler().change_mode(mode_list.next())


def pause():
    """Pauses the execution of all callbacks.

    Only callbacks that are marked to be executed all the time will
    run when the program is paused.
    """
    gremlin.event_handler.EventHandler().pause()


def resume():
    """Resumes the execution of callbacks."""
    gremlin.event_handler.EventHandler().resume()


def toggle_pause_resume():
    """Toggles between executing and not executing callbacks."""
    gremlin.event_handler.EventHandler().toggle_active()
