import ctypes
import enum
from vjoy.vjoy_interface import VJoyState, VJoyInterface
from gremlin.error import VJoyError


class AxisName(enum.Enum):

    """Enumeration of the valid axis names."""

    X = 0x30
    Y = 0x31
    Z = 0x32
    RX = 0x33
    RY = 0x34
    RZ = 0x35
    SL0 = 0x36
    SL1 = 0x37


class Axis(object):

    """Represents an analog axis in vJoy, allows setting the value
    of the axis."""

    def __init__(self, vjoy_id, axis_id):
        """Creates a new object.

        :param vjoy_id the id of the vJoy device this axis belongs to
        :param axis_id the id of the axis this object controls
        """
        self.vjoy_id = vjoy_id
        self.axis_id = axis_id
        self._value = 0.0

        # Retrieve axis minimum and maximum values
        tmp = ctypes.c_ulong()
        VJoyInterface.GetVJDAxisMin(
            self.vjoy_id,
            self.axis_id,
            ctypes.byref(tmp)
        )
        self._min_value = tmp.value
        VJoyInterface.GetVJDAxisMax(
            self.vjoy_id,
            self.axis_id,
            ctypes.byref(tmp)
        )
        self._max_value = tmp.value
        self._half_range = int(self._max_value / 2)

        # If this is not the case our value setter needs to change
        assert(self._min_value == 0)

    @property
    def value(self):
        """Returns the axis position as a value between [-1, 1]"

        :returns position of the axis as a value between [-1, 1]
        """
        return self._value

    @value.setter
    def value(self, value):
        """Sets the position of the axis based on a value between [-1, 1].

        :param value the position of the axis in the range [-1, 1]
        """
        if value > 1 or value < -1:
            raise VJoyError(
                "Wrong data type provided, has to be float in [-1, 1]"
            )
        self._value = min(1.0, max(-1.0, value))

        if not VJoyInterface.SetAxis(
                int(self._half_range + self._half_range * self._value),
                self.vjoy_id,
                self.axis_id
        ):
            raise VJoyError("Failed setting axis value")


class Button(object):

    """Represents a button in vJoy, allows pressing and releasing it."""

    def __init__(self, vjoy_id, button_id):
        """Creates a new object.

        :param vjoy_id the id of the vJoy device this button belongs to
        :param button_id the id of the button this object controls
        """
        self.vjoy_id = vjoy_id
        self.button_id = button_id
        self._is_pressed = False

    @property
    def is_pressed(self):
        return self._is_pressed

    @is_pressed.setter
    def is_pressed(self, is_pressed):
        assert(isinstance(is_pressed, bool))
        self._is_pressed = is_pressed
        self._update()

    def _update(self):
        if not VJoyInterface.SetBtn(self._is_pressed, self.vjoy_id, self.button_id):
            raise VJoyError("Failed updating button state")


class Hat(object):

    """Represents a discrete hat in vJoy, allows setting the direction
    of the hat."""

    # Recognized direction names
    discrete_directions = {
        "North": 0,
        "Up": 0,
        "East": 1,
        "Right": 1,
        "South": 2,
        "Down": 2,
        "West": 3,
        "Left": 3,
        "Neutral": -1
    }

    def __init__(self, vjoy_id, hat_id, hat_type):
        """Creates a new object.

        :param vjoy_id id of the vJoy device this hat belongs to
        :param hat_id the id of the hat this object controls
        """

        self.vjoy_id = vjoy_id
        self.hat_id = hat_id
        self._direction = -1
        self.hat_type = hat_type

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        if self.hat_type == "discrete":
            self._set_discrete_direction(direction)
        elif self.hat_type == "continuous":
            self._set_continuous_direction(direction)
        else:
            raise VJoyError("Invalid hat type specified")

    def _set_discrete_direction(self, direction):
        """Sets the direction of a discrete hat.

        :param direction the direction of the hat
        """
        if direction not in self.discrete_directions:
            raise VJoyError("Invalid direction specified: {}".format(str(direction)))
        self._direction = self.discrete_directions[direction]
        if not VJoyInterface.SetDiscPov(self._direction, self.vjoy_id, self.hat_id):
            raise VJoyError("Failed to set hat direction")

    def _set_continuous_direction(self, direction):
        """Sets the direction of a continuous hat.

        :param direction the angle in degree of the hat
        """
        if direction >= 0:
            val = min(359.99, max(0, direction))
            self._direction = int(val * 100)
        else:
            self._direction = -1

        assert(0 <= self._direction <= 35999 or self._direction == -1)

        if not VJoyInterface.SetContPov(self._direction, self.vjoy_id, self.hat_id):
            raise VJoyError("Failed to set hat direction")


class VJoy(object):

    """Represents a vJoy device present in the system."""

    def __init__(self, vjoy_id):
        """Creates a new object.

        :param vjoy_id id of the vJoy device to initialize.
        """
        self.vjoy_id = None

        if not VJoyInterface.vJoyEnabled():
            raise VJoyError("vJoy is not currently running")
        elif VJoyInterface.GetVJDStatus(vjoy_id) != VJoyState.Free.value:
            raise VJoyError("Requested vJoy device is not available")
        elif not VJoyInterface.AcquireVJD(vjoy_id):
            raise VJoyError("Failed to acquire the vJoy device")

        self.vjoy_id = vjoy_id

        # Initialize all controls
        self.button = self._init_buttons()
        self.axis = self._init_axes()
        self.hat = self._init_hats()

        # Reset all controls
        VJoyInterface.ResetVJD(self.vjoy_id)

    def _init_buttons(self):
        """Retrieves all buttons present on the vJoy device and creates their
        control objects.

        :returns list of Button objects
        """
        buttons = {}
        for btn_id in range(1, VJoyInterface.GetVJDButtonNumber(self.vjoy_id)+1):
            buttons[btn_id] = Button(self.vjoy_id, btn_id)
        return buttons

    def _init_axes(self):
        """Retrieves all axes present on the vJoy device and creates their
        control objects.

        :returns dictionary of Axis objects
        """
        axes = {}
        for axis in AxisName:
            if VJoyInterface.GetVJDAxisExist(self.vjoy_id, axis.value):
                axes[axis] = Axis(self.vjoy_id, axis.value)
        return axes

    def _init_hats(self):
        """Retrieves all hats present on the vJoy device and creates their
        control objects.

        A single device can either have continuous or discrete hats, but
        not both at the same time.

        :returns list of Hat objects
        """
        hats = {}
        for hat_id in range(1, VJoyInterface.GetVJDDiscPovNumber(self.vjoy_id)+1):
            hats[hat_id] = Hat(self.vjoy_id, hat_id, "discrete")
        for hat_id in range(1, VJoyInterface.GetVJDContPovNumber(self.vjoy_id)+1):
            hats[hat_id] = Hat(self.vjoy_id, hat_id, "continuous")
        return hats

    def __del__(self):
        """Release the lock on the vJoy device if we terminate."""
        if self.vjoy_id:
            VJoyInterface.RelinquishVJD(self.vjoy_id)

    def __str__(self):
        """Print information about the vJoy device we're holding.

        :returns string representation of the vJoy device information
        """
        return "vJoyId={0:d} axis={1:d} buttons={2:d} hats={3:d}".format(
                self.vjoy_id,
                len(self.axes),
                len(self.buttons),
                len(self.hats)
        )
