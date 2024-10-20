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

from PySide6 import QtCore

from gremlin import shared_state
from gremlin.common import SingletonDecorator
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.types import PropertyType


class Mode:

    """Simple containiner holding a mode's name and its identifier."""

    def __init__(
            self,
            name: str,
            previous: str | None,
            is_temporary: bool=False
    ):
        """Creates a new Mode instance.

        Args:
            name: name of the mode
            previous: name of the previous mode
            is_temporary: True if the mode is temporary, False otherwise
        """
        self._name = name
        self._previous = previous
        self._is_temporary = is_temporary

    @property
    def name(self) -> str:
        return self._name

    @property
    def previous(self) -> str | None:
        return self._previous

    @previous.setter
    def previous(self, value: str | None) -> None:
        self._previous = value

    @property
    def is_temporary(self) -> bool:
        return self._is_temporary

    @is_temporary.setter
    def is_temporary(self, value: bool) -> None:
        self._is_temporary = value

    def __eq__(self, other) -> bool:
        return (self.name == other.name and
                self.previous == other.previous and
                self.is_temporary == other.is_temporary)


class ModeSequence:

    def __init__(self, modes: List[str]):
        """Creates a new ModeSequence instance.

        Args:
            modes: List of mode names making up the sequence.
        """
        self.modes = modes
        self._current_index = 0

    def next(self) -> str:
        """Returns the next mode in the sequence.

        Returns:
            Next mode in the sequence, wrapping around at the end.
        """
        self._current_index = (self._current_index + 1) % len(self.modes)
        return self.modes[self._current_index]


@SingletonDecorator
class ModeManager(QtCore.QObject):

    """Manages the mode change history."""

    mode_changed = QtCore.Signal(str)

    def __init__(self):
        QtCore.QObject.__init__(self)

        self._mode_stack = [Mode("Invalid", None)]
        self._config = Configuration()

    @property
    def current(self) -> Mode:
        return self._mode_stack[-1]

    def reset(self) -> None:
        self._mode_stack = [
            Mode(shared_state.current_profile.modes.first_mode, None)
        ]
        self._config.set("global", "internal", "last_mode", self.current.name)

    def _exists(self, mode: Mode) -> bool:
        return mode in self._mode_stack

    def _update_mode(self) -> None:
        self._config.set("global", "internal", "last_mode", self.current.name)
        self.mode_changed.emit(self.current.name)

    def cycle(self, sequence: ModeSequence) -> None:
        self.switch_to(Mode(sequence.next(), self.current.name))

    def previous(self) -> None:
        if len(self._mode_stack) < 2:
            return

        # Swap the two top-most elements of the mode stack
        self._mode_stack[-1], self._mode_stack[-2] = \
            self._mode_stack[-2], self._mode_stack[-1]
        self._update_mode()

    def unwind(self) -> None:
        if len(self._mode_stack) < 2:
            return

        # Remove top mode in stack
        self._mode_stack.pop()
        self._update_mode()

    def switch_to(self, mode: Mode) -> None:
        # Detect cycle in the mode stack and resolve it
        if self._exists(mode):
            resolution_mode = Configuration().value(
                "profile", "mode-change", "resolution-mode"
            )
            idx = self._mode_stack.index(mode)

            if not mode.is_temporary:
                if resolution_mode == "oldest":
                    self._mode_stack = self._mode_stack[:idx]
                elif resolution_mode == "newest":
                    self._mode_stack = self._mode_stack[idx+1:]
            # Special handling if the loop is caused by a temporary mode
            else:
                if resolution_mode == "oldest":
                    self._mode_stack = self._mode_stack[:idx]
                if resolution_mode == "newest":
                    # 1. Find the index corresponding to the first non-temporary
                    #    mode entry in the stack before the idx mode
                    idx2 = idx
                    while idx2 > 0 and self._mode_stack[idx2].is_temporary:
                        idx2 -= 1
                    assert not self._mode_stack[idx2].is_temporary
                    # 2. Create new stack that no longer contains the old
                    #    temporary mode instance but retains all previous
                    #    modes until the first non-temporary entry
                    self._mode_stack = [
                        m for m in self._mode_stack[idx2:] if m != mode
                    ]
                    # 3. Fix inconsistent stack entry transitions
                    for a, b in zip(self._mode_stack[:-1], self._mode_stack[1:]):
                        if a.name != b.previous:
                            b.previous = a.name

        self._mode_stack.append(mode)
        self._update_mode()

    def temporary(self, mode: Mode) -> None:
        mode.is_temporary = True
        self.switch_to(mode)

    def leave_temporary(self, mode) -> None:
        mode.is_temporary = True
        if self._mode_stack[-1] == mode:
            self.unwind()
        self._mode_stack = [m for m in self._mode_stack if m != mode]


Configuration().register(
    "profile",
    "mode-change",
    "resolution-mode",
    PropertyType.Selection,
    "oldest",
    "Defines how a mode cycle is resolved.",
    {
        "valid_options": ["oldest", "newest"]
    },
    True
)
