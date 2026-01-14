# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
from typing import (
    Dict,
    TYPE_CHECKING,
)
import uuid

from PySide6 import (
    QtCore,
    QtQml,
)

import dill

from gremlin import (
    auto_mapper,
    shared_state,
    signal,
    swap_devices,
)

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta

QML_IMPORT_NAME = "Gremlin.Tools"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class Tools(QtCore.QObject):

    def __init__(self, parent: ta.OQO = None) -> None:
        super().__init__(parent)

    @QtCore.Slot(str, dict, dict, bool, bool, result=str)
    def createMappings(
        self,
        mode: str,
        physical_devices: Dict[str, bool],
        vjoy_devices: Dict[int, bool],
        overwrite: bool,
        repeat: bool
    ) -> str:
        """
        Create mappings between physical and vJoy devices.

        Args:
            physical_devices: Dictionary of which physical devices are selected
            vjoy_devices: Dictionary indicating selection of vJoy devices
            overwrite: Whether to overwrite existing mappings
            repeat: Whether to repeat vJoy mappings

        Returns:
            A string report for the user summarizing new mappings.
        """
        mapper = auto_mapper.AutoMapper(shared_state.current_profile)
        feedback_string = mapper.generate_mappings(
            [
                dill.GUID.from_str(guid)
                for (guid, chosen) in physical_devices.items() if chosen
            ],
            [
                int(vjoy_id)
                for (vjoy_id, chosen) in vjoy_devices.items() if chosen
            ],
            auto_mapper.AutoMapperOptions(mode, repeat, overwrite),
        )
        signal.signal.profileChanged.emit()
        signal.signal.reloadCurrentInputItem.emit()
        return feedback_string

    @QtCore.Slot(str, str, result=str)
    def swapDevices(self, source_uuid_str: str, target_uuid_str: str) -> str:
        """
        Swaps the specified two devices in the profile.

        Args:
            source_device_uuid: The UUID of the source (from profile) device.
            target_device_uuid: The UUID of the target (connected) device.

        Returns:
            The number of action and input swaps performed.
        """
        try:
            source_uuid = uuid.UUID(source_uuid_str)
            target_uuid = uuid.UUID(target_uuid_str)
            result = swap_devices.swap_devices(
                shared_state.current_profile,
                source_uuid,
                target_uuid
            )
            signal.signal.profileChanged.emit()
            signal.signal.reloadCurrentInputItem.emit()
            return result.as_string()
        except ValueError as e:
            logging.getLogger("system").error(
                f"Invalid UUID provided for swapping devices: "
                f"{source_uuid_str}, {target_uuid_str}"
            )
            return "Failed to swap devices: Invalid UUID provided."
