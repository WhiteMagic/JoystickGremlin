# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Implementation of a very simple finite state machine."""

from collections.abc import Callable
import logging
import threading
from typing import Any, Dict, List, Tuple


class Transition:

    """Represents a single transition in the finite state machine."""

    def __init__(
            self,
            callbacks: List[Callable[..., Any]],
            new_state: str
    ) -> None:
        """Creates a new Transition object.

        Args:
            callback: function to call when executing the transition
            new_state: resulting state of the transition after executing the
                callback
        """
        self.callbacks = callbacks
        self.new_state = new_state


class FiniteStateMachine:

    """Simple finite state machine."""

    def __init__(
            self,
            start_state: str,
            states: List[str],
            actions: List[str],
            transitions: Dict[Tuple[str, str], Transition],
            debug: bool=False,
            identifier: str="FSM"
    ) -> None:
        """Creates a new finite state machine object.

        Args:
            start_state: the state in which the FSM starts in
            states: list of valid states for the FSM
            actions: the possible actions of the FSM
            transitions: dictionary mapping state x action keys to transitions
            debug: logs debug messages if True
            identifier: name used to identify the FSM instance
        """
        assert(start_state in states)

        self.start_state = start_state
        self.states = states
        self.actions = actions
        self.transitions = transitions
        self.current_state = start_state
        self.debug = debug
        self.identifier = identifier
        self._lock = threading.Lock()

    def reset(self) -> None:
        """Resets the FSM to its initial start state."""
        with self._lock:
            self.current_state = self.start_state

    def set_state(self, state: str) -> None:
        """Sets the current state without performing a transition.

        Args:
            state: the state to put the FSM into
        """
        with self._lock:
            if state in self.states:
                self.current_state = state

    def try_perform(self, action: str, *args: Any) -> list[Any] | None:
        """Attempts a state transition, returning None if invalid instead
        of raising.

        Args:
            action: name of the action to execute

        Returns:
            Result of executing the state transition callback(s), or None
            if no transition exists for the current state and action.
        """
        assert(action in self.actions)
        with self._lock:
            key = (self.current_state, action)
            if key not in self.transitions:
                return None
            assert(self.transitions[key].new_state in self.states)

            values = [cb(*args) for cb in self.transitions[key].callbacks]
            if self.debug:
                logging.getLogger("system").debug(
                    f"FSM ({self.identifier}): {self.current_state} -> " +
                    f"{self.transitions[key].new_state} ({action})"
                )
            self.current_state = self.transitions[key].new_state
            return values

    def perform(self, action: str, *args: Any) -> list[Any]:
        """Performs a state transition on the FSM.

        Args:
            action: name of the action to execute

        Returns:
            Result of executing the state transition callback(s).
        """
        result = self.try_perform(action, *args)
        if result is None:
            key = (self.current_state, action)
            logging.getLogger("system").exception(
                f"Missing transition: {key}: {self.transitions.keys()}"
            )
            assert(key in self.transitions)
        return result
