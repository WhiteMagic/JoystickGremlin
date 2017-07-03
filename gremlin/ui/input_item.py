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

import enum
from PyQt5 import QtWidgets, QtCore, QtGui

import gremlin
from gremlin.common import DeviceType, InputType
from . import activation_condition, common


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


class InputItemListModel(common.AbstractModel):

    """Model storing a device's input item list."""

    def __init__(self, device_data, mode):
        """Creates a new instance.

        :param device_data the profile data managed by this model
        :param mode the mode this model manages
        """
        super().__init__()
        self._device_data = device_data
        self._mode = mode

    @property
    def mode(self):
        """Returns the mode handled by this model.

        :return the mode managed by the model
        """
        return self._mode

    @mode.setter
    def mode(self, mode):
        """Sets the mode managed by the model.

        :param mode the mode handled by the model
        """
        self._mode = mode
        self.data_changed.emit()

    def rows(self):
        """Returns the number of rows in the model.

        :return number of rows in the model
        """
        input_items = self._device_data.modes[self._mode]
        return len(input_items.config[InputType.JoystickAxis]) + \
            len(input_items.config[InputType.JoystickButton]) + \
            len(input_items.config[InputType.JoystickHat]) + \
            len(input_items.config[InputType.Keyboard])

    def data(self, index):
        """Returns the data stored at the provided index.

        :param index the index for which to return the data
        :return data stored at the provided index
        """
        input_items = self._device_data.modes[self._mode]
        axis_count = len(input_items.config[InputType.JoystickAxis])
        button_count = len(input_items.config[InputType.JoystickButton])
        hat_count = len(input_items.config[InputType.JoystickHat])
        key_count = len(input_items.config[InputType.Keyboard])

        if key_count > 0:
            sorted_keys = sorted(input_items.config[InputType.Keyboard].keys())
            return input_items.config[InputType.Keyboard][sorted_keys[index]]
        else:
            if index < axis_count:
                # Handle non continuous axis setups
                axis_keys = sorted(
                    input_items.config[InputType.JoystickAxis].keys()
                )
                return input_items.config[InputType.JoystickAxis][
                    axis_keys[index]
                ]
            elif index < axis_count + button_count:
                return input_items.config[InputType.JoystickButton][
                    index - axis_count + 1
                ]
            elif index < axis_count + button_count + hat_count:
                return input_items.config[InputType.JoystickHat][
                    index - axis_count - button_count + 1
                ]

    def event_to_index(self, event):
        """Converts an event to a model index.

        :param event the event to convert
        :return index corresponding to the event's input
        """
        input_items = self._device_data.modes[self._mode]
        offset_map = dict()
        offset_map[InputType.Keyboard] = 0
        offset_map[InputType.JoystickAxis] =\
            len(input_items.config[InputType.Keyboard])
        offset_map[InputType.JoystickButton] = \
            offset_map[InputType.JoystickAxis] + \
            len(input_items.config[InputType.JoystickAxis])
        offset_map[InputType.JoystickHat] = \
            offset_map[InputType.JoystickButton] + \
            len(input_items.config[InputType.JoystickButton])

        return offset_map[event.event_type] + event.identifier - 1


class InputItemListView(common.AbstractView):

    """View displaying the contents of an InputItemListModel."""

    # Conversion from input type to a display name
    type_to_string = {
        InputType.JoystickAxis: "Axis",
        InputType.JoystickButton: "Button",
        InputType.JoystickHat: "Hat",
        InputType.Keyboard: ""
    }

    def __init__(self, parent=None):
        """Creates a new view instance.

        :param parent the parent of the widget
        """
        super().__init__(parent)

        self.shown_input_types = [
            InputType.JoystickAxis,
            InputType.JoystickButton,
            InputType.JoystickHat,
            InputType.Keyboard
        ]

        # Storage for the currently selected index
        self.current_index = None

        # Create required UI items
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout()

        # Configure the widget holding the layout with all the buttons
        self.scroll_widget.setLayout(self.scroll_layout)

        # Configure the scroll area
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

    def limit_input_types(self, types):
        """Limits the items shown to the given types.

        :param types list of input types to display
        """
        self.shown_input_types = types
        self.redraw()

    def redraw(self):
        """Redraws the entire model."""
        common.clear_layout(self.scroll_layout)

        if self.model is None:
            return

        for index in range(self.model.rows()):
            data = self.model.data(index)
            if data.input_type not in self.shown_input_types:
                continue
            label = str(data.input_id)
            if data.input_type == InputType.Keyboard:
                key = gremlin.macro.key_from_code(*data.input_id)
                label = key.name.capitalize()
            elif data.parent.parent.type == DeviceType.VJoy:
                assert(data.input_type == InputType.JoystickAxis)
                label = gremlin.common.vjoy_axis_names[data.input_id-1]
            identifier = InputIdentifier(
                data.input_type,
                data.input_id,
                data.parent.parent.type
            )
            widget = InputItemButton(label, identifier)
            widget.create_action_icons(data)
            widget.update_description(data.description)
            widget.selected.connect(self._create_selection_callback(index))
            self.scroll_layout.addWidget(widget)
        self.scroll_layout.addStretch()

    def redraw_index(self, index):
        """Redraws the view entry at the given index.

        :param index the index of the entry to redraw
        """
        if self.model is None:
            return

        data = self.model.data(index)
        widget = self.scroll_layout.itemAt(index).widget()
        widget.create_action_icons(data)
        widget.update_description(data.description)

    def _create_selection_callback(self, index):
        """Creates a callback handling the selection of items.

        :param index the index of the item to create the callback for
        :return callback to be triggered when the item at the provided index
            is selected
        """
        return lambda x: self.select_item(index)

    def select_item(self, index, emit_signal=True):
        """Handles selecting a specific item.

        :param index the index of the item being selected
        :param emit_signal flag indicating whether or not a signal is to be
            emitted when the item is being selected
        """
        if isinstance(index, gremlin.event_handler.Event):
            index = self.model.event_to_index(index)
        self.current_index = index

        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().setAutoFillBackground(False)
            if i == index:
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)
                item.widget().setAutoFillBackground(True)
                item.widget().setPalette(palette)

        if emit_signal:
            self.item_selected.emit(index)


class InputItemButton(QtWidgets.QFrame):

    """Creates a button like widget which emits an event when pressed.

    This event can be used to display input item specific customization
    widgets. This button also shows icons of the associated actions.
    """

    # Signal emitted whenever this button is pressed
    selected = QtCore.pyqtSignal(InputIdentifier)

    def __init__(self, label, identifier, parent=None):
        """Creates a new instance.

        :param label the label / number of the input item
        :param identifier identifying information about the button
        :param parent the parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)
        self.identifier = identifier
        self.label = str(label)

        self._label_widget = QtWidgets.QLabel(self._create_button_label())
        self._description_widget = QtWidgets.QLabel("")
        self._icon_layout = QtWidgets.QHBoxLayout()
        self._icons = []

        self.setFrameShape(QtWidgets.QFrame.Box)
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.addWidget(self._label_widget, 0, 0)
        self.main_layout.addWidget(self._description_widget, 0, 1)
        self.main_layout.addLayout(self._icon_layout, 0, 2)
        self.main_layout.setColumnMinimumWidth(0, 50)

        self.setMinimumWidth(300)

    def update_description(self, description):
        """Updates the description of the button.

        :param description the description to use
        """
        self._description_widget.setText("<i>{}</i>".format(description))

    def create_action_icons(self, profile_data):
        """Creates the label of this instance.

        Renders the text representing the instance's name as well as
        icons of actions associated with it.

        :param profile_data the profile.InputItem object associated
            with this instance
        """
        common.clear_layout(self._icon_layout)

        # Create the actual icons
        # FIXME: this currently ignores the containers themselves
        self._icon_layout.addStretch(1)
        for container in profile_data.containers:
            for action in container.actions:
                if action is not None:
                    self._icon_layout.addWidget(ActionLabel(action))

    def mousePressEvent(self, event):
        """Emits the input_item_changed event when this instance is
        clicked on by the mouse.

        :param event the mouse event
        """
        self.selected.emit(self.identifier)

    def _create_button_label(self):
        """Creates the label to display on this button.

        :return label to use for this button
        """
        return "{} {}".format(
            common.input_type_to_name[self.identifier.input_type],
            self.label
        )


class ActionLabel(QtWidgets.QLabel):

    """Handles showing the correct icon for the given action."""

    def __init__(self, action_entry, parent=None):
        """Creates a new label for the given entry.

        :param action_entry the entry to create the label for
        :param parent the parent
        """
        QtWidgets.QLabel.__init__(self, parent)
        self.setPixmap(QtGui.QPixmap(action_entry.icon()))


class ContainerSelector(QtWidgets.QWidget):

    """Allows the selection of a container type."""

    # Signal emitted when a container type is selected
    container_added = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """Creates a new selector instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.main_layout = QtWidgets.QHBoxLayout(self)

        self.container_dropdown = QtWidgets.QComboBox()
        for name in self._valid_container_list():
            self.container_dropdown.addItem(name)
        self.add_button = QtWidgets.QPushButton("Add")
        self.add_button.clicked.connect(self._add_container)

        self.main_layout.addWidget(self.container_dropdown)
        self.main_layout.addWidget(self.add_button)

    def _valid_container_list(self):
        """Returns a list of valid actions for this InputItemWidget.

        :return list of valid action names
        """
        container_list = []
        for entry in gremlin.plugin_manager.ContainerPlugins().repository.values():
            container_list.append(entry.name)
        return sorted(container_list)

    def _add_container(self, clicked=False):
        """Handles add button events.

        :param clicked flag indicating whether or not the button was pressed
        """
        self.container_added.emit(self.container_dropdown.currentText())


class AbstractContainerWidget(QtWidgets.QDockWidget):

    """Base class for container widgets."""

    # Signal which is emitted whenever the widget is closed
    closed = QtCore.pyqtSignal(QtWidgets.QWidget)

    # Signal which is emitted whenever the widget's contents change
    modified = QtCore.pyqtSignal()

    # Palette used to render widgets
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Background, QtCore.Qt.lightGray)

    # Maps activation condition data to activation condition widgets
    condition_to_widget = {
        gremlin.base_classes.AxisActivationCondition:
            gremlin.ui.activation_condition.AxisActivationConditionWidget,
        gremlin.base_classes.HatActivationCondition:
            gremlin.ui.activation_condition.HatActivationConditionWidget
    }

    def __init__(self, profile_data, parent=None):
        """Creates a new container widget object.

        :param profile_data the data the container handles
        :param parent the parent of the widget
        """
        assert isinstance(profile_data, gremlin.base_classes.AbstractContainer)
        super().__init__(parent)
        self.profile_data = profile_data
        self.action_widgets = []

        # Basic widget configuration
        self.setWindowTitle(self._get_window_title())
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)

        # Create root widget of the dock element
        self.dock_widget = QtWidgets.QWidget()
        self.dock_widget.setAutoFillBackground(True)
        self.dock_widget.setPalette(self.palette)
        self.setWidget(self.dock_widget)

        # Create layout and place it inside the dock widget
        self.main_layout = QtWidgets.QVBoxLayout(self.dock_widget)

        # Add condition widget
        self.activation_condition_widget = None
        if self.profile_data.activation_condition:
            self.activation_condition_widget = \
                AbstractContainerWidget.condition_to_widget[
                    type(self.profile_data.activation_condition)
                ](self.profile_data.activation_condition)
            self.main_layout.addWidget(self.activation_condition_widget)

        # Create the actual UI
        self._create_ui()

    def _get_widget_index(self, widget):
        """Returns the index of the provided widget.

        :param widget the widget for which to return the index
        :return the index of the provided widget, -1 if not present
        """
        index = -1
        for i, entry in enumerate(self.action_widgets):
            if entry.action_widget == widget:
                index = i
        return index

    def _add_action_widget(self, widget, label):
        """Adds an action widget to the container.

        :param widget the widget to be added
        :param label the label to show in the title
        :return wrapped widget
        """
        wrapped_widget = ActionWrapper(
            widget,
            label,
            self.profile_data.interaction_types
        )
        self.action_widgets.append(wrapped_widget)
        widget.modified.connect(lambda: self.modified.emit())
        wrapped_widget.interacted.connect(
            lambda x: self._handle_interaction(widget, x)
        )
        return wrapped_widget

    def closeEvent(self, event):
        """Emits the closed event when this widget is being closed.

        :param event the close event details
        """
        QtWidgets.QDockWidget.closeEvent(self, event)
        self.closed.emit(self)

    def _handle_interaction(self, widget, action):
        """Handles interaction with widgets inside the container.

        :param widget the widget on which the interaction is being carried out
        :param action the action being applied
        """
        raise gremlin.error.MissingImplementationError(
            "AbstractContainerWidget._handle_interaction not "
            "implemented in subclass"
        )

    def _create_ui(self):
        """Creates the UI elements for the widget."""
        raise gremlin.error.MissingImplementationError(
            "AbstractContainerWidget._create_ui not "
            "implemented in subclass"
        )

    def _get_window_title(self):
        """Returns the title to show on the widget."""
        return self.profile_data.name


class AbstractActionWidget(QtWidgets.QFrame):

    """Base class for all widgets representing actions from the profile
    module."""

    # Signal which is emitted whenever the widget's contents change
    modified = QtCore.pyqtSignal()

    def __init__(self, action_data, parent=None):
        """Creates a new instance.

        :param action_data the sub-classed AbstractAction instance
            associated with this specific action.
        :param parent parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)

        self.action_data = action_data

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self._create_ui()
        self._populate_ui()

    def _create_ui(self):
        """Creates all the elements necessary for the widget."""
        raise gremlin.error.MissingImplementationError(
            "AbstractActionWidget._create_ui not implemented in subclass"
        )

    def _populate_ui(self):
        """Updates this widget's representation based on the provided
        AbstractAction instance.
        """
        raise gremlin.error.MissingImplementationError(
            "ActionWidget._populate_ui not implemented in subclass"
        )

    def _get_input_type(self):
        """Returns the input type this widget's action is associated with.
        
        :return InputType corresponding to this action
        """
        return self.action_data.parent.parent.input_type

    def _get_profile_root(self):
        """Returns the root of the entire profile.
        
        :return root Profile instance
        """
        root = self.action_data
        while not isinstance(root, gremlin.profile.Profile):
            root = root.parent
        return root


class ActionWrapper(QtWidgets.QGroupBox):

    """Wraps the widget associated with a single action inside a container."""

    class Interactions(enum.Enum):
        """Enumeration of possible interactions."""
        Up = 1
        Down = 2
        Delete = 3
        Edit = 4
        Count = 5

    # Signal emitted when an interaction is triggered on an action
    interacted = QtCore.pyqtSignal(Interactions)

    def __init__(self, action_widget, label, allowed_interactions, parent=None):
        """Wraps an existing action widget.

        :param action_widget the action widget to wrap
        :param label the label of the action widget
        :param allowed_interactions list of allowed interaction types
        :param parent the parent of the widget
        """
        super().__init__(parent)
        self.action_widget = action_widget
        self._create_edit_controls(allowed_interactions)

        self.setTitle(label)

        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.addWidget(self.action_widget, 0, 0)
        self.main_layout.addLayout(self.controls_layout, 0, 1)
        self.main_layout.setColumnStretch(0, 2)
        # self.main_layout.setContentsMargins(0, 0, 0, 0)

    def _create_edit_controls(self, allowed_interactions):
        """Creates interaction controls based on the allowed interactions.

        :param allowed_interactions list of allowed interactions
        """
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.red)

        self.controls_layout = QtWidgets.QVBoxLayout()
        if ActionWrapper.Interactions.Up in allowed_interactions:
            self.control_move_up = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_up"), ""
            )
            self.control_move_up.clicked.connect(
                lambda: self.interacted.emit(ActionWrapper.Interactions.Up)
            )
            self.controls_layout.addWidget(self.control_move_up)
        if ActionWrapper.Interactions.Down in allowed_interactions:
            self.control_move_down = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_down"), ""
            )
            self.control_move_down.clicked.connect(
                lambda: self.interacted.emit(ActionWrapper.Interactions.Down)
            )
            self.controls_layout.addWidget(self.control_move_down)
        if ActionWrapper.Interactions.Delete in allowed_interactions:
            self.control_delete = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_delete"), ""
            )
            self.control_delete.clicked.connect(
                lambda: self.interacted.emit(ActionWrapper.Interactions.Delete)
            )
            self.controls_layout.addWidget(self.control_delete)
        if ActionWrapper.Interactions.Edit in allowed_interactions:
            self.control_edit = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_edit"), ""
            )
            self.control_edit.clicked.connect(
                lambda: self.interacted.emit(ActionWrapper.Interactions.Edit)
            )
            self.controls_layout.addWidget(self.control_edit)

        self.help_button = QtWidgets.QPushButton(QtGui.QIcon("gfx/help"), "")
        self.help_button.clicked.connect(self._show_hint)
        self.controls_layout.addWidget(self.help_button)

        self.controls_layout.addStretch(1)

    def _show_hint(self):
        """Displays a hint, explaining the purpose of the action."""
        QtWidgets.QWhatsThis.showText(
            self.help_button.mapToGlobal(QtCore.QPoint(0, 10)),
            gremlin.hints.hint.get(self.action_widget.action_data.tag, "")
        )
