# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
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

from gremlin.event_handler import EventHandler


def switch_mode(mode):
    """Switches the currently active mode to the one provided.

    :param mode the mode to switch to
    """
    EventHandler().change_mode(mode)


def switch_to_previous_mode():
    """Switches to the previously active mode."""
    eh = EventHandler()
    eh.change_mode(eh.previous_mode)


def cycle_modes(mode_list):
    """Cycles to the next mode in the provided mode list.

    If the currently active mode is not in the provided list of modes
    the first mode in the list is activated.

    :param mode_list list of mode names to cycle through
    """
    eh = EventHandler()
    if len(mode_list) == 0:
        mode_list = ["Global"]

    mode = eh.active_mode
    if mode not in mode_list:
        eh.change_mode(mode_list[0])
    else:
        idx = (mode_list.index(mode)+1) % len(mode_list)
        eh.change_mode(mode_list[idx])


def pause():
    """Pauses the execution of all callbacks.

    Only callbacks that are marked to be executed all the time will
    run when the program is paused.
    """
    EventHandler().pause()


def resume():
    """Resumes the execution of callbacks."""
    EventHandler().resume()


def toggle_pause_resume():
    """Toggles between executing and not executing callbacks."""
    EventHandler().toggle_active()
