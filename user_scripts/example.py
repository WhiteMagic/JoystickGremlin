# -*- coding: utf-8; -*-

# Copyright (C) 2025 Lionel Ott
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

from gremlin import types, user_script

bool_var = user_script.BoolVariable(
    "A bool variable",
    "Example bool variable",
    is_optional=True,
    initial_value=True,
)

float_var = user_script.FloatVariable(
    "A float variable",
    "Example float variable",
    is_optional=True,
    initial_value=1.1,
    min_value=-4,
    max_value=10,
)

int_var = user_script.IntegerVariable(
    "An integer variable",
    "Example integer variable",
    is_optional=True,
    initial_value=2,
    min_value=0,
    max_value=10,
)

mode_var = user_script.ModeVariable(
    "A mode variable",
    "Example mode variable",
    is_optional=True,
)

string_var = user_script.StringVariable(
    "A string variable",
    "Example string variable",
    is_optional=True,
    initial_value="example string var",
)

selection_var = user_script.SelectionVariable(
    "A selection variable",
    "Example selection variable",
    is_optional=True,
    option_list=["selection1", "selection2", "selection3"],
    default_index=1,
)

virtual_input_axis_var = user_script.VirtualInputVariable(
    "A virtual axis input variable",
    "Example virtual input variable for an axis",
    is_optional=True,
    valid_types=[types.InputType.JoystickAxis],
)

virtual_input_button_var = user_script.VirtualInputVariable(
    "A virtual button input variable",
    "Example virtual input variable for a button",
    is_optional=True,
    valid_types=[types.InputType.JoystickButton],
)

virtual_input_hat_var = user_script.VirtualInputVariable(
    "A virtual hat input variable",
    "Example virtual input variable for a hat",
    is_optional=True,
    valid_types=[types.InputType.JoystickHat],
)

physical_input_axis_var = user_script.PhysicalInputVariable(
    "A physical axis input variable",
    "Example physical input variable for an axis",
    is_optional=True,
    valid_types=[types.InputType.JoystickAxis],
)

physical_input_button_var = user_script.PhysicalInputVariable(
    "A physical button input variable",
    "Example physical input variable for a button",
    is_optional=True,
    valid_types=[types.InputType.JoystickButton],
)

physical_input_hat_var = user_script.PhysicalInputVariable(
    "A physical hat input variable",
    "Example physical input variable for a hat",
    is_optional=True,
    valid_types=[types.InputType.JoystickHat],
)

physical_input_axis_decorator = physical_input_axis_var.create_decorator(mode_var.value)


@physical_input_axis_decorator.axis(physical_input_axis_var.input_id)
def axis_handler(event):
    """Scales input axis by float_var and writes to output axis."""
    virtual_input_axis_var.remap(event.value * float_var.value)
