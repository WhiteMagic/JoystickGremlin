# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2017 Lionel Ott
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

from PyQt5 import QtWidgets, QtCore, QtGui

import gremlin

# Mapping from types to display names
input_type_to_name = {
    gremlin.common.InputType.JoystickAxis: "Axis",
    gremlin.common.InputType.JoystickButton: "Button",
    gremlin.common.InputType.JoystickHat: "Hat",
    gremlin.common.InputType.Keyboard: "",
}
name_to_input_type = {
    "Axis": gremlin.common.InputType.JoystickAxis,
    "Button": gremlin.common.InputType.JoystickButton,
    "Hat": gremlin.common.InputType.JoystickHat
}


class AbstractModel(QtCore.QObject):

    data_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def rows(self):
        pass

    def data(self, index):
        pass


class AbstractView(QtWidgets.QWidget):

    item_selected = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None

    def set_model(self, model):
        if self.model is not None:
            self.model.data_changed.disconnect(self.redraw)
        self.model = model
        self.model.data_changed.connect(self.redraw)

    def select_item(self, index):
        pass

    def redraw(self):
        pass


class LeftRightPushButton(QtWidgets.QPushButton):

    clicked_right = QtCore.pyqtSignal()

    def __init__(self, label, parent=None):
        super().__init__(label, parent)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.clicked_right.emit()
        else:
            super().mousePressEvent(event)


class NoKeyboardPushButton(QtWidgets.QPushButton):

    """Standard PushButton which does not react to keyboard input."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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


class JoystickSelector(QtWidgets.QWidget):

    """Widget allowing the selection of input items on a physical joystick."""

    def __init__(self, devices, change_cb, valid_types, parent=None):
        """Creates a new JoystickSelector instance.

        :param devices list of devices to choose from
        :param change_cb function to call when changes occur
        :param valid_types valid input types for selection
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.devices = devices
        self.change_cb = change_cb
        self.valid_types = valid_types

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.device_dropdown = None
        self.input_item_dropdowns = []

        self._create_device_dropdown()
        self._create_input_dropdown()

        self._device_id_to_index_map = {}
        self._index_to_device_map = {}
        for i, device in enumerate(
                sorted(self.devices, key=lambda x: x.windows_id)
        ):
            self._device_id_to_index_map[gremlin.util.device_id(device)] = i
            self._index_to_device_map[i] = device

    def get_selection(self):
        """Returns information about the currently selected entry.

        :return dictionary containing selection information
        """
        selection_id = self.device_dropdown.currentIndex()

        if selection_id != -1:
            input_selection = \
                self.input_item_dropdowns[selection_id].currentText()

            arr = input_selection.split()
            windows_id = self._index_to_device_map[selection_id].windows_id
            hardware_id = self._index_to_device_map[selection_id].hardware_id
            input_type = name_to_input_type[arr[0]]
            input_id = int(arr[1])
        else:
            hardware_id = None
            windows_id = None
            input_id = None
            input_type = None

        return {
            "hardware_id": hardware_id,
            "windows_id": windows_id,
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
        if device_id not in [0, None] and \
                device_id in self._device_id_to_index_map:
            dev_id = self._device_id_to_index_map[device_id]

        # If we have no device simply stop here
        if dev_id is None:
            return

        # Retrieve the index of the correct entry in the combobox
        input_name = "{} {:d}".format(
            input_type_to_name[input_type],
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
            gremlin.common.InputType.JoystickAxis: lambda x: x.axes,
            gremlin.common.InputType.JoystickButton: lambda x: x.buttons,
            gremlin.common.InputType.JoystickHat: lambda x: x.hats
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
                        input_type_to_name[input_type],
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


# FIXME: stop repeating type to name maps everywhere

class VJoySelector(QtWidgets.QWidget):

    """Widget allowing the selection of vJoy inputs."""

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
        self.input_item_dropdowns = {}

        self._create_device_dropdown()
        self._create_input_dropdown()

    def get_selection(self):
        """Returns the current selection of the widget.

        :return dictionary containing the current selection
        """
        device_selection = self.device_dropdown.currentText()
        vjoy_device_id = int(device_selection.split()[-1])
        input_selection = \
            self.input_item_dropdowns[vjoy_device_id].currentText()

        arr = input_selection.split()
        vjoy_input_type = name_to_input_type[arr[0]]
        if vjoy_input_type == gremlin.common.InputType.JoystickAxis:
            vjoy_input_id = gremlin.common.vjoy_axis_names.index(
                " ".join(arr[1:])
            ) + 1
        else:
            vjoy_input_id = int(arr[1])

        return {
            "device_id": vjoy_device_id,
            "input_id": vjoy_input_id,
            "input_type": vjoy_input_type
        }

    def set_selection(self, input_type, vjoy_dev_id, vjoy_input_id):
        """Sets the widget's entries to the provided values.

        :param input_type the input type
        :param vjoy_dev_id the id of the vjoy device
        :param vjoy_input_id the id of the input
        """
        # Get the appropriate vjoy device identifier
        if vjoy_dev_id is None:
            dev_id = -1
        else:
            dev_id = self.device_dropdown.findText(
                "vJoy Device {:d}".format(vjoy_dev_id)
            )

        # Retrieve the index of the correct entry in the combobox
        vjoy_proxy = gremlin.joystick_handling.VJoyProxy()
        if input_type == gremlin.common.InputType.JoystickAxis:
            input_name = "{} {}".format(
                input_type_to_name[input_type],
                vjoy_proxy[vjoy_dev_id].axis_name(axis_id=vjoy_input_id)
            )
        else:
            input_name = "{} {:d}".format(
                input_type_to_name[input_type],
                vjoy_input_id
            )
        try:
            btn_id = self.input_item_dropdowns[vjoy_dev_id].findText(input_name)
        except KeyError:
            btn_id = -1

        # If either of the provided entries results in an invalid selection
        # we simply select the first valid thing we come across
        if dev_id == -1 or btn_id == -1:
            dev_id = 0
            btn_id = 0
            vjoy_dev_id = sorted(self.input_item_dropdowns.keys())[0]

        # Select and display correct combo boxes and entries within
        self.device_dropdown.setCurrentIndex(dev_id)
        for entry in self.input_item_dropdowns.values():
            entry.setVisible(False)
        self.input_item_dropdowns[vjoy_dev_id].setVisible(True)
        self.input_item_dropdowns[vjoy_dev_id].setCurrentIndex(btn_id)

    def _create_device_dropdown(self):
        """Creates the vJoy device selection drop downs."""
        self.device_dropdown = QtWidgets.QComboBox(self)
        for dev in sorted(self.vjoy_devices, key=lambda x: x.vjoy_id):
            self.device_dropdown.addItem("vJoy Device {:d}".format(dev.vjoy_id))
        self.main_layout.addWidget(self.device_dropdown)
        self.device_dropdown.activated.connect(self._update_device)

    def _create_input_dropdown(self):
        """Creates the vJoy input item selection drop downs."""
        count_map = {
            gremlin.common.InputType.JoystickAxis: lambda x: x.axis_count,
            gremlin.common.InputType.JoystickButton: lambda x: x.buttons,
            gremlin.common.InputType.JoystickHat: lambda x: x.hats
        }

        self.input_item_dropdowns = {}

        vjoy_proxy = gremlin.joystick_handling.VJoyProxy()

        # Create input item selections for the vjoy devices, each
        # selection will be invisible unless it is selected as the
        # active device
        for dev in self.vjoy_devices:
            selection = QtWidgets.QComboBox(self)
            selection.setMaxVisibleItems(20)

            # Add items based on the input type
            for input_type in self.valid_types:
                for i in range(1, count_map[input_type](dev)+1):
                    if input_type == gremlin.common.InputType.JoystickAxis:
                        selection.addItem("{} {}".format(
                            input_type_to_name[input_type],
                            vjoy_proxy[dev.vjoy_id].axis_name(linear_index=i)
                        ))
                    else:
                        selection.addItem("{} {:d}".format(
                            input_type_to_name[input_type],
                            i
                        ))

            # Add the selection and hide it
            selection.setVisible(False)
            selection.activated.connect(self.change_cb)
            self.main_layout.addWidget(selection)
            self.input_item_dropdowns[dev.vjoy_id] = selection

        # Show the "None" selection entry
        first_key = sorted(self.input_item_dropdowns.keys())[0]
        self.input_item_dropdowns[first_key].setVisible(True)

    def _update_device(self, index):
        """Handles changing the vJoy device selection.

        :param index vjoy device index
        """
        # Hide all selection dropdowns
        for entry in self.input_item_dropdowns.values():
            entry.setVisible(False)

        # Extract vjoy id
        device_selection = self.device_dropdown.itemText(index)
        vjoy_device_id = int(device_selection.split()[-1])

        # Show correct dropdown
        self.input_item_dropdowns[vjoy_device_id].setVisible(True)
        self.input_item_dropdowns[vjoy_device_id].setCurrentIndex(0)
        self.change_cb()


class ActionSelector(QtWidgets.QWidget):

    action_added = QtCore.pyqtSignal(str)

    def __init__(self, input_type, parent=None):
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
        :param parent the parent widget of this widget
        """
        super().__init__(parent)

        self.callback = callback
        self._event_types = event_types
        self._return_kb_event = return_kb_event
        self._multi_keys = multi_keys

        self._multi_key_storage = []

        # Create and configure the ui overlay
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel(
            """<center>Please press the desired {}.
            <br/><br/>
            Pressing ESC aborts.</center>""".format(
                self._valid_event_types_string()
            )
        ))

        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFrameStyle(QtWidgets.QFrame.Plain | QtWidgets.QFrame.Box)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)
        self.setPalette(palette)

        # Start listening to user key presses
        event_listener = gremlin.event_handler.EventListener()
        event_listener.keyboard_event.connect(self._kb_event_cb)
        if gremlin.common.InputType.JoystickAxis in self._event_types or \
                gremlin.common.InputType.JoystickButton in self._event_types or \
                gremlin.common.InputType.JoystickHat in self._event_types:
            event_listener.joystick_event.connect(self._joy_event_cb)

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
            if gremlin.common.InputType.Keyboard in self._event_types and \
                    key != gremlin.macro.key_from_name("esc"):
                if not self._return_kb_event:
                    self.callback(key)
                else:
                    self.callback(event)
                self._close_window()
            elif key == gremlin.macro.key_from_name("esc"):
                self._close_window()
        # Record all key presses and return on the first key release
        else:
            if event.is_pressed:
                if gremlin.common.InputType.Keyboard in self._event_types and \
                                key != gremlin.macro.key_from_name("esc"):
                    if not self._return_kb_event:
                        self._multi_key_storage.append(key)
                    else:
                        self._multi_key_storage.append(event)
                elif key == gremlin.macro.key_from_name("esc"):
                    self._close_window()
            else:
                self.callback(self._multi_key_storage)
                self._close_window()

    def _joy_event_cb(self, event):
        """Passes the pressed joystick event to the provided callback
        and closes the overlay.

        This only passes on joystick button presses.

        :param event the keypress event to be processed
        """
        # Only react to events we're interested in
        if event.event_type not in self._event_types:
            return

        if event.event_type == gremlin.common.InputType.JoystickButton and \
                not event.is_pressed:
            self.callback(event)
            self._close_window()
        elif event.event_type == gremlin.common.InputType.JoystickAxis and \
                abs(event.value) > 0.5:
            self.callback(event)
            self._close_window()
        elif event.event_type == gremlin.common.InputType.JoystickHat and \
                event.value != (0, 0):
            self.callback(event)
            self._close_window()

    def _close_window(self):
        """Closes the overlay window."""
        event_listener = gremlin.event_handler.EventListener()
        event_listener.keyboard_event.disconnect(self._kb_event_cb)
        if gremlin.common.InputType.JoystickAxis in self._event_types or \
                gremlin.common.InputType.JoystickButton in self._event_types or \
                gremlin.common.InputType.JoystickHat in self._event_types:
            event_listener.joystick_event.disconnect(self._joy_event_cb)
        self.close()

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
