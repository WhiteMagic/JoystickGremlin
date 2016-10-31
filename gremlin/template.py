# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
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
from xml.dom import minidom

import gremlin.profile
import gremlin.util


class Template(object):

    """Manages creation and usage of profile templates.

    A template is an abstracted profile which contains the action sets used in
    a profile but is not bound to particular input devices or inputs. As such
    this allows having the logical actions separated from the physical inputs
    and as such templates allow sharing of configurations independent of
    physical devices.
    """

    def __init__(self, profile_data):
        self._profile_data = profile_data

        self._mode_tree = self._profile_data.build_inheritance_tree()
        self._modes = {}
        for mode in gremlin.util.mode_list(self._profile_data):
            self._modes[mode] = []

        self._parse_profile()
        self.create_xml()

    def load_xml(self, fname):
        tree = ElementTree.parse(fname)
        root = tree.getroot()

        for mode in root.findall("./mode"):
            print(mode.attrib["name"])

    def create_xml(self):
        # Create root node
        root = ElementTree.Element("template")
        root.set("version", "1")

        # Add all modes
        for mode, data in self._modes.items():
            node = ElementTree.Element("mode")
            node.set("name", mode)

            for entry in data:
                input_node = entry.to_xml()
                del input_node.attrib["id"]
                node.append(input_node)

            root.append(node)

        # Serialize XML document
        ugly_xml = ElementTree.tostring(root, encoding="unicode")
        dom_xml = minidom.parseString(ugly_xml)
        with open("test.xml", "w") as out:
            out.write(dom_xml.toprettyxml(indent="    "))

        self.load_xml("test.xml")

    def _parse_profile(self):
        for device in self._profile_data.devices.values():
            # print("Device {}".format(device.name))

            for mode in device.modes.values():
                # print("  Mode {}".format(mode.name))

                for input_items in mode.config.values():
                    for entry in input_items.values():
                        if len(entry.actions) > 0 and entry.description != "":
                            # print("    {}".format(entry.input_id))
                            self._modes[mode.name].append(entry)

        for mode, entries in self._modes.items():
            print("{:15s} {: 4d}".format(mode, len(entries)))
        print(self._mode_tree)
