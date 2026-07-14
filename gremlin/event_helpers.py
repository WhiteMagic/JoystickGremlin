# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from PySide6 import QtCore

from gremlin import (
    common,
    logical_device,
    mode_manager,
)
from gremlin.types import InputType
from vjoy.vjoy import VJoyProxy

if TYPE_CHECKING:
    from gremlin import event_handler


class ModeMatch(Enum):
    """Defines how mode matching is performed for button release actions."""

    IgnoreMode = 1
    DifferentMode = 2
    MatchMode = 3


class ReleaseMode(Enum):
    """Defines how button release actions are triggered."""

    OnPress = 1
    OnRelease = 2


@dataclass
class ButtonReleaseEntry:
    callback: Callable[[event_handler.Event], None]
    registration_mode: str
    mode_match: ModeMatch
    release_mode: ReleaseMode


@dataclass
class RegistryKey:
    device_uuid: uuid.UUID
    input_type: InputType
    input_id: int

    @classmethod
    def from_event(cls, event: event_handler.Event) -> RegistryKey:
        """Creates a RegistryKey from an event.

        Args:
            event: the event from which to create the key

        Returns:
            The corresponding RegistryKey instance
        """
        return cls(event.device_guid, event.event_type, event.identifier)

    def __hash__(self) -> int:
        return hash((self.device_uuid, self.input_type, self.input_id))


@common.SingletonDecorator
class ButtonReleaseActions(QtCore.QObject):
    """Ensures a desired action is run when a button is released.

    Registered actions are executed by the EventHandler class after at the end
    of its callback processing. This ensures that release callbacks always
    execute after normal callbacks.
    """

    def __init__(self) -> None:
        """Initializes the instance."""
        QtCore.QObject.__init__(self)

        self._registry = {}

        mm = mode_manager.ModeManager()
        self._current_mode = mm.current.name
        mm.mode_changed.connect(self._mode_changed_cb)

    def register_callback(
        self,
        callback: Callable[[event_handler.Event], None],
        physical_event: event_handler.Event,
        mode_match: ModeMatch = ModeMatch.IgnoreMode,
    ) -> None:
        """Registers a callback with the system.

        Args:
            callback: the function to run when the corresponding button is released
            physical_event: the physical event of the button triggering the callback
            mode_match: defines how mode matching is performed for this entry
        """
        key = RegistryKey.from_event(physical_event)
        if key not in self._registry:
            self._registry[key] = []
        # When the release callback is executed can be controlled via the
        # mode_match argument.
        self._registry[key].append(
            ButtonReleaseEntry(
                callback, physical_event.mode, mode_match, ReleaseMode.OnRelease
            )
        )

    def register_vjoy_button_release(
        self,
        vjoy_input: tuple[int, int],
        physical_event: event_handler.Event,
        activate_on_press: bool,
    ) -> None:
        """Registers a physical and vjoy button pair for tracking.

        This method ensures that a vjoy button is pressed/released when the
        specified physical event occurs next. This is useful for cases where
        an action was triggered in a different mode or using a different
        condition.

        Args:
            vjoy_input: the vjoy button to release, represented as
                (vjoy_device_id, vjoy_button_id)
            physical_event: the button event when release should
                trigger the release of the vjoy button
            activate_on: button state on which to trigger the automatic
                release
        """
        key = RegistryKey.from_event(physical_event)
        if key not in self._registry:
            self._registry[key] = []

        # Only run the release callback if we're in a different mode to avoid
        # sending double release events.
        self._registry[key].append(
            ButtonReleaseEntry(
                lambda _event: self._release_vjoy_callback_prototype(vjoy_input),
                physical_event.mode,
                ModeMatch.DifferentMode,
                ReleaseMode.OnPress if activate_on_press else ReleaseMode.OnRelease,
            )
        )

    def register_logical_button_release(
        self,
        logical_button_id: int,
        physical_event: event_handler.Event,
        activate_on_press: bool,
    ) -> None:
        key = RegistryKey.from_event(physical_event)
        if key not in self._registry:
            self._registry[key] = []

        # Only run the release callback if we're in a different mode to avoid
        # sending double release events.
        self._registry[key].append(
            ButtonReleaseEntry(
                lambda _event: self._release_logical_device_callback_prototype(
                    logical_button_id
                ),
                physical_event.mode,
                ModeMatch.DifferentMode,
                ReleaseMode.OnPress if activate_on_press else ReleaseMode.OnRelease,
            )
        )

    def reset(self) -> None:
        """Wipes the registry database."""
        self._registry = {}

    def process_release(self, event: event_handler.Event) -> None:
        """Runs release callbacks associated with the given event.

        Args:
            event: the event triggering the callback processing
        """
        key = RegistryKey.from_event(event)
        if key not in self._registry:
            return

        new_list = []
        for entry in self._registry.get(key, []):
            run_callback = True
            match entry.mode_match:
                case ModeMatch.IgnoreMode:
                    run_callback = True
                case ModeMatch.DifferentMode:
                    run_callback = self._current_mode != entry.registration_mode
                case ModeMatch.MatchMode:
                    run_callback = self._current_mode == entry.registration_mode

            if run_callback and event.is_pressed == (
                entry.release_mode == ReleaseMode.OnPress
            ):
                entry.callback(event)
            else:
                new_list.append(entry)
        self._registry[key] = new_list

    def _release_vjoy_callback_prototype(self, vjoy_input: tuple[int, int]) -> None:
        """Prototype of a button release callback, used with lambdas.

        Args:
            vjoy_input: the vjoy input data to use in the release
        """
        vjoy = VJoyProxy()
        # Check if the button is valid otherwise we cause Gremlin to crash
        if vjoy_input[0] in vjoy.vjoy_devices and vjoy[vjoy_input[0]].is_button_valid(
            vjoy_input[1]
        ):
            vjoy[vjoy_input[0]].button(vjoy_input[1]).is_pressed = False
        else:
            logging.getLogger("system").warning(
                "Attempted to use non existent button: "
                + f"vJoy {vjoy_input[0]:d} button {vjoy_input[1]:d}"
            )

    def _release_logical_device_callback_prototype(self, input_id: int) -> None:
        """Prototype of a button release callback, used with lambdas.

        Args:
            vjoy_input: the vjoy input data to use in the release
        """
        ld = logical_device.LogicalDevice()
        identifier = ld.Input.Identifier(InputType.JoystickButton, input_id)
        if ld.exists(identifier):
            ld[identifier].update(False)
        else:
            logging.getLogger("system").warning(
                "Attempted to use non existent button: "
                + f"Logical Device button {input_id}."
            )

    def _mode_changed_cb(self, mode: str) -> None:
        """Updates the current mode variable.

        Args:
            mode: name of the now active mode
        """
        self._current_mode = mode
