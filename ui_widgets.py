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


"""
Collection of widgets used in the configuration UI.
"""


import logging
from PyQt5 import QtCore, QtGui, QtWidgets

import action
import action.common
from gremlin import common, error, macro, profile, shared_state, util
from gremlin.event_handler import Event, EventListener, InputType
from gremlin.common import UiInputType


class InputIdentifier(object):

    """Represents the identifier of a single input item."""

    def __init__(self, input_type, input_id, device_type):
        """Creates a new instance.

        :param input_type the type of input
        :param input_id the identifier of the input
        :param device_type the type of device this input belongs to
        """
        self._input_type = input_type
        self._input_id = input_id
        self._device_type = device_type

    @property
    def device_type(self):
        return self._device_type

    @property
    def input_type(self):
        return self._input_type

    @property
    def input_id(self):
        return self._input_id


class InputListenerWidget(QtWidgets.QFrame):

    """Widget overlaying the main gui while waiting for the user
    to press a key."""

    def __init__(self, callback, listen_keyboard, listen_joystick, parent=None):
        """Creates a new instance.

        :param callback the function to pass the key pressed by the
            user to
        :param listen_keyboard flag indicating whether or not to
            listen to keyboard events
        :parma listen_joystick flag indicating whether or not to
            listen to joystick button events
        :param parent the parent widget of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.callback = callback
        self._listen_keyboard = listen_keyboard
        self._listen_joystick = listen_joystick

        # Create and configure the ui overlay
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel(
            """<center>Please press the key / button you want to add.
            <br/><br/>
            Pressing ESC aborts.</center>"""
        ))

        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFrameStyle(QtWidgets.QFrame.Plain | QtWidgets.QFrame.Box)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)
        self.setPalette(palette)

        # Start listening to user key presses
        event_listener = EventListener()
        if listen_keyboard:
            event_listener.keyboard_event.connect(self._kb_event_cb)
        if listen_joystick:
            event_listener.joystick_event.connect(self._joy_event_cb)

    def _kb_event_cb(self, event):
        """Passes the pressed key to the provided callback and closes
        the overlay.

        :param event the keypress event to be processed
        """
        key = macro.key_from_code(
                event.identifier[0],
                event.identifier[1]
        )
        if key != macro.Keys.Esc:
            self.callback(key)
        self._close_window()

    def _joy_event_cb(self, event):
        """Passes the pressed joystick event to the provided callback
        and closes the overlay.

        This only passes on joystick button presses.

        :param event the keypress event to be processed
        """
        if event.event_type == InputType.JoystickButton and \
                event.is_pressed == False:
            self.callback(event)
            self._close_window()

    def _close_window(self):
        """Closes the overlay window."""
        event_listener = EventListener()
        if self._listen_keyboard:
            event_listener.keyboard_event.disconnect(self._kb_event_cb)
        if self._listen_joystick:
            event_listener.joystick_event.disconnect(self._joy_event_cb)
        self.close()


class DeviceInformationWidget(QtWidgets.QWidget):

    """Widget which displays information about all connected joystick
    devices."""

    def __init__(self, devices, parent=None):
        """Creates a new instance.

        :param devices the list of device information objects
        :param parent the parent widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.devices = devices

        self.setWindowTitle("Device Information")
        self.main_layout = QtWidgets.QGridLayout(self)

        self.main_layout.addWidget(QtWidgets.QLabel("<b>Name</b>"), 0, 0)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Axes</b>"), 0, 1)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Buttons</b>"), 0, 2)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Hats</b>"), 0, 3)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>System ID</b>"), 0, 4)
        self.main_layout.addWidget(QtWidgets.QLabel("<b>Hardware ID</b>"), 0, 5)

        for i, entry in enumerate(self.devices):
            self.main_layout.addWidget(
                QtWidgets.QLabel(entry.name), i+1, 0
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.axes)), i+1, 1
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.buttons)), i+1, 2
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.hats)), +i+1, 3
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.windows_id)), i+1, 4
            )
            self.main_layout.addWidget(
                QtWidgets.QLabel(str(entry.hardware_id)), i+1, 5
            )

        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(lambda: self.close())
        self.main_layout.addWidget(self.close_button, len(devices)+1, 3)


class AxisCalibrationWidget(QtWidgets.QWidget):

    """Widget displaying calibration information about a single axis."""

    def __init__(self, parent=None):
        """Creates a new object.

        :param parent the parent widget of this one
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.main_layout = QtWidgets.QGridLayout(self)
        self.limits = [0, 0, 0]

        # Create slider showing the axis position graphically
        self.slider = QtWidgets.QProgressBar()
        self.slider.setMinimum(-32768)
        self.slider.setMaximum(32767)
        self.slider.setValue(self.limits[1])
        self.slider.setMinimumWidth(200)
        self.slider.setMaximumWidth(200)

        # Create the labels
        self.current = QtWidgets.QLabel("0")
        self.current.setAlignment(QtCore.Qt.AlignRight)
        self.minimum = QtWidgets.QLabel("0")
        self.minimum.setAlignment(QtCore.Qt.AlignRight)
        self.center = QtWidgets.QLabel("0")
        self.center.setAlignment(QtCore.Qt.AlignRight)
        self.maximum = QtWidgets.QLabel("0")
        self.maximum.setAlignment(QtCore.Qt.AlignRight)
        self._update_labels()

        # Populate the layout
        self.main_layout.addWidget(self.slider, 0, 0, 0, 3)
        self.main_layout.addWidget(self.current, 0, 3)
        self.main_layout.addWidget(self.minimum, 0, 4)
        self.main_layout.addWidget(self.center, 0, 5)
        self.main_layout.addWidget(self.maximum, 0, 6)

    def set_current(self, value):
        """Updates the limits of the axis.

        :param value the new value
        """
        self.slider.setValue(value)
        if value > self.limits[2]:
            self.limits[2] = value
        if value < self.limits[0]:
            self.limits[0] = value
        self._update_labels()

    def centered(self):
        """Records the value of the center or neutral position."""
        self.limits[1] = self.slider.value()
        self._update_labels()

    def _update_labels(self):
        """Updates the axis limit values."""
        self.current.setText("{: 5d}".format(self.slider.value()))
        self.minimum.setText("{: 5d}".format(self.limits[0]))
        self.center.setText("{: 5d}".format(self.limits[1]))
        self.maximum.setText("{: 5d}".format(self.limits[2]))


class ActionLabel(QtWidgets.QLabel):

    """Handles showing the correct icon for the given action."""

    def __init__(self, action_entry, parent=None):
        """Creates a new label for the given entry.

        :param action_entry the entry to create the label for
        :param parent the parent
        """
        QtWidgets.QLabel.__init__(self, parent)

        if isinstance(action_entry, action.remap.Remap):
            input_string = "axis"
            if action_entry.input_type == UiInputType.JoystickButton:
                input_string = "button"
            elif action_entry.input_type == UiInputType.JoystickHat:
                input_string = "hat"
            self.setPixmap(QtGui.QPixmap(
                "gfx/action/action_remap_{}_{:03d}.png".format(
                        input_string,
                        action_entry.vjoy_input_id
                )
            ))
        else:
            self.setPixmap(QtGui.QPixmap(action_entry.icon))


class InputItemButton(QtWidgets.QFrame):

    """Creates a button like widget which emits an event when pressed.

    This event can be used to display input item specific customization
    widgets. This button also shows icons of the associated actions.
    """

    # Signal emitted whenever this button is pressed
    input_item_clicked = QtCore.pyqtSignal(InputIdentifier)

    def __init__(self, label, identifier, parent=None):
        """Creates a new instance.

        :param label the label / number of the input item
        :param identifier identifying information about the button
        :param parent the parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)
        self.identifier = identifier
        self.label = str(label)
        self._icons = []

        self.setFrameShape(QtWidgets.QFrame.Box)
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel(self._create_button_label()))
        self.main_layout.addStretch(0)
        self.setMinimumSize(100, 40)

    def create_action_icons(self, profile_data):
        """Creates the label of this instance.

        Renders the text representing the instance's name as well as
        icons of actions associated with it.

        :param profile_data the profile.InputItem object associated
            with this instance
        """
        # Clear any potentially existing labels before adding labels
        while self.main_layout.count() > 2:
            item = self.main_layout.takeAt(2)
            item.widget().deleteLater()
            self.main_layout.removeItem(item)

        # Create the actual icons
        for entry in profile_data.actions:
            self.main_layout.addWidget(ActionLabel(entry))

    def mousePressEvent(self, event):
        """Emits the input_item_changed event when this instance is
        clicked on by the mouse.

        :param event the mouse event
        """
        self.input_item_clicked.emit(self.identifier)

    def _create_button_label(self):
        """Creates the label to display on this button.

        :return label to use for this button
        """
        return "{} {}".format(
            common.ui_input_type_to_name(self.identifier.input_type),
            self.label
        )


class AxisConditionWidget(QtWidgets.QWidget):

    """Widget allowing the configuration of the activation condition
    of axis triggers."""

    def __init__(self, change_cb, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.change_cb = change_cb
        self.main_layout = QtWidgets.QHBoxLayout(self)

        self.checkbox = QtWidgets.QCheckBox("Trigger between")

        self.main_layout.addWidget(self.checkbox)

        self.lower_limit = QtWidgets.QDoubleSpinBox()
        self.lower_limit.setRange(-1.0, 1.0)
        self.lower_limit.setSingleStep(0.05)
        self.upper_limit = QtWidgets.QDoubleSpinBox()
        self.upper_limit.setRange(-1.0, 1.0)
        self.upper_limit.setSingleStep(0.05)

        self.main_layout.addWidget(self.lower_limit)
        self.main_layout.addWidget(QtWidgets.QLabel(" and "))
        self.main_layout.addWidget(self.upper_limit)

        self.main_layout.addStretch()
        self.connect_signals()

    def connect_signals(self):
        self.checkbox.stateChanged.connect(self.change_cb)
        self.lower_limit.valueChanged.connect(self.change_cb)
        self.upper_limit.valueChanged.connect(self.change_cb)

    def disconnect_signals(self):
        self.checkbox.stateChanged.disconnect(self.change_cb)
        self.lower_limit.valueChanged.disconnect(self.change_cb)
        self.upper_limit.valueChanged.disconnect(self.change_cb)

    def from_profile(self):
        pass

    def to_profile(self):
        pass


class ButtonConditionWidget(QtWidgets.QWidget):

    """Widget allowing the configuration of the activation condition
    of button like actions."""

    def __init__(self, change_cb, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.change_cb = change_cb
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel("Activate on"))
        self.press = QtWidgets.QCheckBox("press")
        self.release = QtWidgets.QCheckBox("release")
        self.shift_button = QtWidgets.QPushButton("Assign shift button")
        self.main_layout.addWidget(self.press)
        self.main_layout.addWidget(self.release)
        self.main_layout.addWidget(self.shift_button)

        self.connect_signals()

        self.shift_data = None

    def connect_signals(self):
        self.press.stateChanged.connect(self.change_cb)
        self.release.stateChanged.connect(self.change_cb)
        self.shift_button.clicked.connect(self._shift_button_cb)

    def disconnect_signals(self):
        self.press.stateChanged.disconnect(self.change_cb)
        self.release.stateChanged.disconnect(self.change_cb)
        self.shift_button.clicked.disconnect(self._shift_button_cb)

    def from_profile(self, action_data):
        pass

    def to_profile(self, action_data):
        pass

    def _shift_button_cb(self):
        """Queries the user for the shift button to use."""
        self.button_press_dialog = InputListenerWidget(
            self._assign_shift_button_cb,
            True,
            True
        )

        shared_state.set_suspend_input_highlighting(True)

        # Display the dialog centered in the middle of the UI
        geom = self.geometry()
        point = self.mapToGlobal(QtCore.QPoint(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
        ))
        self.button_press_dialog.setGeometry(
            point.x(),
            point.y(),
            300,
            150
        )
        self.button_press_dialog.show()

    def _assign_shift_button_cb(self, value):
        if isinstance(value, Event):
            devices = util.joystick_devices()
            for dev in devices:
                if util.device_id(value) == util.device_id(dev):
                    # Set the button label
                    self.shift_button.setText("{} - Button {:d}".format(
                        dev.name,
                        value.identifier
                    ))

                    # Store the information inside the profile
                    self.shift_data = {
                        "id": value.identifier,
                        "hardware_id": dev.hardware_id,
                        "windows_id": dev.windows_id
                    }
                    break
        elif isinstance(value, macro.Keys.Key):
            self.shift_button.setText(value.name)
            self.shift_data = {
                "id": (value.scan_code, value.is_extended),
                "hardware_id": 0,
                "windows_id": 0
            }

        shared_state.set_suspend_input_highlighting(False)
        self.change_cb()


class HatConditionWidget(QtWidgets.QWidget):

    """Widget allowing the configuration of the activation condition
    of hat actions."""

    def __init__(self, change_cb, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.change_cb = change_cb
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel("Activate on"))
        self.widgets = {}
        for name in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
            self.widgets[name] = QtWidgets.QCheckBox(name)
            self.main_layout.addWidget(self.widgets[name])
        self.connect_signals()

    def connect_signals(self):
        for name in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
            self.widgets[name].stateChanged.connect(self.change_cb)

    def disconnect_signals(self):
        for name in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
            self.widgets[name].stateChanged.disconnect(self.change_cb)

    def from_profile(self, action_data):
        pass

    def to_profile(self, action_data):
        pass


class ActionWidgetContainer(QtWidgets.QDockWidget):

    """Represents a proxy widget which contains another widget and
    simply allows the management of said contained widgets.
    """

    # Signal which is emitted whenever the widget is closed
    closed = QtCore.pyqtSignal(QtWidgets.QWidget)

    # Palette used to render widgets
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Background, QtCore.Qt.lightGray)

    def __init__(self, action_widget, parent=None):
        """Creates a new instance.

        :param action_widget the widget this proxy manages
        :param parent the parent widget of this widget
        """
        QtWidgets.QDockWidget.__init__(self, parent)
        assert(isinstance(
            action_widget,
            action.common.AbstractActionWidget
        ))

        self.action_widget = action_widget

        self.setWindowTitle(action_widget.action_data.name)
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)

        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setAutoFillBackground(True)
        self.main_widget.setPalette(self.palette)

        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self._add_condition()
        self.main_layout.addWidget(self.action_widget)
        self.setWidget(self.main_widget)

    def to_profile(self):
        """Updates the profile data associated with the widget with
        the UI contents."""
        self.action_widget.to_profile()
        if self._is_button_like() and self._has_condition():
            # Extract activation condition data
            self.action_widget.action_data.condition =\
                action.common.ButtonCondition(
                    self.condition.press.isChecked(),
                    self.condition.release.isChecked(),
                    self.condition.shift_data
                )
        elif self._is_hat() and self._has_condition():
            self.action_widget.action_data.condition =\
                action.common.HatCondition(
                    self.condition.widgets["N"].isChecked(),
                    self.condition.widgets["NE"].isChecked(),
                    self.condition.widgets["E"].isChecked(),
                    self.condition.widgets["SE"].isChecked(),
                    self.condition.widgets["S"].isChecked(),
                    self.condition.widgets["SW"].isChecked(),
                    self.condition.widgets["W"].isChecked(),
                    self.condition.widgets["NW"].isChecked()
                )
        elif self._is_axis() and self._has_condition():
            self.action_widget.action_data.condition =\
                action.common.AxisCondition(
                    self.condition.checkbox.isChecked(),
                    self.condition.lower_limit.value(),
                    self.condition.upper_limit.value()
                )

    def _populate_condition(self):
        # Only run if we need a condition
        if not self._has_condition():
            return

        # Get condition data and return if there is nothing
        condition = self.action_widget.action_data.condition
        if condition is None:
            return

        if self._is_button_like():
            self.condition.disconnect_signals()

            self.condition.press.setChecked(condition.on_press)
            self.condition.release.setChecked(condition.on_release)

            # Shift action label
            if condition.shift_button is not None:
                self.condition.shift_data = condition.shift_button
                if condition.shift_button["hardware_id"] == 0:
                    key = macro.key_from_code(
                        condition.shift_button["id"][0],
                        condition.shift_button["id"][1]
                    )
                    self.condition.shift_button.setText(key.name)
                else:
                    devices = util.joystick_devices()
                    dummy_event = Event(
                        InputType.JoystickButton,
                        condition.shift_button["id"],
                        condition.shift_button["hardware_id"],
                        condition.shift_button["windows_id"]
                    )
                    for dev in devices:
                        if util.device_id(dummy_event) == util.device_id(dev):
                            self.condition.shift_button.setText(
                                "{} - Button {:d}".format(
                                    dev.name,
                                    condition.shift_button["id"]
                                ))
            self.condition.connect_signals()

        elif self._is_hat():
            self.condition.disconnect_signals()
            self.condition.widgets["N"].setChecked(condition.on_n)
            self.condition.widgets["NE"].setChecked(condition.on_ne)
            self.condition.widgets["E"].setChecked(condition.on_e)
            self.condition.widgets["SE"].setChecked(condition.on_se)
            self.condition.widgets["S"].setChecked(condition.on_s)
            self.condition.widgets["SW"].setChecked(condition.on_sw)
            self.condition.widgets["W"].setChecked(condition.on_w)
            self.condition.widgets["NW"].setChecked(condition.on_nw)
            self.condition.connect_signals()
        elif self._is_axis():
            self.condition.disconnect_signals()
            self.condition.checkbox.setChecked(condition.is_active)
            self.condition.lower_limit.setValue(condition.lower_limit)
            self.condition.upper_limit.setValue(condition.upper_limit)
            self.condition.connect_signals()

    def closeEvent(self, event):
        """Emits the closed event when this widget is being closed.

        :param event the close event details
        """
        QtWidgets.QDockWidget.closeEvent(self, event)
        self.closed.emit(self)

    def _has_condition(self):
        """Returns whether or not the widget has a condition.

        :return True if a condition is present, False otherwise
        """
        has_condition = False
        input_type = self.action_widget.action_data.parent.input_type
        widget_type = type(self.action_widget)
        if self._is_button_like() and \
                widget_type in action.condition_map[input_type]:
            has_condition = True
        elif self._is_hat() and \
                widget_type in action.condition_map[input_type]:
            has_condition = True
        elif self._is_axis() and \
                widget_type in action.condition_map[input_type]:
            has_condition = True

        return has_condition

    def _add_condition(self):
        """Adds a condition widget to the UI if necessary."""
        input_type = self.action_widget.action_data.parent.input_type
        widget_type = type(self.action_widget)
        condition = None
        if self._is_button_like() and \
                widget_type in action.condition_map[input_type]:
            condition = ButtonConditionWidget(self.to_profile)
        elif self._is_hat() and \
                widget_type in action.condition_map[input_type]:
            condition = HatConditionWidget(self.to_profile)
        elif self._is_axis() and \
                widget_type in action.condition_map[input_type]:
            condition = AxisConditionWidget(self.to_profile)

        if condition is not None:
            self.condition = condition
            self._populate_condition()
            self.main_layout.addWidget(self.condition)

    def _is_button_like(self):
        """Returns True if the action_widget is button like, i.e. a
        joystick button or a keyboard key.

        :return True if the action_widget is associated with a button
            like input type, False otherwise
        """
        input_type = self.action_widget.action_data.parent.input_type
        return input_type in [
            UiInputType.JoystickButton,
            UiInputType.Keyboard
        ]

    def _is_hat(self):
        """Returns True if the action_widget is associated with a hat.

        :return True if the action_widget is associated with a hat,
            False otherwise
        """
        is_hat = self.action_widget.action_data.parent.input_type == \
            UiInputType.JoystickHat
        is_remap = isinstance(self.action_widget.action_data, action.remap.Remap)
        return is_hat and not is_remap

    def _is_axis(self):
        """Returns True if the action_widget is associated witha na axis.

        :return True if the action_widget is associated with an axis,
            False otherwise
        """
        is_axis = self.action_widget.action_data.parent.input_type == \
            UiInputType.JoystickAxis
        return is_axis


class InputItemConfigurationPanel(QtWidgets.QFrame):

    """UI dialog responsible for the configuration of a single
    input item such as an axis, button, hat, or key.
    """

    # Signal which is emitted whenever the configuration changes
    changed = QtCore.pyqtSignal()

    def __init__(self, vjoy_devices, item_profile, parent=None):
        QtWidgets.QFrame.__init__(self, parent)

        self.item_profile = item_profile
        self.vjoy_devices = vjoy_devices

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.button_layout = QtWidgets.QHBoxLayout()
        self.widget_layout = QtWidgets.QVBoxLayout()

        self._create_description()
        self._create_action_dropdown()
        self.main_layout.addLayout(self.widget_layout)

        self.action_widgets = []
        self.from_profile(self.item_profile)

    def _add_widget(self, action_profile, emit=True):
        """Adds an ActionWidget to the ui by placing it into a
        closable container.

        :param action_profile the action type for which to create a new widget
        :param emit whether or not to emit a changed signal
        """
        # In case the profile was just created by adding a new action
        # fill some of the fields.
        if not action_profile.is_valid:
            action_profile.input_type = self.item_profile.input_type
            if self.item_profile.input_type in [
                UiInputType.JoystickButton, UiInputType.Keyboard
            ]:
                action_profile.condition = action.common.ButtonCondition()
                # Remap actions should typically trigger both on press
                # and release
                if isinstance(action_profile, action.remap.Remap):
                    action_profile.condition =\
                        action.common.ButtonCondition(True, True)
            elif self.item_profile.input_type == UiInputType.JoystickHat:
                action_profile.condition = action.common.HatCondition(
                    False, False, False, False, False, False, False, False
                )
            self.item_profile.actions.append(action_profile)

        # Create the widget using the information from the action item
        widget = action_profile.widget(
            action_profile,
            self.vjoy_devices,
            lambda: self.changed.emit()
        )

        # Add the newly created widget to the UI
        self.action_widgets.append(ActionWidgetContainer(widget))
        self.action_widgets[-1].closed.connect(self._remove_widget)
        self.main_layout.addWidget(self.action_widgets[-1])
        if emit:
            self.changed.emit()

        return widget

    def _remove_widget(self, widget, emit=True):
        """Removes a widget from the ui as well as the profile.

        :param widget the widget and associated data to remove
        :param emit emits a changed signal if True, otherwise nothing
            is emitted
        """
        assert(isinstance(widget, ActionWidgetContainer))
        # Remove profile data
        action_data = widget.action_widget.action_data
        assert(action_data in self.item_profile.actions)
        self.item_profile.actions.remove(action_data)
        # Remove UI widgets
        self.main_layout.removeWidget(widget)
        self.action_widgets.remove(widget)
        # Signal change within the widget
        if emit:
            self.changed.emit()

    def _add_action(self, checked=False):
        """Adds a new action to the input item.

        :param checked if the button is checked or not
        """
        # Build label to class map
        lookup = {}
        for klass in profile.action_lookup.values():
            lookup[klass.name] = klass
        # Create desired widget
        selection = lookup[self.action_dropdown.currentText()]
        self._add_widget(selection(self.item_profile))

    def from_profile(self, data):
        """Sets the data of this widget.

        :param data profile.InputItem object containing data for this
            widget
        """
        if not data:
            return

        # Create UI widgets and populate them based on the type of
        # action stored in the profile.
        self.item_profile = data
        for i in range(len(self.item_profile.actions)):
            try:
                self._add_widget(self.item_profile.actions[i], False)
            except error.GremlinError as err:
                logging.exception(str(err))
                raise err
        self.always_execute.setChecked(self.item_profile.always_execute)
        self._description_field.setText(self.item_profile.description)

    def to_profile(self):
        """Updates all action items associated with this input item."""
        for widget in self.action_widgets:
            widget.to_profile()
        self.item_profile.always_execute = self.always_execute.isChecked()
        self.item_profile.description = self._description_field.text()

    def _create_description(self):
        """Creates the description input for the input item."""
        self._description_layout = QtWidgets.QHBoxLayout()
        self._description_layout.addWidget(
            QtWidgets.QLabel("<b>Description</b>")
        )
        self._description_field = QtWidgets.QLineEdit()
        self._description_field.textChanged.connect(self.to_profile)
        self._description_layout.addWidget(self._description_field)

        self.main_layout.addLayout(self._description_layout)

    def _create_action_dropdown(self):
        """Creates a drop down selection with actions that can be
        added to the current input item.
        """
        self.action_layout = QtWidgets.QHBoxLayout()
        self.action_dropdown = QtWidgets.QComboBox()
        for name in self._valid_action_list():
            self.action_dropdown.addItem(name)
        self.action_dropdown.setCurrentText("Remap")
        self.action_layout.addWidget(self.action_dropdown)
        self.add_action_button = QtWidgets.QPushButton("Add")
        self.add_action_button.clicked.connect(self._add_action)
        self.action_layout.addWidget(self.add_action_button)
        self.action_layout.addStretch()
        self.always_execute = QtWidgets.QCheckBox("Always execute")
        self.always_execute.stateChanged.connect(self.to_profile)
        self.action_layout.addWidget(self.always_execute)
        self.main_layout.addLayout(self.action_layout)

    def _valid_action_list(self):
        """Returns a list of valid actions for this InputItemWidget.

        :return list of valid action names
        """
        action_list = []
        for entry in profile.action_lookup.values():
            if self.item_profile.input_type in entry.input_types:
                action_list.append(entry.name)
        return sorted(action_list)


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


class DeviceTabWidget(QtWidgets.QWidget):

    """Represents the content of a tab representing a single device."""

    def __init__(
            self,
            vjoy_devices,
            phys_device,
            device_profile,
            current_mode,
            parent=None
    ):
        QtWidgets.QWidget.__init__(self, parent)

        # Store parameters
        self.device_profile = device_profile

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.input_item_list = InputItemList(
            phys_device,
            device_profile,
            current_mode
        )
        self.configuration_panel = ConfigurationPanel(
            vjoy_devices,
            phys_device,
            device_profile,
            current_mode
        )
        self.input_item_list.input_item_selected.connect(
            self.configuration_panel.refresh
        )
        self.configuration_panel.input_item_changed.connect(
            self.input_item_list.input_item_changed_cb
        )

        self.main_layout.addWidget(self.input_item_list)
        self.main_layout.addWidget(self.configuration_panel)


class InputItemList(QtWidgets.QWidget):

    """Widget responsible for displaying a list of inputs with their
    currently configured action types.
    """

    # Signal emitted when a button has been selected, contains button
    # identifier as well as the mode
    input_item_selected = QtCore.pyqtSignal(InputIdentifier, str)

    # Button background palettes
    cur_palette = QtGui.QPalette()
    cur_palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)

    def __init__(
            self,
            phys_device,
            device_profile,
            current_mode,
            parent=None
    ):
        """Creates a new instance.

        :param phys_device the physical device the list represents
        :param device_profile the profile used to describe the device
        :param current_mode the currently active mode
        :parent the parent of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        # Input item button storage
        self.input_items = {
            UiInputType.JoystickAxis: {},
            UiInputType.JoystickButton: {},
            UiInputType.JoystickHat: {},
            UiInputType.Keyboard: {}
        }

        # Store parameters
        self.phys_device = phys_device
        self.device_profile = device_profile
        self.current_mode = current_mode
        self.current_identifier = None

        # Create required UI items
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout()

        # Configure the widget holding the layout with all the buttons
        self.scroll_widget.setMaximumWidth(350)
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        # Configure the scroll area
        self.scroll_area.setMinimumWidth(300)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

        # If this is the keyboard tab add the button needed to add
        # new keys.
        if self.device_profile.type == profile.DeviceType.Keyboard:
            self.key_add_button = QtWidgets.QPushButton("Add Key")
            self.key_add_button.clicked.connect(self._add_new_key)
            self.main_layout.addWidget(self.key_add_button)

        self._populate_item_list()

    def mode_changed_cb(self, new_mode):
        """Executed when the mode changes.

        :param new_mode the name of the new mode
        """
        self.current_mode = new_mode

        self._populate_item_list()
        if self.current_identifier:
            self._input_item_selection(self.current_identifier)

    def input_item_changed_cb(self, identifier):
        """Executed when the actions associated with an item change.

        :param identifier identification for the item that changed
        """
        input_type = identifier.input_type
        input_id = identifier.input_id

        # If this is a keyboard check if we need to remove the key
        if self.device_profile.type == profile.DeviceType.Keyboard:
            assert(input_type == UiInputType.Keyboard)

            self._populate_item_list()
            if self.current_identifier and self.current_identifier.input_id in self.input_items[UiInputType.Keyboard]:
                item = self.input_items[UiInputType.Keyboard][self.current_identifier.input_id]
                item.setAutoFillBackground(True)
                item.setPalette(self.cur_palette)

            if input_id in self.input_items[input_type]:
                self.input_items[input_type][input_id].create_action_icons(
                    self.device_profile.modes[self.current_mode].get_data(
                        input_type,
                        input_id
                    )
                )

        # Joystick input item entries are never removed
        else:
            self.input_items[input_type][input_id].create_action_icons(
                self.device_profile.modes[self.current_mode].get_data(
                    identifier.input_type,
                    identifier.input_id
                )
            )

    def _populate_item_list(self):
        """Populates the widget with all required items."""
        # Remove existing content
        _clear_layout(self.scroll_layout)
        self.input_items = {
            UiInputType.JoystickAxis: {},
            UiInputType.JoystickButton: {},
            UiInputType.JoystickHat: {},
            UiInputType.Keyboard: {}
        }

        # Bail if the current mode is invalid
        if self.current_mode is None:
            return

        if self.device_profile.type == profile.DeviceType.Keyboard:
            self._populate_keyboard()
        else:
            self._populate_joystick()

        self.scroll_layout.addStretch()

    def _populate_joystick(self):
        """Handles generating the items for a joystick device."""
        input_counts = [
            (UiInputType.JoystickAxis, self.phys_device.axes),
            (UiInputType.JoystickButton, self.phys_device.buttons),
            (UiInputType.JoystickHat, self.phys_device.hats)
        ]

        # Create items for each of the inputs on the device
        for input_type, count in input_counts:
            for i in range(1, count + 1):
                item = InputItemButton(
                    i,
                    InputIdentifier(
                        input_type,
                        i,
                        self.device_profile.type
                    ),
                    self
                )

                item.create_action_icons(
                    self.device_profile.modes[self.current_mode].get_data(
                        input_type,
                        i
                    )
                )
                item.input_item_clicked.connect(
                    self._input_item_selection
                )
                self.input_items[input_type][i] = item
                self.scroll_layout.addWidget(item)

    def _populate_keyboard(self):
        """Handles generating the items for the keyboard."""
        # Add existing keys to the scroll
        mode = self.device_profile.modes[self.current_mode]
        key_dict = {}
        for key, entry in mode._config[UiInputType.Keyboard].items():
            key_dict[macro.key_from_code(key[0], key[1]).name] = entry

        for key_string in sorted(key_dict.keys()):
            # Create the input item
            entry = key_dict[key_string]
            key_code = (entry.input_id[0], entry.input_id[1])
            key = macro.key_from_code(key_code[0], key_code[1])
            item = InputItemButton(
                key.name,
                InputIdentifier(
                    UiInputType.Keyboard,
                    key_code,
                    self.device_profile.type
                ),
                self
            )
            item.create_action_icons(entry)
            item.input_item_clicked.connect(self._input_item_selection)
            # Add the new item to the panel
            self.input_items[UiInputType.Keyboard][key_code] = item
            self.scroll_layout.addWidget(item)

    def _input_item_selection(self, identifier):
        """Selects the item specified by the input type and label..

        This is a callback called when the user clicks on a different
        input item in the ui. Delegates the loading of the
        configuration dialog for the selected input item.

        :param identifier the input item identifier
        """
        # If the current mode is not specified don't do anything
        if self.current_mode is None:
            return

        # Store the newly selected input item
        self.current_identifier = identifier

        # Deselect all input item entries
        for axis_id, axis in self.input_items[UiInputType.JoystickAxis].items():
            axis.setPalette(self.palette())
        for btn_id, button in self.input_items[UiInputType.JoystickButton].items():
            button.setPalette(self.palette())
        for hat_id, hat in self.input_items[UiInputType.JoystickHat].items():
            hat.setPalette(self.palette())
        for key_id, key in self.input_items[UiInputType.Keyboard].items():
            key.setPalette(self.palette())

        # Highlight selected button
        if identifier.input_id in self.input_items[identifier.input_type]:
            item = self.input_items[identifier.input_type][identifier.input_id]
            item.setAutoFillBackground(True)
            item.setPalette(self.cur_palette)
        else:
            self.current_identifier = None

        # Load the correct detail content for the newly selected
        # input item
        if identifier.input_id in self.input_items[identifier.input_type]:
            self.input_item_selected.emit(identifier, self.current_mode)
        else:
            self.current_identifier = None
            self.current_configuration_dialog = None

    def _add_new_key(self):
        """Displays the screen overlay prompting the user to press a
        key which will then be added.
        """
        self.keyboard_press_dialog = InputListenerWidget(
            self._add_key_to_scroll_list_cb,
            True,
            False
        )

        # Display the dialog centered in the middle of the UI
        geom = self.geometry()
        point = self.mapToGlobal(QtCore.QPoint(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
        ))
        self.keyboard_press_dialog.setGeometry(
            point.x(),
            point.y(),
            300,
            150
        )
        self.keyboard_press_dialog.show()

    def _add_key_to_scroll_list_cb(self, key):
        """Adds the key pressed by the user to the list of keyboard
        keys."""
        # Add the new key to the profile if it is valid
        if key is None:
            return

        key_pair = (key.scan_code, key.is_extended)
        # Special handling of the right shift key due to Qt and windows
        # discrepancies in key code representation
        if key == macro.Keys.RShift2:
            key_pair = (key.scan_code, False)

        # Grab the profile entry which creates one if it doesn't exist
        # yet
        self.device_profile.modes[self.current_mode].get_data(
            UiInputType.Keyboard,
            key_pair
        )

        # Recreate the entire UI to have the button show up
        self._populate_item_list()
        self._input_item_selection(InputIdentifier(
            UiInputType.Keyboard,
            key_pair,
            profile.DeviceType.Keyboard
        ))


class ConfigurationPanel(QtWidgets.QWidget):

    """Widget which allows configuration of actions for input items."""

    # Signal emitted when the configuration has changed
    input_item_changed = QtCore.pyqtSignal(InputIdentifier)

    def __init__(
            self,
            vjoy_devices,
            phys_device,
            device_profile,
            current_mode,
            parent=None
    ):
        """Creates a new instance.

        :param vjoy_devices the vjoy devices present in the system
        :param phys_device the physical device being configured
        :param device_profile the profile of the device
        :param current_mode the currently active mode
        :param parent the parent of this widdget
        """
        QtWidgets.QWidget.__init__(self, parent)

        # Store parameters
        self.vjoy_devices = vjoy_devices
        self.phys_device = phys_device
        self.device_profile = device_profile
        self.current_mode = current_mode

        # Storage for the current configuration panel
        self.current_configuration_dialog = None
        self.current_identifier = None

        # Create required UI items
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.configuration_scroll = QtWidgets.QScrollArea()
        self.configuration_widget = QtWidgets.QWidget()
        self.configuration_layout = QtWidgets.QVBoxLayout()

        # Main widget within the scroll area which contains the
        # layout with the actual content
        self.configuration_widget.setMinimumWidth(500)
        self.configuration_widget.setLayout(self.configuration_layout)

        # Scroll area configuration
        self.configuration_scroll.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Minimum
        ))
        self.configuration_scroll.setMinimumWidth(525)
        self.configuration_scroll.setWidget(self.configuration_widget)
        self.configuration_scroll.setWidgetResizable(True)

        # Add scroll area to the main layout
        self.main_layout.addWidget(self.configuration_scroll)

    def refresh(self, identifier, mode_name):
        """Redraws the entire configuration dialog for the given item.

        :param identifier the identifier of the item for which to
                redraw the widget
        """
        self.current_mode = mode_name
        self._remove_invalid_actions_and_inputs()

        # Create InputItemConfigurationPanel object and hook
        # it's signals up
        self.current_configuration_dialog = InputItemConfigurationPanel(
            self.vjoy_devices,
            self.device_profile.modes[self.current_mode].get_data(
                identifier.input_type,
                identifier.input_id
            )
        )
        self.current_configuration_dialog.changed.connect(
            self._input_item_content_changed_cb
        )
        self.current_identifier = identifier

        # Visualize the dialog
        _clear_layout(self.configuration_layout)
        self.configuration_layout.addWidget(
            self.current_configuration_dialog
        )
        self.configuration_layout.addStretch(0)

    def mode_changed_cb(self, new_mode):
        """Executed when the mode changes.

        :param new_mode the name of the new mode
        """
        # Cleanup the content of the previous mode before we switch
        self._remove_invalid_actions_and_inputs()

        # Save new mode
        self.current_mode = new_mode

        # Select previous selection if it exists
        if self.current_identifier is not None:
            self.refresh(self.current_identifier, new_mode)

    def _remove_invalid_actions_and_inputs(self):
        """Perform maintenance on the previously selected item.

        This removes invalid actions and deletes keys without any
        associated actions.
        """
        if self.current_configuration_dialog is not None:
            # Remove actions that have not been properly configured
            item_profile = self.current_configuration_dialog.item_profile
            items_to_delete = []
            for entry in item_profile.actions:
                if not entry.is_valid:
                    items_to_delete.append(entry)
            for entry in items_to_delete:
                item_profile.actions.remove(entry)

            if len(items_to_delete) > 0:
                self.input_item_changed.emit(self.current_identifier)

            # Delete the previously selected item if it contains no
            # action and we're on the keyboard tab. However, only do
            # this if the mode of the configuration dialog and the mode
            # match.
            if self.device_profile.type == profile.DeviceType.Keyboard:
                if (item_profile.parent.name == self.current_mode) and \
                    len(item_profile.actions) == 0:
                    self.device_profile.modes[self.current_mode].delete_data(
                        UiInputType.Keyboard,
                        item_profile.input_id
                    )
                    self.input_item_changed.emit(self.current_identifier)

    def _input_item_content_changed_cb(self):
        """Updates the profile data of an input item when its contents
        change."""
        assert(self.current_identifier is not None)
        assert(self.current_mode in self.device_profile.modes)

        self.current_configuration_dialog.to_profile()
        self.input_item_changed.emit(self.current_identifier)


def _clear_layout(layout):
    """Removes all items from the given layout.

    :param layout the layout from which to remove all items
    """
    while layout.count() > 0:
        child = layout.takeAt(0)
        if child.layout():
            _clear_layout(child.layout())
        elif child.widget():
            child.widget().hide()
            child.widget().deleteLater()
        layout.removeItem(child)
