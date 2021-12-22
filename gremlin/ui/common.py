# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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

import enum
import threading

from PyQt5 import QtWidgets, QtCore, QtGui

import gremlin


class ContainerViewTypes(enum.Enum):

    """Enumeration of view types used by containers."""

    Action = 1
    Condition = 2
    VirtualButton = 3

    @staticmethod
    def to_string(value):
        try:
            return _ContainerView_to_string_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid type in container lookup, {}".format(value)
            )

    @staticmethod
    def to_enum(value):
        try:
            return _ContainerView_to_enum_lookup[value]
        except KeyError:
            raise gremlin.error.GremlinError(
                "Invalid type in container lookup, {}".format(value)
            )


_ContainerView_to_enum_lookup = {
    "action": ContainerViewTypes.Action,
    "condition": ContainerViewTypes.Condition,
    "virtual button": ContainerViewTypes.VirtualButton
}


_ContainerView_to_string_lookup = {
    ContainerViewTypes.Action: "Action",
    ContainerViewTypes.Condition: "Condition",
    ContainerViewTypes.VirtualButton: "Virtual Button"
}


class AbstractModel(QtCore.QObject):

    """Base class for MVC models."""

    data_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Creates a new model.

        :param parent the parent of this model
        """
        super().__init__(parent)

    def rows(self):
        """Returns the number of rows in the model.

        :return number of rows
        """
        pass

    def data(self, index):
        """Returns the data entry stored at the provided index.

        :param index the index for which to return data
        :return data stored at the given index
        """
        pass


class AbstractView(QtWidgets.QWidget):

    """Base class for MVC views."""

    # Signal emitted when a entry is selected
    item_selected = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        """Creates a new view instance.

        :param parent the parent of this view widget
        """
        super().__init__(parent)
        self.model = None

    def set_model(self, model):
        """Sets the model to display with this view.

        :param model the model to visualize
        """
        if self.model is not None:
            self.model.data_changed.disconnect(self.redraw)
        self.model = model
        self._model_changed()
        self.model.data_changed.connect(self.redraw)

    def select_item(self, index):
        """Selects the item at the provided index

        :param index the index of the item to select
        """
        pass

    def redraw(self):
        """Redraws the view."""
        pass

    def _model_changed(self):
        """Called when a model is added or updated to allow user code to run."""
        pass


class LeftRightPushButton(QtWidgets.QPushButton):

    """Implements a push button that distinguishes between left and right
    mouse clicks."""

    # Signal emitted when the button is pressed using the right mouse button
    clicked_right = QtCore.pyqtSignal()

    def __init__(self, label, parent=None):
        """Creates a new button instance.

        :param label the text to display on the button
        :param parent the parent of this button
        """
        super().__init__(label, parent)

    def mousePressEvent(self, event):
        """Handles mouse press events.

        :param event the mouse press event to handle
        """
        if event.button() == QtCore.Qt.RightButton:
            self.clicked_right.emit()
        else:
            super().mousePressEvent(event)


class NoKeyboardPushButton(QtWidgets.QPushButton):

    """Standard PushButton which does not react to keyboard input."""

    def __init__(self, *args, **kwargs):
        """Creates a new instance."""
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        """Handles key press events by ignoring them.

        :param event the key event to handle
        """
        pass


class DynamicDoubleSpinBox(QtWidgets.QDoubleSpinBox):

    """Implements a double spin box which dynamically overwrites entries."""

    valid_chars = [str(v) for v in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]] + ["-"]
    decimal_point = "."

    def __init__(self, parent=None):
        """Create a new instance with the specified parent.

        :param parent the parent of this widget
        """
        super().__init__(parent)
        DynamicDoubleSpinBox.decimal_point = self.locale().decimalPoint()
        if DynamicDoubleSpinBox.decimal_point not in DynamicDoubleSpinBox.valid_chars:
            DynamicDoubleSpinBox.valid_chars.append(
                DynamicDoubleSpinBox.decimal_point
            )

    def validate(self, text, pos):
        """Validates the provided string.

        This takes the pre-validation string and formats it as a float of fixed
        length before submitting it for validation.

        :param text the input to be validated
        :param pos the position in the string
        """
        try:
            # Discard invalid characters
            if 0 <= pos-1 < len(text):
                if text[pos-1] not in DynamicDoubleSpinBox.valid_chars:
                    text = text[:pos-1] + text[pos:]
                    pos -= 1

            # Replace empty parts with the value 0
            parts = text.split(self.locale().decimalPoint())
            for part in parts:
                if len(part) == 0:
                    part = "0"

            # Convert number to a string representation we can convert to
            # a float so we can truncate the decimal places as required
            value_string = "{}.{}".format(parts[0], parts[1])
            format_string = "{{:.{:d}f}}".format(self.decimals())
            value_string = format_string.format(float(value_string))

            # Use decimal place separator dictated by the locale settings
            text = value_string.replace(".", DynamicDoubleSpinBox.decimal_point)

            return super().validate(text, pos)
        except (ValueError, IndexError):
            return super().validate(text, pos)


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
        super().__init__(parent)

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


class AbstractInputSelector(QtWidgets.QWidget):

    def __init__(self, change_cb, valid_types, parent=None):
        super().__init__(parent)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.chage_cb = change_cb
        self.valid_types = valid_types
        self.device_list = []

        self.device_dropdown = None
        self.input_item_dropdowns = []
        self._device_id_registry = []
        self._input_type_registry = []

        self._initialize()
        self._create_device_dropdown()
        self._create_input_dropdown()

    def get_selection(self):
        device_id = None
        input_id = None
        input_type = None

        device_index = self.device_dropdown.currentIndex()
        if device_index != -1:
            device_id = self._device_id_registry[device_index]
            input_index = self.input_item_dropdowns[device_index].currentIndex()

            if input_index == -1:
                input_index = 0
                input_value = self.input_item_dropdowns[device_index].itemText(
                    input_index)
            else:
                input_value = self.input_item_dropdowns[device_index].currentText()
            input_type = self._input_type_registry[device_index][input_index]

            if input_type == gremlin.common.InputType.JoystickAxis:
                input_id = gremlin.common.AxisNames.to_enum(input_value).value
            else:
                input_id = int(input_value.split()[-1])

        return {
            "device_id": device_id,
            "input_id": input_id,
            "input_type": input_type
        }

    def set_selection(self, input_type, device_id, input_id):
        if device_id not in self._device_id_registry:
            return

        # Get the index of the combo box associated with this device
        dev_id = self._device_id_registry.index(device_id)

        # Retrieve the index of the correct entry in the combobox
        input_name = gremlin.common.input_to_ui_string(input_type, input_id)
        entry_id = self.input_item_dropdowns[dev_id].findText(input_name)

        # Select and display correct combo boxes and entries within
        self.device_dropdown.setCurrentIndex(dev_id)
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)
        self.input_item_dropdowns[dev_id].setVisible(True)
        self.input_item_dropdowns[dev_id].setCurrentIndex(entry_id)

    def _update_device(self, index):
        # Hide all selection dropdowns
        for entry in self.input_item_dropdowns:
            entry.setVisible(False)

        # Show correct dropdown
        self.input_item_dropdowns[index].setVisible(True)
        self.input_item_dropdowns[index].setCurrentIndex(0)
        self._execute_callback()

    def _initialize(self):
        raise gremlin.error.MissingImplementationError(
            "Missing implementation of AbstractInputSelector._initialize"
        )

    def _format_device_name(self, device):
        raise gremlin.error.MissingImplementationError(
            "Missing implementation of AbstractInputSelector._format_device_name"
        )

    def _device_identifier(self, device):
        raise gremlin.error.MissingImplementationError(
            "Missing implementation of AbstractInputSelector._device_identifier"
        )

    def _create_device_dropdown(self):
        self.device_dropdown = QtWidgets.QComboBox(self)
        for device in self.device_list:
            self.device_dropdown.addItem(self._format_device_name(device))
            self._device_id_registry.append(self._device_identifier(device))
        self.main_layout.addWidget(self.device_dropdown)
        self.device_dropdown.activated.connect(self._update_device)

    def _create_input_dropdown(self):
        count_map = {
            gremlin.common.InputType.JoystickAxis: lambda x: x.axis_count,
            gremlin.common.InputType.JoystickButton: lambda x: x.button_count,
            gremlin.common.InputType.JoystickHat: lambda x: x.hat_count
        }

        self.input_item_dropdowns = []
        self._input_type_registry = []

        # Create input item selections for the devices. Each selection
        # will be invisible unless it is selected as the active device
        for device in self.device_list:
            selection = QtWidgets.QComboBox(self)
            selection.setMaxVisibleItems(20)
            self._input_type_registry.append([])

            # Add items based on the input type
            for input_type in self.valid_types:
                for i in range(count_map[input_type](device)):
                    input_id = i+1
                    if input_type == gremlin.common.InputType.JoystickAxis:
                        input_id = device.axis_map[i].axis_index

                    selection.addItem(gremlin.common.input_to_ui_string(
                        input_type,
                        input_id
                    ))
                    self._input_type_registry[-1].append(input_type)

            # Add the selection and hide it
            selection.setVisible(False)
            selection.activated.connect(self._execute_callback)
            self.main_layout.addWidget(selection)
            self.input_item_dropdowns.append(selection)

        # Show the first entry by default
        if len(self.input_item_dropdowns) > 0:
            self.input_item_dropdowns[0].setVisible(True)

    def _execute_callback(self):
        self.chage_cb(self.get_selection())


class JoystickSelector(AbstractInputSelector):

    """Widget allowing the selection of input items on a physical joystick."""

    def __init__(self, change_cb, valid_types, parent=None):
        """Creates a new JoystickSelector instance.

        :param change_cb function to call when changes occur
        :param valid_types valid input types for selection
        :param parent the parent of this widget
        """
        super().__init__(change_cb, valid_types, parent)

    def _initialize(self):
        potential_devices = sorted(
            gremlin.joystick_handling.physical_devices(),
            key=lambda x: (x.name, x.device_guid)
        )
        for dev in potential_devices:
            input_counts = {
                gremlin.common.InputType.JoystickAxis: dev.axis_count,
                gremlin.common.InputType.JoystickButton: dev.button_count,
                gremlin.common.InputType.JoystickHat: dev.hat_count
            }

            has_inputs = False
            for valid_type in self.valid_types:
                if input_counts.get(valid_type, 0) > 0:
                    has_inputs = True

            if has_inputs:
                self.device_list.append(dev)

    def _format_device_name(self, device):
        return device.name

    def _device_identifier(self, device):
        return device.device_guid


class VJoySelector(AbstractInputSelector):

    """Widget allowing the selection of vJoy inputs."""

    def __init__(self, change_cb, valid_types, invalid_ids={}, parent=None):
        """Creates a widget to select a vJoy output.

        :param change_cb callback to execute when the widget changes
        :param valid_types the input type to present in the selection
        :param invalid_ids list of vid values of vjoy devices to not consider
        :param parent of this widget
        """
        self.invalid_ids = invalid_ids
        super().__init__(change_cb, valid_types, parent)

    def _initialize(self):
        potential_devices = sorted(
            gremlin.joystick_handling.vjoy_devices(),
            key=lambda x: x.vjoy_id
        )
        for dev in potential_devices:
            input_counts = {
                gremlin.common.InputType.JoystickAxis: dev.axis_count,
                gremlin.common.InputType.JoystickButton: dev.button_count,
                gremlin.common.InputType.JoystickHat: dev.hat_count
            }

            has_inputs = False
            for valid_type in self.valid_types:
                if input_counts.get(valid_type, 0) > 0:
                    has_inputs = True

            if not self.invalid_ids.get(dev.vjoy_id, False) and has_inputs:
                self.device_list.append(dev)

    def _format_device_name(self, device):
        return "vJoy Device {:d}".format(device.vjoy_id)

    def _device_identifier(self, device):
        return device.vjoy_id


class ActionSelector(QtWidgets.QWidget):

    """Widget permitting the selection of actions."""

    # Signal emitted when an action is going to be added
    action_added = QtCore.pyqtSignal(str)

    def __init__(self, input_type, parent=None):
        """Creates a new selector instance.

        :param input_type the input type for which the action selector is
            being created
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.input_type = input_type

        self.main_layout = QtWidgets.QHBoxLayout(self)

        self.action_dropdown = QtWidgets.QComboBox()
        for name in self._valid_action_list():
            self.action_dropdown.addItem(name)
        cfg = gremlin.config.Configuration()
        self.action_dropdown.setCurrentText(cfg.default_action)
        self.add_button = QtWidgets.QPushButton("Add")
        self.add_button.clicked.connect(self._add_action)

        self.main_layout.addWidget(self.action_dropdown)
        self.main_layout.addWidget(self.add_button)

    def _valid_action_list(self):
        """Returns a list of valid actions for this InputItemWidget.

        :return list of valid action names
        """
        action_list = []
        if self.input_type == gremlin.common.DeviceType.VJoy:
            action_list.append("Response Curve")
        else:
            for entry in gremlin.plugin_manager.ActionPlugins().repository.values():
                if self.input_type in entry.input_types:
                    action_list.append(entry.name)
        return sorted(action_list)

    def _add_action(self, clicked=False):
        """Handles selecting of an action to be added.

        :param clicked flag indicating whether or not the action resulted from
            a click
        """
        self.action_added.emit(self.action_dropdown.currentText())


class BaseDialogUi(QtWidgets.QWidget):

    """Base class for all UI dialogs.

    The main purpose of this class is to provide the closed signal to dialogs
    so that the main application can react to the dialog being closed if
    desired.
    """

    # Signal emitted when the dialog is being closed
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Creates a new options UI instance.

        :param parent the parent of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

    def closeEvent(self, event):
        """Closes the calibration window.

        :param event the close event
        """
        self.closed.emit()


class ModeWidget(QtWidgets.QWidget):

    """Displays the ui for mode selection and management of a device."""

    # Signal emitted when the mode changes
    mode_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.mode_list = []

        self.profile = None
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self._create_widget()

    def populate_selector(self, profile_data, current_mode=None):
        """Adds entries for every mode present in the profile.

        :param profile_data the device for which the mode selection is generated
        :param current_mode the currently active mode
        """
        # To prevent emitting lots of change events the slot is first
        # disconnected and then at the end reconnected again.
        self.selector.currentIndexChanged.disconnect(self._mode_changed_cb)

        self.profile = profile_data

        # Remove all existing items
        while self.selector.count() > 0:
            self.selector.removeItem(0)
        self.mode_list = []

        # Create mode name labels visualizing the tree structure
        inheritance_tree = self.profile.build_inheritance_tree()
        labels = []
        self._inheritance_tree_to_labels(labels, inheritance_tree, 0)

        # Filter the mode names such that they only occur once below
        # their correct parent
        mode_names = []
        display_names = []
        for entry in labels:
            if entry[0] in mode_names:
                idx = mode_names.index(entry[0])
                if len(entry[1]) > len(display_names[idx]):
                    del mode_names[idx]
                    del display_names[idx]
                    mode_names.append(entry[0])
                    display_names.append(entry[1])
            else:
                mode_names.append(entry[0])
                display_names.append(entry[1])

        # Add properly arranged mode names to the drop down list
        for display_name, mode_name in zip(display_names, mode_names):
            self.selector.addItem(display_name)
            self.mode_list.append(mode_name)

        # Select currently active mode
        if len(mode_names) > 0:
            if current_mode is None or current_mode not in self.mode_list:
                current_mode = mode_names[0]
            self.selector.setCurrentIndex(self.mode_list.index(current_mode))
            self._mode_changed_cb(self.mode_list.index(current_mode))

        # Reconnect change signal
        self.selector.currentIndexChanged.connect(self._mode_changed_cb)

    @QtCore.pyqtSlot(int)
    def _mode_changed_cb(self, idx):
        """Callback function executed when the mode selection changes.

        :param idx id of the now selected entry
        """
        self.mode_changed.emit(self.mode_list[idx])

    def _inheritance_tree_to_labels(self, labels, tree, level):
        """Generates labels to use in the dropdown menu indicating inheritance.

        :param labels the list containing all the labels
        :param tree the part of the tree to be processed
        :param level the indentation level of this tree
        """
        for mode, children in sorted(tree.items()):
            labels.append((mode, "{}{}{}".format(
                "  " * level,
                "" if level == 0 else " ",
                mode
            )))
            self._inheritance_tree_to_labels(labels, children, level+1)

    def _create_widget(self):
        """Creates the mode selection and management dialog."""
        # Size policies used
        min_min_sp = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Minimum
        )
        exp_min_sp = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Minimum
        )

        # Create mode selector and related widgets
        self.label = QtWidgets.QLabel("Mode")
        self.label.setSizePolicy(min_min_sp)
        self.selector = QtWidgets.QComboBox()
        self.selector.setSizePolicy(exp_min_sp)
        self.selector.setMinimumContentsLength(20)

        # Connect signal
        self.selector.currentIndexChanged.connect(self._mode_changed_cb)

        # Add widgets to the layout
        self.main_layout.addStretch(10)
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.selector)


class InputListenerWidget(QtWidgets.QFrame):

    """Widget overlaying the main gui while waiting for the user
    to press a key."""

    def __init__(
            self,
            callback,
            event_types,
            return_kb_event=False,
            multi_keys=False,
            filter_func=None,
            parent=None
    ):
        """Creates a new instance.

        :param callback the function to pass the key pressed by the
            user to
        :param event_types the events to capture and return
        :param return_kb_event whether or not to return the kb event (True) or
            the key itself (False)
        :param multi_keys whether or not to return multiple key presses (True)
            or return after the first initial press (False)
        :param filter_func function applied to inputs which filters out more
            complex unwanted inputs
        :param parent the parent widget of this widget
        """
        super().__init__(parent)

        self.callback = callback
        self._event_types = event_types
        self._return_kb_event = return_kb_event
        self._multi_keys = multi_keys
        self.filter_func = filter_func

        self._abort_timer = threading.Timer(1.0, self.close)
        self._multi_key_storage = []

        # Create and configure the ui overlay
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel(
            """<center>Please press the desired {}.
            <br/><br/>
            Hold ESC for one second to abort.</center>""".format(
                self._valid_event_types_string()
            )
        ))

        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFrameStyle(QtWidgets.QFrame.Plain | QtWidgets.QFrame.Box)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)
        self.setPalette(palette)

        # Disable ui input selection on joystick input
        gremlin.shared_state.set_suspend_input_highlighting(True)

        # Start listening to user key presses
        event_listener = gremlin.event_handler.EventListener()
        event_listener.keyboard_event.connect(self._kb_event_cb)
        if gremlin.common.InputType.JoystickAxis in self._event_types or \
                gremlin.common.InputType.JoystickButton in self._event_types or \
                gremlin.common.InputType.JoystickHat in self._event_types:
            event_listener.joystick_event.connect(self._joy_event_cb)
        elif gremlin.common.InputType.Mouse in self._event_types:
            gremlin.windows_event_hook.MouseHook().start()
            event_listener.mouse_event.connect(self._mouse_event_cb)

    def _joy_event_cb(self, event):
        """Passes the pressed joystick event to the provided callback
        and closes the overlay.

        This only passes on joystick button presses.

        :param event the keypress event to be processed
        """
        # Ensure input highlighting is turned off, even if input request
        # dialogs are spawned in quick succession
        gremlin.shared_state.set_suspend_input_highlighting(True)

        # Only react to events we're interested in
        if event.event_type not in self._event_types:
            return
        if self.filter_func is not None and not self.filter_func(event):
            return

        # Ensure the event corresponds to a significant enough change in input
        process_event = gremlin.input_devices.JoystickInputSignificant() \
            .should_process(event)
        if event.event_type == gremlin.common.InputType.JoystickButton:
            process_event &= not event.is_pressed

        if process_event:
            gremlin.input_devices.JoystickInputSignificant().reset()
            self.callback(event)
            self.close()

    def _kb_event_cb(self, event):
        """Passes the pressed key to the provided callback and closes
        the overlay.

        :param event the keypress event to be processed
        """
        key = gremlin.macro.key_from_code(
                event.identifier[0],
                event.identifier[1]
        )

        # Return immediately once the first key press is detected
        if not self._multi_keys:
            if event.is_pressed and key == gremlin.macro.key_from_name("esc"):
                if not self._abort_timer.is_alive():
                    self._abort_timer.start()
            elif not event.is_pressed and \
                    gremlin.common.InputType.Keyboard in self._event_types:
                if not self._return_kb_event:
                    self.callback(key)
                else:
                    self.callback(event)
                self._abort_timer.cancel()
                self.close()
        # Record all key presses and return on the first key release
        else:
            if event.is_pressed:
                if gremlin.common.InputType.Keyboard in self._event_types:
                    if not self._return_kb_event:
                        self._multi_key_storage.append(key)
                    else:
                        self._multi_key_storage.append(event)
                if key == gremlin.macro.key_from_name("esc"):
                    # Start a timer and close if it expires, aborting the
                    # user input request
                    if not self._abort_timer.is_alive():
                        self._abort_timer.start()
            else:
                self._abort_timer.cancel()
                self.callback(self._multi_key_storage)
                self.close()

        # Ensure the timer is cancelled and reset in case the ESC is released
        # and we're not looking to return keyboard events
        if key == gremlin.macro.key_from_name("esc") and not event.is_pressed:
            self._abort_timer.cancel()
            self._abort_timer = threading.Timer(1.0, self.close)

    def _mouse_event_cb(self, event):
        self.callback(event)
        self.close()

    def closeEvent(self, evt):
        """Closes the overlay window."""
        event_listener = gremlin.event_handler.EventListener()
        event_listener.keyboard_event.disconnect(self._kb_event_cb)
        if gremlin.common.InputType.JoystickAxis in self._event_types or \
                gremlin.common.InputType.JoystickButton in self._event_types or \
                gremlin.common.InputType.JoystickHat in self._event_types:
            event_listener.joystick_event.disconnect(self._joy_event_cb)
        elif gremlin.common.InputType.Mouse in self._event_types:
            event_listener.mouse_event.disconnect(self._mouse_event_cb)

        # Stop mouse hook in case it is running
        gremlin.windows_event_hook.MouseHook().stop()

        # Delay un-suspending input highlighting to allow an axis that's being
        # moved to return to its center without triggering an input highlight
        gremlin.shared_state.delayed_input_highlighting_suspension()
        super().closeEvent(evt)

    def _valid_event_types_string(self):
        """Returns a formatted string containing the valid event types.

        :return string representing the valid event types
        """
        valid_str = []
        if gremlin.common.InputType.JoystickAxis in self._event_types:
            valid_str.append("Axis")
        if gremlin.common.InputType.JoystickButton in self._event_types:
            valid_str.append("Button")
        if gremlin.common.InputType.JoystickHat in self._event_types:
            valid_str.append("Hat")
        if gremlin.common.InputType.Keyboard in self._event_types:
            valid_str.append("Key")

        return ", ".join(valid_str)


def clear_layout(layout):
    """Removes all items from the given layout.

    :param layout the layout from which to remove all items
    """
    while layout.count() > 0:
        child = layout.takeAt(0)
        if child.layout():
            clear_layout(child.layout())
        elif child.widget():
            child.widget().hide()
            child.widget().deleteLater()
        layout.removeItem(child)
