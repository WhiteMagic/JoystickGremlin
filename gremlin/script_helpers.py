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

"""This is a collection of functions that make writing of scripts
a bit easier by providing commonly used functionality."""


def save_axis_state(vjoy):
    """Returns an object representing the current state of all axes.

    :param vjoy the vJoy instance to store the axss state of
    :return dictionary storing the axes state
    """
    state = {}
    for key, axis in vjoy.axis.items():
        state[key] = axis.value
    return state

def load_axis_state(vjoy, state):
    """Sets the provided state in the vJoy instance.

    :param vjoy the vJoy instance to modify
    :param state the axis state to set in the vJoy instance
    """
    for key, value in state.items():
        vjoy.axis[key].value = value
        print(key, value)
