# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
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


from xml.etree import ElementTree
from PyQt5 import QtCore, QtWidgets

from mako.template import Template

import gremlin
from gremlin.common import UiInputType


def format_condition(condition, data=None):
    """Returns code representing the button condition.

    :param condition the condition to turn into textual python code
    :param data additional data that may be used to pass information
    :return python code representing the condition
    """
    if isinstance(condition, ButtonCondition):
        shift_term = ""
        if condition.shift_button is not None:
            # Keyboard key is being used as a shift button
            if condition.shift_button["hardware_id"] == 0:
                shift_term = "keyboard.is_pressed(gremlin.macro.key_from_code({:d}, {}))".format(
                    condition.shift_button["id"][0],
                    condition.shift_button["id"][1]
                )
            # Joystick button is being used as a shift button
            else:
                shift_term = "joy[{:d}].button({:d}).is_pressed".format(
                    condition.shift_button["windows_id"],
                    condition.shift_button["id"]
                )

            shift_term = " and {}".format(shift_term)

        if condition.on_press and condition.on_release:
            condition_term = "    if True"
        elif condition.on_press:
            condition_term = "    if is_pressed"
        elif condition.on_release:
            condition_term = "    if not is_pressed"
        else:
            condition_term = "    if False"

        return "{}{}:".format(condition_term, shift_term)
    elif isinstance(condition, HatCondition):
        positive_instances = []
        if condition.on_n:
            positive_instances.append((0, 1))
        if condition.on_ne:
            positive_instances.append((1, 1))
        if condition.on_e:
            positive_instances.append((1, 0))
        if condition.on_se:
            positive_instances.append((1, -1))
        if condition.on_s:
            positive_instances.append((0, -1))
        if condition.on_sw:
            positive_instances.append((-1, -1))
        if condition.on_w:
            positive_instances.append((-1, 0))
        if condition.on_nw:
            positive_instances.append((-1, 1))

        condition_text = ", ".join(
            ["({}, {})".format(v[0], v[1]) for v in positive_instances]
        )
        return "    if value in [{}]:".format(condition_text)
    else:
        return "    if True:"


def list_to_string(params):
    """Returns a textual representing of a list.

    :param params the parameters to turn into a lists
    :return textual representation of the parameters
    """
    if len(params) == 0:
        return ""
    elif len(params) == 1:
        return "\"{0}\"".format(params[0])
    else:
        return "[" + ", ".join(["\"{0}\"".format(v) for v in params]) + "]"


def string_to_bool(text):
    """Returns text into a boolean variable.

    :param text the text to convert
    :return bool representing the text
    """
    return text.lower() in ["true", "yes", "t", "1"]


def coords_to_string(container):
    """Returns a textual representation of a sequence of coordinates.

    :param container container holding the coordinates
    :return textual representing of the coordinates
    """
    return "[{}]".format(", ".join(
        ["({:.4f}, {:.4f})".format(e[0], e[1]) for e in container])
    )


# Dictionary containing template helper functions
template_helpers = {
    "format_condition": format_condition,
    "list_tostring": list_to_string,
    "string_to_bool": string_to_bool,
    "coords_to_string": coords_to_string,
}


class NoKeyboardPushButton(QtWidgets.QPushButton):

    """Standard PushButton which does not react to keyboard input."""

    def __init__(self, *args, **kwargs):
        QtWidgets.QPushButton.__init__(self, *args, **kwargs)

    def keyPressEvent(self, event):
        pass


class DualSlider(QtWidgets.QWidget):

    """Slider widget which provides two sliders to define a range. The
    lower and upper slider cannot pass through each other."""

    # Signal emitted when a value changes. (Handle, Value)
    valueChanged = QtCore.pyqtSignal(int, int)
    # Signal emitted when a handle is pressed (Handle)
    sliderPressed = QtCore.pyqtSignal(int)
    # Signal emitted when a handle is moved (Handle, Value)
    sliderMoved = QtCore.pyqtSignal(int, int)
    # Signal emitted when a handle is released (Handle)
    sliderReleased = QtCore.pyqtSignal(int)

    # Enumeration of handle codes used by the widget
    LowerHandle = 1
    UpperHandle = 2

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self._lower_position = 0
        self._upper_position = 100
        self._range = [0, 100]
        self._active_handle = None

    def setRange(self, min_val, max_val):
        """Sets the range of valid values of the slider.

        :param min_val the minimum value any slider can take on
        :param max_val the maximum value any slider can take on
        """
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        self._range = [min_val, max_val]
        self._lower_position = min_val
        self._upper_position = max_val

    def range(self):
        """Returns the range, i.e. minimum and maximum of accepted
        values.

        :return pair containing (minimum, maximum) allowed values
        """
        return self._range

    def setPositions(self, lower, upper):
        """Sets the position of both handles.

        :param lower value of the lower handle
        :param upper value of the upper handle
        """
        lower = self._constrain_value(self.LowerHandle, lower)
        upper = self._constrain_value(self.UpperHandle, upper)
        self._lower_position = lower
        self._upper_position = upper
        self.valueChanged.emit(self.LowerHandle, lower)
        self.valueChanged.emit(self.UpperHandle, upper)
        self.update()

    def positions(self):
        """Returns the positions of both handles.

        :return tuple containing the values of (lower, upper) handle
        """
        return [self._lower_position, self._upper_position]

    def setLowerPosition(self, value):
        """Sets the position of the lower handle.

        :param value the new value of the lower handle
        """
        value = self._constrain_value(self.LowerHandle, value)
        self._lower_position = value
        self.valueChanged.emit(self.LowerHandle, value)
        self.update()

    def setUpperPosition(self, value):
        """Sets the position of the upper handle.

        :param value the new value of the upper handle
        """
        value = self._constrain_value(self.UpperHandle, value)
        self._upper_position = value
        self.valueChanged.emit(self.UpperHandle, value)
        self.update()

    def lowerPosition(self):
        """Returns the position of the lower handle.

        :return position of the lower handle
        """
        return self._lower_position

    def upperPosition(self):
        """Returns the position of the upper handle.

        :return position of the upper handle
        """
        return self._upper_position

    def _get_common_option(self):
        """Returns a QStyleOptionSlider object with the common options
        already specified.

        :return pre filled options object
        """
        option = QtWidgets.QStyleOptionSlider()
        option.initFrom(self)
        option.minimum = self._range[0]
        option.maximum = self._range[1]
        return option

    def _constrain_value(self, handle, value):
        """Returns a value constraint such that it is valid in the given
        setting.

        :param handle the handle for which this value is intended
        :param value the desired value for the handle
        :return a value constrained such that it is valid for the
            slider's current state
        """
        slider = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider,
            self._get_common_option(),
            QtWidgets.QStyle.SC_SliderHandle
        )

        if handle == self.LowerHandle:
            return gremlin.util.clamp(
                value,
                self._range[0],
                self._upper_position - self._width_to_logical(slider.width())
            )
        else:
            return gremlin.util.clamp(
                value,
                self._lower_position + self._width_to_logical(slider.width()),
                self._range[1]
            )

    def _width_to_logical(self, value):
        """Converts a width in pixels to the logical representation.

        :param value the width in pixels
        :return logical value corresponding to the provided width
        """
        groove_rect = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider,
            self._get_common_option(),
            QtWidgets.QStyle.SC_SliderGroove
        )
        return int(round(
            (value / groove_rect.width()) * (self._range[1] - self._range[0])
        ))

    def _position_to_logical(self, pos):
        """Converts a pixel position on a slider to it's logical
        representation.

        :param pos the pixel position on the slider
        :return logical representation of the position on the slider
        """
        groove_rect = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider,
            self._get_common_option(),
            QtWidgets.QStyle.SC_SliderGroove
        )
        return QtWidgets.QStyle.sliderValueFromPosition(
            self._range[0],
            self._range[1],
            pos - groove_rect.left(),
            groove_rect.right() - groove_rect.left()
        )

    def sizeHint(self):
        """Returns the size hint for the widget in its current state.

        :return hint about the correct size of this widget
        """
        return QtWidgets.QSlider().sizeHint()

    def minimumSizeHint(self):
        """Returns the minimal size of this widget.

        :return minimal size of this widget
        """
        return QtCore.QSize(31, 17)

    def mousePressEvent(self, evt):
        """Tracks active state of the handles.

        :param evt the mouse event
        """
        position = QtCore.QPoint(evt.pos().x(), evt.pos().y())
        option = QtWidgets.QStyleOptionSlider(self._get_common_option())
        option.sliderPosition = self._lower_position
        option.sliderValue = self._lower_position
        option.subControls = QtWidgets.QStyle.SC_SliderHandle

        control = self.style().hitTestComplexControl(
            QtWidgets.QStyle.CC_Slider,
            option,
            position
        )
        lower_clicked = False
        if control == QtWidgets.QStyle.SC_SliderHandle:
            lower_clicked = True

        option.sliderPosition = self._upper_position
        option.sliderValue = self._upper_position
        control = self.style().hitTestComplexControl(
            QtWidgets.QStyle.CC_Slider,
            option,
            position
        )
        upper_clicked = False
        if control == QtWidgets.QStyle.SC_SliderHandle:
            upper_clicked = True

        if lower_clicked:
            self._active_handle = self.LowerHandle
            self.sliderPressed.emit(self.LowerHandle)
        elif upper_clicked:
            self._active_handle = self.UpperHandle
            self.sliderPressed.emit(self.UpperHandle)
        else:
            self._active_handle = None

        self.update()

    def mouseReleaseEvent(self, evt):
        """Ensures active handles get released.

        :param evt the mouse event
        """
        if self._active_handle is not None:
            self.sliderReleased.emit(self._active_handle)
            self._active_handle = None
            self.update()

    def mouseMoveEvent(self, evt):
        """Updates the position of the active slider if applicable.

        :param evt the mouse event
        """
        if self._active_handle:
            value = self._position_to_logical(evt.pos().x())
            if self._active_handle == self.LowerHandle:
                self._lower_position =\
                    self._constrain_value(self.LowerHandle, value)
                value = self._lower_position
            elif self._active_handle == self.UpperHandle:
                self._upper_position =\
                    self._constrain_value(self.UpperHandle, value)
                value = self._upper_position
            self.valueChanged.emit(self._active_handle, value)
            self.sliderMoved.emit(self._active_handle, value)
            self.update()

    def paintEvent(self, evt):
        """Repaints the entire widget.

        :param evt the paint event
        """
        painter = QtWidgets.QStylePainter(self)

        common_option = self._get_common_option()

        # Draw the groove for the handles to move on
        option = QtWidgets.QStyleOptionSlider(common_option)
        option.subControls = QtWidgets.QStyle.SC_SliderGroove
        painter.drawComplexControl(QtWidgets.QStyle.CC_Slider, option)

        # Draw lower handle
        option_lower = QtWidgets.QStyleOptionSlider(common_option)
        option_lower.sliderPosition = self._lower_position
        option_lower.sliderValue = self._lower_position
        option_lower.subControls = QtWidgets.QStyle.SC_SliderHandle

        # Draw upper handle
        option_upper = QtWidgets.QStyleOptionSlider(common_option)
        option_upper.sliderPosition = self._upper_position
        option_upper.sliderValue = self._upper_position
        option_upper.subControls = QtWidgets.QStyle.SC_SliderHandle

        if self._active_handle:
            if self._active_handle == self.LowerHandle:
                option = option_lower
            else:
                option = option_upper
            option.activeSubControls = QtWidgets.QStyle.SC_SliderHandle
            option.state |= QtWidgets.QStyle.State_Sunken

        painter.drawComplexControl(QtWidgets.QStyle.CC_Slider, option_lower)
        painter.drawComplexControl(QtWidgets.QStyle.CC_Slider, option_upper)


class JoystickSelector(QtWidgets.QWidget):

    """Widget allowing the selection of input items on a physical joystick."""

    # Mapping from types to display names
    type_to_name_map = {
        UiInputType.JoystickAxis: "Axis",
        UiInputType.JoystickButton: "Button",
        UiInputType.JoystickHat: "Hat",
        UiInputType.Keyboard: "Button",
    }
    name_to_type_map = {
        "Axis": UiInputType.JoystickAxis,
        "Button": UiInputType.JoystickButton,
        "Hat": UiInputType.JoystickHat
    }

    def __init__(self, devices, change_cb, valid_types, parent=None):
        """Creates a new JoystickSelector instance.

        :param devices list of devices to choose from
        :param change_cb function to call when changes occur
        :param valid_types valid input types for selection
        :param parent the parent of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.devices = devices
        self.change_cb = change_cb
        self.valid_types = valid_types

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.device_dropdown = None
        self.input_item_dropdowns = []

        self._create_device_dropdown()
        self._create_input_dropdown()

        self._device_id_to_index_map = {}
        self._index_to_device_id_map = {}
        for i, device in enumerate(sorted(self.devices, key=lambda x: x.windows_id)):
            self._device_id_to_index_map[gremlin.util.device_id(device)] = i
            self._index_to_device_id_map[i] = gremlin.util.device_id(device)

    def get_selection(self):
        """Returns information about the currently selected entry.

        :return dictionary containing selection information
        """
        selection_id = self.device_dropdown.currentIndex()

        if selection_id != -1:
            input_selection = \
                self.input_item_dropdowns[selection_id].currentText()

            arr = input_selection.split()
            device_id = self._index_to_device_id_map[selection_id]
            input_type = self.name_to_type_map[arr[0]]
            input_id = int(arr[1])
        else:
            device_id = None
            input_id = None
            input_type = None

        return {
            "device_id": device_id,
            "input_id": input_id,
            "input_type": input_type
        }

    def set_selection(self, input_type, device_id, input_id):
        """Sets the current selection to the provided values.

        :param input_type the type of input
        :param device_id the id of the device
        :param input_id the id of the input
        """
        # Get the appropriate vjoy device identifier
        dev_id = None
        if device_id not in [0, None] and device_id in self._device_id_to_index_map:
            dev_id = self._device_id_to_index_map[device_id]

        # If we have no device simply stop here
        if dev_id is None:
            return

        # Retrieve the index of the correct entry in the combobox
        input_name = "{} {:d}".format(
            self.type_to_name_map[input_type],
            input_id
        )
        btn_id = self.input_item_dropdowns[dev_id].findText(input_name)

        # Select and display correct combo boxes and entries within
        self.device_dropdown.setCurrentIndex(dev_id)
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)
        self.input_item_dropdowns[dev_id].setVisible(True)
        self.input_item_dropdowns[dev_id].setCurrentIndex(btn_id)

    def _create_device_dropdown(self):
        """Creates the vJoy device selection drop downs."""
        self.device_dropdown = QtWidgets.QComboBox(self)
        for device in sorted(self.devices, key=lambda x: x.windows_id):
            self.device_dropdown.addItem(device.name)
        self.main_layout.addWidget(self.device_dropdown)
        self.device_dropdown.activated.connect(self._update_device)

    def _create_input_dropdown(self):
        """Creates the vJoy input item selection drop downs."""
        count_map = {
            UiInputType.JoystickAxis: lambda x: x.axes,
            UiInputType.JoystickButton: lambda x: x.buttons,
            UiInputType.JoystickHat: lambda x: x.hats
        }

        self.input_item_dropdowns = []

        # Create input item selections for the vjoy devices, each
        # selection will be invisible unless it is selected as the
        # active device
        for device in sorted(self.devices, key=lambda x: x.windows_id):
            selection = QtWidgets.QComboBox(self)
            selection.setMaxVisibleItems(20)

            # Add items based on the input type
            for input_type in self.valid_types:
                for i in range(1, count_map[input_type](device)+1):
                    selection.addItem("{} {:d}".format(
                        self.type_to_name_map[input_type],
                        i
                    ))

            # Add the selection and hide it
            selection.setVisible(False)
            selection.activated.connect(self.change_cb)
            self.main_layout.addWidget(selection)
            self.input_item_dropdowns.append(selection)

        # Show the "None" selection entry
        if len(self.input_item_dropdowns) > 0:
            self.input_item_dropdowns[0].setVisible(True)

    def _update_device(self, index):
        """Handles changing the vJoy device selection.

        :param index vjoy device index
        """
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)
        self.input_item_dropdowns[index].setVisible(True)
        self.input_item_dropdowns[index].setCurrentIndex(0)
        self.change_cb()


class VJoySelector(QtWidgets.QWidget):

    """Widget allowing the selection of vJoy inputs."""

    # Mapping from types to display names
    type_to_name_map = {
        UiInputType.JoystickAxis: "Axis",
        UiInputType.JoystickButton: "Button",
        UiInputType.JoystickHat: "Hat",
        UiInputType.Keyboard: "Button",
    }
    name_to_type_map = {
        "Axis": UiInputType.JoystickAxis,
        "Button": UiInputType.JoystickButton,
        "Hat": UiInputType.JoystickHat
    }

    def __init__(self, vjoy_devices, change_cb, valid_types, parent=None):
        """Creates a widget to select a vJoy output.

        :param vjoy_devices the list of available vjoy devices
        :param change_cb callback to execute when the widget changes
        :param valid_types the input type to present in the selection
        :param parent of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.vjoy_devices = vjoy_devices
        self.change_cb = change_cb
        self.valid_types = valid_types

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.device_dropdown = None
        self.input_item_dropdowns = []

        self._create_device_dropdown()
        self._create_input_dropdown()

    def get_selection(self):
        """Returns the current selection of the widget.

        :return dictionary containing the current selection
        """
        vjoy_device_id = self.device_dropdown.currentIndex()
        input_selection = \
            self.input_item_dropdowns[vjoy_device_id].currentText()
        # Count devices starting at 1 rather then 0
        vjoy_device_id += 1

        arr = input_selection.split()
        vjoy_input_type = self.name_to_type_map[arr[0]]
        vjoy_item_id = int(arr[1])

        return {
            "device_id": vjoy_device_id,
            "input_id": vjoy_item_id,
            "input_type": vjoy_input_type
        }

    def set_selection(self, input_type, device_id, input_id):
        """Sets the widget's entries to the provided values.

        :param input_type the input type
        :param device_id the id of the device
        :param input_id the id of the input
        """
        # Get the appropriate vjoy device identifier
        dev_id = 0
        if device_id not in [0, None]:
            dev_id = self.device_dropdown.findText(
                "vJoy Device {:d}".format(device_id)
            )

        # Retrieve the index of the correct entry in the combobox
        input_name = "{} {:d}".format(
            self.type_to_name_map[input_type],
            input_id
        )
        btn_id = self.input_item_dropdowns[dev_id].findText(input_name)

        # Select and display correct combo boxes and entries within
        self.device_dropdown.setCurrentIndex(dev_id)
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)
        self.input_item_dropdowns[dev_id].setVisible(True)
        self.input_item_dropdowns[dev_id].setCurrentIndex(btn_id)

    def _create_device_dropdown(self):
        """Creates the vJoy device selection drop downs."""
        self.device_dropdown = QtWidgets.QComboBox(self)
        for i in range(1, len(self.vjoy_devices)+1):
            self.device_dropdown.addItem("vJoy Device {:d}".format(i))
        self.main_layout.addWidget(self.device_dropdown)
        self.device_dropdown.activated.connect(self._update_device)

    def _create_input_dropdown(self):
        """Creates the vJoy input item selection drop downs."""
        count_map = {
            UiInputType.JoystickAxis: lambda x: x.axes,
            UiInputType.JoystickButton: lambda x: x.buttons,
            UiInputType.JoystickHat: lambda x: x.hats
        }

        self.input_item_dropdowns = []

        # Create input item selections for the vjoy devices, each
        # selection will be invisible unless it is selected as the
        # active device
        for dev in self.vjoy_devices:
            selection = QtWidgets.QComboBox(self)
            selection.setMaxVisibleItems(20)

            # Add items based on the input type
            for input_type in self.valid_types:
                for i in range(1, count_map[input_type](dev)+1):
                    selection.addItem("{} {:d}".format(
                        self.type_to_name_map[input_type],
                        i
                    ))

            # Add the selection and hide it
            selection.setVisible(False)
            selection.activated.connect(self.change_cb)
            self.main_layout.addWidget(selection)
            self.input_item_dropdowns.append(selection)

        # Show the "None" selection entry
        self.input_item_dropdowns[0].setVisible(True)

    def _update_device(self, index):
        """Handles changing the vJoy device selection.

        :param index vjoy device index
        """
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)
        self.input_item_dropdowns[index].setVisible(True)
        self.input_item_dropdowns[index].setCurrentIndex(0)
        self.change_cb()


class AbstractAction(object):

    """Base class for all actions that can be encoded via the XML and
    UI system."""

    next_code_id = 0

    def __init__(self, parent):
        """Creates a new instance.

        :parent the InputItem which is the parent to this action
        """
        assert(isinstance(parent, gremlin.profile.InputItem))
        self.parent = parent
        self.condition = None
        self.is_valid = False
        self._create_default_condition()

    def from_xml(self, node):
        """Populates the instance with data from the given XML node.

        :param node the XML node to populate fields with
        """
        self._parse_xml(node)
        self._parse_condition(node)
        self.is_valid = True

    def _parse_xml(self, node):
        """Parses a XML node for content to display.

        :param node the XML node to parse
        """
        raise gremlin.error.MissingImplementationError(
            "AbstractAction.from_xml not implemented in subclass"
        )

    def to_xml(self):
        """Returns a XML node representing the instance's contents.

        :return XML node representing the state of this instance
        """
        node = self._generate_xml()
        self._generate_condition(node)
        return node

    def icon(self):
        """Returns the icon to use when representing the action.

        :return icon to use
        """
        raise gremlin.error.MissingImplementationError(
            "AbstractAction.icon not implemented in subclass"
        )

    def _create_default_condition(self):
        if self.parent.input_type in [UiInputType.JoystickButton, UiInputType.Keyboard]:
            self.condition = ButtonCondition()
        elif self.parent.input_type == UiInputType.JoystickAxis:
            self.condition = None
        elif self.parent.input_type == UiInputType.JoystickHat:
            self.condition = HatCondition(
                False, False, False, False, False, False, False, False
            )

    def _generate_xml(self):
        """Generates the XML node for this action.

        :return XML node representing this action
        """
        raise gremlin.error.MissingImplementationError(
            "AbstractAction.to_xml not implemented in subclass"
        )

    def to_code(self):
        """Returns python code corresponding to this instance.

        :return Python code represented by this instance
        """
        code = self._generate_code()
        AbstractAction.next_code_id += 1
        return code

    def _generate_code(self):
        """Generates Python code for this action.

        :return code fragments representing the action
        """
        raise gremlin.error.MissingImplementationError(
            "AbstractAction.to_code not implemented in subclass"
        )

    def _code_generation(self, template_name, params):
        """Generates the code using the provided data.

        :param template_name base name of the templates
        :param params the parameters to pass to the template
        :return dictionary containing generated code
        """
        params["axis_button_name"] = "axis_button_{:04d}".format(
            AbstractAction.next_code_id
        )
        params["axis_button_cb"] = "axis_button_callback_{:04d}".format(
            AbstractAction.next_code_id
        )
        params["helpers"] = template_helpers
        params["InputType"] = UiInputType

        body_code = Template(
            filename="action_plugins/{}/body.tpl".format(template_name)
        ).render(
            **params
        )
        global_code = Template(
            filename="action_plugins/{}/global.tpl".format(template_name)
        ).render(
            **params
        )
        return {
            "body": body_code,
            "global": global_code
        }

    def _parse_condition(self, node):
        """Parses condition information of the action's XML node.

        :param node the XML from which to extract condition data
        """
        parser_map = {
            UiInputType.JoystickAxis: parse_axis_condition,
            UiInputType.JoystickButton: parse_button_condition,
            UiInputType.JoystickHat: parse_hat_condition,
            UiInputType.Keyboard: parse_button_condition
        }
        assert(self.parent.input_type in parser_map)
        self.condition = parser_map[self.parent.input_type](node)

    def _generate_condition(self, node):
        """Reads condition data from the action and stores them in the
        XML node.

        :param node the XML node in which to store condition information
        """
        type_action_map = gremlin.plugin_manager.ActionPlugins().type_action_map
        input_type = self.parent.input_type
        action_widget = type(self)
        button_types = [
            UiInputType.JoystickButton,
            UiInputType.Keyboard
        ]

        # If no condition is present simply return
        if self.condition is None:
            return

        if input_type in button_types and \
                action_widget in type_action_map[input_type]:
            node.set("on-press", str(self.condition.on_press))
            node.set("on-release", str(self.condition.on_release))

            if self.condition.shift_button is not None:
                shift_node = ElementTree.Element("shift")
                shift_node.set(
                    "hardware_id",
                    str(self.condition.shift_button["hardware_id"])
                )
                shift_node.set(
                    "windows_id",
                    str(self.condition.shift_button["windows_id"])
                )
                if self.condition.shift_button["hardware_id"] == 0:
                    shift_node.set(
                        "id",
                        str(self.condition.shift_button["id"][0])
                    )
                    shift_node.set(
                        "extended",
                        str(self.condition.shift_button["id"][1])
                    )
                else:
                    shift_node.set(
                        "id",
                        str(self.condition.shift_button["id"])
                    )
                node.append(shift_node)

        elif input_type == UiInputType.JoystickHat and \
                action_widget in type_action_map[input_type]:
            node.set("on-n", str(self.condition.on_n))
            node.set("on-ne", str(self.condition.on_ne))
            node.set("on-e", str(self.condition.on_e))
            node.set("on-se", str(self.condition.on_se))
            node.set("on-s", str(self.condition.on_s))
            node.set("on-sw", str(self.condition.on_sw))
            node.set("on-w", str(self.condition.on_w))
            node.set("on-nw", str(self.condition.on_nw))
        elif input_type == UiInputType.JoystickAxis and \
                action_widget in type_action_map[input_type]:
            node.set("is-active", str(self.condition.is_active))
            node.set("lower-limit", str(self.condition.lower_limit))
            node.set("upper-limit", str(self.condition.upper_limit))


class AbstractActionWidget(QtWidgets.QFrame):

    """Base class for all widgets representing actions from the profile
    module."""

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        """Creates a new instance.

        :param action_data the sub-classed AbstractAction instance
            associated with this specific action.
        :param vjoy_devices list of vjoy devices available
        :param change_cb the callback to execute when changes occur
        :param parent parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)

        self.action_data = action_data
        self.vjoy_devices = vjoy_devices
        self.change_cb = change_cb
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self._setup_ui()
        self.initialize_from_profile(self.action_data)

    def _setup_ui(self):
        """Creates all the elements necessary for the widget."""
        raise gremlin.error.MissingImplementationError(
            "AbstractActionWidget._setup_ui not implemented in subclass"
        )

    def to_profile(self):
        """Updates the action_data object of this instance with the
        current state of the widget.
        """
        raise gremlin.error.MissingImplementationError(
            "ActionWidget.to_profile not implemented in subclass"
        )

    def initialize_from_profile(self, action_data):
        """Updates this widget's representation based on the provided
        AbstractAction instance.

        :param action_data the data with which to populate this action
        """
        raise gremlin.error.MissingImplementationError(
            "ActionWidget.from_profile not implemented in subclass"
        )


class AxisCondition(object):

    """Indicates when an action associated with an axis is to be run."""

    def __init__(self, is_active, lower_limit, upper_limit):
        """Creates a new instance.

        :param lower_limit lower axis limit of the activation range
        :param upper_limit upper axis limit of the activation range
        """
        self.is_active = is_active
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit


class ButtonCondition(object):

    """Indicates when an action associated with a button is to be run"""

    def __init__(self, on_press=True, on_release=False, shift_button=None):
        """Creates a new instance.

        :param on_press when True the action is executed when the button
            is pressed
        :param on_release when True the action is execute when the
            button is released
        """
        self.on_press = on_press
        self.on_release = on_release
        self.shift_button = shift_button


class HatCondition(object):

    """Indicates when an action associated with a hat is to be run."""

    def __init__(self, on_n, on_ne, on_e, on_se, on_s, on_sw, on_w, on_nw):
        """Creates a new instance."""
        self.on_n = on_n
        self.on_ne = on_ne
        self.on_e = on_e
        self.on_se = on_se
        self.on_s = on_s
        self.on_sw = on_sw
        self.on_w = on_w
        self.on_nw = on_nw


def input_type_to_tag(input_type):
    """Returns the XML tag corresponding to the given InputType enum.

    :param input_type InputType enum to translate into a XML tag
    :return XML tag corresponding to the provided InputType enum
    """
    lookup = {
        UiInputType.JoystickAxis: "axis",
        UiInputType.JoystickButton: "button",
        UiInputType.JoystickHat: "hat",
        UiInputType.Keyboard: "key",
    }
    if input_type in lookup:
        return lookup[input_type]
    else:
        raise gremlin.error.ProfileError(
            "Invalid input type specified {}".format(input_type)
        )


def parse_axis_condition(node):
    """Returns an AxisCondition based on the xml node's content.

    :param node the xml node to parse
    :return AxisCondition corresponding to the node's content
    """
    try:
        is_active = parse_bool(node.get("is-active"))
        lower_limit = parse_float(node.get("lower-limit"))
        upper_limit = parse_float(node.get("upper-limit"))

        return AxisCondition(is_active, lower_limit, upper_limit)
    except gremlin.error.ProfileError:
        return AxisCondition(False, 0, 0)


def parse_button_condition(node):
    """Returns a ButtonCondition corresponding to the node's content.

    :param node the xml node to parse
    :return ButtonCondition corresponding to the node's content
    """
    # Read normal button state condition data
    try:
        on_press = parse_bool(node.get("on-press"))
    except gremlin.error.ProfileError:
        on_press = None
    try:
        on_release = parse_bool(node.get("on-release"))
    except gremlin.error.ProfileError:
        on_release = None

    if on_press is None and on_release is None:
        on_press = True
        on_release = False
    else:
        on_press = False if on_press is None else on_press
        on_release = False if on_release is None else on_release

    # Attempt to read shift button data
    for entry in node.findall("shift"):
        hardware_id = int(entry.get("hardware_id"))
        windows_id = int(entry.get("windows_id"))

        if hardware_id == 0:
            id_data = (
                int(entry.get("id")),
                parse_bool(entry.get("extended"))
            )
        else:
            id_data = int(entry.get("id"))

        return ButtonCondition(
            on_press,
            on_release,
            {
                "hardware_id": hardware_id,
                "windows_id": windows_id,
                "id": id_data
            }
        )

    return ButtonCondition(on_press, on_release)


def parse_hat_condition(node):
    """Returns a HatCondition corresponding to the node's content.

    :param node the xml node to parse
    :return HatCondition corresponding to the node's content
    """
    # Remap actions don't have associated conditions
    if node.tag == "remap":
        return None

    on_n = read_bool(node, "on-n")
    on_ne = read_bool(node, "on-ne")
    on_e = read_bool(node, "on-e")
    on_se = read_bool(node, "on-se")
    on_s = read_bool(node, "on-s")
    on_sw = read_bool(node, "on-sw")
    on_w = read_bool(node, "on-w")
    on_nw = read_bool(node, "on-nw")

    return HatCondition(on_n, on_ne, on_e, on_se, on_s, on_sw, on_w, on_nw)


def read_bool(node, key, default_value=False):
    """Attempts to read a boolean value.

    If there is an error when reading the given field from the node
    the default value is returned instead.

    :param node the node from which to read the value
    :param key the key to read from the node
    :param default_value the default value to return in case of errors
    """
    try:
        return parse_bool(node.get(key))
    except gremlin.error.ProfileError:
        return default_value


def parse_bool(value):
    """Returns the boolean representation of the provided value.

    :param value the value as string to parse
    :return representation of value as either True or False
    """
    try:
        int_value = int(value)
        if int_value in [0, 1]:
            return int_value == 1
        else:
            raise gremlin.error.ProfileError(
                "Invalid bool value used: {}".format(value)
            )
    except ValueError:
        if value.lower() in ["true", "false"]:
            return True if value.lower() == "true" else False
        else:
            raise gremlin.error.ProfileError(
                "Invalid bool value used: {}".format(value)
            )
    except TypeError:
        raise gremlin.error.ProfileError(
            "Invalid type provided: {}".format(type(value))
        )


def parse_float(value):
    """Returns the float representation of the provided value.

    :param value the value as string to parse
    :return representation of value as float
    """
    try:
        return float(value)
    except ValueError:
        raise gremlin.error.ProfileError(
            "Invalid float value used: {}".format(value)
        )
    except TypeError:
        raise gremlin.error.ProfileError(
            "Invalid type provided: {}".format(type(value))
        )
