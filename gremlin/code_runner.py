# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import os
import sys
import threading
from typing import TYPE_CHECKING

from gremlin import (
    audio_player,
    device_initialization,
    error,
    event_handler,
    input_cache,
    macro,
    mode_manager,
    profile,
    sendinput,
    signal,
    tts,
    user_script,
)
from gremlin.base_classes import (
    AbstractFunctor,
    Value,
    reset_functor_tree,
    teardown_functor_tree,
)
from gremlin.config import Configuration
from gremlin.input_refresh import RefreshPhysicalInputs
from gremlin.types import (
    ActionProperty,
    Event,
    HatDirection,
    InputType,
    ModeType,
)
from vjoy.vjoy import VJoyProxy

if TYPE_CHECKING:
    from action_plugins.root import RootData


class CallbackObject:
    """Represents the callback executed in reaction to an input."""

    def __init__(self, root_action: RootData) -> None:
        """Creates a new callback instance for an action sequence.

        Args:
            root_action: root action of the action sequence
        """
        self._root_action = root_action
        self._functor: AbstractFunctor = root_action.functor(root_action)

    @property
    def always_execute(self) -> bool:
        """Returns True if the callback should be executed even when Gremlin
        is paused.

        Returns:
            True if the callback is to be always executed
        """
        actions = self._root_action.get_actions()[0]
        values = [ActionProperty.AlwaysExecute in a.properties for a in actions]
        return any(values)

    def __call__(self, event: Event, mode_type: ModeType) -> bool:
        """Runs the action sequence's functor with the event.

        Args:
            event: the event to process
            mode_type: how the action sequence was reached

        Returns:
            True if the action sequence wants the next event of the input
        """
        return self._functor(event, self._create_value(event, mode_type))

    def reset(self) -> None:
        """Resets the action sequence's functors."""
        reset_functor_tree(self._functor)

    def teardown(self) -> None:
        """Stops timers and threads of the action sequence's functors."""
        teardown_functor_tree(self._functor)

    def _create_value(self, event: Event, mode_type: ModeType) -> Value:
        """Returns the value the action sequence's functor processes.

        Args:
            event: the event to create the value for
            mode_type: how the action sequence was reached

        Returns:
            Value of the event
        """
        if event.event_type in [InputType.JoystickAxis, InputType.JoystickHat]:
            value = Value(event.value, mode_type)
        elif event.event_type in [
            InputType.JoystickButton,
            InputType.Keyboard,
            InputType.VirtualButton,
        ]:
            value = Value(event.is_pressed, mode_type)
        else:
            raise error.GremlinError("Invalid event type")

        # A foreign action sequence only ever sees a center value for a hat event, the
        # raw value remains untouched.
        if mode_type == ModeType.Foreign and event.event_type == InputType.JoystickHat:
            value.current = HatDirection.Center
        return value


def resolve_start_mode(active_profile: profile.Profile) -> str:
    """Returns the mode a profile should start in based on its settings.

    Args:
        active_profile: the profile being started

    Returns:
        Name of the mode to start in
    """
    mode_names = active_profile.modes.mode_names()
    startup_mode = active_profile.settings.startup_mode
    if startup_mode in mode_names:
        return startup_mode

    if startup_mode == "Last Active" and active_profile.fpath is not None:
        last_mode = (
            Configuration()
            .value("global", "internal", "last-mode-per-profile")
            .get(str(active_profile.fpath), None)
        )
        if last_mode in mode_names:
            return last_mode

    return active_profile.modes.first_mode


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
        self._macro_termination_thread: threading.Thread | None = None

    def is_running(self) -> bool:
        """Returns whether the code runner is executing code.

        Returns:
            True if code is being executed, False otherwise
        """
        return self._running

    def start(self, profile: profile.Profile) -> None:
        """Starts listening to events and loads all existing callbacks.

        Args:
            profile: the profile to use when generating all the callbacks
        """
        self.wait_for_macros_to_terminate()
        self._profile = profile
        self._reset_state()

        # Set default macro action delay.
        macro.MacroManager().default_delay = self._profile.settings.macro_default_delay

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
            evt_listener.gremlin_active = True

            # Start various manager-style classes.
            user_script.periodic_registry.start()
            macro.MacroManager().start()
            audio_player.AudioPlayer().start()
            tts.TTSManager().start()
            sendinput.MouseMotionManager().start()

            self._running = True
            self.event_handler.resume()

            mode_manager.ModeManager().switch_to(
                mode_manager.Mode(resolve_start_mode(self._profile), "Default"),
                refresh_axes=False,
            )

            # Physical values from the axis refresh have to override initial ones.
            self._apply_vjoy_initial_values()
            if Configuration().value(
                "global", "behavior", "refresh-axis-on-activation"
            ):
                RefreshPhysicalInputs.refresh_axes()
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
            evt_lst.gremlin_active = False
        self._running = False

        # Stop functor timers and threads before dropping the callbacks.
        self.event_handler.teardown_callbacks()

        # Empty various callback registries.
        user_script.callback_registry.clear()
        self.event_handler.clear()

        # Stop periodic events and clear registry.
        user_script.periodic_registry.stop()
        user_script.periodic_registry.clear()

        # Macros finish off the GUI thread, vJoy is released once they have ended.
        self._macro_termination_thread = threading.Thread(
            target=self._terminate_macros, daemon=True
        )
        self._macro_termination_thread.start()
        sendinput.MouseMotionManager().stop()
        audio_player.AudioPlayer().stop()
        tts.TTSManager().stop()

        self._profile = None

    def wait_for_macros_to_terminate(self) -> None:
        """Blocks until the macros of the last stop have ended and vJoy is released."""
        if self._macro_termination_thread is not None:
            self._macro_termination_thread.join()
            self._macro_termination_thread = None

    def _terminate_macros(self) -> None:
        """Ends all macros, then relinquishes the vJoy devices they may use."""
        macro.MacroManager().stop()
        VJoyProxy.reset()

    def _reset_state(self) -> None:
        """Resets all states to their default values."""
        user_script.callback_registry.clear()

    def _apply_vjoy_initial_values(self) -> None:
        # Store state of all vJoy axes before we do anything.
        vjoy_state = {}
        for vjoy_dev in device_initialization.vjoy_devices():
            vjoy_state[vjoy_dev.vjoy_id] = {}
            try:
                cache_dev = input_cache.Joystick()[vjoy_dev.device_guid.uuid]
                for entry in vjoy_dev.axis_map:
                    # The axis_map may have empty entries, which need to be ignored.
                    if entry.axis_index == 0:
                        continue
                    vjoy_state[vjoy_dev.vjoy_id][entry.axis_index] = cache_dev.axis(
                        entry.axis_index
                    ).value
            except error.GremlinError as err:
                logging.getLogger("system").warning(
                    f"Unable to retrieve state for vJoy {vjoy_dev.vjoy_id} ({err})."
                )

        # Axes that are already non-zero keep their value.
        for vid, data in self._profile.settings.vjoy_initial_values.items():
            try:
                vjoy_proxy = VJoyProxy()[vid]
            except error.VJoyError as err:
                logging.getLogger("system").warning(
                    f"Unable to set initial values for vJoy {vid} ({err})."
                )
                continue
            for aid, value in data.items():
                if value != 0.0 and vjoy_state.get(vid, {}).get(aid) == 0.0:
                    vjoy_proxy.axis(axis_id=aid).value = value

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
            script_folder = os.path.normcase(os.path.abspath(script.path.parent))
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
        for input_items in self._profile.inputs.values():
            for input_item in input_items:
                # Event on which to trigger the input's action sequences.
                event = Event(
                    event_type=input_item.input_type,
                    device_guid=input_item.device_id,
                    identifier=input_item.input_id,
                    mode=input_item.mode,
                )
                for root_action in input_item.action_sequences:
                    self.event_handler.add_callback(
                        event.device_guid,
                        input_item.mode,
                        event,
                        CallbackObject(root_action),
                    )
