# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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

import gremlin.plugin_manager


class Backend(QtCore.QObject):

    def __init__(self, parent=None):
        super().__init__(parent)

        #self._action_list = QtCore.QVariantList()#QtCore.QStringListModel(["Remap", "Macro", "Response Curve"])
        #self._action_list.append("Remap")
        #self._action_list = ["Remap", "Macro"]

    @Property(type="QVariantList", constant=True)
    def action_list(self):
        print(gremlin.plugin_manager.ActionPlugins().repository.keys())
        #print(self._action_list.rowCount())
        #return self._action_list
        return list(gremlin.plugin_manager.ActionPlugins().repository.keys())