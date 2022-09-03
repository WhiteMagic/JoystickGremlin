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

import json
import logging
import time
import os
import re

from typing import Any

from PySide6 import QtCore

from gremlin import common, error, util, types


@common.SingletonDecorator
class Configuration:

    """Responsible for loading and saving configuration data."""

    def __init__(self):
        """Creates a new instance, loading the current configuration."""
        self._data = {}
        self._last_reload = None
        self.load()

        self.watcher = QtCore.QFileSystemWatcher([
            os.path.join(util.userprofile_path(), "configuration.json")
        ])
        self.watcher.fileChanged.connect(self.load)

    def load(self):
        """Loads the configuration file's content."""
        if self._last_reload is not None and \
                time.time() - self._last_reload < 1:
            return

        fname = os.path.join(util.userprofile_path(), "configuration.json")
        # Attempt to load the configuration file if this fails set
        # default empty values.
        load_successful = False
        json_data = {}
        if os.path.isfile(fname):
            with open(fname) as hdl:
                try:
                    decoder = json.JSONDecoder()
                    json_data = decoder.decode(hdl.read())
                    load_successful = True
                except ValueError:
                    pass
        if not load_successful:
            self._data = {}

        # Convert data based on property types
        self._data = {}
        for key, entry in json_data.items():
            data_type = types.PropertyType.to_enum(entry["type"])
            self._data[key] = {
                "value": util.property_from_string(data_type, entry["value"]),
                "type": data_type
            }

        # Save all data
        self._last_reload = time.time()
        self.save()

    def save(self):
        """Writes the configuration file to disk."""
        # Convert all data to string representations
        json_data = {}
        for key, entry in self._data.items():
            json_data[key] = {
                "value": util.property_to_string(
                    entry["type"],
                    entry["value"]
                ),
                "type": types.PropertyType.to_string(entry["type"])
            }

        # Write data to file
        fname = os.path.join(util.userprofile_path(), "configuration.json")
        with open(fname, "w") as hdl:
            encoder = json.JSONEncoder(
                sort_keys=True,
                indent=4
            )
            hdl.write(encoder.encode(json_data))

    def register(
        self,
        key: str,
        data_type: types.PropertyType,
        initial_value: Any
    ) -> None:
        """Registers a new configuration parameter.
        
        Args:
            key: name by which the new parameter will be accessed
            data_type: type of data that is expected to be stored
            initial_value: initial value of the paramter
        """
        if key in self._data:
            old_data_type = self._data[key]["type"]
            if data_type != old_data_type:
                logging.warning(
                    f"Data type for key '{key}' changed, updating from " +
                    f"'{old_data_type}' to '{data_type}'")
            else:
                return
        
        self._data[key] = {
            "value": initial_value,
            "type": data_type
        }
        self.save()

    def set(self, key: str, value: Any) -> None:
        """Sets the value of a specific parameter.
        
        Args:
            key: name of the parameter to store
            value: new value for the parameter
        """
        if key not in self._data:
            raise error.GremlinError(f"No parameter with key '{key}' exists")
        
        if util.has_correct_type(value, self._data[key]["type"]):
            self._data[key]["value"] = value
            self.save()
        else:
            data_type = self._data[key]["type"]
            raise error.GremlinError(
                f"Value has wrong data type, expted: " +
                f"'{data_type}' got '{type(value)}'"
            )

    def get(self, key: str) -> Any:
        """Returns the value associated with the given parameter.
        
        Args:
            key: name of the parameter whose value to retrieve
        
        Returns:
            Value associated with the given parameter
        """
        if key not in self._data:
            raise error.GremlinError(f"No parameter with key {key} exists")
        
        return self._data[key]["value"]

    # def set_calibration(self, dev_id, limits):
    #     """Sets the calibration data for all axes of a device.

    #     :param dev_id the id of the device
    #     :param limits the calibration data for each of the axes
    #     """
    #     identifier = str(dev_id)
    #     if identifier in self._data["calibration"]:
    #         del self._data["calibration"][identifier]
    #     self._data["calibration"][identifier] = {}

    #     for i, limit in enumerate(limits):
    #         if limit[2] - limit[0] == 0:
    #             continue
    #         axis_name = "axis_{}".format(i+1)
    #         self._data["calibration"][identifier][axis_name] = [
    #             limit[0], limit[1], limit[2]
    #         ]
    #     self.save()

    # def get_calibration(self, dev_id, axis_id):
    #     """Returns the calibration data for the desired axis.

    #     :param dev_id the id of the device
    #     :param axis_id the id of the desired axis
    #     :return the calibration data for the desired axis
    #     """
    #     identifier = str(dev_id)
    #     axis_name = "axis_{}".format(axis_id)
    #     if identifier not in self._data["calibration"]:
    #         return [-32768, 0, 32767]
    #     if axis_name not in self._data["calibration"][identifier]:
    #         return [-32768, 0, 32767]

    #     return self._data["calibration"][identifier][axis_name]

    # def get_executable_list(self):
    #     """Returns a list of all executables with associated profiles.

    #     :return list of executable paths
    #     """
    #     return list(sorted(
    #         self._data["profiles"].keys(),
    #         key=lambda x: x.lower())
    #     )

    # def remove_profile(self, exec_path):
    #     """Removes the executable from the configuration.

    #     :param exec_path the path to the executable to remove
    #     """
    #     if self._has_profile(exec_path):
    #         del self._data["profiles"][exec_path]
    #         self.save()

    # def get_profile(self, exec_path):
    #     """Returns the path to the profile associated with the given executable.

    #     :param exec_path the path to the executable for which to
    #         return the profile
    #     :return profile associated with the given executable
    #     """
    #     return self._data["profiles"].get(exec_path, None)

    # def get_profile_with_regex(self, exec_path):
    #     """Returns the path to the profile associated with the given executable.

    #     This considers all path entries that do not resolve to an actual file
    #     in the system as a regular expression. Regular expressions will be
    #     searched in order after true files have been checked.

    #     :param exec_path the path to the executable for which to
    #         return the profile
    #     :return profile associated with the given executable
    #     """
    #     # Handle the normal case where the path matches directly
    #     profile_path = self.get_profile(exec_path)
    #     if profile_path is not None:
    #         logging.getLogger("system").info(
    #             "Found exact match for {}, returning {}".format(
    #                 exec_path,
    #                 profile_path
    #             )
    #         )
    #         return profile_path

    #     # Handle non files by treating them as regular expressions, returning
    #     # the first successful match.
    #     for key, value in sorted(
    #             self._data["profiles"].items(),
    #             key=lambda x: x[0].lower()
    #     ):
    #         # Ignore valid files
    #         if os.path.exists(key):
    #             continue

    #         # Treat key as regular expression and attempt to match it to the
    #         # provided executable path
    #         if re.search(key, exec_path) is not None:
    #             logging.getLogger("system").info(
    #                 "Found regex match in {} for {}, returning {}".format(
    #                     key,
    #                     exec_path,
    #                     value
    #                 )
    #             )
    #             return value

    # def set_profile(self, exec_path, profile_path):
    #     """Stores the executable and profile combination.

    #     :param exec_path the path to the executable
    #     :param profile_path the path to the associated profile
    #     """
    #     self._data["profiles"][exec_path] = profile_path
    #     self.save()

    # def set_last_mode(self, profile_path, mode_name):
    #     """Stores the last active mode of the given profile.

    #     :param profile_path profile path for which to store the mode
    #     :param mode_name name of the active mode
    #     """
    #     if profile_path is None or mode_name is None:
    #         return
    #     self._data["last_mode"][profile_path] = mode_name
    #     self.save()

    # def get_last_mode(self, profile_path):
    #     """Returns the last active mode of the given profile.

    #     :param profile_path profile path for which to return the mode
    #     :return name of the mode if present, None otherwise
    #     """
    #     return self._data["last_mode"].get(profile_path, None)

    # def _has_profile(self, exec_path):
    #     """Returns whether or not a profile exists for a given executable.

    #     :param exec_path the path to the executable
    #     :return True if a profile exists, False otherwise
    #     """
    #     return exec_path in self._data["profiles"]

    # @property
    # def last_profile(self):
    #     """Returns the last used profile.

    #     :return path to the most recently used profile
    #     """
    #     return self._data.get("last_profile", None)

    # @last_profile.setter
    # def last_profile(self, value):
    #     """Sets the last used profile.

    #     :param value path to the most recently used profile
    #     """
    #     self._data["last_profile"] = value

    #     # Update recent profiles
    #     if value is not None:
    #         current = self.recent_profiles
    #         if value in current:
    #             del current[current.index(value)]
    #         current.insert(0, value)
    #         current = current[0:5]
    #         self._data["recent_profiles"] = current
    #     self.save()

    # @property
    # def recent_profiles(self):
    #     """Returns a list of recently used profiles.

    #     :return list of recently used profiles
    #     """
    #     return self._data.get("recent_profiles", [])

    # @property
    # def autoload_profiles(self):
    #     """Returns whether or not to automatically load profiles.

    #     This enables / disables the process based profile autoloading.

    #     :return True if auto profile loading is active, False otherwise
    #     """
    #     return self._data.get("autoload_profiles", False)

    # @autoload_profiles.setter
    # def autoload_profiles(self, value):
    #     """Sets whether or not to automatically load profiles.

    #     This enables / disables the process based profile autoloading.

    #     :param value Flag indicating whether or not to enable / disable the
    #         feature
    #     """
    #     if type(value) == bool:
    #         self._data["autoload_profiles"] = value
    #         self.save()

    # @property
    # def keep_last_autoload(self):
    #     """Returns whether or not to keep last autoloaded profile active when it would otherwise
    #     be automatically disabled.

    #     This setting prevents unloading an autoloaded profile when not changing to another one.

    #     :return True if last profile keeping is active, False otherwise
    #     """
    #     return self._data.get("keep_last_autoload", False)

    # @keep_last_autoload.setter
    # def keep_last_autoload(self, value):
    #     """Sets whether or not to keep last autoloaded profile active when it would otherwise
    #     be automatically disabled.

    #     This setting prevents unloading an autoloaded profile when not changing to another one.

    #     :param value Flag indicating whether or not to enable / disable the
    #         feature
    #     """
    #     if type(value) == bool:
    #         self._data["keep_last_autoload"] = value
    #         self.save()

    # @property
    # def highlight_input(self):
    #     """Returns whether or not to highlight inputs.

    #     This enables / disables the feature where using a physical input
    #     automatically selects it in the UI.

    #     :return True if the feature is enabled, False otherwise
    #     """
    #     return self._data.get("highlight_input", True)

    # @highlight_input.setter
    # def highlight_input(self, value):
    #     """Sets whether or not to highlight inputs.

    #     This enables / disables the feature where using a physical input
    #     automatically selects it in the UI.

    #     :param value Flag indicating whether or not to enable / disable the
    #         feature
    #     """
    #     if type(value) == bool:
    #         self._data["highlight_input"] = value
    #         self.save()

    # @property
    # def highlight_device(self):
    #     """Returns whether or not highlighting swaps device tabs.

    #     This enables / disables the feature where using a physical input
    #     automatically swaps to the correct device tab.

    #     :return True if the feature is enabled, False otherwise
    #     """
    #     return self._data.get("highlight_device", False)

    # @highlight_device.setter
    # def highlight_device(self, value):
    #     """Sets whether or not to swap device tabs to highlight inputs.

    #     This enables / disables the feature where using a physical input
    #     automatically swaps to the correct device tab.

    #     :param value Flag indicating whether or not to enable / disable the
    #         feature
    #     """
    #     if type(value) == bool:
    #         self._data["highlight_device"] = value
    #         self.save()

    # @property
    # def mode_change_message(self):
    #     """Returns whether or not to show a windows notification on mode change.

    #     :return True if the feature is enabled, False otherwise
    #     """
    #     return self._data.get("mode_change_message", False)

    # @mode_change_message.setter
    # def mode_change_message(self, value):
    #     """Sets whether or not to show a windows notification on mode change.

    #     :param value True to enable the feature, False to disable
    #     """
    #     self._data["mode_change_message"] = bool(value)
    #     self.save()

    # @property
    # def activate_on_launch(self):
    #     """Returns whether or not to activate the profile on launch.

    #     :return True if the profile is to be activate on launch, False otherwise
    #     """
    #     return self._data.get("activate_on_launch", False)

    # @activate_on_launch.setter
    # def activate_on_launch(self, value):
    #     """Sets whether or not to activate the profile on launch.

    #     :param value aactivate profile on launch if True, or not if False
    #     """
    #     self._data["activate_on_launch"] = bool(value)
    #     self.save()

    # @property
    # def close_to_tray(self):
    #     """Returns whether or not to minimze the application when closing it.

    #     :return True if closing minimizes to tray, False otherwise
    #     """
    #     return self._data.get("close_to_tray", False)

    # @close_to_tray.setter
    # def close_to_tray(self, value):
    #     """Sets whether or not to minimize to tray instead of closing.

    #     :param value minimize to tray if True, close if False
    #     """
    #     self._data["close_to_tray"] = bool(value)
    #     self.save()

    # @property
    # def start_minimized(self):
    #     """Returns whether or not to start Gremlin minimized.

    #     :return True if starting minimized, False otherwise
    #     """
    #     return self._data.get("start_minimized", False)

    # @start_minimized.setter
    # def start_minimized(self, value):
    #     """Sets whether or not to start Gremlin minimized.

    #     :param value start minimized if True and normal if False
    #     """
    #     self._data["start_minimized"] = bool(value)
    #     self.save()

    # @property
    # def default_action(self):
    #     """Returns the default action to show in action drop downs.

    #     :return default action to show in action selection drop downs
    #     """
    #     return self._data.get("default_action", "Remap")

    # @default_action.setter
    # def default_action(self, value):
    #     """Sets the default action to show in action drop downs.

    #     :param value the name of the default action to show
    #     """
    #     self._data["default_action"] = str(value)
    #     self.save()

    # @property
    # def macro_axis_polling_rate(self):
    #     """Returns the polling rate to use when recording axis macro actions.

    #     :return polling rate to use when recording a macro with axis inputs
    #     """
    #     return self._data.get("macro_axis_polling_rate", 0.1)

    # @macro_axis_polling_rate.setter
    # def macro_axis_polling_rate(self, value):
    #     self._data["macro_axis_polling_rate"] = value
    #     self.save()

    # @property
    # def macro_axis_minimum_change_rate(self):
    #     """Returns the minimum change in value required to record an axis event.

    #     :return minimum axis change required
    #     """
    #     return self._data.get("macro_axis_minimum_change_rate", 0.005)

    # @macro_axis_minimum_change_rate.setter
    # def macro_axis_minimum_change_rate(self, value):
    #     self._data["macro_axis_minimum_change_rate"] = value
    #     self.save()

    # @property
    # def macro_record_axis(self):
    #     return self._data.get("macro_record_axis", False)

    # @macro_record_axis.setter
    # def macro_record_axis(self, value):
    #     self._data["macro_record_axis"] = bool(value)
    #     self.save()

    # @property
    # def macro_record_button(self):
    #     return self._data.get("macro_record_button", True)

    # @macro_record_button.setter
    # def macro_record_button(self, value):
    #     self._data["macro_record_button"] = bool(value)
    #     self.save()

    # @property
    # def macro_record_hat(self):
    #     return self._data.get("macro_record_hat", True)

    # @macro_record_hat.setter
    # def macro_record_hat(self, value):
    #     self._data["macro_record_hat"] = bool(value)
    #     self.save()

    # @property
    # def macro_record_keyboard(self):
    #     return self._data.get("macro_record_keyboard", True)

    # @macro_record_keyboard.setter
    # def macro_record_keyboard(self, value):
    #     self._data["macro_record_keyboard"] = bool(value)
    #     self.save()

    # @property
    # def macro_record_mouse(self):
    #     return self._data.get("macro_record_mouse", False)

    # @macro_record_mouse.setter
    # def macro_record_mouse(self, value):
    #     self._data["macro_record_mouse"] = bool(value)
    #     self.save()

    # @property
    # def window_size(self):
    #     """Returns the size of the main Gremlin window.

    #     :return size of the main Gremlin window
    #     """
    #     return self._data.get("window_size", None)

    # @window_size.setter
    # def window_size(self, value):
    #     """Sets the size of the main Gremlin window.

    #     :param value the size of the main Gremlin window
    #     """
    #     self._data["window_size"] = value
    #     self.save()

    # @property
    # def window_location(self):
    #     """Returns the position of the main Gremlin window.

    #     :return position of the main Gremlin window
    #     """
    #     return self._data.get("window_location", None)

    # @window_location.setter
    # def window_location(self, value):
    #     """Sets the position of the main Gremlin window.

    #     :param value the position of the main Gremlin window
    #     """
    #     self._data["window_location"] = value
    #     self.save()
