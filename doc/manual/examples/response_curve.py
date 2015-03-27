import gremlin
from gremlin.spline import CubicSpline
from vjoy.vjoy import AxisName

chfs = gremlin.input_devices.JoystickDecorator(
    "CH Fighterstick USB",
    2382820288,
    "global"
)

curve = CubicSpline([
    (-1.0, -1.0),
    (-0.5, -0.25),
    ( 0.0,  0.0),
    ( 0.5,  0.25),
    ( 1.0,  1.0)
])

@chfs.axis(1)
def pitch(event, vjoy):
    vjoy[1].axis[AxisName.X].value = curve(event.value)

@chfs.axis(2)
def yaw(event, vjoy):
    vjoy[1].axis[AxisName.Y].value = curve(event.value)
