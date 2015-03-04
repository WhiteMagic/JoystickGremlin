import gremlin
from vjoy.vjoy import AxisName

def set_throttle(vjoy, value):
    vjoy[1].axis[AxisName.Z].value = value

@gremlin.input_devices.keyboard("1")
def throttle_0(event, vjoy):
    if event.is_pressed:
        set_throttle(vjoy, -1.0)

@gremlin.input_devices.keyboard("2")
def throttle_33(event, vjoy):
    if event.is_pressed:
        set_throttle(vjoy, -0.33)

@gremlin.input_devices.keyboard("3")
def throttle_66(event, vjoy):
    if event.is_pressed:
        set_throttle(vjoy, 0.33)

@gremlin.input_devices.keyboard("4")
def throttle_100(event, vjoy):
    if event.is_pressed:
        set_throttle(vjoy, 1.0)
