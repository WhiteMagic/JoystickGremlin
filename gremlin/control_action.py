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


from typing import List

from gremlin.common import SingletonDecorator
from gremlin.error import GremlinError
import gremlin.event_handler


class Mode:

    """Simple containiner holding a mode's name and its identifier."""

    def __init__(self, name: str, identifier: str):
        """Creates a new Mode instance.

        Args:
            name: The name of the mode
            identifier: The identifier of the mode
        """
        self._name = name
        self._identifier = identifier

    @property
    def name(self) -> str:
        return self._name

    @property
    def identifier(self) -> str:
        return self._identifier

    def __eq__(self, other) -> bool:
        return self.identifier == other.identifier


class ModeSequence:

    def __init__(self, modes: List[Mode]):
        """Creates a new ModeSequence instance.

        Args:
            modes: List of modes making up the sequence.
        """
        self.modes = modes
        self._current_index = 0

    def next(self) -> Mode:
        """Returns the next mode in the sequence.

        Returns:
            Next mode in the sequence, wrapping around at the end.
        """
        self._current_index = (self._current_index + 1) % len(self.modes)
        return self.modes[self._current_index]


@SingletonDecorator
class ModeManager:

    """Manages the mode change history."""

    def __init__(self):
        self._mode_stack = []

    def _exists(self, mode: Mode) -> bool:
        return mode in self._mode_stack

    # def cycle(self) -> None:
    #     pass

    def previous(self) -> None:
        if len(self._mode_stack) < 2:
            raise GremlinError(
                "Attempting to switch to previous mode with less than two"
                "modes on the stack."
            )

        gremlin.event_handler.EventHandler().change_mode(
            self._mode_stack[-2].name
        )

    def unwind(self) -> None:
        if len(self._mode_stack) < 2:
            raise GremlinError(
                "Attempting to unwind the mode stack with less than two modes."
            )

        mode = self._mode_stack.pop()
        gremlin.event_handler.EventHandler().change_mode(mode.name)

    def switch_to(self, mode: Mode) -> None:
        if self._exists(mode):
            self._mode_stack.remove(mode)
        self._mode_stack.append(mode)
        gremlin.event_handler.EventHandler().change_mode(mode.name)

    # def temporary(self, mode: Mode) -> None:
    #     pass


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
