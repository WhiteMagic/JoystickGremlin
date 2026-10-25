# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import dataclasses
import logging
import os
import sys
import uuid
from pathlib import Path

from PySide6 import (
    QtCore,
    QtGui,
    QtQml,
)

import dill
import gremlin.ui.type_aliases as ta
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
    types,
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
from gremlin.ui.util import (
    read_release_notes,
    to_local_path,
    updated_recent_profiles,
)

QML_IMPORT_NAME = "Gremlin.UI"
QML_IMPORT_MAJOR_VERSION = 1

_max_recent_profiles = 5


@dataclasses.dataclass(frozen=True)
class InputSelection:
    """Input selected on a device together with its index in the input list."""

    identifier: InputIdentifier
    index: int


@ta.QmlElement
class UIState(QtCore.QObject):
    """Holds the state of the UI to simplify complex interactions.

    The various UI elements retrieve the state they should be in from this
    instance while being able to set state only via method calls.
    """

    deviceChanged = QtCore.Signal()
    inputChanged = QtCore.Signal()
    modeChanged = QtCore.Signal()
    tabChanged = QtCore.Signal()
    selectIndex = QtCore.Signal(int)

    _NO_SELECTION = InputSelection(InputIdentifier(), 0)

    def __init__(self, parent: ta.OQO = None) -> None:
        super().__init__(parent)

        self._current_device = dill.UUID_Invalid
        self._selection_by_device: dict[uuid.UUID | None, InputSelection] = {}
        self._current_mode = "Default"
        self._current_tab = "physical"

        event_handler.EventListener().device_change_event.connect(self._device_change)
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

    @QtCore.Slot(str)
    def setCurrentDevice(self, device_name: str) -> None:
        device_uuid = uuid.UUID(device_name)
        if device_uuid != self._current_device:
            self._current_device = device_uuid
            self.deviceChanged.emit()
            self.inputChanged.emit()

    @QtCore.Slot(InputIdentifier, int)
    def setCurrentInput(self, input: InputIdentifier, index: int) -> None:
        # Takes ownership of the identifier.
        previous = self._selection_by_device.get(input.device_guid)
        if (
            previous is not None
            and previous.identifier == input
            and previous.index == index
        ):
            input.deleteLater()
        else:
            input.setParent(self)
            if previous is not None:
                previous.identifier.deleteLater()
            self._selection_by_device[input.device_guid] = InputSelection(input, index)
            self.inputChanged.emit()

    @QtCore.Slot(str)
    def setCurrentMode(self, mode_name: str) -> None:
        if mode_name != self._current_mode:
            self._current_mode = mode_name
            self.modeChanged.emit()
            self.inputChanged.emit()

    def reset_mode(self, mode_name: str) -> None:
        # Emits even if unchanged, as the profile's mode list may have changed.
        self._current_mode = mode_name
        self.modeChanged.emit()
        self.inputChanged.emit()

    @QtCore.Slot(str)
    def setCurrentTab(self, tab: str) -> None:
        if tab != self._current_tab:
            self._current_tab = tab
            self.tabChanged.emit()

    @QtCore.Property(str, notify=deviceChanged)
    def currentDevice(self) -> str:
        return str(self._current_device).upper()

    @QtCore.Property(InputIdentifier, notify=inputChanged)
    def currentInput(self) -> InputIdentifier:
        return self._current_selection().identifier

    @QtCore.Property(int, notify=inputChanged)
    def currentInputIndex(self) -> int:
        return self._current_selection().index

    @QtCore.Property(str, notify=modeChanged)
    def currentMode(self) -> str:
        return self._current_mode

    @QtCore.Property(str, notify=tabChanged)
    def currentTab(self) -> str:
        return self._current_tab

    def _current_selection(self) -> InputSelection:
        return self._selection_by_device.get(self._current_device, self._NO_SELECTION)

    def __str__(self) -> str:
        selection = self._current_selection()
        return (
            f"{self._current_device} {selection.identifier.input_id} "
            + f"{selection.index}  {self._current_tab}"
        )


@common.SingletonDecorator
class Backend(QtCore.QObject):
    """Allows interfacing between the QML frontend and the Python backend."""

    windowTitleChanged = QtCore.Signal()
    profileChanged = QtCore.Signal()
    recentProfilesChanged = QtCore.Signal()
    inputConfigurationChanged = QtCore.Signal()
    activityChanged = QtCore.Signal()
    propertyChanged = QtCore.Signal()
    uiChanged = QtCore.Signal()
    quitRequested = QtCore.Signal()

    def __init__(
        self, engine: QtQml.QQmlApplicationEngine, parent: ta.OQO = None
    ) -> None:
        super().__init__(parent)

        self.engine = engine
        self.config = config.Configuration()
        self._show_release_notes = self._update_last_run_version()
        self.profile = profile.Profile()
        shared_state.current_profile = self.profile
        self._last_error = ""
        self.runner = code_runner.CodeRunner()
        self.ui_state = UIState(self)
        self.process_monitor = process_monitor.ProcessMonitor()
        self.process_monitor.start()

        self.joystick_change_monitor = device_helpers.JoystickInputSignificant()

        self._current_input_item_model: InputItemModel | None = None
        self._script_list_model = ScriptListModel(self.profile.scripts, self)

        # Hookup various mode change related callbacks
        mm = mode_manager.ModeManager()
        mm.modeChanged.connect(self._emit_change)
        self.profileChanged.connect(self._profile_change_handler)
        self.process_monitor.process_changed.connect(self._active_process_changed_cb)

        event_handler.EventHandler().is_active.connect(
            lambda: self.activityChanged.emit()
        )
        event_handler.EventListener().device_change_event.connect(self._device_change)
        event_handler.EventListener().joystick_event.connect(self._highlight_input)

        self.profileChanged.emit()

    def _highlight_input(self, event: types.Event) -> None:
        if (
            not self.config.value("global", "behavior", "input-highlighting")
            or shared_state.suspend_input_highlighting()
        ):
            return

        current_input = self.ui_state.currentInput
        if (
            self.ui_state.currentTab == "physical"
            and current_input.device_guid == event.device_guid
            and self.joystick_change_monitor.should_process(event)
        ):
            new_input = InputIdentifier(
                event.device_guid, event.event_type, event.identifier
            )
            if current_input.linear_index != new_input.linear_index:
                signal.setInputIndex.emit(new_input.linear_index)

    def _profile_change_handler(self) -> None:
        # Update shared state before any other parts update.
        shared_state.current_profile = self.profile
        mode_manager.ModeManager().reset()
        self._script_list_model.set_script_manager(self.profile.scripts)

        # Emit signals for various parts of the system.
        self.windowTitleChanged.emit()
        signal.reloadUi.emit()
        signal.profileChanged.emit()
        self.ui_state.reset_mode(mode_manager.ModeManager().current.name)

    def _device_change(self) -> None:
        behavior = self.config.value("global", "behavior", "device-change-behavior")
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

    @QtCore.Slot()
    def emitConfigChanged(self) -> None:
        signal.configChanged.emit()
        audio_player.AudioPlayer().refresh()

    def check_for_updates(self) -> None:
        if self.config.value("global", "general", "check-for-updates"):
            # Attempt to retrieve the latest version information, if this fails
            # silently abort.
            version_string = util.latest_gremlin_version()
            if version_string is None:
                return

            # Parse version strings into semantic versions and compare them. If
            # a newer version is available show a notification. Store the new
            # version so the user is only ever notified once.
            version = util.parse_version(version_string)
            last_version = util.parse_version(
                self.config.value("global", "internal", "last-known-version")
            )
            if last_version < version:
                version_string = ".".join(str(x) for x in version)
                signal.showNotification.emit(
                    "New version available",
                    f"A newer version of Joystick Gremlin, {version_string} "
                    f"is available.",
                )
                self.config.set(
                    "global", "internal", "last-known-version", version_string
                )

    def _update_last_run_version(self) -> bool:
        """Records the running version and reports if release notes are due.

        Returns:
            True if the release notes should be shown on startup.
        """
        current_version = util.get_code_version()
        show_notes = util.should_show_release_notes(
            self.config.value("global", "internal", "last-run-version"),
            current_version,
        )
        self.config.set("global", "internal", "last-run-version", current_version)
        return show_notes

    @QtCore.Property(bool, constant=True)
    def showReleaseNotesOnStartup(self) -> bool:
        return self._show_release_notes and read_release_notes().strip() != ""

    def _active_process_changed_cb(self, path: str) -> None:
        """Handles changes to the active process.

        If the profile auto-loading option is disabled nothing is done.
        Otherwise the profile associated with the newly active process is
        loaded and then activated. Should
        """
        if not self.config.value("profile", "automation", "enable-auto-loading"):
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

    @QtCore.Property(str, notify=propertyChanged)
    def gremlinVersion(self) -> str:
        """Returns the current version of Gremlin.

        Returns:
            The current version of Gremlin.
        """
        return util.get_code_release()

    @QtCore.Property(UIState, notify=uiChanged)
    def uiState(self) -> UIState:
        return self.ui_state

    @QtCore.Property(bool, notify=activityChanged)
    def gremlinPaused(self) -> bool:
        """Returns True if Gremlin is paused, False otherwise.

        Returns:
            True if Gremlin is paused, False otherwise.
        """
        return not event_handler.EventHandler().process_callbacks

    @QtCore.Property(bool, notify=activityChanged)
    def gremlinActive(self) -> bool:
        """Returns whether or not a Gremlin profile is active.

        Returns:
            True if a profile is active, False otherwise
        """
        return self.runner.is_running()

    @QtCore.Slot()
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
            shared_state.set_suspend_input_highlighting(True)
            self.runner.start(self.profile)
        else:
            # Stop running the code
            self.runner.stop()
            if self.config.value("global", "behavior", "input-highlighting"):
                shared_state.set_suspend_input_highlighting(False)
        self.activityChanged.emit()

    def minimize(self) -> None:
        """Minimizes the application to the taskbar."""
        root_window = self.engine.rootObjects()[0]
        root_window.setVisibility(QtGui.QWindow.Visibility.Minimized)

    @QtCore.Slot(InputIdentifier, result=int)
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
                False,
            )
            return len(item.action_sequences)
        except error.ProfileError:
            return 0

    @QtCore.Slot(InputIdentifier, int, result=InputItemModel)
    def getInputItem(
        self, identifier: InputIdentifier, enumeration_index: int
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
                True,
            )
            if self._current_input_item_model is not None:
                self._current_input_item_model.dispose()
                self._current_input_item_model.deleteLater()
            model = InputItemModel(item, enumeration_index, self)
            self._current_input_item_model = model
            return model
        except error.ProfileError:
            pass

    @QtCore.Slot()
    def pauseInputHighlighting(self) -> None:
        shared_state.set_suspend_input_highlighting(True)

    @QtCore.Slot()
    def resumeInputHighlighting(self) -> None:
        shared_state.set_suspend_input_highlighting(False)

    @QtCore.Property(type=list, notify=recentProfilesChanged)
    def recentProfiles(self) -> list[str]:
        """Returns a list of recently used profiles.

        Returns:
            List of recently used profiles
        """
        return self.config.value("global", "internal", "recent-profiles")

    @QtCore.Slot()
    def newProfile(self) -> None:
        """Creates a new profile."""
        self.activate_gremlin(False)
        self.profile = profile.Profile()
        self.profileChanged.emit()
        signal.reloadCurrentInputItem.emit()
        signal.reloadUi.emit()

    @QtCore.Slot(str)
    def saveProfile(self, qml_url: str) -> None:
        """Saves the current profile in the given path.

        Args:
            qml_url: QML url to the path to store the current profile in
        """
        path = to_local_path(qml_url)
        self.profile.fpath = path
        self.profile.to_xml(self.profile.fpath)
        self._record_profile_use(path)
        self.windowTitleChanged.emit()

    @QtCore.Slot(result=str)
    def profilePath(self) -> str:
        """Returns the current profile's path.

        Returns:
            File path of the current profile
        """
        path = self.profile.fpath
        return "" if path is None else str(path)

    @QtCore.Slot(str)
    def loadProfile(self, fpath: str) -> None:
        """Loads a profile from the specified path.

        Args:
            fpath: File path to the profile file to load
        """
        local_path = to_local_path(fpath)
        if self._load_profile(str(local_path)):
            self._record_profile_use(local_path)
        self.profileChanged.emit()
        signal.reloadCurrentInputItem.emit()

    @QtCore.Property(bool, notify=propertyChanged)
    def profileContainsUnsavedChanges(self) -> bool:
        """Returns whether or not the current profile contains unsaved changes.

        Returns:
            True if the current profile contains unsaved changes, False
            otherwise
        """
        return self.profile.has_unsaved_changes()

    @QtCore.Property(type=ScriptListModel, constant=True)
    def scriptListModel(self) -> ScriptListModel:
        return self._script_list_model

    @QtCore.Property(type=str, notify=propertyChanged)
    def currentMode(self) -> str:
        return mode_manager.ModeManager().current.name

    @QtCore.Property(type=str, notify=windowTitleChanged)
    def windowTitle(self) -> str:
        """Returns the current window title.

        Returns:
            String to use as window title
        """
        if self.profile and self.profile.fpath:
            return str(self.profile.fpath)
        else:
            return ""

    def _record_profile_use(self, path: Path) -> None:
        """Records the given profile as the most recently used one.

        Args:
            path: file path of the profile that was loaded or saved
        """
        self.config.set("global", "internal", "last-profile", str(path))
        self.config.set(
            "global",
            "internal",
            "recent-profiles",
            updated_recent_profiles(
                self.config.value("global", "internal", "recent-profiles"),
                path,
                _max_recent_profiles,
            ),
        )
        self.recentProfilesChanged.emit()

    def _load_profile(self, fpath: str) -> bool:
        """Attempts to load the profile at the provided path.

        Args:
            fpath: The file path from which to load the profile

        Returns:
            True if the profile was loaded, False otherwise
        """
        # Check if there exists a file with this path.
        if not os.path.isfile(fpath):
            display_error(f"Unable to load profile '{fpath}', no such file.")
            return False

        # Disable the program if it is running when we're loading a
        # new profile.
        self.activate_gremlin(False)

        # Attempt to load the new profile.
        try:
            LogicalDevice().reset()
            new_profile = profile.Profile()
            profile_was_converted = new_profile.from_xml(fpath)

            profile_folder = os.path.normcase(os.path.abspath(os.path.dirname(fpath)))
            if profile_folder not in [
                os.path.normcase(os.path.abspath(path)) for path in sys.path
            ]:
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
            logging.getLogger("system").exception(f"Invalid profile content: {e}")
            self.newProfile()
            return False
        except error.ProfileError as e:
            # Parsing the profile went wrong, stop loading and start with an
            # empty profile.
            self.newProfile()
            display_error(f"Failed to load the profile {fpath}.", str(e))
            return False
        return True
