import logging
import gremlin
from gremlin.cubic_spline import CubicSpline
from gremlin.input_devices import keyboard, macro
from vjoy.vjoy import AxisName

# Create joystick decorator for the CH Fighterstick in global mode
chfs = gremlin.input_devices.JoystickDecorator(
    "CH Fighterstick USB",
    2382820288,
    "global"
)
chfs_roll = gremlin.input_devices.JoystickDecorator(
    "CH Fighterstick USB",
    2382820288,
    "roll"
)
chpp = gremlin.input_devices.JoystickDecorator(
    "CH Pro Pedals USB",
    2382820032,
    "global"
)

# Sensitivity curve setup
default_curve = CubicSpline([
    (-1.00, -1.00),
    (-0.75, -0.65),
    (-0.25, -0.15),
    ( 0.00,  0.00),
    ( 0.25,  0.15),
    ( 0.75,  0.65),
    ( 1.00,  1.00),
])
sniper_curve = CubicSpline([
    (-1.00, -0.50),
    (-0.50, -0.175),
    ( 0.00,  0.00),
    ( 0.50,  0.175),
    ( 1.00,  0.50)
])
one_to_one_curve = CubicSpline([
    (-1.0, -1.0),
    ( 0.0,  0.0),
    ( 1.0,  1.0)
])

left_pedal = 0
right_pedal = 0

# Build macros so we don't construct them each time the callback is run
shield_macros = {
    "reset": macro.Macro(),
    "front": macro.Macro(),
    "rear": macro.Macro(),
    "left": macro.Macro(),
    "right": macro.Macro()
}
shield_macros["reset"].tap("KP5")
shield_macros["front"].press("KP8")
shield_macros["front"].pause(0.5)
shield_macros["front"].release("KP8")
shield_macros["rear"].press("KP2")
shield_macros["rear"].pause(0.5)
shield_macros["rear"].release("KP2")
shield_macros["left"].press("KP4")
shield_macros["left"].pause(0.5)
shield_macros["left"].release("KP4")
shield_macros["right"].press("KP6")
shield_macros["right"].pause(0.5)
shield_macros["right"].release("KP6")

cm_flare = macro.Macro()
cm_flare.tap(macro.Keys.Z)
cm_flare.tap(macro.Keys.M)
cm_flare.tap(macro.Keys.Z)

cm_chaff = macro.Macro()
cm_chaff.tap(macro.Keys.M)

active_weapon_groups = {}
active_curve = default_curve
#active_curve = one_to_one_curve


def set_weapon_group(gid, is_pressed):
    global active_curve
    if is_pressed:
        active_curve = sniper_curve
        active_weapon_groups[gid] = True
    else:
        active_weapon_groups[gid] = False
        if sum(active_weapon_groups.values()) == 0:
            active_curve = default_curve

def pedal_position():
    return right_pedal / 2 - left_pedal / 2


@chfs.button(11)
def reset_shields(event):
    if event.is_pressed:
        shield_macros["reset"].run()


@chfs.hat(1)
def shield_management(event):
    if event.value == (0, 1):
        shield_macros["front"].run()
    elif event.value == (0, -1):
        shield_macros["rear"].run()
    elif event.value == (1, 0):
        shield_macros["right"].run()
    elif event.value == (-1, 0):
        shield_macros["left"].run()


is_firing = False
@chfs.button(1)
def fire_group1(event):
    set_weapon_group(1, event.is_pressed)


@chfs.button(4)
def fire_group2(event):
    set_weapon_group(4, event.is_pressed)


@chfs.button(16)
def launch_flare(event, vjoy):
    if event.is_pressed:
        cm_flare.run()


@chfs.button(14)
def launch_chaff(event, vjoy):
    if event.is_pressed:
        cm_chaff.run()


@chfs.axis(1)
def axis1(event, vjoy):
    vjoy[1].axis[AxisName.X].value = active_curve(event.value)


@chfs.axis(2)
def axis2(event, vjoy):
    vjoy[1].axis[AxisName.Y].value = active_curve(event.value)


@chfs_roll.axis(1)
def axis2(event, vjoy):
    vjoy[1].axis[AxisName.RX].value = event.value


#@chpp.axis(1)
#def left_pedal(event, vjoy):
#    global left_pedal
#    left_pedal = event.value
#    vjoy[1].axis[AxisName.RZ].value = pedal_position()

#@chpp.axis(2)
#def right_pedal(event, vjoy):
#    global right_pedal
#    right_pedal = event.value
#    vjoy[1].axis[AxisName.RZ].value = pedal_position()


@keyboard("LAlt", "roll")
def reset_roll(event, vjoy):
    if not event.is_pressed:
        vjoy[1].axis[AxisName.RX].value = 0.0
        gremlin.control_action.switch_mode("global")


@keyboard("1")
def throttle_0(event, vjoy):
    vjoy[1].axis[AxisName.Z].value = 1.0


@keyboard("2")
def throttle_33(event, vjoy):
    vjoy[1].axis[AxisName.Z].value = 0.33


@keyboard("3")
def throttle_66(event, vjoy):
    vjoy[1].axis[AxisName.Z].value = -0.33


@keyboard("4")
def throttle_100(event, vjoy):
    vjoy[1].axis[AxisName.Z].value = -1.0
