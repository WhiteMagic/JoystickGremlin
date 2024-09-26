# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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
from gremlin.base_classes import Value
import gremlin.fsm
from gremlin import error, event_handler, input_devices, joystick_handling, \
    macro, mode_manager, profile, sendinput, user_plugin, util
from gremlin.types import AxisButtonDirection, HatDirection, InputType


class VirtualButton(metaclass=ABCMeta):

    """Implements a button like interface."""

    def __init__(self):
        """Creates a new instance."""
        self._fsm = self._initialize_fsm()

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
    def __call__(self, event: event_handler.Event) -> List[bool]:
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

    def __call__(self, event: event_handler.Event) -> List[bool]:
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

    def __call__(self, event: event_handler.Event) -> List[bool]:
        is_pressed = HatDirection.to_enum(event.value) in self._directions
        action = "press" if is_pressed else "release"
        has_changed = self._fsm.perform(action)
        return [is_pressed] if has_changed else []


class VirtualButtonFunctor:

    def __init__(
        self,
        virtual_button: VirtualButton,
        event_template: event_handler.Event
    ):
        self._virtual_button = virtual_button
        self._event_template = event_template
        self._event_listener = event_handler.EventListener()

    def process_event(self, event: event_handler.Event, value: Value) -> None:
        states = self._virtual_button.process_event(event)
        for state in states:
            new_event = self._event_template.clone()
            new_event.is_pressed = state
            new_event.raw_value = state
            self._event_listener.virtual_event.emit(new_event)

class CallbackObject:

    """Represents the callback executed in reaction to an input."""

    c_next_virtual_identifier = 1

    def __init__(self, binding: gremlin.profile.InputItemBinding):
        """Creates a new callback instance for a specific input item.

        Args:
            action: actions bound to a single input item
        """
        self._binding = binding
        self._functor = None
        self._virtual_identifier = 0

        # Differentiate between bindings utilizing virtual buttons and those
        # that react to raw physical inputs
        if self._binding.virtual_button is not None:
            self._virtual_identifier = CallbackObject.c_next_virtual_identifier
            CallbackObject.c_next_virtual_identifier += 1
            self._virtual_event_setup()
        else:
            self._physical_event_setup()

    def __call__(self, event: event_handler.Event) -> None:
        values = self._generate_values(event)
        for i, value in enumerate(values):
            self._functor(event, value)

            # Pause between the execution of subsequent bindings
            if i < len(values)-1:
                time.sleep(0.05)

    def _physical_event_setup(self) -> None:
        """Configures the callback object for traditional physical events."""
        self._functor = self._binding.root_action.functor(
            self._binding.root_action
        )

    def _virtual_event_setup(self) -> None:
        """Configures the callback object for virtual button handling.

        This creates callbacks that emit virtual button events in reaction to
        the input items physical events. The actions bound to the input item
        in turn will trigger in response to the emitted virtual events.
        """
        # Create template virtual event
        virtual_event = event_handler.Event(
            event_type=InputType.VirtualButton,
            identifier=self._virtual_identifier,
            device_guid=dill.GUID_Virtual,
            mode=mode_manager.ModeManager().current.name,
            is_pressed=False,
            raw_value=False
        )

        # Create virtual button instance and virtual event generator
        vb_instance = self._binding.virtual_button
        if isinstance(vb_instance, gremlin.profile.VirtualAxisButton):
            self._functor = VirtualButtonFunctor(
                VirtualAxisButton(
                    vb_instance.lower_limit,
                    vb_instance.upper_limit,
                    vb_instance.direction
                ),
                virtual_event
            )
        elif isinstance(vb_instance, gremlin.profile.VirtualHatButton):
            self._functors = VirtualButtonFunctor(
                VirtualHatButton(vb_instance.directions),
                virtual_event
            )
        else:
            raise error.GremlinError(
                "Attempting to create virtual event setup when no virtual " +
                "button is configured."
            )

        # Create new callback entries for the virtual button event to execute
        # the actions. This requires the creation of "fake" InputItem and
        # InputItemBinding instances to create another CallbackObject to
        # handle the virtual button events.
        # Create virtual InputItem instance
        phys_item = self._binding.input_item
        virt_item = profile.InputItem(phys_item.library)
        virt_item.device_id = dill.GUID_Virtual
        virt_item.input_type = InputType.VirtualButton
        virt_item.input_id = self._virtual_identifier
        virt_item.mode = phys_item.mode
        virt_item.action_sequences = phys_item.action_configurations
        virt_item.always_execute = phys_item.always_execute
        virt_item.is_active = phys_item.is_active
        # Create virtual InputItemBinding instance
        virt_binding = profile.InputItemBinding(virt_item)
        virt_binding.description = self._binding.description
        virt_binding.library_reference = self._binding.library_reference
        virt_binding.behavior = InputType.JoystickButton
        virt_binding.virtual_button = None
        # Create callback reacting to the virtual button event using the new
        # virtual binding that mirrors the original physical one
        eh = event_handler.EventHandler()
        eh.add_callback(
            dill.GUID_Virtual,
            self._binding.input_item.mode,
            virtual_event,
            CallbackObject(virt_binding),
            virt_binding.input_item.always_execute
        )

    def _generate_values(self, event):
        if event.event_type in [InputType.JoystickAxis, InputType.JoystickHat]:
            value = Value(event.value)
        elif event.event_type in [
            InputType.JoystickButton,
            InputType.Keyboard,
            InputType.VirtualButton
        ]:
            value = Value(event.is_pressed)
        else:
            raise gremlin.error.GremlinError("Invalid event type")

        return [value]


class CodeRunner:

    """Runs the actual profile code."""

    def __init__(self):
        """Creates a new code runner instance."""
        self.event_handler = event_handler.EventHandler()
        self.event_handler.add_plugin(input_devices.JoystickPlugin())
        self.event_handler.add_plugin(input_devices.VJoyPlugin())
        self.event_handler.add_plugin(input_devices.KeyboardPlugin())

        self._profile = None
        self._running = False

    def is_running(self) -> bool:
        """Returns whether the code runner is executing code.

        Returns:
            True if code is being executed, False otherwise
        """
        return self._running

    def start(self, profile: gremlin.profile.Profile, start_mode: str) -> None:
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
            if settings.startup_mode in self._profile.modes.mode_names():
                start_mode = settings.startup_mode

        # Set default macro action delay
        gremlin.macro.MacroManager().default_delay = settings.default_delay

        try:
            # Process actions define in user plugins
            self._setup_plugins()

            # Create callbacks fom the user code
            # FIXME: This seems like it's no longer actively used and should
            #        be removed in its entirety
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
            for mode_name in self._profile.modes.mode_names():
                self.event_handler.add_callback(
                    0,
                    mode_name,
                    None,
                    lambda x: x,
                    False
                )

            # Process action sequences defined via the UI
            self._setup_profile()

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
            evt_listener.keyboard_event.connect(
                self.event_handler.process_event
            )
            evt_listener.joystick_event.connect(
                self.event_handler.process_event
            )
            evt_listener.virtual_event.connect(
                self.event_handler.process_event
            )
            evt_listener.gremlin_active = True

            input_devices.periodic_registry.start()
            macro.MacroManager().start()

            mode_manager.ModeManager().switch_to(
                mode_manager.Mode(start_mode, "global")
            )
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
            evt_lst.keyboard_event.disconnect(self.event_handler.process_event)
            evt_lst.joystick_event.disconnect(self.event_handler.process_event)
            evt_lst.virtual_event.disconnect(self.event_handler.process_event)
            evt_lst.gremlin_active = False
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
        # Collect action sequences from physical inputs and intermediate
        # output entries
        item_list = sum(self._profile.inputs.values(), [])
        action_sequences = sum([e.action_sequences for e in item_list], [])

        # Create executable unit for each action
        for action in action_sequences:
            # Event on which to trigger this action
            event = event_handler.Event(
                event_type=action.input_item.input_type,
                device_guid=action.input_item.device_id,
                identifier=action.input_item.input_id,
                mode=action.input_item.mode
            )

            # Generate executable unit for the linked library item
            self.event_handler.add_callback(
                event.device_guid,
                action.input_item.mode,
                event,
                CallbackObject(action),
                action.input_item.always_execute
            )
