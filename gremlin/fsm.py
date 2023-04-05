# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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

"""Implementation of a very simple finite state machine."""

import logging


class Transition:

    """Represents a single transition in the finite state machine."""

    def __init__(self, callback, new_state):
        """Creates a new Transition object.

        :param callback the function to call when this transition occurs
        :param new_state the state the state machine is in after
            executing this transition
        """
        self.callback = callback
        self.new_state = new_state


class FiniteStateMachine:

    """Simple finite state machine."""

    def __init__(self, start_state, states, actions, transitions, debug=False):
        """Creates a new finite state machine object.

        :param start_state the state in which the FSM starts in
        :param states the set of states
        :param actions the possible actions of the FSM
        :param transitions the states x actions transition matrix
        :param debug log debug messages if True
        """
        assert(start_state in states)

        self.states = states
        self.actions = actions
        self.transitions = transitions
        self.current_state = start_state
        self.debug = debug

    def perform(self, action):
        """Performs a state transition on the FSM.

        :param action the action to perform
        :return returns the state transition function's return value
        """
        key = (self.current_state, action)
        assert(action in self.actions)
        assert(key in self.transitions)
        assert(self.transitions[key].new_state in self.states)
        value = self.transitions[key].callback()
        if self.debug:
            logging.getLogger("system").debug("FSM: {} -> {} ({})".format(
                self.current_state,
                self.transitions[key].new_state,
                action
            ))
        self.current_state = self.transitions[key].new_state
        return value
