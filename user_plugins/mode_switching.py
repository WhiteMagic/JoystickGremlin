import gremlin

chfs = gremlin.input_devices.JoystickDecorator(
    "CH Fighterstick USB",
    2382820288,
    "Global"
)

mode_list = gremlin.control_action.ModeList(
        ["Global", "Radio", "Landing"]
)

@chfs.button(10)
def temporary_mode_switch(event):
    if event.is_pressed:
        gremlin.control_action.switch_mode("Radio")
    else:
        gremlin.control_action.switch_to_previous_mode()

@chfs.button(11)
def cycle_modes(event):
    if event.is_pressed:
        gremlin.control_action.cycle_modes(mode_list)

@chfs.button(12)
def switch_to_global(event):
    if event.is_pressed:
        gremlin.control_action.switch_mode("Global")
