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

from abc import ABCMeta, abstractmethod
import copy
import importlib
import logging
import os
import random
import string
import sys
import time
from typing import List, Tuple

import dill

import gremlin
import gremlin.actions
import gremlin.fsm
import gremlin.profile
from gremlin import event_handler, input_devices, \
    joystick_handling, macro, sendinput, user_plugin, util
from gremlin.types import AxisButtonDirection, HatDirection, InputType, \
    MergeAxisOperation
import vjoy as vjoy_module



class VirtualButton(metaclass=ABCMeta):

    """Implements a button like interface."""

    def __init__(self):
        """Creates a new instance."""
        self._fsm = self._initialize_fsm()
        #self._is_pressed = False

    def _initialize_fsm(self):
        """Initializes the state of the button FSM."""
        states = ["up", "down"]
        actions = ["press", "release"]
        transitions = {
            ("up", "press"): gremlin.fsm.Transition(self._press, "down"),
            ("up", "release"): gremlin.fsm.Transition(self._noop, "up"),
            ("down", "release"): gremlin.fsm.Transition(self._release, "up"),
            ("down", "press"): gremlin.fsm.Transition(self._noop, "down")
        }
        return gremlin.fsm.FiniteStateMachine("up", states, actions, transitions)

    @abstractmethod
    def process_event(self, event: event_handler.Event) -> List[bool]:
        """Process the input event and updates the value as needed.

        Args:
            event: The input event to process

        Returns:
            List of states to process
        """
        pass

    def _press(self) -> bool:
        """Executes the "press" action."""
        return True

    def _release(self) -> bool:
        """Executes the "release" action."""
        return True

    def _noop(self) -> bool:
        """Performs "noop" action."""
        return False


class VirtualAxisButton(VirtualButton):

    def __init__(
            self,
            lower_limit: float,
            upper_limit: float,
            direction: AxisButtonDirection
    ):
        super().__init__()
        self._lower_limit = lower_limit
        self._upper_limit = upper_limit
        self._direction = direction
        self._last_value = None

    def process_event(self, event: event_handler.Event) -> List[bool]:
        forced_activation = False
        direction = AxisButtonDirection.Anywhere
        if self._last_value is None:
            self._last_value = event.value
        else:
            # Check if we moved over the activation region between two
            # consecutive measurements
            if self._last_value < self._lower_limit and \
                    event.value > self._upper_limit:
                forced_activation = True
            elif self._last_value > self._upper_limit and \
                    event.value < self._lower_limit:
                forced_activation = True

            # Determine direction in which the axis is moving
            if self._last_value < event.value:
                direction = AxisButtonDirection.Below
            elif self._last_value > event.value:
                direction = AxisButtonDirection.Above

        self._last_value = event.value

        # If the input moved across the activation the activation will be
        # forced by returning a pulse signal.
        states = []
        if forced_activation:
            self._fsm.perform("press")
            self._fsm.perform("release")
            states = [True, False]
        inside_range = self._lower_limit <= event.value <= self._upper_limit
        valid_direction = direction == self._direction or \
            self._direction == AxisButtonDirection.Anywhere
        if inside_range and valid_direction:
            states = [True] if self._fsm.perform("press") else []
        else:
            states = [False] if self._fsm.perform("release") else []

        return states


class VirtualHatButton(VirtualButton):

    """Treats directional hat events as a button."""

    def __init__(self, directions):
        super().__init__()
        self._directions = directions

    def process_event(self, event: event_handler.Event) -> List[bool]:
        is_pressed = HatDirection.to_enum(event.value) in self._directions
        action = "press" if is_pressed else "release"
        has_changed = self._fsm.perform(action)
        return [is_pressed] if has_changed else []


class CallbackObject:

    """Represents the callback executed in reaction to an input."""

    def __init__(self, action):
        self._action = action
        self._execution_tree = \
            action.library_reference.action_tree.genertate_execution_tree()

        self._generate_values = self._default_generate_values
        self._virtual_button = None
        if isinstance(self._action.virtual_button, gremlin.profile.VirtualAxisButton):
            self._virtual_button = VirtualAxisButton(
                self._action.virtual_button.lower_limit,
                self._action.virtual_button.upper_limit,
                self._action.virtual_button.direction
            )
            self._generate_values = self._virtual_generate_values
        elif isinstance(self._action.virtual_button, gremlin.profile.VirtualHatButton):
            self._virtual_button = VirtualHatButton(
                self._action.virtual_button.directions
            )
            self._generate_values = self._virtual_generate_values

    def __call__(self, event):
        values = self._generate_values(event)

        for i, value in enumerate(values):
            stack = self._execution_tree.children[::-1]
            while len(stack) > 0:
                node = stack.pop()
                result = node.value.process_event(event, value)

                # Only execute child nodes if the parent node was executed
                # successfully
                if result:
                    stack.extend(node.children[::-1])

            # Allow a short period of time before processing the execution
            # tree again with a new value
            if i < len(values)-1:
                time.sleep(0.05)

    def _default_generate_values(self, event):
        if event.event_type in [InputType.JoystickAxis, InputType.JoystickHat]:
            value = gremlin.actions.Value(event.value)
        elif event.event_type in [InputType.JoystickButton, InputType.Keyboard]:
            value = gremlin.actions.Value(event.is_pressed)
        else:
            raise gremlin.error.GremlinError("Invalid event type")

        return [value]

    def _virtual_generate_values(self, event):
        values = []
        if event.event_type in [InputType.JoystickAxis, InputType.JoystickHat]:
            states = self._virtual_button.process_event(event)
            for state in states:
                values.append(gremlin.actions.Value(state))
        else:
            raise gremlin.error.GremlinError("Invalid event type")

        return values


class CodeRunner:

    """Runs the actual profile code."""

    def __init__(self):
        """Creates a new code runner instance."""
        self.event_handler = event_handler.EventHandler()
        self.event_handler.add_plugin(input_devices.JoystickPlugin())
        self.event_handler.add_plugin(input_devices.VJoyPlugin())
        self.event_handler.add_plugin(input_devices.KeyboardPlugin())

        self._profile = None
        self._vjoy_curves = VJoyCurves()
        self._merge_axes = []
        self._running = False

    def is_running(self):
        """Returns whether or not the code runner is executing code.

        :return True if code is being executed, False otherwise
        """
        return self._running

    def start(self, profile: gremlin.profile.Profile, start_mode: str):
        """Starts listening to events and loads all existing callbacks.

        Args:
            profile: the profile to use when generating all the callbacks
            start_mode: the mode in which to start Gremlin
        """
        self._profile = profile
        self._reset_state()

        # Check if we want to override the start mode as determined by the
        # heuristic
        settings = self._profile.settings
        if settings.startup_mode is not None:
            if settings.startup_mode in self._profile.modes.mode_list():
                start_mode = settings.startup_mode

        # Set default macro action delay
        gremlin.macro.MacroManager().default_delay = settings.default_delay

        try:
            self._setup_plugins()

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
            for mode_name in self._profile.modes.mode_list():
                self.event_handler.add_callback(
                    0,
                    mode_name,
                    None,
                    lambda x: x,
                    False
                )

            self._setup_profile()

            # Create merge axis callbacks
            # for entry in profile.merge_axes:
            #     merge_axis = MergeAxis(
            #         entry["vjoy"]["vjoy_id"],
            #         entry["vjoy"]["axis_id"],
            #         entry["operation"]
            #     )
            #     self._merge_axes.append(merge_axis)
            #
            #     # Lower axis callback
            #     event = event_handler.Event(
            #         event_type=gremlin.common.InputType.JoystickAxis,
            #         device_guid=entry["lower"]["device_guid"],
            #         identifier=entry["lower"]["axis_id"]
            #     )
            #     self.event_handler.add_callback(
            #         event.device_guid,
            #         entry["mode"],
            #         event,
            #         merge_axis.update_axis1,
            #         False
            #     )
            #
            #     # Upper axis callback
            #     event = event_handler.Event(
            #         event_type=gremlin.common.InputType.JoystickAxis,
            #         device_guid=entry["upper"]["device_guid"],
            #         identifier=entry["upper"]["axis_id"]
            #     )
            #     self.event_handler.add_callback(
            #         event.device_guid,
            #         entry["mode"],
            #         event,
            #         merge_axis.update_axis2,
            #         False
            #     )

            # Create vJoy response curve setups
            # self._vjoy_curves.profile_data = profile.vjoy_devices
            # self.event_handler.mode_changed.connect(
            #     self._vjoy_curves.mode_changed
            # )

            # Use inheritance to build duplicate parent actions in children
            # if the child mode does not override the parent's action
            self.event_handler.build_event_lookup(self._profile.modes)

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
                "Unable to launch due to missing user plugin: {}"
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
            # self.event_handler.mode_changed.disconnect(
            #     self._vjoy_curves.mode_changed
            # )
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
        self.event_handler._active_mode = self._profile.modes.first_mode
        self.event_handler._previous_mode = self._profile.modes.first_mode
        input_devices.callback_registry.clear()

    def _setup_plugins(self):
        """Handles loading and configuring of loaded plugins."""
        # Retrieve list of current paths searched by Python
        system_paths = [os.path.normcase(os.path.abspath(p)) for p in sys.path]

        # Populate custom module variable registry
        var_reg = user_plugin.variable_registry
        for plugin in self._profile.plugins:
            # Perform system path mangling for import statements
            path, _ = os.path.split(
                os.path.normcase(os.path.abspath(plugin.file_name))
            )
            if path not in system_paths:
                system_paths.append(path)

            # Load module specification so we can later create multiple
            # instances if desired
            spec = importlib.util.spec_from_file_location(
                "".join(random.choices(string.ascii_lowercase, k=16)),
                plugin.file_name
            )

            # Process each instance in turn
            for instance in plugin.instances:
                # Skip all instances that are not fully configured
                if not instance.is_configured():
                    continue

                # Store variable values in the registry
                for var in instance.variables.values():
                    var_reg.set(
                        plugin.file_name,
                        instance.name,
                        var.name,
                        var.value
                    )

                # Load the modules
                tmp = importlib.util.module_from_spec(spec)
                tmp.__gremlin_identifier = (plugin.file_name, instance.name)
                spec.loader.exec_module(tmp)

        # Update system path list searched by Python in order to locate the
        # plugins properly
        sys.path = system_paths

    def _setup_profile(self):
        item_list = sum(self._profile.inputs.values(), [])
        action_list = sum([e.action_configurations for e in item_list], [])

        # Create executable unit for each action
        for action in action_list:
            # Event on which to trigger this action
            event = event_handler.Event(
                event_type=action.input_item.input_type,
                device_guid=action.input_item.device_id,
                identifier=action.input_item.input_id
            )

            # Generate executable unit for the linked library item
            self.event_handler.add_callback(
                event.device_guid,
                action.input_item.mode,
                event,
                self._create_callback(action),
                action.input_item.always_execute
            )

    def _callback(self, tree, action, event):
        values = self._generate_values(event)
        if event.event_type in [InputType.JoystickAxis, InputType.JoystickHat]:
            value = gremlin.actions.Value(event.value)
        elif event.event_type in [
            InputType.JoystickButton,
            InputType.Keyboard,
            InputType.VirtualButton
        ]:
            value = gremlin.actions.Value(event.is_pressed)
        else:
            raise gremlin.error.GremlinError("Invalid event type")

        shared_value = copy.deepcopy(value)

        # Execute the nodes in the tree
        stack = tree.children[::-1]
        while len(stack) > 0:
            node = stack.pop()
            result = node.value.process_event(event, shared_value)

            if result:
                stack.extend(node.children[::-1])

    def _create_callback(self, action):
        return CallbackObject(action)

        # # Create input callbacks based on the profile's content
        # for device in profile.devices.values():
        #     for mode in device.modes.values():
        #         for input_items in mode.config.values():
        #             for input_item in input_items.values():
        #                 # Only add callbacks for input items that actually
        #                 # contain actions
        #                 if len(input_item.containers) == 0:
        #                     continue
        #
        #                 event = event_handler.Event(
        #                     event_type=input_item.input_type,
        #                     device_guid=device.device_guid,
        #                     identifier=input_item.input_id
        #                 )
        #
        #                 # Create possibly several callbacks depending
        #                 # on the input item's content
        #                 callbacks = []
        #                 for container in input_item.containers:
        #                     if not container.is_valid():
        #                         logging.getLogger("system").warning(
        #                             "Incomplete container ignored"
        #                         )
        #                         continue
        #                     callbacks.extend(container.generate_callbacks())
        #
        #                 for cb_data in callbacks:
        #                     if cb_data.event is None:
        #                         self.event_handler.add_callback(
        #                             device.device_guid,
        #                             mode.name,
        #                             event,
        #                             cb_data.callback,
        #                             input_item.always_execute
        #                         )
        #                     else:
        #                         self.event_handler.add_callback(
        #                             dill.GUID_Virtual,
        #                             mode.name,
        #                             cb_data.event,
        #                             cb_data.callback,
        #                             input_item.always_execute
        #                         )


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
        for guid, device in self.profile_data.items():
            if mode_name in device.modes:
                for aid, data in device.modes[mode_name].config[
                        gremlin.common.InputType.JoystickAxis
                ].items():
                    # Get integer axis id in case an axis enum was used
                    axis_id = vjoy_module.vjoy.VJoy.axis_equivalence.get(aid, aid)
                    vjoy_id = joystick_handling.vjoy_id_from_guid(guid)

                    if len(data.containers) > 0 and \
                            vjoy[vjoy_id].is_axis_valid(axis_id):
                        action = data.containers[0].action_sets[0][0]
                        vjoy[vjoy_id].axis(aid).set_deadzone(*action.deadzone)
                        vjoy[vjoy_id].axis(aid).set_response_curve(
                            action.mapping_type,
                            action.control_points
                        )


class MergeAxis:

    """Merges inputs from two distinct axes into a single one."""

    def __init__(
            self,
            vjoy_id: int,
            input_id: int,
            operation: MergeAxisOperation
    ):
        self.axis_values = [0.0, 0.0]
        self.vjoy_id = vjoy_id
        self.input_id = input_id
        self.operation = operation

    def _update(self):
        """Updates the merged axis value."""
        value = 0.0
        if self.operation == MergeAxisOperation.Average:
            value = (self.axis_values[0] - self.axis_values[1]) / 2.0
        elif self.operation == MergeAxisOperation.Minimum:
            value = min(self.axis_values[0], self.axis_values[1])
        elif self.operation == MergeAxisOperation.Maximum:
            value = max(self.axis_values[0], self.axis_values[1])
        elif self.operation == MergeAxisOperation.Sum:
            value = gremlin.util.clamp(
                self.axis_values[0] + self.axis_values[1],
                -1.0,
                1.0
            )
        else:
            raise gremlin.error.GremlinError(
                "Invalid merge axis operation detected, \"{}\"".format(
                    str(self.operation)
                )
            )

        gremlin.joystick_handling.VJoyProxy()[self.vjoy_id]\
            .axis(self.input_id).value = value

    def update_axis1(self, event: gremlin.event_handler.Event):
        """Updates information for the first axis.

        Args:
            event: data event for the first axis
        """
        self.axis_values[0] = event.value
        self._update()

    def update_axis2(self, event: gremlin.event_handler.Event):
        """Updates information for the second axis.

        Args:
            event: data event for the second axis
        """
        self.axis_values[1] = event.value
        self._update()
