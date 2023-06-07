# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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
import logging

log = logging.getLogger("mode_stack")

class ModeList:

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



class Mode:
    def __init__(self, mode_name, temporary, cycled=False): # TODO: remove =False from cycled when everything else works to cleanup the API
        self._mode_name = mode_name
        self._temp = temporary
        self._cycled = cycled


    @property
    def mode_name(self):
        return self._mode_name


    @property
    def is_temp(self):
        return self._temp


    @property
    def is_cycled(self):
        return self._cycled


    def __str__(self):
        return f"{self.__class__.__name__}(name: {self._mode_name}, temp: {self._temp}, cycled: {self._cycled})"


    def __repr__(self):
        return self.__str__()

# a stack of modes - used when using switch to previous and temporary modes
mode_stack = []

# only use temporary mode check if specified
def mode_stack_is_last_mode(mode, temporary=None):

    # if temporary is not specified, we remove temp nodes before doing the check
    # to be able to return True for cases where mode_stack has the following
    # content 'non-temp-mode-A, temp-mode-B' and 'non-temp-mode-A' is being
    # passed as mode

    if not temporary:
        mode_stack_check = list(filter(lambda m: not m.is_temp, mode_stack))
    else:
        mode_stack_check = mode_stack

    return mode_stack_check and mode_stack_check[-1].mode_name == mode and ((temporary is None) or (mode_stack_check[-1].is_temp == temporary))


def mode_stack_get_prev():
    return mode_stack[-2] if len(mode_stack) > 1 else mode_stack[0]


def mode_stack_get_last():
    return mode_stack[-1]


def mode_stack_remove(mode, temporary=None):
    global mode_stack  
    result = filter(lambda m: not (m.mode_name == mode and (temporary is None or m.is_temp == temporary)), mode_stack)
    mode_stack = list(result)


def mode_stack_reset(mode = None):
    global mode_stack
    if mode:
        mode_stack = [Mode(mode, False)]
    else:
        mode_stack = []
    log.debug("mode_stack reset")


def cycled_mode_already_stacked(mode):
    global mode_stack
    result = filter(lambda m: m.mode_name == mode and m.is_cycled and not m.is_temp, mode_stack)
    if len(list(result)) > 0:
        return True
    return False


def remove_cycled_mode(mode):
    global mode_stack
    result = filter(lambda m: not (m.mode_name == mode and m.is_cycled and not m.is_temp), mode_stack)
    mode_stack = list(result)


def switch_mode(mode, temporary=False):
    """Switches the currently active mode to the one provided.

    :param mode the mode to switch to
    """
    
    log.debug(f"switch_mode({mode}): {mode_stack}")
    
    if not mode_stack_is_last_mode(mode, temporary=temporary):
        log.debug(f"Adding mode {mode} to mode_stack. temporary={temporary}")
        mode_stack.append(Mode(mode, temporary))

    gremlin.event_handler.EventHandler().change_mode(mode)
    log.debug(f"switch_mode({mode}, {temporary}): done - {mode_stack}")


def switch_to_previous_mode(mode_name=None):
    """Switches to the previously active mode."""

    log.debug(f"switch_to_previous_mode({mode_name}): {mode_stack}")

    # can't go beyond first mode
    if len(mode_stack) == 1:
        log.debug(f"switch_to_previous_mode({mode_name}): ignoring, can't go beyond first mode.")
        return

    # if switching to previous mode is a result of temporary mode switch
    # button being released and that temporary mode was not on the top of the stack
    # keep the current mode and remove the temporary mode from the stack

    temporary = None

    # switch_to_previous_mode w/o mode_name gets called when non-temporary switch to previous mode is called
    # therefore we can safely the last mode used from the stack
    if not mode_name:
        mode_name = mode_stack_get_last().mode_name

    eh = gremlin.event_handler.EventHandler()   
    if mode_stack_is_last_mode(mode_name):
        prev_mode = mode_stack_get_prev().mode_name;
        mode_stack_remove(mode_name)
        eh.change_mode(prev_mode)
        log.debug(f"switch_to_previous_mode({mode_name}) performed.")
    else:
        mode_stack_remove(mode_name, temporary=True)
        eh.change_mode(mode_stack_get_last().mode_name) # update status bar (mode count)
        log.debug(f"switch_to_previous_mode({mode_name}) ignored.")
        

    log.debug(f"switch_to_previous_mode({mode_name}): done - {mode_stack}")


def cycle_modes(mode_list):
    """Cycles to the next mode in the provided mode list.

    If the currently active mode is not in the provided list of modes
    the first mode in the list is activated.

    :param mode_list list of mode names to cycle through
    """
    # if the mode being switched to is already in the mode_stack
    # remove it first, so the mode stack does not continuously grow.
    # If someone is cycling through all the modes it will
    # increase the mode stack only by number of modes in the
    # mode_list

    mode = mode_list.next()

    if cycled_mode_already_stacked(mode):
        log.debug(f"Removing cycled mode {mode} from stack.")
        remove_cycled_mode(mode)

    log.debug(f"Adding cycled mode {mode} to mode_stack.")
    mode_stack.append(Mode(mode, temporary=False, cycled=True))

    gremlin.event_handler.EventHandler().change_mode(mode)

    log.debug(f"cycle_modes({mode}): done - {mode_stack}")


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
