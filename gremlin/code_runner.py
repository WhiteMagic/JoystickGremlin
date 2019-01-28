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

import logging

import dill

import gremlin
from gremlin import event_handler, input_devices, \
    joystick_handling, macro, sendinput, util
import vjoy as vjoy_module


class CodeRunner:

    """Runs the actual profile code."""

    def __init__(self):
        """Creates a new code runner instance."""
        self.event_handler = event_handler.EventHandler()
        self.event_handler.add_plugin(input_devices.JoystickPlugin())
        self.event_handler.add_plugin(input_devices.VJoyPlugin())
        self.event_handler.add_plugin(input_devices.KeyboardPlugin())

        self._inheritance_tree = None
        self._vjoy_curves = VJoyCurves()
        self._merge_axes = []
        self._running = False

    def is_running(self):
        """Returns whether or not the code runner is executing code.

        :return True if code is being executed, False otherwise
        """
        return self._running

    def start(self, inheritance_tree, settings, start_mode, profile):
        """Starts listening to events and loads all existing callbacks.

        :param inheritance_tree tree encoding inheritance between the
            different modes
        :param settings profile settings to apply at launch
        :param start_mode the mode in which to start Gremlin
        :param profile the profile to use when generating all the callbacks
        """
        # Reset states to their default values
        self._inheritance_tree = inheritance_tree
        self._reset_state()

        # Check if we want to override the star mode as determined by the
        # heuristic
        if settings.startup_mode is not None:
            if settings.startup_mode in gremlin.profile.mode_list(profile):
                start_mode = settings.startup_mode

        # Load the generated code
        try:
            # Load generated python code
            gremlin_code = util.load_module("gremlin_code")

            # Create callbacks fom the user code
            callback_count = 0
            for dev_id, modes in input_devices.callback_registry.registry.items():
                for mode, events in modes.items():
                    for event, callback_list in events.items():
                        for callback in callback_list.values():
                            self.event_handler.add_callback(
                                dev_id,
                                mode,
                                event,
                                callback[0],
                                callback[1]
                            )
                            callback_count += 1

            # Add a fake keyboard action which does nothing to the callbacks
            # in every mode in order to have empty modes be "present"
            for mode_name in gremlin.profile.mode_list(profile):
                self.event_handler.add_callback(
                    0,
                    mode_name,
                    None,
                    lambda x: x,
                    False
                )

            # Create input callbacks based on the profile's content
            for device in profile.devices.values():
                for mode in device.modes.values():
                    for input_items in mode.config.values():
                        for input_item in input_items.values():
                            # Only add callbacks for input items that actually
                            # contain actions
                            if len(input_item.containers) == 0:
                                continue

                            event = event_handler.Event(
                                event_type=input_item.input_type,
                                device_guid=device.device_guid,
                                identifier=input_item.input_id
                            )

                            # Create possibly several callbacks depending
                            # on the input item's content
                            callbacks = []
                            for container in input_item.containers:
                                if not container.is_valid():
                                    logging.getLogger("system").warning(
                                        "Incomplete container ignored"
                                    )
                                    continue
                                callbacks.extend(container.generate_callbacks())

                            for cb_data in callbacks:
                                if cb_data.event is None:
                                    self.event_handler.add_callback(
                                        device.device_guid,
                                        mode.name,
                                        event,
                                        cb_data.callback,
                                        input_item.always_execute
                                    )
                                else:
                                    self.event_handler.add_callback(
                                        dill.GUID_Virtual,
                                        mode.name,
                                        cb_data.event,
                                        cb_data.callback,
                                        input_item.always_execute
                                    )

            # Create merge axis callbacks
            for entry in profile.merge_axes:
                merge_axis = MergeAxis(
                    entry["vjoy"]["vjoy_id"],
                    entry["vjoy"]["axis_id"]
                )
                self._merge_axes.append(merge_axis)

                # Lower axis callback
                event = event_handler.Event(
                    event_type=gremlin.common.InputType.JoystickAxis,
                    device_guid=entry["lower"]["device_guid"],
                    identifier=entry["lower"]["axis_id"]
                )
                self.event_handler.add_callback(
                    event.device_guid,
                    entry["mode"],
                    event,
                    merge_axis.update_axis1,
                    False
                )

                # Upper axis callback
                event = event_handler.Event(
                    event_type=gremlin.common.InputType.JoystickAxis,
                    device_guid=entry["upper"]["device_guid"],
                    identifier=entry["upper"]["axis_id"]
                )
                self.event_handler.add_callback(
                    event.device_guid,
                    entry["mode"],
                    event,
                    merge_axis.update_axis2,
                    False
                )

            # Create vJoy response curve setups
            self._vjoy_curves.profile_data = profile.vjoy_devices
            self.event_handler.mode_changed.connect(
                self._vjoy_curves.mode_changed
            )

            # Use inheritance to build input action lookup table
            self.event_handler.build_event_lookup(inheritance_tree)

            # Set vJoy axis default values
            for vid, data in settings.vjoy_initial_values.items():
                vjoy_proxy = joystick_handling.VJoyProxy()[vid]
                for aid, value in data.items():
                    vjoy_proxy.axis(linear_index=aid).set_absolute_value(value)

            # Connect signals
            evt_listener = event_handler.EventListener()
            kb = input_devices.Keyboard()
            evt_listener.keyboard_event.connect(
                self.event_handler.process_event
            )
            evt_listener.joystick_event.connect(
                self.event_handler.process_event
            )
            evt_listener.virtual_event.connect(
                self.event_handler.process_event
            )
            evt_listener.keyboard_event.connect(kb.keyboard_event)
            evt_listener.gremlin_active = True

            input_devices.periodic_registry.start()
            macro.MacroManager().start()

            self.event_handler.change_mode(start_mode)
            self.event_handler.resume()
            self._running = True

            sendinput.MouseController().start()
        except ImportError as e:
            util.display_error(
                "Unable to launch due to missing custom modules: {}"
                .format(str(e))
            )

    def stop(self):
        """Stops listening to events and unloads all callbacks."""
        # Disconnect all signals
        if self._running:
            evt_lst = event_handler.EventListener()
            kb = input_devices.Keyboard()
            evt_lst.keyboard_event.disconnect(self.event_handler.process_event)
            evt_lst.joystick_event.disconnect(self.event_handler.process_event)
            evt_lst.virtual_event.disconnect(self.event_handler.process_event)
            evt_lst.keyboard_event.disconnect(kb.keyboard_event)
            evt_lst.gremlin_active = False
            self.event_handler.mode_changed.disconnect(
                self._vjoy_curves.mode_changed
            )
        self._running = False

        # Empty callback registry
        input_devices.callback_registry.clear()
        self.event_handler.clear()

        # Stop periodic events and clear registry
        input_devices.periodic_registry.stop()
        input_devices.periodic_registry.clear()

        macro.MacroManager().stop()
        sendinput.MouseController().stop()

        # Remove all claims on VJoy devices
        joystick_handling.VJoyProxy.reset()

    def _reset_state(self):
        """Resets all states to their default values."""
        self.event_handler._active_mode =\
            list(self._inheritance_tree.keys())[0]
        self.event_handler._previous_mode =\
            list(self._inheritance_tree.keys())[0]
        input_devices.callback_registry.clear()


class VJoyCurves:

    """Handles setting response curves on vJoy devices."""

    def __init__(self):
        """Creates a new instance"""
        self.profile_data = None

    def mode_changed(self, mode_name):
        """Called when the mode changes and updates vJoy response curves.

        :param mode_name the name of the new mode
        """
        if not self.profile_data:
            return

        vjoy = gremlin.joystick_handling.VJoyProxy()
        for vid, device in self.profile_data.items():
            if mode_name in device.modes:
                for aid, data in device.modes[mode_name].config[
                        gremlin.common.InputType.JoystickAxis
                ].items():
                    # Get integer axis id in case an axis enum was used
                    axis_id = vjoy_module.vjoy.VJoy.axis_equivalence.get(aid, aid)

                    if len(data.containers) > 0 and vjoy[vid].is_axis_valid(axis_id):
                        action = data.containers[0].action_sets[0][0]
                        vjoy[vid].axis(aid).set_deadzone(*action.deadzone)
                        vjoy[vid].axis(aid).set_response_curve(
                            action.mapping_type,
                            action.control_points
                        )


class MergeAxis:

    """Merges inputs from two distinct axes into a single one."""

    def __init__(self, vjoy_id, input_id):
        self.axis_values = [0.0, 0.0]
        self.vjoy_id = vjoy_id
        self.input_id = input_id

    def _update(self):
        """Updates the merged axis value."""
        value = (self.axis_values[0] - self.axis_values[1]) / 2.0
        gremlin.joystick_handling.VJoyProxy()[self.vjoy_id]\
            .axis(self.input_id).value = value

    def update_axis1(self, event):
        """Updates information for the first axis.

        :param event data event for the first axis
        """
        self.axis_values[0] = event.value
        self._update()

    def update_axis2(self, event):
        """Updates information for the second axis.

        :param event data event for the second axis
        """
        self.axis_values[1] = event.value
        self._update()
