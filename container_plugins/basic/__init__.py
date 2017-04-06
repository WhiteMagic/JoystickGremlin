# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2017 Lionel Ott
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

from xml.etree import ElementTree

from mako.template import Template

import gremlin
import gremlin.ui.input_item


class BasicContainerWidget(gremlin.ui.input_item.AbstractContainerWidget):

    def __init__(self, profile_data, parent=None):
        super().__init__(profile_data, parent)

    def _create_ui(self):
        if len(self.profile_data.actions) > 0:
            assert len(self.profile_data.actions) == 1
            action_widget = self.profile_data.actions[0].widget(
                self.profile_data.actions[0]
            )
            self.main_layout.addWidget(self._add_action_widget(action_widget))
        else:
            if self.profile_data.get_device_type() == gremlin.common.DeviceType.VJoy:
                action_selector = gremlin.ui.common.ActionSelector(
                    gremlin.common.DeviceType.VJoy
                )
            else:
                action_selector = gremlin.ui.common.ActionSelector(
                    self.profile_data.parent.input_type
                )
            action_selector.action_added.connect(self._add_action)
            self.main_layout.addWidget(action_selector)

    def _add_action(self, action_name):
        plugin_manager = gremlin.plugin_manager.ActionPlugins()
        action_item = plugin_manager.get_class(action_name)(self.profile_data)
        self.profile_data.add_action(action_item)
        self.modified.emit()

    def _handle_interaction(self, widget, action):
        if action == gremlin.ui.input_item.ActionWrapper.Interactions.Edit:
            self.profile_data.actions = []
            self.modified.emit()

    def _get_window_title(self):
        if len(self.profile_data.actions) > 0:
            return self.profile_data.actions[0].name
        else:
            return "Basic"


class BasicContainer(gremlin.base_classes.AbstractContainer):

    name = "Basic"
    tag = "basic"
    widget = BasicContainerWidget
    input_types = [
        gremlin.common.InputType.JoystickButton,
        gremlin.common.InputType.Keyboard
    ]
    interaction_types = [
        gremlin.ui.input_item.ActionWrapper.Interactions.Edit,
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

    def _parse_xml(self, node):
        pass

    def _generate_xml(self):
        node = ElementTree.Element("container")
        node.set("type", "basic")
        for action in self.actions:
            node.append(action.to_xml())
        return node

    def _generate_code(self):
        tpl = Template(filename="container_plugins/chain/global.tpl")
        code = gremlin.profile.CodeBlock(
            static_code=tpl.render(
                entry=self,
                id=gremlin.profile.ProfileData.next_code_id
            )
        )
        for action in self.actions:
            block = action.to_code()
            code.append(block)
        return code

    def _is_valid(self):
        return len(self.actions) == 1


# Plugin definitions
version = 1
name = "basic"
create = BasicContainer
