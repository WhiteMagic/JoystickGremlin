# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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
import gremlin.common
import gremlin.types
from ..types import InputType, DeviceType
from . import activation_condition, common, virtual_button


# Cache storage for container tab selections
g_container_tab_state = common.ViewStateCache()


class InputIdentifier:

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

        if event.event_type == InputType.JoystickAxis:
            # Generate a mapping from axis index to linear axis index
            axis_index_to_linear_index = {}
            axis_keys = sorted(input_items.config[InputType.JoystickAxis].keys())
            for l_idx, a_idx in enumerate(axis_keys):
                axis_index_to_linear_index[a_idx] = l_idx

            return offset_map[event.event_type] + \
                   axis_index_to_linear_index[event.identifier]
        else:
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

            identifier = InputIdentifier(
                data.input_type,
                data.input_id,
                data.parent.parent.type
            )
            widget = InputItemButton(identifier)
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
        # If the index is actually an event we have to correctly translate the
        # event into an index, taking the possible non-contiguous nature of
        # axes into account
        if isinstance(index, gremlin.event_handler.Event):
            index = self.model.event_to_index(index)
        self.current_index = index

        # Go through all entries in the layout, deselecting those that are
        # actual widgets and selecting the previously selected one
        valid_index = False
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().setAutoFillBackground(False)
                if i == index:
                    palette = QtGui.QPalette()
                    palette.setColor(QtGui.QPalette.Background, QtCore.Qt.darkGray)
                    item.widget().setAutoFillBackground(True)
                    item.widget().setPalette(palette)
                    valid_index = True

        if emit_signal and valid_index:
            self.item_selected.emit(index)


class ActionSetModel(common.AbstractModel):

    """Model storing a set of actions."""

    def __init__(self, action_set=[]):
        super().__init__()
        self._action_set = action_set

    def rows(self):
        return len(self._action_set)

    def data(self, index):
        return self._action_set[index]

    def add_action(self, action):
        self._action_set.append(action)
        self.data_changed.emit()

    def remove_action(self, action):
        if action in self._action_set:
            del self._action_set[self._action_set.index(action)]
        self.data_changed.emit()


class ActionSetView(common.AbstractView):

    """View displaying the action set content."""

    class Interactions(enum.Enum):
        """Enumeration of possible interactions."""
        Up = 1
        Down = 2
        Delete = 3
        Edit = 4
        Add = 5
        Count = 6

    # Signal emitted when an interaction is triggered on an action
    interacted = QtCore.pyqtSignal(Interactions)

    def __init__(
            self,
            profile_data,
            label,
            view_type=common.ContainerViewTypes.Action,
            parent=None
    ):
        super().__init__(parent)
        self.view_type = view_type
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.profile_data = profile_data
        self.allowed_interactions = profile_data.get_container().interaction_types
        self.label = label

        # Create a group box widget in which everything else will be placed
        self.group_widget = QtWidgets.QGroupBox(self.label)
        self.main_layout.addWidget(self.group_widget)

        # Create group box contents
        self.group_layout = QtWidgets.QGridLayout()
        self.group_widget.setLayout(self.group_layout)
        self.action_layout = QtWidgets.QVBoxLayout()

        # Only show edit controls in the basic tab
        if self.view_type == common.ContainerViewTypes.Action:
            self._create_edit_controls()
            self.group_layout.addLayout(self.action_layout, 0, 0)
            self.group_layout.addLayout(self.controls_layout, 0, 1)
        else:
            self.group_layout.addLayout(self.action_layout, 0, 0)
        self.group_layout.setColumnStretch(0, 2)

        # Only permit adding actions from the basic tab and if the tab is
        # not associated with a vJoy device
        if self.view_type == common.ContainerViewTypes.Action and \
                self.profile_data.parent.get_device_type() != DeviceType.VJoy:
            self.action_selector = gremlin.ui.common.ActionSelector(
                profile_data.parent.input_type
            )
            self.action_selector.action_added.connect(self._add_action)
            self.group_layout.addWidget(self.action_selector, 1, 0)

    def redraw(self):
        common.clear_layout(self.action_layout)

        if self.model is None:
            return

        if self.view_type == common.ContainerViewTypes.Action:
            for index in range(self.model.rows()):
                data = self.model.data(index)
                widget = data.widget(data, self.profile_data)
                widget.action_modified.connect(self.model.data_changed.emit)
                wrapped_widget = BasicActionWrapper(widget)
                wrapped_widget.closed.connect(self._create_closed_cb(widget))
                self.action_layout.addWidget(wrapped_widget)
        elif self.view_type == common.ContainerViewTypes.Condition:
            for index in range(self.model.rows()):
                data = self.model.data(index)
                widget = data.widget(data)
                widget.action_modified.connect(self.model.data_changed.emit)
                wrapped_widget = ConditionActionWrapper(widget)
                self.action_layout.addWidget(wrapped_widget)

    def _add_action(self, action_name):
        plugin_manager = gremlin.plugin_manager.ActionPlugins()
        action_item = plugin_manager.get_class(action_name)(self.profile_data)
        self.model.add_action(action_item)

    def _create_closed_cb(self, widget):
        """Create callbacks to remove individual containers from the model.

        :param widget the container widget to be removed
        :return callback function to remove the provided widget from the
            model
        """
        return lambda: self.model.remove_action(widget.action_data)

    def _create_edit_controls(self):
        """Creates interaction controls based on the allowed interactions.

        :param allowed_interactions list of allowed interactions
        """
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.red)

        self.controls_layout = QtWidgets.QVBoxLayout()
        if ActionSetView.Interactions.Up in self.allowed_interactions:
            self.control_move_up = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_up"), ""
            )
            self.control_move_up.clicked.connect(
                lambda: self.interacted.emit(ActionSetView.Interactions.Up)
            )
            self.controls_layout.addWidget(self.control_move_up)
        if ActionSetView.Interactions.Down in self.allowed_interactions:
            self.control_move_down = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_down"), ""
            )
            self.control_move_down.clicked.connect(
                lambda: self.interacted.emit(ActionSetView.Interactions.Down)
            )
            self.controls_layout.addWidget(self.control_move_down)
        if ActionSetView.Interactions.Delete in self.allowed_interactions:
            self.control_delete = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_delete"), ""
            )
            self.control_delete.clicked.connect(
                lambda: self.interacted.emit(ActionSetView.Interactions.Delete)
            )
            self.controls_layout.addWidget(self.control_delete)
        if ActionSetView.Interactions.Edit in self.allowed_interactions:
            self.control_edit = QtWidgets.QPushButton(
                QtGui.QIcon("gfx/button_edit"), ""
            )
            self.control_edit.clicked.connect(
                lambda: self.interacted.emit(ActionSetView.Interactions.Edit)
            )
            self.controls_layout.addWidget(self.control_edit)

        self.controls_layout.addStretch(1)


class InputItemButton(QtWidgets.QFrame):

    """Creates a button like widget which emits an event when pressed.

    This event can be used to display input item specific customization
    widgets. This button also shows icons of the associated actions.
    """

    # Signal emitted whenever this button is pressed
    selected = QtCore.pyqtSignal(InputIdentifier)

    def __init__(self, identifier, parent=None):
        """Creates a new instance.

        :param identifier identifying information about the button
        :param parent the parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)
        self.identifier = identifier

        self._label_widget = QtWidgets.QLabel(
            gremlin.common.input_to_ui_string(
                self.identifier.input_type,
                self.identifier.input_id
            )
        )
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
        for reference in profile_data.library_references:
            container = reference.get_container()
            # for container in profile_data.containers:
            for actions in [a for a in container.action_sets if a is not None]:
                for action in actions:
                    if action is not None:
                        self._icon_layout.addWidget(ActionLabel(action))

    def mousePressEvent(self, event):
        """Emits the input_item_changed event when this instance is
        clicked on by the mouse.

        :param event the mouse event
        """
        self.selected.emit(self.identifier)


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

    def __init__(self, input_type, parent=None):
        """Creates a new selector instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)
        self.input_type = input_type

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
            if self.input_type in entry.input_types:
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

    # Signal which is emitted whenever the widget's contents change as well as
    # the UI tab that was active when the event was emitted
    container_modified = QtCore.pyqtSignal()

    # Palette used to render widgets
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Background, QtCore.Qt.lightGray)

    # Maps virtual button data to virtual button widgets
    virtual_axis_to_widget = {
        gremlin.profile.VirtualAxisButton:
            gremlin.ui.virtual_button.VirtualAxisButtonWidget,
        gremlin.profile.VirtualHatButton:
            gremlin.ui.virtual_button.VirtualHatButtonWidget
    }

    def __init__(self, library_reference, parent=None):
        """Creates a new container widget object.

        Parameters
        ==========
        library_reference : gremlin.profile.LibraryReference
            reference to the gremlin.profile.LibraryData object being
            configured by this widget
        parent : QtCore.QObject
            object which is the parent of this one
        """
        super().__init__(parent)

        assert isinstance(library_reference, gremlin.profile.LibraryReference)

        self.library_reference = library_reference
        self.action_widgets = []

        self.setTitleBarWidget(TitleBar(
            self._get_window_title(),
            gremlin.hints.hint.get(self.library_reference.get_container().tag, ""),
            self.remove
        ))

        # Create tab widget to display various UI controls in
        self.dock_tabs = QtWidgets.QTabWidget()
        self.dock_tabs.setTabPosition(QtWidgets.QTabWidget.East)
        self.setWidget(self.dock_tabs)

        # Create the individual tabs
        self._create_action_tab()
        if self.library_reference.get_device_type() != DeviceType.VJoy:
            self._create_activation_condition_tab()
            self._create_virtual_button_tab()

        self.dock_tabs.currentChanged.connect(self._tab_changed)

        # Select appropriate tab
        self._select_tab(
            g_container_tab_state.get(self.library_reference.uuid)
        )

    def _create_action_tab(self):
        # Create root widget of the dock element
        self.action_tab_widget = QtWidgets.QWidget()

        # Create layout and place it inside the dock widget
        self.action_layout = QtWidgets.QVBoxLayout(self.action_tab_widget)

        # Create the actual UI
        self.dock_tabs.addTab(self.action_tab_widget, "Action")
        self._create_action_ui()
        self.action_layout.addStretch(10)

    def _create_activation_condition_tab(self):
        # Create widget to place inside the tab
        self.activation_condition_tab_widget = QtWidgets.QWidget()
        self.activation_condition_layout = QtWidgets.QVBoxLayout(
            self.activation_condition_tab_widget
        )

        # Create activation condition UI widget
        self.activation_condition_widget = \
            activation_condition.ActivationConditionWidget(self.library_reference)
        self.activation_condition_widget.activation_condition_modified.connect(
            self.container_modified.emit
        )

        # Put everything together
        self.activation_condition_layout.addWidget(
            self.activation_condition_widget
        )
        self.dock_tabs.addTab(
            self.activation_condition_tab_widget,
            "Condition"
        )

        self._create_condition_ui()
        self.activation_condition_layout.addStretch(10)

    def _create_virtual_button_tab(self):
        # Return if nothing is to be done
        if not self.library_reference.virtual_button:
            return

        # Create widget to place inside the tab
        self.virtual_button_tab_widget = QtWidgets.QWidget()
        self.virtual_button_layout = QtWidgets.QVBoxLayout(
            self.virtual_button_tab_widget
        )

        # Create actual virtual button UI
        self.virtual_button_widget = \
            AbstractContainerWidget.virtual_axis_to_widget[
                type(self.library_reference.virtual_button)
            ](self.library_reference.virtual_button)

        # Put everything together
        self.virtual_button_layout.addWidget(self.virtual_button_widget)
        self.dock_tabs.addTab(self.virtual_button_tab_widget, "Virtual Button")
        self.virtual_button_layout.addStretch(10)

    def _select_tab(self, view_type):
        if view_type is None:
            return

        try:
            tab_title = common.ContainerViewTypes.to_string(view_type).title()

            for i in range(self.dock_tabs.count()):
                if self.dock_tabs.tabText(i) == tab_title:
                    self.dock_tabs.setCurrentIndex(i)
        except gremlin.error.GremlinError as err:
            print(err)
            return

    def _tab_changed(self, index):
        try:
            tab_text = self.dock_tabs.tabText(index)
            g_container_tab_state.set(
                self.library_reference.uuid,
                common.ContainerViewTypes.to_enum(tab_text.lower())
            )
        except gremlin.error.GremlinError:
            return

    def _get_widget_index(self, widget):
        """Returns the index of the provided widget.

        :param widget the widget for which to return the index
        :return the index of the provided widget, -1 if not present
        """
        index = -1
        for i, entry in enumerate(self.action_widgets):
            if entry == widget:
                index = i
        return index

    def _create_action_set_widget(self, action_set_data, label, view_type):
        """Adds an action widget to the container.

        :param action_set_data data of the actions which form the action set
        :param label the label to show in the title
        :param view_type visualization type
        :return wrapped widget
        """
        action_set_model = ActionSetModel(action_set_data)
        action_set_view = ActionSetView(
            self.library_reference,
            label,
            view_type
        )
        action_set_view.set_model(action_set_model)
        action_set_view.interacted.connect(
            lambda x: self._handle_interaction(action_set_view, x)
        )

        # Store the view widget so we can use it for interactions later on
        self.action_widgets.append(action_set_view)

        return action_set_view

    def remove(self, _):
        """Emits the closed event when this widget is being closed."""
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

    def _create_action_ui(self):
        """Creates the UI elements for the widget."""
        raise gremlin.error.MissingImplementationError(
            "AbstractContainerWidget._create_basic_ui not "
            "implemented in subclass"
        )

    def _create_condition_ui(self):
        """Creates the UI elements for the widget."""
        raise gremlin.error.MissingImplementationError(
            "AbstractContainerWidget._create_condition_ui not "
            "implemented in subclass"
        )

    def _get_window_title(self):
        """Returns the title to show on the widget."""
        return self.library_reference.get_container().name


class AbstractActionWidget(QtWidgets.QFrame):

    """Base class for all widgets representing actions from the profile
    module."""

    # Signal which is emitted whenever the widget's contents change
    action_modified = QtCore.pyqtSignal()

    def __init__(
            self,
            action_data,
            library_reference,
            layout_type=QtWidgets.QVBoxLayout,
            parent=None
    ):
        """Creates a new widget to configure a particular action type..

        Parameters
        ==========
        action_data : gremlin.base_classes.AbstractAction
            instance holding input type agnostic information about the action
        library_reference : gremlin.profile.LibraryReference
            the library reference this action is being configured on
        layout_type : QtWidgets.QLayout
            type of layout to use for the widget
        parent : QtCore.QObject
            parent widget
        """
        QtWidgets.QFrame.__init__(self, parent)

        assert(isinstance(action_data, gremlin.base_classes.AbstractAction))
        assert(isinstance(library_reference, gremlin.profile.LibraryReference))

        self.action_data = action_data
        self.library_reference = library_reference

        self.main_layout = layout_type(self)
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
        return self.library_reference.parent.input_type

    def _get_profile_root(self):
        """Returns the root of the entire profile.

        :return root Profile instance
        """
        root = self.library_reference.parent
        while not isinstance(root, gremlin.profile.Profile):
            root = root.parent
        return root


class AbstractActionWrapper(QtWidgets.QDockWidget):

    """Base class for all action widget wrappers.

    The specializations of this class will be used to contain an action
    widget while rendering the UI components needed for a specific view.
    """

    def __init__(self, action_widget, parent=None):
        """Wrapes a widget inside a docking container.

        :param action_widget the action widget to wrap
        :param parent the parent of this widget
        """
        super().__init__(parent)
        self.action_widget = action_widget

        # Create widget sitting in the root of the dock element
        self.dock_widget = QtWidgets.QFrame()
        self.dock_widget.setFrameShape(QtWidgets.QFrame.Box)
        self.dock_widget.setObjectName("frame")
        self.dock_widget.setStyleSheet(
            "#frame { border: 1px solid #949494; border-top: none; background-color: #afafaf; }"
        )
        self.setWidget(self.dock_widget)

        # Create default layout
        self.main_layout = QtWidgets.QVBoxLayout(self.dock_widget)


class TitleBarButton(QtWidgets.QAbstractButton):

    """Button usable in the titlebar of dock widgets."""

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

    def sizeHint(self):
        """Returns the ideal size of this widget.

        :return ideal size of the widget
        """
        self.ensurePolished()

        size = 2 * self.style().pixelMetric(
            QtWidgets.QStyle.PM_DockWidgetTitleBarButtonMargin
        )

        if not self.icon().isNull():
            icon_size = self.style().pixelMetric(
                QtWidgets.QStyle.PM_SmallIconSize
            )
            sz = self.icon().actualSize(QtCore.QSize(icon_size, icon_size))
            size += max(sz.width(), sz.height())

        return QtCore.QSize(size, size)

    def enterEvent(self, event):
        """Handles the event of the widget being entered.

        :param event the event to handle
        """
        if self.isEnabled():
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handles the event of leaving the widget.

        :param event the event to handle
        """
        if self.isEnabled():
            self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """Render the widget based on its current state.

        :param event the rendering event
        """
        p = QtGui.QPainter(self)

        options = QtWidgets.QStyleOptionToolButton()
        options.initFrom(self)
        options.state |= QtWidgets.QStyle.State_AutoRaise

        if self.style().styleHint(QtWidgets.QStyle.SH_DockWidget_ButtonsHaveFrame):
            if self.isEnabled() \
                    and self.underMouse() \
                    and not self.isChecked() \
                    and not self.isDown():
                options.state |= QtWidgets.QStyle.State_Raised
            if self.isChecked():
                options.state |= QtWidgets.QStyle.State_On
            if self.isDown():
                options.state |= QtWidgets.QStyle.State_Sunken
            self.style().drawPrimitive(
                QtWidgets.QStyle.PE_PanelButtonTool,
                options,
                p,
                self
            )

        options.icon = self.icon()
        options.subControls = QtWidgets.QStyle.SC_None
        options.activeSubControls = QtWidgets.QStyle.SC_None
        options.features = QtWidgets.QStyleOptionToolButton.None_
        options.arrowType = QtCore.Qt.NoArrow
        size = self.style().pixelMetric(
            QtWidgets.QStyle.PM_SmallIconSize
        )
        options.iconSize = QtCore.QSize(size, size)
        self.style().drawComplexControl(
            QtWidgets.QStyle.CC_ToolButton, options, p, self
        )


class TitleBar(QtWidgets.QFrame):

    """Represents a titlebar for use with dock widgets.

    This titlebar behaves like the default DockWidget title bar with the
    exception that it has a "help" button which will display some information
    about the content of the widget.
    """

    def __init__(self, label, hint, close_cb, parent=None):
        """Creates a new instance.

        :param label the label of the title bar
        :param hint the hint to show if needed
        :param close_cb the function to call when closing the widget
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.hint = hint
        self.label = QtWidgets.QLabel(label)
        self.help_button = TitleBarButton()
        self.help_button.setIcon(QtGui.QIcon("gfx/help"))
        self.help_button.clicked.connect(self._show_hint)
        self.close_button = TitleBarButton()
        self.close_button.setIcon(QtGui.QIcon("gfx/close"))
        self.close_button.clicked.connect(close_cb)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(5, 0, 5, 0)

        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.layout.addWidget(self.help_button)
        self.layout.addWidget(self.close_button)

        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setObjectName("frame")
        self.setStyleSheet(
            "#frame { border: 1px solid #949494; background-color: #dadada; }"
        )

        self.setLayout(self.layout)

    def _show_hint(self):
        """Displays a hint, explaining the purpose of the action."""
        QtWidgets.QWhatsThis.showText(
            self.help_button.mapToGlobal(QtCore.QPoint(0, 10)),
            self.hint
        )


class BasicActionWrapper(AbstractActionWrapper):

    """Wraps an action widget and displays the basic config dialog."""

    # Signal which is emitted whenever the widget is closed
    closed = QtCore.pyqtSignal(QtWidgets.QWidget)

    def __init__(self, action_widget, parent=None):
        """Wraps an existing action widget.

        :param action_widget the action widget to wrap
        :param parent the parent of the widget
        """
        super().__init__(action_widget, parent)

        self.setTitleBarWidget(TitleBar(
            action_widget.action_data.name,
            gremlin.hints.hint.get(self.action_widget.action_data.tag, ""),
            self.remove
        ))

        self.main_layout.addWidget(self.action_widget)

    def remove(self, _):
        """Emits the closed event when this widget is being closed."""
        self.closed.emit(self)


class ConditionActionWrapper(AbstractActionWrapper):

    """Wraps an action widget and displays the condition config dialog."""

    def __init__(self, action_widget, parent=None):
        """Wraps an existing action widget.

        :param action_widget the action widget to wrap
        :param parent the parent of the widget
        """
        super().__init__(action_widget, parent)

        # Disable all dock features and give it a title
        self.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.setWindowTitle(action_widget.action_data.name)

        # Setup activation condition UI
        action_data = self.action_widget.action_data
        if action_data.parent.activation_condition_type == "action":
            if action_data.activation_condition is None:
                action_data.activation_condition = \
                    gremlin.base_classes.ActivationCondition(
                        [],
                        gremlin.base_classes.ActivationRule.All
                    )

            self.condition_model = activation_condition.ConditionModel(
                action_data.activation_condition
            )
            self.condition_view = activation_condition.ConditionView()
            self.condition_view.set_model(self.condition_model)
            self.condition_view.redraw()
            self.main_layout.addWidget(self.condition_view)
        else:
            action_data.activation_condition = None
