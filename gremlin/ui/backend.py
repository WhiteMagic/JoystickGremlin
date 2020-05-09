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

import logging
import os
import sys
import time
from typing import List

from PySide2 import QtCore
from PySide2.QtCore import Property, Signal, Slot

from gremlin import config
from gremlin import error
from gremlin import plugin_manager
from gremlin import profile
from gremlin import shared_state

from gremlin.types import InputType
from gremlin.ui.device import InputIdentifier
from gremlin.ui.profile import InputItemModel


class Backend(QtCore.QObject):

    """Allows interfacing between the QML frontend and the Python backend."""

    windowTitleChanged = Signal()
    recentProfilesChanged = Signal()
    lastErrorChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.profile = None
        self._last_error = ""

    @Slot(InputIdentifier, result=InputItemModel)
    def getInputItem(self, identifier: InputIdentifier) -> InputItemModel:
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

    @Property(type="QVariantList", notify=recentProfilesChanged)
    def recentProfiles(self) -> "QVariantList":
        return config.Configuration().recent_profiles

    @Slot()
    def newProfile(self) -> None:
        # TODO: implement this for QML
        # self.ui.actionActivate.setChecked(False)
        # self.activate(False)

        self.profile = profile.Profile()
        shared_state.current_profile = self.profile
        self.windowTitleChanged.emit()

    @Slot(str)
    def saveProfile(self, fpath) -> None:
        self.profile.fpath = QtCore.QUrl(fpath).toLocalFile()
        self.profile.to_xml(self.profile.fpath)
        self.windowTitleChanged.emit()

    @Slot(result=str)
    def profilePath(self) -> str:
        return self.profile.fpath

    @Slot(str)
    def loadProfile(self, fpath):
        self._load_profile(QtCore.QUrl(fpath).toLocalFile())

    @Property(type="QVariantList", constant=True)
    def action_list(self):
        return list(plugin_manager.ActionPlugins().repository.keys())

    @Slot(str)
    def add_action(self, action_name: str):
        print(action_name)

    @Property(type=str, notify=windowTitleChanged)
    def windowTitle(self) -> str:
        if self.profile and self.profile.fpath:
            return self.profile.fpath
        else:
            return ""

    @Property(str, notify=lastErrorChanged)
    def lastError(self) -> str:
        return self._last_error

    def display_error(self, msg):
        self._last_error = msg
        self.lastErrorChanged.emit()

    def _load_profile(self, fpath):
        """Attempts to load the profile at the provided path."""
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
            cfg = gremlin.config.Configuration()
            cfg.last_profile = None
            self.new_profile()
            gremlin.util.display_error(
                "Failed to load the profile {} due to:\n\n{}".format(
                    fname, e
                )
            )