# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from PySide6 import QtCore

from gremlin import shared_state
from gremlin.common import SingletonDecorator
from gremlin.config import Configuration
from gremlin.input_refresh import RefreshPhysicalInputs
from gremlin.types import PropertyType


class Mode:
    """Simple containiner holding a mode's name and its identifier."""

    def __init__(
        self, name: str, previous: str | None, is_temporary: bool = False
    ) -> None:
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

    def __eq__(self, other: Mode) -> bool:
        return (
            self.name == other.name
            and self.previous == other.previous
            and self.is_temporary == other.is_temporary
        )


class ModeSequence:
    def __init__(self, modes: list[str]) -> None:
        """Creates a new ModeSequence instance.

        Args:
            modes: List of mode names making up the sequence.
        """
        self.modes = modes
        self._current_index = -1

    def next(self) -> str:
        """Returns the next mode in the sequence.

        Returns:
            Next mode in the sequence, wrapping around at the end.
        """
        # next_index = self._current_index % len(self.modes)
        self._current_index = (self._current_index + 1) % len(self.modes)
        return self.modes[self._current_index]


@SingletonDecorator
class ModeManager(QtCore.QObject):
    """Manages the mode change history."""

    mode_changed = QtCore.Signal(str)

    def __init__(self) -> None:
        QtCore.QObject.__init__(self)

        self._mode_stack = [Mode("Invalid", None)]
        self._config = Configuration()

    @property
    def current(self) -> Mode:
        return self._mode_stack[-1]

    def reset(self) -> None:
        self._mode_stack = [Mode(shared_state.current_profile.modes.first_mode, None)]
        self._config.set("global", "internal", "last-mode", self.current.name)

    def _exists(self, mode: Mode) -> bool:
        return mode in self._mode_stack

    def _update_mode(self) -> None:
        self._config.set("global", "internal", "last-mode", self.current.name)
        self.mode_changed.emit(self.current.name)
        if self._config.value("global", "general", "refresh-axis-on-mode-change"):
            RefreshPhysicalInputs.refresh_axes()

    def cycle(self, sequence: ModeSequence) -> None:
        self.switch_to(Mode(sequence.next(), self.current.name))

    def previous(self) -> None:
        if len(self._mode_stack) < 2:
            return

        # Swap the two top-most elements of the mode stack
        self._mode_stack[-1], self._mode_stack[-2] = (
            self._mode_stack[-2],
            self._mode_stack[-1],
        )
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
                "action", "change-mode", "resolution-mode"
            )
            idx = self._mode_stack.index(mode)

            if not mode.is_temporary:
                if resolution_mode == "Oldest":
                    self._mode_stack = self._mode_stack[:idx]
                elif resolution_mode == "Newest":
                    self._mode_stack = self._mode_stack[idx + 1 :]
            # Special handling if the loop is caused by a temporary mode
            else:
                if resolution_mode == "Oldest":
                    self._mode_stack = self._mode_stack[:idx]
                if resolution_mode == "Newest":
                    # 1. Find the index corresponding to the first non-temporary
                    #    mode entry in the stack before the idx mode
                    idx2 = idx
                    while idx2 > 0 and self._mode_stack[idx2].is_temporary:
                        idx2 -= 1
                    assert not self._mode_stack[idx2].is_temporary
                    # 2. Create new stack that no longer contains the old
                    #    temporary mode instance but retains all previous
                    #    modes until the first non-temporary entry
                    self._mode_stack = [m for m in self._mode_stack[idx2:] if m != mode]
                    # 3. Fix inconsistent stack entry transitions
                    for a, b in zip(self._mode_stack[:-1], self._mode_stack[1:]):
                        if a.name != b.previous:
                            b.previous = a.name

        self._mode_stack.append(mode)
        self._update_mode()

    def temporary(self, mode: Mode) -> None:
        mode.is_temporary = True
        self.switch_to(mode)

    def leave_temporary(self, mode: Mode) -> None:
        mode.is_temporary = True
        if self._mode_stack[-1] == mode:
            self.unwind()
        self._mode_stack = [m for m in self._mode_stack if m != mode]


Configuration().register(
    "action",
    "change-mode",
    "resolution-mode",
    PropertyType.Selection,
    "Oldest",
    "Defines how a what mode is switched to in the case that a cyclical mode "
    'traversal is detected. "Oldest" switches to the oldest mode in '
    'the cycle while "newest" finds the most recent common mode and '
    "switches to that one.",
    {"valid_options": ["Oldest", "Newest"]},
    True,
)
