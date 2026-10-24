# SPDX-License-Identifier: GPL-3.0-only

"""Creates the Python models QML items own.

PySide6 never frees a Python object QML instantiates (PYSIDE-1407), so every type
QML creates and destroys has to be created through this factory instead, with the
owning QML item as parent. Once PYSIDE-1407 is fixed the factory can be retired.
"""

from __future__ import annotations

from PySide6 import (
    QtCore,
    QtQml,
)

from gremlin.config import Configuration
from gremlin.ui.device import (
    AxisCalibration,
    DeviceAxisSeries,
    DeviceAxisState,
    DeviceButtonState,
    DeviceHatState,
    DeviceListModel,
    LogicalDeviceSelectorModel,
    VJoyDevices,
)
from gremlin.ui.log_viewer import LogSource
from gremlin.ui.option import (
    ActionSequenceOrdering,
    ConfigSectionModel,
    ProfileAutoLoadingModel,
    ThemeSelectionModel,
    TTSVoiceSelectionModel,
)
from gremlin.ui.profile import (
    ModeHierarchyModel,
    ModeListModel,
    ProfileDeviceListModel,
)
from gremlin.ui.tools import Tools
from gremlin.ui.util import (
    InputListenerModel,
    ProcessListModel,
    ReleaseNotes,
)
from gremlin.ui.window_geometry import WindowGeometry

QML_IMPORT_NAME = "Gremlin.UI"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
@QtQml.QmlSingleton
class ModelFactory(QtCore.QObject):
    """Creates models parented to the QML item that owns them."""

    @QtCore.Slot(QtCore.QObject, result=VJoyDevices)
    def vjoyDevices(self, parent: QtCore.QObject) -> VJoyDevices:
        return VJoyDevices(parent)

    @QtCore.Slot(QtCore.QObject, result=LogicalDeviceSelectorModel)
    def logicalDeviceSelectorModel(
        self, parent: QtCore.QObject
    ) -> LogicalDeviceSelectorModel:
        return LogicalDeviceSelectorModel(parent)

    @QtCore.Slot(QtCore.QObject, result=InputListenerModel)
    def inputListenerModel(self, parent: QtCore.QObject) -> InputListenerModel:
        return InputListenerModel(parent)

    @QtCore.Slot(QtCore.QObject, result=ModeListModel)
    def modeListModel(self, parent: QtCore.QObject) -> ModeListModel:
        return ModeListModel(parent)

    @QtCore.Slot(QtCore.QObject, str, result=DeviceListModel)
    def deviceListModel(
        self, parent: QtCore.QObject, device_type: str
    ) -> DeviceListModel:
        """Creates a device list model.

        Args:
            parent: QML item owning the model
            device_type: one of "physical", "virtual", "input", or "all"
        """
        model = DeviceListModel(parent)
        model.deviceType = device_type
        return model

    @QtCore.Slot(QtCore.QObject, result=ModeHierarchyModel)
    def modeHierarchyModel(self, parent: QtCore.QObject) -> ModeHierarchyModel:
        return ModeHierarchyModel(parent)

    @QtCore.Slot(QtCore.QObject, result=ProfileDeviceListModel)
    def profileDeviceListModel(self, parent: QtCore.QObject) -> ProfileDeviceListModel:
        return ProfileDeviceListModel(parent)

    @QtCore.Slot(QtCore.QObject, result=Tools)
    def tools(self, parent: QtCore.QObject) -> Tools:
        return Tools(parent)

    @QtCore.Slot(QtCore.QObject, result=AxisCalibration)
    def axisCalibration(self, parent: QtCore.QObject) -> AxisCalibration:
        return AxisCalibration(parent)

    @QtCore.Slot(QtCore.QObject, result=DeviceAxisSeries)
    def deviceAxisSeries(self, parent: QtCore.QObject) -> DeviceAxisSeries:
        return DeviceAxisSeries(parent)

    @QtCore.Slot(QtCore.QObject, result=DeviceAxisState)
    def deviceAxisState(self, parent: QtCore.QObject) -> DeviceAxisState:
        return DeviceAxisState(parent)

    @QtCore.Slot(QtCore.QObject, result=DeviceButtonState)
    def deviceButtonState(self, parent: QtCore.QObject) -> DeviceButtonState:
        return DeviceButtonState(parent)

    @QtCore.Slot(QtCore.QObject, result=DeviceHatState)
    def deviceHatState(self, parent: QtCore.QObject) -> DeviceHatState:
        return DeviceHatState(parent)

    @QtCore.Slot(QtCore.QObject, result=LogSource)
    def logSource(self, parent: QtCore.QObject) -> LogSource:
        return LogSource(parent)

    @QtCore.Slot(QtCore.QObject, result=ReleaseNotes)
    def releaseNotes(self, parent: QtCore.QObject) -> ReleaseNotes:
        return ReleaseNotes(parent)

    @QtCore.Slot(QtCore.QObject, result=ConfigSectionModel)
    def configSectionModel(self, parent: QtCore.QObject) -> ConfigSectionModel:
        return ConfigSectionModel(parent)

    @QtCore.Slot(QtCore.QObject, result=ActionSequenceOrdering)
    def actionSequenceOrdering(self, parent: QtCore.QObject) -> ActionSequenceOrdering:
        return ActionSequenceOrdering(parent)

    @QtCore.Slot(QtCore.QObject, result=ProfileAutoLoadingModel)
    def profileAutoLoadingModel(
        self, parent: QtCore.QObject
    ) -> ProfileAutoLoadingModel:
        return ProfileAutoLoadingModel(parent)

    @QtCore.Slot(QtCore.QObject, result=ProcessListModel)
    def processListModel(self, parent: QtCore.QObject) -> ProcessListModel:
        return ProcessListModel(parent)

    @QtCore.Slot(QtCore.QObject, result=TTSVoiceSelectionModel)
    def ttsVoiceSelectionModel(self, parent: QtCore.QObject) -> TTSVoiceSelectionModel:
        return TTSVoiceSelectionModel(parent)

    @QtCore.Slot(QtCore.QObject, result=ThemeSelectionModel)
    def themeSelectionModel(self, parent: QtCore.QObject) -> ThemeSelectionModel:
        return ThemeSelectionModel(parent)

    @QtCore.Slot(QtCore.QObject, str, int, int, int, int, result=WindowGeometry)
    def windowGeometry(
        self,
        parent: QtCore.QObject,
        name: str,
        default_width: int,
        default_height: int,
        min_width: int,
        min_height: int,
    ) -> WindowGeometry:
        """Creates the persisted (or defaulted) geometry for a window.

        Args:
            parent: QML window owning the geometry
            name: config entry name, e.g. "main-window-geometry"
            default_width: width to fall back to if nothing was persisted
            default_height: height to fall back to if nothing was persisted
            min_width: minimum width the window accepts, used for validation
            min_height: minimum height the window accepts, used for validation
        """
        return WindowGeometry(
            Configuration(),
            name,
            default_width,
            default_height,
            min_width,
            min_height,
            parent,
        )
