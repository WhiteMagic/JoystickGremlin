import gremlin
from gremlin.spline import CubicSpline
from vjoy.vjoy import AxisName

tm16000 = gremlin.input_devices.JoystickDecorator(
        "Thrusmaster 16000M", 5314651233
)

default_curve = CubicSpline(
        [(-1.0, -1.0), (0.0, 0.0), (1.0, 1.0)]
)
sniper_curve = CubicSpline(
        [(-1.0, 0.5), (0.0, 0.0), (1.0, 0.5)]
)

active_weapon_groups = {}
active_curve = default_curve

def set_weapon_group(gid, is_pressed):
    global active_curve
    global active_weapon_groups
    if is_pressed:
        active_curve = sniper_curve
        active_weapon_groups[gid] = True
    else:
        active_weapon_groups[gid] = False
        if sum(active_weapon_groups.values()) == 0:
            active_curve = default_curve

@tm16000.button(1)
def weapon_group_1(event, vjoy):
    set_weapon_group(1, event.is_pressed)
    vjoy[1].button[1].is_pressed = event.is_pressed

@tm16000.button(2)
def weapon_group_2(event, vjoy):
    set_weapon_group(2, event.is_pressed)
    vjoy[1].button[2].is_pressed = event.is_pressed

@tm16000.button(3)
def weapon_group_3(event, vjoy):
    set_weapon_group(3, event.is_pressed)
    vjoy[1].button[3].is_pressed = event.is_pressed

@tm16000.axis(1)
def pitch(event, vjoy):
    vjoy[1].axis[AxisName.X].value = active_curve(event.value)

@tm16000.axis(2)
def yaw(event, vjoy):
    vjoy[1].axis[AxisName.Y].value = active_curve(event.value)
