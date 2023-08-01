# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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
import os
import sys
from typing import List
import uuid

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import code_runner, common, config, error, \
    profile, shared_state, types
from gremlin.signal import signal

from gremlin.ui.device import InputIdentifier, IODevice
from gremlin.ui.profile import InputItemModel


config.Configuration().register(
    "global",
    "common",
    "recent_profiles",
    types.PropertyType.List,
    [],
    "List of recently opened profiles",
    False
)


@common.SingletonDecorator
class Backend(QtCore.QObject):

    """Allows interfacing between the QML frontend and the Python backend."""

    windowTitleChanged = Signal()
    recentProfilesChanged = Signal()
    lastErrorChanged = Signal()
    inputConfigurationChanged = Signal()
    activityChanged = Signal()


    def __init__(self, parent=None):
        super().__init__(parent)

        self.profile = profile.Profile()
        self._last_error = ""
        self._action_state = {}
        self.runner = code_runner.CodeRunner()

    @Property(bool, notify=activityChanged)
    def gremlinActive(self) -> bool:
        """Returns whether or not a Gremlin profile is active.

        Returns:
            True if a profile is active, False otherwise
        """
        return self.runner.is_running()

    @Slot()
    def toggleActiveState(self):
        """Toggles Gremlin between active and inactive."""
        self.activate_gremlin(not self.runner.is_running())

    def activate_gremlin(self, activate: bool):
        """Sets the activity state of Gremlin.

        Args:
            activate: If True activates the profile, if False deactivates
                the profile if one is active
        """
        if activate:
            # Generate the code for the profile and run it
            # self._profile_auto_activated = False
            self.runner.start(
                self.profile,
                "Default"
            )
            #self.ui.tray_icon.setIcon(QtGui.QIcon("gfx/icon_active.ico"))
        else:
            # Stop running the code
            self.runner.stop()
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
                False
            )
            return len(item.action_sequences)
        except error.ProfileError as e:
            return 0

    @Slot(InputIdentifier, result=InputItemModel)
    def getInputItem(self, identifier: InputIdentifier) -> InputItemModel:
        """Returns a model for a specified InputItem.

        Args:
            identifier: Identifier of a specific InputItem

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
                True
            )
            return InputItemModel(item, self)
        except error.ProfileError as e:
            print(e)

    @Slot(result=IODevice)
    def getIODevice(self) -> IODevice:
        return IODevice(self)

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

    @Property(type=list, notify=recentProfilesChanged)
    def recentProfiles(self) -> List[str]:
        """Returns a list of recently used profiles.

        Returns:
            List of recently used profiles
        """
        return config.Configuration().value("global", "common", "recent_profiles")

    @Slot()
    def newProfile(self) -> None:
        """Creates a new profile."""
        self.activate_gremlin(False)
        self.profile = profile.Profile()
        shared_state.current_profile = self.profile
        self.windowTitleChanged.emit()
        signal.reloadUi.emit()

    @Slot(str)
    def saveProfile(self, fpath: str) -> None:
        """Saves the current profile in the given path.

        Args:
            path: Path to the file in which to store the current profile
        """
        self.profile.fpath = fpath
        self.profile.to_xml(self.profile.fpath)
        self.windowTitleChanged.emit()

    @Slot(result=str)
    def profilePath(self) -> str:
        """Returns the current profile's path.

        Returns:
            File path of the current profile
        """
        return self.profile.fpath

    @Slot(str)
    def loadProfile(self, fpath):
        """Loads a profile from the specified path.

        Args:
            fpath: Path to the file containing the profile to load
        """
        self._load_profile(fpath)
        signal.reloadUi.emit()

    @Property(type=str, notify=windowTitleChanged)
    def windowTitle(self) -> str:
        """Returns the current window title.

        Returns:
            String to use as window title
        """
        if self.profile and self.profile.fpath:
            return self.profile.fpath
        else:
            return ""

    @Property(str, notify=lastErrorChanged)
    def lastError(self) -> str:
        """Returns the last error that occurred.

        Returns:
            Last error to occurr
        """
        return self._last_error

    def display_error(self, msg: str) -> None:
        """Forces the display of a specific error message.

        Args:
            msg: The error message to display
        """
        self._last_error = msg
        self.lastErrorChanged.emit()

    def _load_profile(self, fpath):
        """Attempts to load the profile at the provided path.

        Args:
            fpath: The file path from which to load the profile
        """
        # Check if there exists a file with this path
        if not os.path.isfile(fpath):
            self.display_error(
                f"Unable to load profile '{fpath}', no such file."
            )
            return

        # Disable the program if it is running when we're loading a
        # new profile
        # TODO: implement this for QML
        #self.ui.actionActivate.setChecked(False)
        #self.activate(False)

        # Attempt to load the new profile
        try:
            # self.profile = profile.Profile()
            # self.profile.from_xml(fpath)

            new_profile = profile.Profile()
            profile_was_converted = new_profile.from_xml(fpath)

            profile_folder = os.path.dirname(fpath)
            if profile_folder not in sys.path:
                sys.path = list(set(sys.path))
                sys.path.insert(0, profile_folder)

            # self._sanitize_profile(new_profile)
            self.profile = new_profile
            # self._profile_fname = fname
            # self._update_window_title()
            shared_state.current_profile = self.profile
            self.windowTitleChanged.emit()

            # Save the profile at this point if it was converted from a prior
            # profile version, as otherwise the change detection logic will
            # trip over insignificant input item additions.
            if profile_was_converted:
                self.profile.to_xml(fpath)
        except (KeyError, TypeError) as e:
            # An error occurred while parsing an existing profile,
            # creating an empty profile instead
            logging.getLogger("system").exception(
                "Invalid profile content:\n{}".format(e)
            )
            self.newProfile()
        except error.ProfileError as e:
            # Parsing the profile went wrong, stop loading and start with an
            # empty profile
            #cfg = config.Configuration()
            self.newProfile()
            self.display_error(
                f"Failed to load the profile {fpath} due to:\n\n{e}"
            )