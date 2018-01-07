# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2018 Lionel Ott
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
from gremlin.ui.input_item import AbstractActionWidget



class NoOpActionWidget(AbstractActionWidget):

    """Widget for the NoOp action."""

    def __init__(self, action_data, parent=None):
        super().__init__(action_data, parent)
        assert(isinstance(action_data, NoOpAction))

    def _create_ui(self):
        self.label = QtWidgets.QLabel("NoOp")
        self.main_layout.addWidget(self.label)

    def _populate_ui(self):
        pass


class NoOpActionFunctor(AbstractFunctor):

    """Functor, executing the NoOp action."""

    def __init__(self, action):
        super().__init__(action)

    def process_event(self, event, value):
        return True


class NoOpAction(AbstractAction):

    """Action which performs no operation."""

    name = "NoOp"
    tag = "noop"

    default_button_activation = (True, False)
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    functor = NoOpActionFunctor
    widget = NoOpActionWidget

    def __init__(self, parent):
        super().__init__(parent)

    def icon(self):
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        return False

    def _parse_xml(self, node):
        pass

    def _generate_xml(self):
        return ElementTree.Element("noop")

    def _is_valid(self):
        return True


version = 1
name = "noop"
create = NoOpAction