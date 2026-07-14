# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import os
import sys
import time
from abc import (
    ABCMeta,
    abstractmethod,
)

import dill
from gremlin import (
    audio_player,
    device_initialization,
    error,
    event_handler,
    event_helpers,
    fsm,
    input_cache,
    macro,
    mode_manager,
    profile,
    sendinput,
    signal,
    tts,
    user_script,
)
from gremlin.base_classes import Value
from gremlin.config import Configuration
from gremlin.input_refresh import RefreshPhysicalInputs
from gremlin.types import (
    ActionProperty,
    AxisButtonDirection,
    HatDirection,
    InputType,
)
from vjoy.vjoy import VJoyProxy


class VirtualButton(metaclass=ABCMeta):
    """Implements a button like interface."""

    def __init__(self) -> None:
        """Creates a new instance."""
        self._fsm = self._initialize_fsm()

    def _initialize_fsm(self) -> fsm.FiniteStateMachine:
        """Initializes the state of the button FSM."""
        states = ["up", "down"]
        actions = ["press", "release"]

        def noop() -> bool:
            return False

        def press() -> bool:
            return True

        def release() -> bool:
            return True

        transitions = {
            ("up", "press"): fsm.Transition([press], "down"),
            ("up", "release"): fsm.Transition([noop], "up"),
            ("down", "release"): fsm.Transition([release], "up"),
            ("down", "press"): fsm.Transition([noop], "down"),
        }
        return fsm.FiniteStateMachine("up", states, actions, transitions)

    @abstractmethod
    def __call__(self, event: event_handler.Event) -> list[bool]:
        """Process the input event and updates the value as needed.

        Args:
            event: The input event to process

        Returns:
            List of states to process
        """
        pass


class VirtualAxisButton(VirtualButton):
    def __init__(
        self, lower_limit: float, upper_limit: float, direction: AxisButtonDirection
    ) -> None:
        super().__init__()
        self._lower_limit = lower_limit
        self._upper_limit = upper_limit
        self._direction = direction
        self._last_value = None

    def __call__(self, event: event_handler.Event) -> list[bool]:
        value = event.value if event.value is not None else 0.0
        forced_activation = False
        newly_initialized = False
        direction = AxisButtonDirection.Anywhere

        if self._last_value is None:
            newly_initialized = True
            self._last_value = event.value
        else:
            # Check if we moved over the activation region between two
            # consecutive measurements
            if self._last_value < self._lower_limit and value > self._upper_limit:
                forced_activation = True
            elif self._last_value > self._upper_limit and value < self._lower_limit:
                forced_activation = True

            # Determine direction in which the axis is moving
            if self._last_value < value:
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
        inside_range = self._lower_limit <= value <= self._upper_limit
        valid_direction = (
            direction == self._direction
            or self._direction == AxisButtonDirection.Anywhere
        )
        if inside_range and valid_direction:
            if newly_initialized:
                self._fsm.set_state("down")
            else:
                states = [True] if self._fsm.perform("press")[0] else []
        else:
            states = [False] if self._fsm.perform("release")[0] else []

        return states


class VirtualHatButton(VirtualButton):
    """Treats directional hat events as a button."""

    def __init__(self, directions: list[HatDirection]) -> None:
        super().__init__()
        self._directions = directions

    def __call__(self, event: event_handler.Event) -> list[bool]:
        is_pressed = event.value in self._directions
        action = "press" if is_pressed else "release"
        has_changed = self._fsm.perform(action)[0]
        return [is_pressed] if has_changed else []


class VirtualButtonFunctor:
    def __init__(
        self, virtual_button: VirtualButton, event_template: event_handler.Event
    ) -> None:
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

    def __init__(self, binding: profile.InputItemBinding) -> None:
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
        values = [ActionProperty.AlwaysExecute in a.properties for a in actions]
        return any(values)

    def __call__(self, event: event_handler.Event) -> None:
        values = self._generate_values(event)
        for i, value in enumerate(values):
            self._functor(event, value)

            # Pause between the execution of subsequent bindings
            if i < len(values) - 1:
                time.sleep(0.01)

    def _physical_event_setup(self) -> None:
        """Configures the callback object for traditional physical events."""
        self._functor = self._binding.root_action.functor(self._binding.root_action)

    def _virtual_event_setup(self) -> None:
        """Configures the callback object for virtual button handling.

        This creates callbacks that emit virtual button events in reaction to
        the input items physical events. The actions bound to the input item
        in turn will trigger in response to the emitted virtual events.
        """
        if self._binding.input_item.mode is None:
            logging.getLogger("system").warning(
                "Virtual button configured for input item with no mode, ignoring."
            )
            return

        # Create template virtual event
        virtual_event = event_handler.Event(
            event_type=InputType.VirtualButton,
            identifier=self._virtual_identifier,
            device_guid=dill.UUID_Virtual,
            mode=self._binding.input_item.mode,
            is_pressed=False,
            raw_value=False,
        )

        # Create virtual button instance and virtual event generator
        vb_instance = self._binding.virtual_button
        if isinstance(vb_instance, profile.VirtualAxisButton):
            self._functor = VirtualButtonFunctor(
                VirtualAxisButton(
                    vb_instance.lower_limit,
                    vb_instance.upper_limit,
                    vb_instance.direction,
                ),
                virtual_event,
            )
        elif isinstance(vb_instance, profile.VirtualHatButton):
            self._functor = VirtualButtonFunctor(
                VirtualHatButton(vb_instance.directions), virtual_event
            )
        else:
            raise error.GremlinError(
                "Attempting to create virtual event setup when no virtual "
                + "button is configured."
            )

        # Create new callback entries for the virtual button event to execute
        # the actions. This requires the creation of "fake" InputItem and
        # InputItemBinding instances to create another CallbackObject to
        # handle the virtual button events.
        # Create virtual InputItem instance
        virt_item = profile.InputItem(self._binding.input_item.library)
        virt_item.device_id = dill.UUID_Virtual
        virt_item.input_type = InputType.VirtualButton
        virt_item.input_id = self._virtual_identifier
        virt_item.mode = self._binding.input_item.mode
        virt_item.action_sequences = [self._binding]
        virt_item.is_active = self._binding.input_item.is_active

        # Create virtual InputItemBinding instance
        virt_binding = profile.InputItemBinding(virt_item)
        virt_binding.root_action = self._binding.root_action
        virt_binding.behavior = InputType.JoystickButton
        virt_binding.virtual_button = None

        # Create callback reacting to the virtual button event using the new
        # virtual binding that mirrors the original physical one
        eh = event_handler.EventHandler()
        eh.add_callback(
            dill.UUID_Virtual,
            self._binding.input_item.mode,
            virtual_event,
            CallbackObject(virt_binding),
        )

    def _generate_values(self, event: event_handler.Event) -> list[Value]:
        if event.event_type in [InputType.JoystickAxis, InputType.JoystickHat]:
            value = Value(event.value)
        elif event.event_type in [
            InputType.JoystickButton,
            InputType.Keyboard,
            InputType.VirtualButton,
        ]:
            value = Value(event.is_pressed)
        else:
            raise error.GremlinError("Invalid event type")

        return [value]


class CodeRunner:
    """Runs the actual profile code."""

    def __init__(self) -> None:
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

    def start(self, profile: profile.Profile, start_mode: str) -> None:
        """Starts listening to events and loads all existing callbacks.

        Args:
            profile: the profile to use when generating all the callbacks
            start_mode: the mode in which to start Gremlin
        """
        self._profile = profile
        self._reset_state()

        # Check if we want to override the start mode as determined by the
        # heuristic.
        settings = self._profile.settings
        if settings.startup_mode is not None:
            if settings.startup_mode in self._profile.modes.mode_names():
                start_mode = settings.startup_mode

        # Set default macro action delay.
        macro.MacroManager().default_delay = settings.macro_default_delay

        try:
            # Process actions defined in user plugins.
            self._setup_user_scripts()

            # Add a fake keyboard action which does nothing to the callbacks
            # in every mode in order to have empty modes be "present".
            for mode_name in self._profile.modes.mode_names():
                self.event_handler.add_callback(0, mode_name, None, lambda x: x)

            # Create callbacks fom the user scripts and other code.
            callback_count = 0
            for dev_id, modes in user_script.callback_registry.registry.items():
                for mode, events in modes.items():
                    for event, callback_list in events.items():
                        for callback in callback_list.values():
                            self.event_handler.add_callback(
                                dev_id, mode, event, callback
                            )
                            callback_count += 1

            # Process action sequences defined via the UI.
            self._setup_profile()

            # Use inheritance to build duplicate parent actions in children
            # if the child mode does not override the parent's action.
            self.event_handler.build_event_lookup(self._profile.modes.mode_list())

            # Connect signals.
            evt_listener = event_handler.EventListener()
            evt_listener.keyboard_event.connect(self.event_handler.process_event)
            evt_listener.joystick_event.connect(self.event_handler.process_event)
            evt_listener.virtual_event.connect(self.event_handler.process_event)
            evt_listener.gremlin_active = True

            # Start various manager-style classes.
            user_script.periodic_registry.start()
            macro.MacroManager().start()
            audio_player.AudioPlayer().start()
            tts.TTSManager().start()

            mode_manager.ModeManager().switch_to(
                mode_manager.Mode(start_mode, "Default")
            )
            self.event_handler.resume()
            self._running = True

            sendinput.MouseController().start()
            self._refresh_axes()
        except ImportError as e:
            signal.display_error(
                "Unable to launch due to a missing user plugin.", str(e)
            )

    def stop(self) -> None:
        """Stops listening to events and unloads all callbacks."""
        # Disconnect all signals.
        if self._running:
            evt_lst = event_handler.EventListener()
            evt_lst.keyboard_event.disconnect(self.event_handler.process_event)
            evt_lst.joystick_event.disconnect(self.event_handler.process_event)
            evt_lst.virtual_event.disconnect(self.event_handler.process_event)
            evt_lst.gremlin_active = False
        self._running = False

        # Empty callback registry.
        user_script.callback_registry.clear()
        self.event_handler.clear()

        # Stop periodic events and clear registry.
        user_script.periodic_registry.stop()
        user_script.periodic_registry.clear()

        # Stop all manager classes.
        macro.MacroManager().stop()
        sendinput.MouseController().stop()
        audio_player.AudioPlayer().stop()
        tts.TTSManager().stop()

        # Remove all claims on VJoy devices.
        VJoyProxy.reset()

    def _reset_state(self) -> None:
        """Resets all states to their default values."""
        self.event_handler._active_mode = self._profile.modes.first_mode
        self.event_handler._previous_mode = self._profile.modes.first_mode
        user_script.callback_registry.clear()
        event_helpers.ButtonReleaseActions().reset()

    def _refresh_axes(self) -> None:
        # Store state of all vJoy axes before we do anything.
        vjoy_state = {}
        for vjoy_dev in device_initialization.vjoy_devices():
            vjoy_state[vjoy_dev.vjoy_id] = {}
            cache_dev = input_cache.Joystick()[vjoy_dev.device_guid.uuid]
            for entry in vjoy_dev.axis_map:
                # The axis_map may have empty entries, which need to be ignored.
                if entry.axis_index == 0:
                    continue
                vjoy_state[vjoy_dev.vjoy_id][entry.axis_index] = cache_dev.axis(
                    entry.axis_index
                ).value

        # Refresh physical input states.
        if Configuration().value("global", "general", "refresh-axis-on-activation"):
            RefreshPhysicalInputs.refresh_axes()

        # Set vJoy axis default values unless the axis changed its value due
        # to an axis refresh.
        for vid, data in self._profile.settings.vjoy_initial_values.items():
            vjoy_proxy = VJoyProxy()[vid]
            for aid, value in data.items():
                if value != 0.0 and vjoy_state[vid][aid] == 0.0:
                    vjoy_proxy.axis(linear_index=aid).value = value

    def _setup_user_scripts(self) -> None:
        """Handles loading and configuring of user scripts."""
        # Retrieve the list of current paths searched by Python.
        system_paths = [os.path.normcase(os.path.abspath(p)) for p in sys.path]

        user_script.periodic_registry.clear()
        # Update system path for the user scripts.
        for script in self._profile.scripts.scripts:
            if not script.is_configured:
                continue

            # Perform system path mangling for import statements.
            script_folder = str(script.path.parent)
            if script_folder not in system_paths:
                system_paths.append(script_folder)

            # Ensure script has up to date variable content.
            script.reload()

        # Update the system path list searched by Python in order to locate the
        # plugins properly.
        sys.path = system_paths

    def _setup_profile(self) -> None:
        # Collect action sequences from physical inputs and logical device
        # input entries.
        item_list = sum(self._profile.inputs.values(), [])
        action_sequences = sum([e.action_sequences for e in item_list], [])

        # Create executable unit for each action.
        for action in action_sequences:
            # Event on which to trigger this action.
            event = event_handler.Event(
                event_type=action.input_item.input_type,
                device_guid=action.input_item.device_id,
                identifier=action.input_item.input_id,
                mode=action.input_item.mode,
            )

            # Generate executable unit for the linked library item.
            self.event_handler.add_callback(
                event.device_guid, action.input_item.mode, event, CallbackObject(action)
            )
