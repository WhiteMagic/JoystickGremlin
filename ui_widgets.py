"""
Collection of widgets used in the configuration UI.
"""


import logging
from PyQt5 import QtCore, QtGui, QtWidgets

import action.common
from gremlin import common, error, macro, profile
from gremlin.event_handler import EventListener
from gremlin.common import UiInputType


class KeystrokeListenerWidget(QtWidgets.QFrame):

    """Widget overlaying the main gui while waiting for the user
    to press a key."""

    def __init__(self, callback, parent=None):
        """Creates a new instance.

        :param callback the function to pass the key pressed by the
            user to
        :param parent the parent widget of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.callback = callback

        # Create and configure the ui overlay
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel(
            """<center>Please press the key you want to add.
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
        event_listener.keyboard_event.connect(self._kb_event_cb)

    def _kb_event_cb(self, event):
        """Passes the pressed key to the provided callback and closes
        the overlay.

        :param event the keypress event to be processed
        """
        key = macro.key_from_code(event.identifier[0], event.identifier[1])
        if key != macro.Keys.Esc:
            self.callback(key)
        self._close_window()

    def _close_window(self):
        """Closes the overlay window."""
        event_listener = EventListener()
        event_listener.keyboard_event.disconnect(self._kb_event_cb)
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


class InputItemButton(QtWidgets.QFrame):

    """Creates a button like widget which emits an event when pressed.

    This event can be used to display input item specific customization
    widgets. This button also shows icons of the associated actions.
    """

    # Signal emitted whenever this button is pressed
    input_item_changed = QtCore.pyqtSignal(UiInputType, str)

    def __init__(self, item_label, item_type, parent=None):
        """Creates a new instance.

        :param item_label the id of the input item
        :param item_type the type of the input item, i.e. axis, button or hat
        :param parent the parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)
        self.item_type = item_type
        self.item_label = str(item_label)
        self._icons = []

        self.setFrameShape(QtWidgets.QFrame.Box)
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel(self._create_label()))
        self.main_layout.addStretch(0)
        self.setMinimumSize(100, 40)

    def set_labels(self, profile_data):
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
            icon = QtWidgets.QLabel()
            icon.setPixmap(QtGui.QPixmap(entry.icon))
            self.main_layout.addWidget(icon)

    def mousePressEvent(self, event):
        """Emits the input_item_changed event when this instance is
        clicked on by the mouse.

        :param event the mouse event
        """
        self.input_item_changed.emit(self.item_type, self.item_label)

    def _create_label(self):
        """Creates the label to display on this button.

        :return label to use for this button
        """
        type_name = common.ui_input_type_to_name(self.item_type)
        label = self.item_label
        if self.item_type == UiInputType.JoystickHatDirection:
            input_id = int(int(self.item_label) / 10)
            direction = int(int(self.item_label) % 10)
            label = "{} {}".format(
                input_id,
                common.index_to_direction(direction)
            )
        return "{} {}".format(type_name, label)


class ConditionWidget(QtWidgets.QWidget):

    """Widget allowing the configuration of the activation condition
    of actions."""

    def __init__(self, change_cb, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.change_cb = change_cb
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(QtWidgets.QLabel("Activate on"))
        self.press = QtWidgets.QCheckBox("press")
        self.press.stateChanged.connect(self.change_cb)
        self.release = QtWidgets.QCheckBox("release")
        self.release.stateChanged.connect(self.change_cb)
        self.main_layout.addWidget(self.press)
        self.main_layout.addWidget(self.release)

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
        if self._is_button_like():
            self.condition = ConditionWidget(self.to_profile)
            self._set_conditions()
            self.main_layout.addWidget(self.condition)

        self.main_layout.addWidget(self.action_widget)
        self.setWidget(self.main_widget)

    def to_profile(self):
        """Updates the profile data associated with the widget with
        the UI contents."""
        self.action_widget.to_profile()
        if self._is_button_like():
            self.action_widget.action_data.condition =\
                action.common.ButtonCondition(
                    self.condition.press.isChecked(),
                    self.condition.release.isChecked()
                )

    def _set_conditions(self):
        condition = self.action_widget.action_data.condition
        if self._is_button_like():
            self.condition.press.setChecked(condition.on_press)
            self.condition.release.setChecked(condition.on_release)

    def closeEvent(self, event):
        """Emits the closed event when this widget is being closed.

        :param event the close event details
        """
        QtWidgets.QDockWidget.closeEvent(self, event)
        self.closed.emit(self)

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


class InputItemWidget(QtWidgets.QFrame):

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

        # Filter the mode names such that they only occur once below their
        # correct parent
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

        # Reconnect change signal
        self.selector.currentIndexChanged.connect(self._mode_changed_cb)

        # Select currently active mode
        if len(mode_names) > 0:
            if current_mode is None:
                current_mode = mode_names[0]
            self.selector.setCurrentIndex(self.mode_list.index(current_mode))
            self._mode_changed_cb(self.mode_list.index(current_mode))

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


class DeviceWidget(QtWidgets.QWidget):

    """Displays a single device configuration."""

    cur_palette = QtGui.QPalette()
    cur_palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)

    def __init__(self, vjoy_devices, device_data, device_profile, current_mode, parent=None):
        """Creates a new DeviceWidget object.

        :param vjoy_devices list of vjoy devices
        :param device_data information about the physical device
            represented by this widget
        :param device_profile the profile data associated with this
            device
        :param current_mode the currently active mode
        :param parent the parent widget of this object
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.device_data = device_data
        self.device_profile = device_profile
        self.vjoy_devices = vjoy_devices

        self.input_items = {
            UiInputType.JoystickAxis: {},
            UiInputType.JoystickButton: {},
            UiInputType.JoystickHat: {},
            UiInputType.JoystickHatDirection: {},
            UiInputType.Keyboard: {}
        }

        self.current_mode = current_mode
        self.current_selection = None
        self.current_configuration_dialog = None

        # Create ui
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self._create_ui()

    def _input_item_selection(self, input_type, input_label):
        """Selects the item specified by the input type and label..

        This is a callback called when the user clicks on a different
        input item in the ui.
        Delegates the loading of the configuration dialog for the
        selected input item.

        :param input_type the type of the input item
        :param input_label the id of the input item
        """
        # If the current mode is not specified don't do anything
        if self.current_mode is None:
            return

        # Convert the input_label to an id usable as a lookup key
        if input_type == UiInputType.Keyboard:
            assert(isinstance(input_label, str))
            key = macro.key_from_name(input_label)
            input_id = (key.scan_code, key.is_extended)
        else:
            input_id = int(input_label)

        # Perform maintenance on the previously selected item, i.e.
        # removing invalid actions and deleting keys without any
        # associated actions.
        if self.current_configuration_dialog is not None:
            item_profile = self.current_configuration_dialog.item_profile
            items_to_delete = []
            for entry in item_profile.actions:
                if not entry.is_valid:
                    items_to_delete.append(entry)
            for entry in items_to_delete:
                item_profile.actions.remove(entry)
            if self.current_selection is not None:
                self.input_items[self.current_selection[0]]\
                    [self.current_selection[1]].set_labels(item_profile)

            # Delete the previously selected item if it contains no
            # action and we're on the keyboard tab
            if self.device_profile.type == profile.DeviceType.Keyboard:
                if len(item_profile.actions) == 0:
                    self._remove_keyboard_input_item_button(item_profile)

        # Store the newly selected input item
        self.current_selection = (input_type, input_id)

        # Deselect all input item entries
        for axis_id, axis in self.input_items[UiInputType.JoystickAxis].items():
            axis.setPalette(self.palette())
        for btn_id, button in self.input_items[UiInputType.JoystickButton].items():
            button.setPalette(self.palette())
        for hat_id, hat in self.input_items[UiInputType.JoystickHat].items():
            hat.setPalette(self.palette())
        for hat_dir_id, hat_dir in self.input_items[UiInputType.JoystickHatDirection].items():
            hat_dir.setPalette(self.palette())
        for key_id, key in self.input_items[UiInputType.Keyboard].items():
            key.setPalette(self.palette())

        # Load the correct detail content for the newly selected
        # input item
        if input_id in self.input_items[input_type]:
            self._prepare_configuration_panel(input_type, input_id)
        else:
            self.current_selection = None
            self.current_configuration_dialog = None

    def change_mode(self, name):
        """Update the currently selected mode when it is changed.

        :param name the name of the new mode
        """
        self.current_mode = name
        self.input_items = {
            UiInputType.JoystickAxis: {},
            UiInputType.JoystickButton: {},
            UiInputType.JoystickHat: {},
            UiInputType.JoystickHatDirection: {},
            UiInputType.Keyboard: {}
        }
        self._create_ui()

        # Reselect the previous selection if there was one
        if self.current_selection:
            self._input_item_selection(
                self.current_selection[0],
                self.current_selection[1]
            )

    def _create_ui(self):
        """Clears the main layout of existing contents and initializes
        the UI from scratch."""
        _clear_layout(self.main_layout)

        self.overview_layout = QtWidgets.QVBoxLayout()
        self._create_input_item_scroll()
        self._create_configuration_panel()

    def _prepare_configuration_panel(self, input_type, input_label):
        """Prepares the configuration panel for the selected input type.

        :param input_type type of input that has been selected
        :param input_label the id of the specific input item
        """
        # Convert the input_label to an id usable as a lookup key
        if input_type == UiInputType.Keyboard:
            assert(isinstance(input_label, tuple))
            key = macro.key_from_code(input_label[0], input_label[1])
            input_id = (key.scan_code, key.is_extended)
        else:
            input_id = int(input_label)

        # Highlight selected button
        item = self.input_items[input_type][input_id]
        item.setAutoFillBackground(True)
        item.setPalette(self.cur_palette)

        # Remove all items from self.configuration_layout
        self.configuration_layout = QtWidgets.QVBoxLayout()
        self.configuration_widget = QtWidgets.QWidget()
        self.configuration_widget.setLayout(self.configuration_layout)
        self.configuration_scroll.setWidget(self.configuration_widget)

        # Create ButtonWidget object and hook it's signals up
        self.current_configuration_dialog = InputItemWidget(
            self.vjoy_devices,
            self.device_profile.modes[self.current_mode].get_data(
                input_type,
                input_id
            )
        )

        # Connect callback for changes in input items
        self.current_configuration_dialog.changed.connect(
            self._input_item_content_changed_cb
        )

        # Add ButtonWidget object to self.configuration_layout
        self.configuration_layout.addWidget(
            self.current_configuration_dialog
        )
        self.configuration_layout.addStretch(0)

    def _input_item_content_changed_cb(self):
        """Updates the profile data of an input item when it's contents
        change."""
        assert(self.current_selection is not None)
        assert(self.current_mode in self.device_profile.modes)

        self.current_configuration_dialog.to_profile()
        item = self.device_profile.modes[self.current_mode].get_data(
            self.current_selection[0],
            self.current_selection[1]
        )

        self.input_items[self.current_selection[0]]\
            [self.current_selection[1]].set_labels(item)

    def _create_input_item_scroll(self):
        """Creates the panel showing all the inputs available on a
        given device.
        """
        # Populate with input items
        self.input_item_layout = QtWidgets.QVBoxLayout()

        # Populate with all joystick inputs available
        if self.device_profile.type == profile.DeviceType.Joystick:
            input_counts = [
                (UiInputType.JoystickAxis, self.device_data.axes),
                (UiInputType.JoystickButton, self.device_data.buttons),
                (UiInputType.JoystickHat, self.device_data.hats)
            ]

            for input_type, count in input_counts:
                for i in range(1, count+1):
                    item = InputItemButton(i, input_type, self)
                    if self.current_mode is not None:
                        item.set_labels(
                            self.device_profile.modes[self.current_mode].get_data(
                                input_type,
                                i
                            )
                        )
                    item.input_item_changed.connect(self._input_item_selection)
                    self.input_items[input_type][i] = item
                    self.input_item_layout.addWidget(item)

                    # Add hat direction specific items
                    if input_type == UiInputType.JoystickHat:
                        for j in range(1, 9):
                            input_id = i*10 + j
                            item = InputItemButton(
                                input_id,
                                UiInputType.JoystickHatDirection,
                                self
                            )
                            if self.current_mode is not None:
                                item.set_labels(
                                    self.device_profile.modes[self.current_mode].get_data(
                                        UiInputType.JoystickHatDirection,
                                        input_id
                                    )
                                )
                            item.input_item_changed.connect(
                                self._input_item_selection
                            )
                            self.input_items[UiInputType.JoystickHatDirection][input_id] = item
                            self.input_item_layout.addWidget(item)

        # Populate with configured keyboard inputs
        elif self.device_profile.type == profile.DeviceType.Keyboard:
            if self.current_mode is not None:
                # Add existing keys to the scroll
                mode = self.device_profile.modes[self.current_mode]
                key_dict = {}
                for key, entry in mode._config[UiInputType.Keyboard].items():
                    key_dict[macro.key_from_code(key[0], key[1]).name] = entry
                for key in sorted(key_dict.keys()):
                    entry = key_dict[key]
                    key_code = (entry.input_id[0], entry.input_id[1])
                    key = macro.key_from_code(key_code[0], key_code[1])
                    item = InputItemButton(key.name, UiInputType.Keyboard, self)
                    item.set_labels(entry)
                    item.input_item_changed.connect(self._input_item_selection)
                    self.input_items[UiInputType.Keyboard][key_code] = item
                    self.input_item_layout.addWidget(item)

        # Encountered some other type which should never occur
        else:
            raise error.GremlinError(" Invalid device type encountered")

        # Create widget to display input items in
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_widget.setMinimumWidth(350)
        self.scroll_widget.setLayout(self.input_item_layout)

        # Display widget inside a scroll area
        self.input_item_scroll = QtWidgets.QScrollArea()
        self.input_item_scroll.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        ))
        self.input_item_scroll.setMinimumWidth(375)
        self.input_item_scroll.setWidget(self.scroll_widget)

        # Add scroll area to main layout
        self.overview_layout.addWidget(self.input_item_scroll)
        self.main_layout.addLayout(self.overview_layout)

        if self.device_profile.type == profile.DeviceType.Keyboard:
            # Add a button that allows adding new keys
            new_key_button = QtWidgets.QPushButton("Add Key")
            new_key_button.clicked.connect(self._add_new_key)
            self.overview_layout.addWidget(new_key_button)

    def _create_configuration_panel(self):
        """Creates the panel which will show input item specific
        configuration options.
        """
        # Layout which will contain all the actual widgets we want to display
        self.configuration_layout = QtWidgets.QVBoxLayout()

        # Main widget within the scroll area which contains the actual layout
        self.configuration_widget = QtWidgets.QWidget()
        self.configuration_widget.setMinimumWidth(500)
        self.configuration_widget.setLayout(self.configuration_layout)

        # Scroll area configuration
        self.configuration_scroll = QtWidgets.QScrollArea()
        self.configuration_scroll.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Minimum
        ))
        self.configuration_scroll.setMinimumWidth(525)
        self.configuration_scroll.setWidget(self.configuration_widget)
        self.configuration_scroll.setWidgetResizable(True)

        # Add scroll area to the main layout
        self.main_layout.addWidget(self.configuration_scroll)

    def _add_new_key(self):
        """Displays the screen overlay prompting the user to press a
        key which will then be added.
        """
        self.keyboard_press_dialog = KeystrokeListenerWidget(
            self._add_key_to_scroll_list_cb
        )
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
        key_pair = (key.scan_code, key.is_extended)
        input_item = profile.InputItem(
            self.device_profile.modes[self.current_mode]
        )
        input_item.input_type = UiInputType.Keyboard
        input_item.input_id = key_pair
        self.device_profile.modes[self.current_mode].get_data(
            UiInputType.Keyboard,
            key_pair
        )

        self._create_ui()
        self.current_selection = (UiInputType.Keyboard, key_pair)
        self._prepare_configuration_panel(
            UiInputType.Keyboard, key_pair
        )

    def _remove_keyboard_input_item_button(self, item_profile):
        """Removes an input item selection button from the keyboard
        list.

        :param item_profile the profile of the key to remove
        """
        self.device_profile.modes[self.current_mode].delete_data(
            UiInputType.Keyboard,
            item_profile.input_id
        )

        layout_index = self.input_item_layout.indexOf(
            self.input_items[item_profile.input_type][item_profile.input_id]
        )
        layout_item = self.input_item_layout.itemAt(layout_index)
        layout_item.widget().deleteLater()
        self.input_item_layout.removeItem(layout_item)
        del self.input_items[item_profile.input_type][item_profile.input_id]
        self.input_item_layout.addStretch()


def _clear_layout(layout):
    """Removes all items from the given layout.

    :param layout the layout from which to remove all items
    """
    while layout.count() > 0:
        child = layout.takeAt(0)
        if child.layout():
            _clear_layout(child.layout())
        elif child.widget():
            child.widget().deleteLater()
        layout.removeItem(child)
