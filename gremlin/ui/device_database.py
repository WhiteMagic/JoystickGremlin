# -*- coding: utf-8; -*-

# Copyright (C) 2019 Lionel Ott
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

"""Device database management for storing and retrieving device information."""

from __future__ import annotations

import json
from json.decoder import JSONDecodeError
import logging
import uuid
from typing import Any, Dict, Optional

from gremlin.common import SingletonDecorator
from gremlin.types import InputType


class DeviceMapping:
    """Maps device information for internal storage."""

    def __init__(self, input_map: Dict[str, Any]) -> None:
        self._input_map = input_map

    @property
    def type(self) -> InputType:
        """Returns the type of the input."""
        return InputType.to_enum(self._input_map["type"])

    @property
    def id(self) -> int:
        """Returns the id of the input."""
        return self._input_map["id"]

    @property
    def label(self) -> str:
        """Returns the label of the input."""
        return self._input_map["label"]

    @property
    def always_visible(self) -> bool:
        """Returns whether or not the input is always visible."""
        return self._input_map.get("always_visible", False)

    @property
    def description(self) -> str:
        """Returns the description of this input."""
        return self._input_map.get("description", "")

    def __eq__(self, other: Any) -> bool:
        """Compares two DeviceMapping instances for equality."""
        if not isinstance(other, DeviceMapping):
            return False
        return self.type == other.type and \
            self.id == other.id and \
            self.label == other.label and \
            self.always_visible == other.always_visible

    def __ne__(self, other: Any) -> bool:
        """Compares two DeviceMapping instances for inequality."""
        return not (self == other)


@SingletonDecorator
class DeviceDatabase:
    """Database storing device information."""

    def __init__(self) -> None:
        """Creates a new database instance."""
        self._db: Dict[uuid.UUID, Dict[str, Any]] = {}
        self._load_database()

    def add_device(self, device_guid: uuid.UUID, label_map: Dict[int, str]) -> None:
        """Adds a new device to the database.

        Args:
            device_guid: GUID of the device to add
            label_map: Mapping from input id to label for each input
        """
        self._db[device_guid] = label_map
        self._save_database()

    def get_device_information(
            self,
            device_guid: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Returns information about the specified device.

        Args:
            device_guid: GUID of the device for which to return data

        Returns:
            Dictionary containing device information if it exists
        """
        return self._db.get(device_guid, None)

    def _load_database(self) -> None:
        """Loads the database content from storage."""
        try:
            with open("device_db.json", "r") as hdl:
                data = json.load(hdl)
                for entry in data:
                    self._db[uuid.UUID(entry["guid"])] = entry["inputs"]
        except FileNotFoundError:
            logging.getLogger("system").warning("Device database not found")
        except JSONDecodeError as e:
            logging.getLogger("system").error(
                f"Failed to load device database due to: {e}"
            )

    def _save_database(self) -> None:
        """Saves the database content to storage."""
        data = []
        for guid, inputs in self._db.items():
            data.append({
                "guid": str(guid),
                "inputs": inputs
            })

        try:
            with open("device_db.json", "w") as hdl:
                json.dump(data, hdl, indent=4)
        except IOError as e:
            logging.getLogger("system").error(
                f"Failed to save device database due to: {e}"
            )
