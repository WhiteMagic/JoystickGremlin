# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

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
    min_value=-20,
    max_value=10,
)

key_var = user_script.KeyboardVariable(
    "A keyboard variable",
    "Example keyboard variable",
    is_optional=True,
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

@physical_input_axis_var.decorator(mode_var)
def axis_handler(event):
    """Scales input axis by float_var and writes to output axis."""
    virtual_input_axis_var.remap(event.value * float_var.value)


@physical_input_button_var.decorator(mode_var)
def button_handler(event):
    """XORs the input button with bool_var and writes to output button."""
    virtual_input_button_var.remap(event.is_pressed ^ bool_var.value)


@physical_input_hat_var.decorator(mode_var)
def hat_handler(event):
    """Forwards the input hat unmodified to output hat."""
    virtual_input_hat_var.remap(event.value)

@key_var.decorator(mode_var)
def keyboard_handler(event):
    print("Keyboard event:", event)
