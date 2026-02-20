# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import os
import sys
from typing import (
    List,
    TYPE_CHECKING,
)
import uuid

from PySide6 import (
    QtCore,
    QtQml,
    QtGui,
)
from PySide6.QtCore import (
    Property,
    Signal,
    Slot,
)

import dill

from gremlin import (
    audio_player,
    code_runner,
    common,
    config,
    device_helpers,
    device_initialization,
    error,
    event_handler,
    mode_manager,
    process_monitor,
    profile,
    shared_state,
    util,
)
from gremlin.logical_device import LogicalDevice
from gremlin.signal import (
    display_error,
    signal,
)
from gremlin.ui.device import InputIdentifier
from gremlin.ui.profile import InputItemModel
from gremlin.ui.script import ScriptListModel


if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.UI"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class UIState(QtCore.QObject):

    """Holds the state of the UI to simplify complex interactions.

    The various UI elements retrieve the state they should be in from this
    instance while being able to set state only via method calls.
    """

    deviceChanged = Signal()
    inputChanged = Signal()
    modeChanged = Signal()
    tabChanged = Signal()
    selectIndex = Signal(int)

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        self._current_device = dill.UUID_Invalid
        self._current_input = {}
        self._current_mode = "Default"
        self._current_tab = "physical"

        event_handler.EventListener().device_change_event.connect(
            self._device_change
        )
        signal.profileChanged.connect(self._device_change)

    def _device_change(self) -> None:
        # We only care about this in case we've selected a physical device
        if self._current_tab != "physical":
            return

        devices = device_initialization.physical_devices()
        selection_valid = False
        for dev in devices:
            if dev.device_guid.uuid == self._current_device:
                selection_valid = True
                break

        if not selection_valid:
            if len(devices) > 0:
                self.setCurrentDevice(str(devices[0].device_guid))
            else:
                self.setCurrentDevice(str(dill.UUID_Invalid))
                self.setCurrentTab("logical")

    @Slot(str)
    def setCurrentDevice(self, device_name: str) -> None:
        device_uuid = uuid.UUID(device_name)
        if device_uuid != self._current_device:
            self._current_device = device_uuid
            self.deviceChanged.emit()
            self.inputChanged.emit()

    @Slot(InputIdentifier, int)
    def setCurrentInput(self, input: InputIdentifier, index: int) -> None:
        value = (input, index)
        if value != self._current_input.get(input.device_guid, None):
            self._current_input[input.device_guid] = value
            self.inputChanged.emit()

    @Slot(str)
    def setCurrentMode(self, mode_name: str) -> None:
        if mode_name != self._current_mode:
            self._current_mode = mode_name
            self.modeChanged.emit()
            self.inputChanged.emit()

    @Slot(str)
    def setCurrentTab(self, tab: str) -> None:
        if tab != self._current_tab:
            self._current_tab = tab
            self.tabChanged.emit()

    @Property(str, notify=deviceChanged)
    def currentDevice(self) -> str:
        return str(self._current_device).upper()

    @Property(InputIdentifier, notify=inputChanged)
    def currentInput(self) -> InputIdentifier:
        return self._current_input.get(
            self._current_device,
            (InputIdentifier(), 0)
        )[0]

    @Property(int, notify=inputChanged)
    def currentInputIndex(self) -> int:
        return self._current_input.get(
            self._current_device,
            (InputIdentifier(), 0)
        )[1]

    @Property(str, notify=modeChanged)
    def currentMode(self) -> str:
        return self._current_mode

    @Property(str, notify=tabChanged)
    def currentTab(self) -> str:
        return self._current_tab

    def __str__(self) -> str:
        cur_input = self._current_input.get(
            self._current_device,
            (InputIdentifier(), 0)
        )
        return f"{self._current_device} {cur_input[0].input_id} " + \
            f"{cur_input[1]}  {self._current_tab}"


@common.SingletonDecorator
class Backend(QtCore.QObject):

    """Allows interfacing between the QML frontend and the Python backend."""

    windowTitleChanged = Signal()
    profileChanged = Signal()
    recentProfilesChanged = Signal()
    inputConfigurationChanged = Signal()
    activityChanged = Signal()
    propertyChanged = Signal()
    uiChanged = Signal()

    def __init__(
        self,
        engine: QtQml.QQmlApplicationEngine,
        parent: ta.OQO=None
    ) -> None:
        super().__init__(parent)

        self.engine = engine
        self.config = config.Configuration()
        self.profile = profile.Profile()
        shared_state.current_profile = self.profile
        self._last_error = ""
        self._action_state = {}
        self.runner = code_runner.CodeRunner()
        self.ui_state = UIState(self)
        self.process_monitor = process_monitor.ProcessMonitor()
        self.process_monitor.start()

        self.joystick_change_monitor = device_helpers.JoystickInputSignificant()

        # Hookup various mode change related callbacks
        mm = mode_manager.ModeManager()
        mm.mode_changed.connect(self._emit_change)
        self.profileChanged.connect(mm.reset)
        self.profileChanged.connect(
            lambda: self.ui_state.setCurrentMode(mm.current.name)
        )
        self.profileChanged.connect(self._profile_change_handler)
        self.process_monitor.process_changed.connect(
            self._active_process_changed_cb
        )

        event_handler.EventHandler().is_active.connect(
            lambda: self.activityChanged.emit()
        )
        event_handler.EventListener().device_change_event.connect(
            self._device_change
        )
        event_handler.EventListener().joystick_event.connect(
            self._highlight_input
        )

        self.profileChanged.emit()

    def _highlight_input(self, event: event_handler.Event) -> None:
        if not self.config.value("global", "general", "input-highlighting") \
                or shared_state.suspend_input_highlighting():
            return

        current_input = self.ui_state.currentInput
        if self.ui_state.currentTab == "physical" \
                and current_input.device_guid == event.device_guid \
                and self.joystick_change_monitor.should_process(event):
            new_input = InputIdentifier(
                event.device_guid,
                event.event_type,
                event.identifier
            )
            if current_input.linear_index != new_input.linear_index:
                signal.setInputIndex.emit(new_input.linear_index)

    def _profile_change_handler(self) -> None:
        # Update shared state before any other parts update.
        shared_state.current_profile = self.profile

        # Emit signals for various parts of the system.
        self.windowTitleChanged.emit()
        signal.reloadUi.emit()
        signal.profileChanged.emit()

    def _device_change(self) -> None:
        behavior = self.config.value(
            "global", "general", "device-change-behavior"
        )
        match behavior:
            case "Disable":
                self.activate_gremlin(False)
            case "Ignore":
                pass
            case "Reload":
                if self.gremlinActive:
                    self.activate_gremlin(False)
                    self.activate_gremlin(True)

    def _emit_change(self) -> None:
        """Emits the signal required for property changes to propagate."""
        self.propertyChanged.emit()

    @Slot()
    def emitConfigChanged(self) -> None:
        signal.configChanged.emit()
        audio_player.AudioPlayer().refresh()

    def check_for_updates(self) -> None:
        parse_version = lambda v: [int(x) for x in v.split(".")]
        if self.config.value("global", "general", "check-for-updates"):
            # Attempt to retrieve the latest version information, if this fails
            # silently abort.
            version_string = util.latest_gremlin_version()
            if version_string is None:
                return

            # Parse version strings into semantic versions and compare them. If
            # a newer version is available show a notification. Store the new
            # version so the user is only ever notified once.
            version = parse_version(version_string)
            last_version = parse_version(
                self.config.value("global", "internal", "last-known-version")
            )
            if last_version < version:
                version_string = ".".join(str(x) for x in version)
                signal.showNotification.emit(
                    "New version available",
                    f"A newer version of Joystick Gremlin, {version_string} "
                    f"is available."
                )
                self.config.set(
                    "global", "internal", "last-known-version", version_string
                )

    def _active_process_changed_cb(self, path: str) -> None:
        """Handles changes to the active process.

        If the profile auto-loading option is disabled nothing is done.
        Otherwise the profile associated with the newly active process is
        loaded and then activated. Should
        """
        if not self.config.value( "profile", "automation", "enable-auto-loading"):
            return

        profile_path = config.get_profile_with_regex(path)
        # Found a valid profile to load.
        if profile_path:
            if self.profile.fpath != profile_path:
                self.activate_gremlin(False)
                self.loadProfile(profile_path)
            if not self.gremlinActive:
                self.activate_gremlin(True)
        # No valid profile specified for the new execuable.
        else:
            if not self.config.value(
                "profile", "automation", "remain-active-on-focus-loss"
            ):
                self.activate_gremlin(False)

    @Property(UIState, notify=uiChanged)
    def uiState(self) -> UIState:
        return self.ui_state

    @Property(bool, notify=activityChanged)
    def gremlinPaused(self) -> bool:
        """Returns True if Gremlin is paused, False otherwise.

        Returns:
            True if Gremlin is paused, False otherwise.
        """
        return not event_handler.EventHandler().process_callbacks

    @Property(bool, notify=activityChanged)
    def gremlinActive(self) -> bool:
        """Returns whether or not a Gremlin profile is active.

        Returns:
            True if a profile is active, False otherwise
        """
        return self.runner.is_running()

    @Slot()
    def toggleActiveState(self) -> None:
        """Toggles Gremlin between active and inactive."""
        self.activate_gremlin(not self.runner.is_running())

    def activate_gremlin(self, activate: bool) -> None:
        """Sets the activity state of Gremlin.

        Args:
            activate: If True activates the profile, if False deactivates
                the profile if one is active
        """
        if activate:
            # Generate the code for the profile and run it
            # self._profile_auto_activated = False
            shared_state.set_suspend_input_highlighting(True)
            self.runner.start(
                self.profile,
                self.profile.modes.first_mode
            )
            #self.ui.tray_icon.setIcon(QtGui.QIcon("gfx/icon_active.ico"))
        else:
            # Stop running the code
            self.runner.stop()
            if self.config.value("global", "general", "input-highlighting"):
                shared_state.set_suspend_input_highlighting(False)
            # self._update_statusbar_active(False)
            # self._profile_auto_activated = False
            # current_tab = self.ui.devices.currentWidget()
            # if type(current_tab) in [
            #     gremlin.ui.device_tab.JoystickDeviceTabWidget,
            #     gremlin.ui.device_tab.KeyboardDeviceTabWidget
            # ]:
            #     self.ui.devices.currentWidget().refresh()
            # self.ui.tray_icon.setIcon(QtGui.QIcon("gfx/icon.ico"))
        self.activityChanged.emit()

    def minimize(self) -> None:
        """Minimizes the application to the taskbar."""
        root_window = self.engine.rootObjects()[0]
        root_window.setVisibility(QtGui.QWindow.Visibility.Minimized)

    @Slot(InputIdentifier, result=int)
    def getActionCount(self, identifier: InputIdentifier) -> int:
        """Returns the number of actions associated with an input.

        Args:
            identifier: Identifier of a specific InputItem

        Returns:
            Number of actions associated with the InputItem specified by
            the provided identifier
        """
        if identifier is None:
            return 0

        try:
            item = self.profile.get_input_item(
                identifier.device_guid,
                identifier.input_type,
                identifier.input_id,
                self.ui_state.currentMode,
                False
            )
            return len(item.action_sequences)
        except error.ProfileError as e:
            return 0

    @Slot(InputIdentifier, int, result=InputItemModel)
    def getInputItem(
        self,
        identifier: InputIdentifier,
        enumeration_index: int
    ) -> InputItemModel | None:
        """Returns a model for a specified InputItem.

        Args:
            identifier: Identifier of a specific InputItem
            enumeration_index: Index of the model in the device input listing

        Returns:
            Model instance representing the specified InputItem
        """
        if identifier is None:
            return
        try:
            item = self.profile.get_input_item(
                identifier.device_guid,
                identifier.input_type,
                identifier.input_id,
                self.ui_state.currentMode,
                True
            )
            return InputItemModel(item, enumeration_index, self)
        except error.ProfileError as e:
            pass

    @QtCore.Slot()
    def pauseInputHighlighting(self) -> None:
        shared_state.set_suspend_input_highlighting(True)

    @QtCore.Slot()
    def resumeInputHighlighting(self) -> None:
        shared_state.set_suspend_input_highlighting(False)

    @Slot(str, int, result=bool)
    def isActionExpanded(self, uuid_str: str, index: int) -> bool:
        """Returns whether or not a specific action is expanded in the UI.

        Args:
            uuid: uuid of the action
            index: index of the particular action

        Returns:
            True if the action is expanded, False otherwise
        """
        return self._action_state.get((uuid.UUID(uuid_str), index), True)

    @Slot(str, int, bool)
    def setIsActionExpanded(
        self,
        uuid_str: str,
        index: int,
        is_expanded: bool
    ) -> None:
        """Sets a specific action's expanded state.

        Args:
            uuid: uuid of the action
            index: index of the particular action
            is_expanded: True if the action is expanded, False otherwise
        """
        self._action_state[(uuid.UUID(uuid_str), index)] = bool(is_expanded)

    @Property(bool, notify=propertyChanged)
    def useDarkMode(self) -> bool:
        """Returns whether or not dark mode is enabled.

        Returns:
            True if dark mode is enabled, False otherwise
        """
        return self.config.value("global", "general", "dark-mode")

    @Property(type=list, notify=recentProfilesChanged)
    def recentProfiles(self) -> List[str]:
        """Returns a list of recently used profiles.

        Returns:
            List of recently used profiles
        """
        return self.config.value("global", "internal", "recent-profiles")

    @Slot()
    def newProfile(self) -> None:
        """Creates a new profile."""
        self.activate_gremlin(False)
        self.profile = profile.Profile()
        self.profileChanged.emit()
        signal.reloadCurrentInputItem.emit()
        signal.reloadUi.emit()

    @Slot(str)
    def saveProfile(self, fpath: str) -> None:
        """Saves the current profile in the given path.

        Args:
            path: Path to the file in which to store the current profile
        """
        self.profile.fpath = fpath
        self.profile.to_xml(self.profile.fpath)
        self.config.set("global", "internal", "last-profile", fpath)
        self.windowTitleChanged.emit()

    @Slot(result=str)
    def profilePath(self) -> str:
        """Returns the current profile's path.

        Returns:
            File path of the current profile
        """
        path = self.profile.fpath
        return "" if path is None else str(path)

    @Slot(str)
    def loadProfile(self, fpath: str) -> None:
        """Loads a profile from the specified path.

        Args:
            fpath: Path to the file containing the profile to load
        """
        self._load_profile(fpath)
        self.config.set("global", "internal", "last-profile", fpath)
        self.profileChanged.emit()

    @Property(bool, notify=propertyChanged)
    def profileContainsUnsavedChanges(self) -> bool:
        """Returns whether or not the current profile contains unsaved changes.

        Returns:
            True if the current profile contains unsaved changes, False
            otherwise
        """
        return self.profile.has_unsaved_changes()

    @Property(type=ScriptListModel, notify=profileChanged)
    def scriptListModel(self) -> ScriptListModel:
        return ScriptListModel(self.profile.scripts, self)

    @Property(type=str, notify=propertyChanged)
    def currentMode(self) -> str:
        return mode_manager.ModeManager().current.name

    @Property(type=str, notify=windowTitleChanged)
    def windowTitle(self) -> str:
        """Returns the current window title.

        Returns:
            String to use as window title
        """
        if self.profile and self.profile.fpath:
            return str(self.profile.fpath)
        else:
            return ""

    def _load_profile(self, fpath: str) -> None:
        """Attempts to load the profile at the provided path.

        Args:
            fpath: The file path from which to load the profile
        """
        # Check if there exists a file with this path.
        if not os.path.isfile(fpath):
            display_error(f"Unable to load profile '{fpath}', no such file.")
            return

        # Disable the program if it is running when we're loading a
        # new profile.
        self.activate_gremlin(False)

        # Attempt to load the new profile.
        try:
            LogicalDevice().reset()
            new_profile = profile.Profile()
            profile_was_converted = new_profile.from_xml(fpath)

            profile_folder = os.path.dirname(fpath)
            if profile_folder not in sys.path:
                sys.path = list(set(sys.path))
                sys.path.insert(0, profile_folder)

            self.profile = new_profile

            # Save the profile at this point if it was converted from a prior
            # profile version, as otherwise the change detection logic will
            # trip over insignificant input item additions.
            if profile_was_converted:
                self.profile.to_xml(fpath)
        except (KeyError, TypeError) as e:
            # An error occurred while parsing an existing profile, creating
            # an empty profile instead.
            logging.getLogger("system").exception(
                "Invalid profile content:\n{}".format(e)
            )
            self.newProfile()
        except error.ProfileError as e:
            # Parsing the profile went wrong, stop loading and start with an
            # empty profile.
            self.newProfile()
            display_error(f"Failed to load the profile {fpath}.", str(e))
