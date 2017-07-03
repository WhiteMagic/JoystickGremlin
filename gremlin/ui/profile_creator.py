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


import copy

from PyQt5 import QtWidgets

from gremlin import common, joystick_handling, macro, profile, util
import gremlin.ui.common
import gremlin.ui.input_item


class ProfileCreator(gremlin.ui.common.BaseDialogUi):

    """Displays a dialog to create a new profile from an existing one.

    This dialog shows all actions present in an existing profile and allows
    the user to bind them to new buttons, creating a new customized profile.
    """

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the data to use as the template
        :param parent the parent widget of this one
        """
        gremlin.ui.common.BaseDialogUi.__init__(self, parent)
        self.profile_data = profile_data
        self.new_profile = self._create_empty_profile()

        self.mode_index = {}
        self._binding_registry = {}

        self.setWindowTitle("Profile Creator")
        self.setMinimumSize(500, 700)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self._create_ui()

    def update_binding(self, mode, input_item, event):
        """Updates the key bindings of the new profile.

        :param mode the mode for which this mapping is added
        :param input_item the InputItem for which this mapping is done
        :param event the input to use in the binding
        """
        # Handle the removal of a binding if one exists
        if event is None and input_item in self._binding_registry:
            item = self._binding_registry[input_item]
            item.containers = []
            item.always_execute = False
            item.description = None

            del self._binding_registry[input_item]

        # Add a new binding
        else:
            device_id = util.device_id(event)

            # Get the input item to be mapped then modify it and set it again
            item = self.new_profile.devices[device_id].modes[mode].get_data(
                event.event_type,
                event.identifier
            )

            item.containers = copy.deepcopy(input_item.containers)
            item.always_execute = input_item.always_execute
            item.description = input_item.description

            self.new_profile.devices[device_id].modes[mode].set_data(
                item.input_type,
                item.input_id,
                item
            )

            self._binding_registry[input_item] = item

        self._create_ui()
        self.toolbox.setCurrentIndex(self.mode_index[mode])

    def _mode_list(self):
        """Returns the list of modes present in the profile data.

        :return list of sorted mode names
        """
        modes = []
        for device in self.profile_data.devices.values():
            modes.extend(device.modes.keys())
        return sorted(set(modes))

    def _create_ui(self):
        """Creates the UI of this dialog."""
        gremlin.ui.common.clear_layout(self.main_layout)
        self.mode_index = {}

        # Create the drawers for each of the modes
        self.toolbox = QtWidgets.QToolBox()
        for i, mode in enumerate(self._mode_list()):
            self.mode_index[mode] = i
            self.toolbox.addItem(
                ModeBindings(
                    self.profile_data,
                    self.new_profile,
                    self._binding_registry,
                    mode,
                    self.update_binding
                ),
                mode
            )
        self.main_layout.addWidget(self.toolbox)

        # Create the help text indicating how to use the template tool
        self.help_text = QtWidgets.QLabel(
            "To map an input to an action, left click on the corresponding "
            "button and then moved or press the desired physical input."
            "To delete a mapping simply right click on the corresponding "
            "button. When done click on the \"Save\" button to save a "
            "new profile."
        )
        self.help_text.setWordWrap(True)
        self.help_text.setFrameShape(QtWidgets.QFrame.Box)
        self.help_text.setStyleSheet("QLabel {background-color : #FFF4B0;}")
        self.help_text.setMargin(10)
        self.main_layout.addWidget(self.help_text)

        # Button to save the new profile
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_profile)
        self.main_layout.addWidget(self.save_button)

    def save_profile(self):
        """Saves the current bindings as a new profile.

        Asks the user for the file in which to store the new profile and then
        stores it.
        """
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            None,
            "Save Profile",
            util.userprofile_path(),
            "XML files (*.xml)"
        )
        if fname != "":
            self.new_profile.to_xml(fname)

    def _create_empty_profile(self):
        """Returns an empty profile based on the provided template.

        The returned profile will be identical to the template with the
        exception that no bindings are present.

        :return profile matching the template but lacking any bindings
        """
        new_profile = copy.deepcopy(self.profile_data)

        for device in new_profile.devices.values():
            for mode in device.modes.values():
                for input_items in mode.config.values():
                    for input_item in input_items.values():
                        input_item.containers = []
                        input_item.description = []
                        input_item.always_execute = False

        return new_profile


class ModeBindings(QtWidgets.QWidget):

    """Allows binding of inputs to actions of a particular mode."""

    def __init__(
            self,
            profile_data,
            new_profile,
            bound_inputs,
            mode,
            update_cb,
            parent=None
    ):
        """Creates a new instance.

        :param profile_data the profile for which to create new bindings
        :param new_profile the new profile with the current bindings
        :param bound_inputs dictionary of used bindings
        :param mode the mode handled by this instance
        :param update_cb function to call when a new binding is made
        :param parent the parend of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.profile_data = profile_data
        self.new_profile = new_profile
        self.update_cb = update_cb
        self.bound_inputs = bound_inputs
        self.mode = mode
        self.device_names = self._get_device_names()

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self._inputs = []
        self._create_ui()

    def _create_ui(self):
        """Creates the UI elements for each bindable action."""
        all_input_types = [
            common.InputType.Keyboard,
            common.InputType.JoystickAxis,
            common.InputType.JoystickButton,
            common.InputType.JoystickHat
        ]

        # Find all input items associated with this mode and show them as
        # a bindable item in the UI
        sorted_devices = sorted(
            self.profile_data.devices.values(),
            key=lambda x: x.name
        )
        for device in sorted_devices:
            for input_type in all_input_types:
                data = device.modes[self.mode].config[input_type]
                for input_item in sorted(data.values(), key=lambda x: x.input_id):
                    if len(input_item.containers) == 0:
                        continue

                    self._inputs.append(BindableAction(
                        input_item,
                        self._get_bound_to_string(input_item),
                        self._create_input_cb(input_item)
                    ))
                    self.main_layout.addWidget(self._inputs[-1])

        self.main_layout.addStretch(0)

    def _get_bound_to_string(self, input_item):
        """Returns a string representing the input the action is bound to.

        :param input_item the entry for which to generate the string
        :return string indicating what input is bound to the given entry
        """
        if input_item not in self.bound_inputs:
            return "Unbound"

        bound_input = self.bound_inputs[input_item]

        # Special handling of keyboards
        if bound_input.parent.parent.hardware_id == 0:
            key_name = macro.key_from_code(
                bound_input.input_id[0],
                bound_input.input_id[1]
            ).name
            return "{} - {}".format(
                self.device_names[bound_input.parent.parent.hardware_id],
                key_name
            )
        else:
            return "{} - {} {}".format(
                self.device_names[bound_input.parent.parent.hardware_id],
                profile.input_type_to_tag(bound_input.input_type).capitalize(),
                bound_input.input_id
            )

    def _create_input_cb(self, input_item):
        """Creates a callback function for the provided input item.

        :param input_item the input item for which to create the callback
        :return callback function to use with the provided input item
        """
        return lambda x: self.update_cb(self.mode, input_item, x)

    def _get_device_names(self):
        """Creates a dictionary mapping device hardware ids to their names.

        :return dictionary mapping device hardware id to the corresponding name
        """
        devices = joystick_handling.joystick_devices()
        device_lookup = {}
        for dev in devices:
            device_lookup[dev.hardware_id] = dev.name
        device_lookup[util.get_device_id(0, 0)] = "Keyboard"
        return device_lookup


class BindableAction(QtWidgets.QWidget):

    """UI widget for a single action that can be bound to an input."""

    # Stores which input types are valid together
    valid_bind_types = {
        common.InputType.JoystickAxis: [
            common.InputType.JoystickAxis
        ],
        common.InputType.JoystickButton: [
            common.InputType.JoystickButton,
            common.InputType.Keyboard
        ],
        common.InputType.JoystickHat: [
            common.InputType.JoystickHat
        ],
        common.InputType.Keyboard: [
            common.InputType.JoystickButton,
            common.InputType.Keyboard
        ]
    }

    def __init__(self, input_item, label, input_cb, parent=None):
        """Creates a new instance.

        :param input_item the item for which this instance is created
        :param label string indicating what input this item is
            bound to at the moment
        :param input_cb callback function to call when the button is pressed
        :param parent the parent of this widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.input_type = input_item.input_type
        self.input_cb = input_cb

        description = "Missing description"
        if input_item.description != "":
            description = input_item.description

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.description = QtWidgets.QLabel(description)
        self.bound_action = gremlin.ui.common.LeftRightPushButton(label)
        self.bound_action.setMinimumWidth(200)
        self.bound_action.setMaximumWidth(200)
        self.bound_action.clicked.connect(self._bind_action)
        self.bound_action.clicked_right.connect(lambda: self.input_cb(None))

        self.main_layout.addWidget(self.description)
        self.icon_layout = QtWidgets.QHBoxLayout()
        self.icon_layout.addStretch()

        for container in input_item.containers:
            for action in container.actions:
                self.icon_layout.addWidget(
                    gremlin.ui.input_item.ActionLabel(action))
        self.main_layout.addLayout(self.icon_layout)
        self.main_layout.addWidget(self.bound_action)

    def _bind_action(self):
        """Prompts the user for the input to bind to this item."""
        self.button_press_dialog = gremlin.ui.common.InputListenerWidget(
            self.input_cb,
            BindableAction.valid_bind_types[self.input_type],
            return_kb_event=True
        )

        # Display the dialog centered in the middle of the UI
        root = self
        while root.parent():
            root = root.parent()
        geom = root.geometry()

        self.button_press_dialog.setGeometry(
            geom.x() + geom.width() / 2 - 150,
            geom.y() + geom.height() / 2 - 75,
            300,
            150
        )
        self.button_press_dialog.show()
