# -*- coding: utf-8; -*-

# Copyright (C) 2016 Lionel Ott
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
from vjoy.vjoy import VJoyProxy

from gremlin.base_classes import Value
from gremlin import audio_player, device_helpers, error, event_handler, fsm, \
    macro, mode_manager, profile, sendinput, user_script, util
from gremlin.types import ActionProperty, AxisButtonDirection, HatDirection, \
    InputType


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
            ("up", "press"): fsm.Transition([self._press], "down"),
            ("up", "release"): fsm.Transition([self._noop], "up"),
            ("down", "release"): fsm.Transition([self._release], "up"),
            ("down", "press"): fsm.Transition([self._noop], "down")
        }
        return fsm.FiniteStateMachine("up", states, actions, transitions)

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

        # If the input moved across the activation an activation will be
        # emitted as a single pulse.
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

    def __call__(self, event: event_handler.Event, value: Value) -> None:
        states = self._virtual_button(event)
        for state in states:
            new_event = self._event_template.clone()
            new_event.is_pressed = state
            new_event.raw_value = state
            self._event_listener.virtual_event.emit(new_event)

class CallbackObject:

    """Represents the callback executed in reaction to an input."""

    c_next_virtual_identifier = 1

    def __init__(self, binding: profile.InputItemBinding):
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

    @property
    def always_execute(self) -> bool:
        """Returns True if the callback should be executed even when Gremlin
        is paused.

        Returns:
            True if the callback is to be always executed
        """
        actions = self._binding.root_action.get_actions()[0]
        values = [
            ActionProperty.AlwaysExecute in a.properties for a in actions
        ]
        return any(values)

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

    def _create_virtual_event_template(self) -> event_handler.Event:
        """Create template virtual event for button handling.
        
        Returns:
            Template virtual event
        """
        return event_handler.Event(
            event_type=InputType.VirtualButton,
            identifier=self._virtual_identifier,
            device_guid=dill.GUID_Virtual,
            mode=mode_manager.ModeManager().current.name,
            is_pressed=False,
            raw_value=False
        )

    def _create_virtual_button_functor(self, vb_instance, virtual_event) -> VirtualButtonFunctor:
        """Create functor for virtual button based on instance type.
        
        Args:
            vb_instance: Virtual button profile instance
            virtual_event: Virtual event template
            
        Returns:
            VirtualButtonFunctor for the button type
            
        Raises:
            GremlinError: If virtual button is not configured
        """
        if isinstance(vb_instance, profile.VirtualAxisButton):
            return VirtualButtonFunctor(
                VirtualAxisButton(
                    vb_instance.lower_limit,
                    vb_instance.upper_limit,
                    vb_instance.direction
                ),
                virtual_event
            )
        elif isinstance(vb_instance, profile.VirtualHatButton):
            return VirtualButtonFunctor(
                VirtualHatButton(vb_instance.directions),
                virtual_event
            )
        else:
            raise error.GremlinError(
                "Attempting to create virtual event setup when no virtual " +
                "button is configured."
            )

    def _create_virtual_input_item(self) -> profile.InputItem:
        """Create virtual InputItem for button event handling.
        
        Returns:
            Virtual InputItem instance
        """
        virt_item = profile.InputItem(self._binding.input_item.library)
        virt_item.device_id = dill.GUID_Virtual
        virt_item.input_type = InputType.VirtualButton
        virt_item.input_id = self._virtual_identifier
        virt_item.mode = self._binding.input_item.mode
        virt_item.action_sequences = [self._binding]
        virt_item.is_active = self._binding.input_item.is_active
        return virt_item

    def _create_virtual_binding(self, virt_item: profile.InputItem) -> profile.InputItemBinding:
        """Create virtual InputItemBinding mirroring the original.
        
        Args:
            virt_item: Virtual input item
            
        Returns:
            Virtual InputItemBinding instance
        """
        virt_binding = profile.InputItemBinding(virt_item)
        virt_binding.root_action = self._binding.root_action
        virt_binding.behavior = InputType.JoystickButton
        virt_binding.virtual_button = None
        return virt_binding

    def _register_virtual_callback(self, virt_binding: profile.InputItemBinding, virtual_event) -> None:
        """Register callback for virtual button event.
        
        Args:
            virt_binding: Virtual binding instance
            virtual_event: Virtual event template
        """
        eh = event_handler.EventHandler()
        eh.add_callback(
            dill.GUID_Virtual,
            self._binding.input_item.mode,
            virtual_event,
            CallbackObject(virt_binding)
        )

    def _virtual_event_setup(self) -> None:
        """Configures the callback object for virtual button handling.

        This creates callbacks that emit virtual button events in reaction to
        the input items physical events. The actions bound to the input item
        in turn will trigger in response to the emitted virtual events.
        """
        # Create template and functor
        virtual_event = self._create_virtual_event_template()
        vb_instance = self._binding.virtual_button
        self._functor = self._create_virtual_button_functor(vb_instance, virtual_event)

        # Create virtual item and binding
        virt_item = self._create_virtual_input_item()
        virt_binding = self._create_virtual_binding(virt_item)

        # Register callback for virtual events
        self._register_virtual_callback(virt_binding, virtual_event)

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
            raise error.GremlinError("Invalid event type")

        return [value]


class CodeRunner:

    """Runs the actual profile code."""

    def __init__(self):
        """Creates a new code runner instance."""
        self.event_handler = event_handler.EventHandler()
        self.event_handler.add_plugin(user_script.JoystickPlugin())
        self.event_handler.add_plugin(user_script.VJoyPlugin())
        self.event_handler.add_plugin(user_script.KeyboardPlugin())

        self._profile = None
        self._running = False

    def is_running(self) -> bool:
        """Returns whether the code runner is executing code.

        Returns:
            True if code is being executed, False otherwise
        """
        return self._running

    def _determine_start_mode(self, start_mode: str) -> str:
        """Determine the actual start mode based on profile settings.
        
        Args:
            start_mode: Initial start mode
            
        Returns:
            Final start mode to use
        """
        settings = self._profile.settings
        if settings.startup_mode is not None:
            if settings.startup_mode in self._profile.modes.mode_names():
                return settings.startup_mode
        return start_mode

    def _configure_macro_settings(self) -> None:
        """Configure macro action default delay."""
        macro.MacroManager().default_delay = self._profile.settings.default_delay

    def _add_empty_mode_callbacks(self) -> None:
        """Add fake callbacks to empty modes to make them 'present'."""
        for mode_name in self._profile.modes.mode_names():
            self.event_handler.add_callback(
                0,
                mode_name,
                None,
                lambda x: x
            )

    def _register_user_callbacks(self) -> int:
        """Register all user script callbacks.
        
        Returns:
            Number of callbacks registered
        """
        callback_count = 0
        for dev_id, modes in user_script.callback_registry.registry.items():
            for mode, events in modes.items():
                for event, callback_list in events.items():
                    for callback in callback_list.values():
                        self.event_handler.add_callback(
                            dev_id,
                            mode,
                            event,
                            callback
                        )
                        callback_count += 1
        return callback_count

    def _initialize_vjoy_defaults(self) -> None:
        """Set vJoy axis default values from profile settings."""
        for vid, data in self._profile.settings.vjoy_initial_values.items():
            vjoy_proxy = VJoyProxy()[vid]
            for aid, value in data.items():
                vjoy_proxy.axis(linear_index=aid).set_absolute_value(value)

    def _connect_event_listeners(self) -> None:
        """Connect event listener signals to event handler."""
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

    def _start_managers(self, start_mode: str) -> None:
        """Start all managers and switch to initial mode.
        
        Args:
            start_mode: Mode to switch to on startup
        """
        user_script.periodic_registry.start()
        macro.MacroManager().start()
        mode_manager.ModeManager().switch_to(
            mode_manager.Mode(start_mode, "global")
        )
        self.event_handler.resume()
        sendinput.MouseController().start()

    def start(self, profile: profile.Profile, start_mode: str) -> None:
        """Starts listening to events and loads all existing callbacks.

        Args:
            profile: the profile to use when generating all the callbacks
            start_mode: the mode in which to start Gremlin
        """
        self._profile = profile
        self._reset_state()

        # Determine actual start mode
        start_mode = self._determine_start_mode(start_mode)
        self._configure_macro_settings()

        try:
            # Setup user scripts and callbacks
            self._setup_user_scripts()
            self._add_empty_mode_callbacks()
            self._register_user_callbacks()

            # Setup profile actions and inheritance
            self._setup_profile()
            self.event_handler.build_event_lookup(self._profile.modes.mode_list())

            # Initialize hardware and connect listeners
            self._initialize_vjoy_defaults()
            self._connect_event_listeners()

            # Start all managers
            self._start_managers(start_mode)
            self._running = True

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
        user_script.callback_registry.clear()
        self.event_handler.clear()

        # Stop periodic events and clear registry
        user_script.periodic_registry.stop()
        user_script.periodic_registry.clear()

        macro.MacroManager().stop()
        sendinput.MouseController().stop()

        # Remove all claims on VJoy devices
        VJoyProxy.reset()

        # Remove other possibly long-running aspects
        audio_player.AudioPlayer().stop()

    def _reset_state(self):
        """Resets all states to their default values."""
        self.event_handler._active_mode = self._profile.modes.first_mode
        self.event_handler._previous_mode = self._profile.modes.first_mode
        user_script.callback_registry.clear()
        device_helpers.ButtonReleaseActions().reset()

    def _setup_user_scripts(self):
        """Handles loading and configuring of user scripts."""
        # Retrieve the list of current paths searched by Python
        system_paths = [os.path.normcase(os.path.abspath(p)) for p in sys.path]

        # Populate custom module variable registry <-- nope
        # Update system path for the user scripts
        for script in self._profile.scripts.scripts:
            if not script.is_configured:
                continue

            # Perform system path mangling for import statements
            script_folder = str(script.path.parent)
            if script_folder not in system_paths:
                system_paths.append(script_folder)

            # Ensure script has up to date variable content
            script.reload()

        # Update the system path list searched by Python in order to locate the
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
                CallbackObject(action)
            )
