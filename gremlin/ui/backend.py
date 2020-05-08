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


from PySide2 import QtCore
from PySide2.QtCore import Property, Signal, Slot

from gremlin import error
from gremlin import plugin_manager
from gremlin import profile

from gremlin.types import InputType
from gremlin.ui.device import InputIdentifier
from gremlin.ui.profile import InputItemModel


class Backend(QtCore.QObject):

    """Allows interfacing between the QML frontend and the Python backend."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.profile = None

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

    @Slot(str)
    def saveProfile(self, fpath):
        self.profile.fpath = QtCore.QUrl(fpath).toLocalFile()
        self.profile.to_xml(self.profile.fpath)

    @Slot(result=str)
    def profilePath(self) -> str:
        return self.profile.fpath

    @Slot(str)
    def loadProfile(self, fpath) -> None:
        pass

    @Property(type="QVariantList", constant=True)
    def action_list(self):
        return list(plugin_manager.ActionPlugins().repository.keys())

    @Slot(str)
    def add_action(self, action_name: str):
        print(action_name)

    @Slot(str)
    def load_profile(self, fpath: str) -> None:
        # TODO: copy code and logic from the old joystick_gremlin.py file
        #       for handling of profile loading
        self.profile = profile.Profile()
        self.profile.from_xml(fpath)