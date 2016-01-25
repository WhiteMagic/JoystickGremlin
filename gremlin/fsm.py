# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
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


class Transition(object):

    """Represents a single transition in the finite state machine."""

    def __init__(self, callback, new_state):
        """Creates a new Transition object.

        :param callback the function to call when this transition occurs
        :param new_state the state the state machine is in after
            executing this transition
        """
        self.callback = callback
        self.new_state = new_state


class FiniteStateMachine(object):

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
        """
        key = (self.current_state, action)
        assert(action in self.actions)
        assert(key in self.transitions)
        assert(self.transitions[key].new_state in self.states)
        self.transitions[key].callback()
        if self.debug:
            logging.debug("FSM: {} -> {} ({})".format(
                self.current_state,
                self.transitions[key].new_state,
                action
            ))
        self.current_state = self.transitions[key].new_state


if __name__ == "__main__":

    def no_op():
        print("no op")

    def manual_on():
        print("-> DC manual")

    def manual_off():
        print("<- DC manual")

    def auto_on():
        print("-> DC auto")

    def auto_off():
        print("<- DC auto")

    def mtb():
        print("DC manual -> DC both")

    def btm():
        print("DC both -> DC manual")

    def bta():
        print("DC both -> DC auto")

    def reset():
        print("reset")

    
    states = ["DC Off", "DC Manual", "DC Auto", "DC Both"]
    actions = ["reset", "manual", "auto"]
    transitions = {
        ("DC Off", "reset"):        Transition(no_op, "DC Off"),
        ("DC Off", "manual"):       Transition(manual_on, "DC Manual"),
        ("DC Off", "auto"):         Transition(auto_on, "DC Auto"),
        ("DC Auto", "reset"):       Transition(reset, "DC Off"),
        ("DC Auto", "manual"):      Transition(no_op, "DC Auto"),
        ("DC Auto", "auto"):        Transition(auto_off, "DC Off"),
        ("DC Manual", "reset"):     Transition(reset, "DC Off"),
        ("DC Manual", "manual"):    Transition(manual_off, "DC Off"),
        ("DC Manual", "auto"):      Transition(mtb, "DC Both"),
        ("DC Both", "reset"):       Transition(reset, "DC Off"),
        ("DC Both", "manual"):      Transition(bta, "DC Auto"),
        ("DC Both", "auto"):        Transition(btm, "DC Manual")
    }
    fsm = FiniteStateMachine("DC Off", states, actions, transitions)
    fsm.perform("reset")
    fsm.perform("manual")
    fsm.perform("auto")
    fsm.perform("auto")
    fsm.perform("manual")
