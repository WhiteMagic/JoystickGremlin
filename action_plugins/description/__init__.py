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


import os
from PyQt5 import QtWidgets
from xml.etree import ElementTree

from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
import gremlin.ui.input_item


class DescriptionActionWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget for the description action."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent=parent)
        assert(isinstance(action_data, DescriptionAction))

    def _create_ui(self):
        self.inner_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel("<b>Action description</b>")
        self.description = QtWidgets.QLineEdit()
        self.description.textChanged.connect(self._update_description)
        self.inner_layout.addWidget(self.label)
        self.inner_layout.addWidget(self.description)
        self.main_layout.addLayout(self.inner_layout)

    def _populate_ui(self):
        self.description.setText(self.action_data.description)

    def _update_description(self, value):
        self.action_data.description = value


class DescriptionActionFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)

    def process_event(self, event, value):
        return True


class DescriptionAction(AbstractAction):

    """Action for adding a description to a set of actions."""

    name = "Description"
    tag = "description"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = DescriptionActionFunctor
    widget = DescriptionActionWidget

    def __init__(self, parent):
        super().__init__(parent)
        self.description = ""

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        return False

    def _parse_xml(self, node):
        self.description = gremlin.profile.safe_read(
            node, "description", str, ""
        )

    def _generate_xml(self):
        node = ElementTree.Element("description")
        node.set("description", str(self.description))
        return node

    def _is_valid(self):
        return True


version = 1
name = "description"
create = DescriptionAction
