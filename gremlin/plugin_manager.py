# -*- coding: utf-8; -*-

# Copyright (C) 2016 Lionel Ott
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


from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
import sys
from typing import TypeVar, TYPE_CHECKING

from PySide6 import QtQml

from gremlin import common, config, error, shared_state, util
from gremlin.types import ActionProperty, InputType, DataCreationMode

if TYPE_CHECKING:
    from gremlin.base_classes import AbstractActionData

    Plugin = type[AbstractActionData]
    PluginList = list[Plugin]
    PluginDict = dict[str, Plugin]


@common.SingletonDecorator
class PluginManager:

    """Handles discovery and handling of action plugins."""

    def __init__(self) -> None:
        """Initializes the action plugin manager."""
        self._plugins : PluginDict = {}
        self._type_to_action_map : dict[InputType, PluginList] = {}
        self._name_to_type_map : PluginDict = {}
        self._tag_to_type_map : PluginDict = {}
        self._parameter_requirements : dict[str, PluginList] = {}

        self._discover_plugins(Path(util.resource_path("action_plugins")), True)
        path = Path(config.Configuration().value(
            "global", "general", "plugin_directory"
        ))
        if path.is_dir():
            self._discover_plugins(path, False)

        self._create_type_action_map()
        self._create_action_name_map()

    @property
    def repository(self) -> PluginDict:
        """Returns the dictionary of all found plugins.

        :return dictionary containing all plugins found
        """
        return self._plugins

    @property
    def type_action_map(self) -> dict[InputType, PluginList]:
        """Returns a mapping from input types to valid action plugins.

        :return mapping from input types to associated actions
        """
        return self._type_to_action_map

    @property
    def tag_map(self) -> PluginDict:
        """Returns the mapping from an action tag to the action plugin.

        :return mapping from action name to action plugin
        """
        return self._tag_to_type_map

    def get_class(self, name: str) -> Plugin:
        """Returns the class object corresponding to the given name.

        :param name of the action class to return
        :return class object corresponding to the provided name
        """
        if name not in self._name_to_type_map:
            raise error.GremlinError(
                "No action with name '{}' exists".format(name)
            )
        return self._name_to_type_map[name]

    def plugins_requiring_parameter(
        self,
        param_name: str
    ) -> PluginList:
        """Returns the list of plugins requiring a certain parameter.

        :param param_name the parameter name required by the returned actions
        :return list of actions requiring a certain parameter in the callback
        """
        return self._parameter_requirements.get(param_name, [])

    def create_instance(
        self,
        name: str,
        input_type: InputType
    ) -> AbstractActionData:
        """Creates an action instance which is stored in the library.

        Args:
            name: name of the action to create an instance of
            input_type: the input type associated with the new instance

        Returns:
            The newly created action instance
        """
        cls = self.get_class(name)
        creation_mode = DataCreationMode.Create
        if ActionProperty.ReuseByDefault in cls.properties:
            creation_mode = DataCreationMode.Reuse
        instance = cls.create(creation_mode, input_type)
        shared_state.current_profile.library.add_action(instance)
        return instance

    def _create_type_action_map(self) -> None:
        """Creates a lookup table from input types to available actions."""
        self._type_to_action_map : dict[InputType, PluginList]= {
            InputType.JoystickAxis: [],
            InputType.JoystickButton: [],
            InputType.JoystickHat: [],
            InputType.Keyboard: []
        }

        for entry in self._plugins.values():
            for input_type in entry.input_types:
                self._type_to_action_map[input_type].append(entry)

    def _create_action_name_map(self) -> None:
        """Creates a lookup table from action names to actions."""
        for entry in self._plugins.values():
            self._name_to_type_map[entry.name] = entry
            self._tag_to_type_map[entry.tag] = entry

    def _discover_plugins(self, path: Path, is_core: bool) -> None:
        """Processes known plugin folders for action plugins.

        Args:
            path: path to the folder to scan for action plugins
            is_core: whether the folder is part of the core Gremlin or user
                specified
        """
        if not is_core:
            sys.path.insert(0, str(path))

        for root, _, files in os.walk(path):
            for _ in [v for v in files if v == "__init__.py"]:
                try:
                    # Attempt to load the file and if it looks like a proper
                    # action_plugins store it in the registry.
                    module = os.path.split(root)[1]

                    plugin_module_name = f"{path.name}.{module}"
                    if not is_core:
                        plugin_module_name = module
                    try:
                        plugin = importlib.import_module(plugin_module_name)
                    except (ModuleNotFoundError, ImportError) as e:
                        logging.getLogger("system").error(
                            f"Failed to load plugin '{plugin_module_name}' "
                            f"with error: '{e}"
                        )
                        continue

                    # Verify requirements for the plugin are satisfied.
                    if "create" in plugin.__dict__ \
                            and plugin.create.can_create():
                        # Store plugin class information.
                        self._plugins[plugin.create.tag] = plugin.create
                        logging.getLogger("system").debug(
                            "Loaded: {}".format(plugin.create.tag)
                        )

                        # Register QML type.
                        QtQml.qmlRegisterType(
                            plugin.create.model,
                            "Gremlin.ActionPlugins",
                            1,
                            0,
                            plugin.create.model.__name__
                        )
                    else:
                        del plugin
                except Exception as e:
                    # Log an error and ignore the action_plugins if anything
                    # is wrong with it.
                    logging.getLogger("system").warning(
                        "Loading action_plugins '{}' failed due to: {}".format(
                            root.split("\\")[-1],
                            e
                        )
                    )
                    raise(e)
