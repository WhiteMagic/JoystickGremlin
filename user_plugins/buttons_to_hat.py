import gremlin
from gremlin.user_plugin import *


mode = ModeVariable(
        "Mode",
        "The mode to use for this mapping"
)
vjoy_hat = VirtualInputVariable(
        "Output Hat",
        "vJoy hat to use as the output",
        [gremlin.common.InputType.JoystickHat]
)
btn_1 = PhysicalInputVariable(
        "Button Up",
        "Button which will be mapped to the up direction of the hat.",
        [gremlin.common.InputType.JoystickButton]
)
btn_2 = PhysicalInputVariable(
        "Button Right",
        "Button which will be mapped to the right direction of the hat.",
        [gremlin.common.InputType.JoystickButton]
)
btn_3 = PhysicalInputVariable(
        "Button Down",
        "Button which will be mapped to the down direction of the hat.",
        [gremlin.common.InputType.JoystickButton]
)
btn_4 = PhysicalInputVariable(
        "Button Left",
        "Button which will be mapped to the left direction of the hat.",
        [gremlin.common.InputType.JoystickButton]
)

state = [0, 0]

decorator_1 = btn_1.create_decorator(mode.value)
decorator_2 = btn_2.create_decorator(mode.value)
decorator_3 = btn_3.create_decorator(mode.value)
decorator_4 = btn_4.create_decorator(mode.value)


def set_state(vjoy):
    device = vjoy[vjoy_hat.value["device_id"]]
    device.hat(vjoy_hat.value["input_id"]).direction  = tuple(state)


@decorator_1.button(btn_1.input_id)
def button_1(event, vjoy):
    global state
    state[1] = 1 if event.is_pressed else 0
    set_state(vjoy)


@decorator_2.button(btn_2.input_id)
def button_2(event, vjoy):
    global state
    state[0] = 1 if event.is_pressed else 0
    set_state(vjoy)


@decorator_3.button(btn_3.input_id)
def button_3(event, vjoy):
    global state
    state[1] = -1 if event.is_pressed else 0
    set_state(vjoy)


@decorator_4.button(btn_4.input_id)
def button_4(event, vjoy):
    global state
    state[0] = -1 if event.is_pressed else 0
    set_state(vjoy)
