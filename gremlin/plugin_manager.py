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


import importlib
import logging
import os

from . import common, error


@common.SingletonDecorator
class ContainerPlugins:

    """Handles discovery and handling of container plugins."""

    def __init__(self):
        """Initializes the container plugin manager."""
        self._plugins = {}
        self._discover_plugins()

        self._tag_to_type_map = {}
        self._name_to_type_map = {}

        self._create_maps()

    @property
    def repository(self):
        """Returns the dictionary of all found plugins.

        :return dictionary containing all plugins found
        """
        return self._plugins

    @property
    def tag_map(self):
        """Returns the mapping from a container tag to the container plugin.

        :return mapping from container name to container plugin
        """
        return self._tag_to_type_map

    def get_class(self, name):
        """Returns the class object corresponding to the given name.

        :param name of the container class to return
        :return class object corresponding to the provided name
        """
        if name not in self._name_to_type_map:
            raise error.GremlinError(
                "No container with name '{}' exists".format(name)
            )
        return self._name_to_type_map[name]

    def _discover_plugins(self):
        """Processes known plugin folders for action plugins."""
        for root, dirs, files in os.walk("container_plugins"):
            for fname in [v for v in files if v == "__init__.py"]:
                try:
                    folder, module = os.path.split(root)
                    if folder != "container_plugins":
                        continue

                    # Attempt to load the file and if it looks like a proper
                    # action_plugins store it in the registry
                    plugin = importlib.import_module(
                        "container_plugins.{}".format(module)
                    )
                    if "version" in plugin.__dict__:
                        self._plugins[plugin.name] = plugin.create
                        logging.getLogger("system").debug(
                            "Loaded: {}".format(plugin.name)
                        )
                    else:
                        del plugin
                except Exception as e:
                    # Log an error and ignore the action_plugins if
                    # anything is wrong with it
                    logging.getLogger("system").warning(
                        "Loading container_plugins '{}' failed due to: {}".format(
                            fname,
                            e
                        )
                    )

    def _create_maps(self):
        """Creates a lookup table from container tag to container object."""
        for entry in self._plugins.values():
            self._tag_to_type_map[entry.tag] = entry
            self._name_to_type_map[entry.name] = entry


@common.SingletonDecorator
class ActionPlugins:

    """Handles discovery and handling of action plugins."""

    def __init__(self):
        """Initializes the action plugin manager."""
        self._plugins = {}
        self._type_to_action_map = {}
        self._type_to_name_map = {}
        self._name_to_type_map = {}
        self._tag_to_type_map = {}
        self._parameter_requirements = {}

        self._discover_plugins()

        self._create_type_action_map()
        self._create_action_name_map()

    @property
    def repository(self):
        """Returns the dictionary of all found plugins.

        :return dictionary containing all plugins found
        """
        return self._plugins

    @property
    def type_action_map(self):
        """Returns a mapping from input types to valid action plugins.

        :return mapping from input types to associated actions
        """
        return self._type_to_action_map

    @property
    def tag_map(self):
        """Returns the mapping from an action tag to the action plugin.

        :return mapping from action name to action plugin
        """
        return self._tag_to_type_map

    def get_class(self, name):
        """Returns the class object corresponding to the given name.

        :param name of the action class to return
        :return class object corresponding to the provided name
        """
        if name not in self._name_to_type_map:
            raise error.GremlinError(
                "No action with name '{}' exists".format(name)
            )
        return self._name_to_type_map[name]

    def plugins_requiring_parameter(self, param_name):
        """Returns the list of plugins requiring a certain parameter.

        :param param_name the parameter name required by the returned actions
        :return list of actions requiring a certain parameter in the callback
        """
        return self._parameter_requirements.get(param_name, [])

    def _create_type_action_map(self):
        """Creates a lookup table from input types to available actions."""
        self._type_to_action_map = {
            common.InputType.JoystickAxis: [],
            common.InputType.JoystickButton: [],
            common.InputType.JoystickHat: [],
            common.InputType.Keyboard: []
        }

        for entry in self._plugins.values():
            for input_type in entry.input_types:
                self._type_to_action_map[input_type].append(entry)

    def _create_action_name_map(self):
        """Creates a lookup table from action names to actions."""
        for entry in self._plugins.values():
            self._name_to_type_map[entry.name] = entry
            self._tag_to_type_map[entry.tag] = entry

    def _discover_plugins(self):
        """Processes known plugin folders for action plugins."""
        for root, dirs, files in os.walk("action_plugins"):
            for _ in [v for v in files if v == "__init__.py"]:
                try:
                    folder, module = os.path.split(root)
                    if folder != "action_plugins":
                        continue

                    # Attempt to load the file and if it looks like a proper
                    # action_plugins store it in the registry
                    plugin = importlib.import_module(
                        "action_plugins.{}".format(module)
                    )
                    if "version" in plugin.__dict__:
                        self._plugins[plugin.name] = plugin.create
                        logging.getLogger("system").debug(
                            "Loaded: {}".format(plugin.name)
                        )
                    else:
                        del plugin
                except Exception as e:
                    # Log an error and ignore the action_plugins if
                    # anything is wrong with it
                    logging.getLogger("system").warning(
                        "Loading action_plugins '{}' failed due to: {}".format(
                            root.split("\\")[-1],
                            e
                        )
                    )
