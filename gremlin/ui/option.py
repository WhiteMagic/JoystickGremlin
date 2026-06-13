# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import (
    cast,
    Any,
    Dict,
    Optional,
    TYPE_CHECKING,
)

from PySide6 import (
    QtCore,
    QtQml,
)
from PySide6.QtCore import (
    Property,
    Signal,
    Slot
)

import gremlin.config
from gremlin.common import SingletonMetaclass
from gremlin.error import (
    GremlinError,
    MissingImplementationError,
)
from gremlin.signal import signal
from gremlin.tts import TTSManager
from gremlin.types import PropertyType

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.Config"
QML_IMPORT_MAJOR_VERSION = 1


@QtQml.QmlElement
class ConfigSectionModel(QtCore.QAbstractListModel):

    """Exposes the sections present in the configuration as a list model."""

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"name"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"groupModel"),
    }

    def __init__(self, parent: Optional[QtCore.QObject]=None) -> None:
        super().__init__(parent)

        self._config = gremlin.config.Configuration()
        self._option = MetaConfigOption()

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._combined_sections())

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role not in self.roles:
            return None

        sections = self._combined_sections()
        if index.row() >= len(sections):
            return None

        match self.roles[role]:
            case "name":
                return sections[index.row()]
            case "groupModel":
                return ConfigGroupModel(sections[index.row()])

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles

    def _combined_sections(self) -> list[str]:
        def priority(name: str) -> int:
            match name:
                case "global":
                    return 0
                case "action":
                    return 1
                case _:
                    return 99
        return list(sorted(
            set(self._config.sections() + self._option.sections()),
            key=priority
        ))


@QtQml.QmlElement
class ConfigGroupModel(QtCore.QAbstractListModel):

    """Exposes the groups present in a specific configuration section as a
    list model.
    """

    changed = Signal()

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"groupName"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"entryModel"),
    }

    def __init__(
            self,
            section: str,
            parent: Optional[QtCore.QObject]=None
    ) -> None:
        super().__init__(parent)

        self._config = gremlin.config.Configuration()
        self._option = MetaConfigOption()
        self._section_name = section

    @Property(str, notify=changed) # type: ignore
    def sectionName(self) -> str:
        return self._section_name

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._combined_groups())

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        groups = self._combined_groups()
        if index.row() < len(groups):
            match self.roles[role]:
                case "entryModel":
                    return ConfigEntryModel(
                        self._section_name, groups[index.row()]
                    )
                case "groupName":
                    return groups[index.row()]
        else:
            return None

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles

    def _combined_groups(self) -> list[str]:
        return list(sorted(set(
            self._config.groups(self._section_name) +
            self._option.groups(self._section_name)
        )))


@QtQml.QmlElement
class ConfigEntryModel(QtCore.QAbstractListModel):

    """Exposes the entries in a section's group as a list model."""

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"data_type"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"value"),
        QtCore.Qt.ItemDataRole.UserRole + 3: QtCore.QByteArray(b"description"),
        QtCore.Qt.ItemDataRole.UserRole + 4: QtCore.QByteArray(b"properties"),
        QtCore.Qt.ItemDataRole.UserRole + 5: QtCore.QByteArray(b"name"),
    }

    def __init__(
        self,
        section: str,
        group: str,
        parent: Optional[QtCore.QObject]=None
    ) -> None:
        super().__init__(parent)

        self._config = gremlin.config.Configuration()
        self._option = MetaConfigOption()
        self._section_name = section
        self._group_name = group

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._combined_entries())

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        entries = self._combined_entries()
        if not index.isValid() or index.row() >= len(entries):
            return None

        value = None
        if role in self.roles:
            role_name = bytes(self.roles[role].data()).decode()

            name = entries[index.row()]
            if role_name == "name":
                name = re.sub(r"^[0-9]+-", "", name)
                return re.sub(r"[_-]+", " ", name).capitalize()
            # Separate handling of config and meta option entries.
            if self._config.exists(self._section_name, self._group_name, name):
                key = [self._section_name, self._group_name, entries[index.row()]]
                value = self._config.get(*key, role_name)
                # Convert path values to strings.
                if role_name == "value":
                    if self._config.data_type(*key) == PropertyType.Path:
                        value = str(value)
                if isinstance(value, PropertyType):
                    value = PropertyType.to_string(value)
            else:
                match role_name:
                    case "description":
                        value = self._option.description(
                            self._section_name, self._group_name, name
                        )
                    case "value":
                        value = self._option.qml_widget(
                            self._section_name, self._group_name, name
                        )().qml_path
                    case "data_type":
                        value = "meta_option"
        return value

    def setData(
            self,
            index: ta.ModelIndex,
            value: Any,
            role: int=QtCore.Qt.ItemDataRole.EditRole
    ) -> bool:
        entries = self._combined_entries()
        if not index.isValid() or index.row() >= len(entries):
            return False

        name = entries[index.row()]
        if not self._config.exists(self._section_name, self._group_name, name):
            raise GremlinError(
                "Cannot set data for non-config entry " +
                f"{self._section_name}.{self._group_name}.{name}"
            )

        if self.roles[role] == "value":
            key = [self._section_name, self._group_name, entries[index.row()]]
            if self._config.data_type(*key) == PropertyType.Path:
                value = Path(value)

            self._config.set(*key, value)
            self.dataChanged.emit(index, index, {role})
            # Enable other UI elements to react to configuration changes.
            signal.configChanged.emit()
            return True
        return False

    def flags(self, index: ta.ModelIndex) -> QtCore.Qt.ItemFlag:
        return super().flags(index) | QtCore.Qt.ItemFlag.ItemIsEditable

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles

    def _combined_entries(self) -> list[str]:
        return list(sorted(set(
            self._config.entries(self._section_name, self._group_name) +
            self._option.entries(self._section_name, self._group_name)
        )))


class BaseMetaConfigOptionWidget:

    @property
    def qml_path(self) -> str:
        return self._qml_path()

    def _qml_path(self) -> str:
        raise MissingImplementationError(
            "BaseMetaConfigOptionWidget: Subclasses must implement the " +
            "qml_path method."
        )


@QtQml.QmlElement
class ActionSequenceOrdering(QtCore.QAbstractListModel, BaseMetaConfigOptionWidget):

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"name"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"visible"),
        QtCore.Qt.ItemDataRole.UserRole + 3: QtCore.QByteArray(b"index"),
    }

    def __init__(self, parent: Optional[QtCore.QObject]=None) -> None:
        QtCore.QAbstractListModel.__init__(self, parent)
        BaseMetaConfigOptionWidget.__init__(self)

        self._config = gremlin.config.Configuration()
        self._cfg_key = ["action", "general", "action-priorities"]

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._config.value(*self._cfg_key))

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role in self.roles:
            data = self._config.value(*self._cfg_key)[index.row()]
            match self.roles[role]:
                case "name":
                    return data[0]
                case "visible":
                    return data[1]
                case "index":
                    return index.row()
                case _:
                    raise GremlinError(f"Unknown role name {role}")
        else:
            raise GremlinError("Invalid role encountered")

    def setData(
            self,
            index: ta.ModelIndex,
            value: Any,
            role: int=QtCore.Qt.ItemDataRole.EditRole
    ) -> bool:
        data = self._config.value(*self._cfg_key)
        match cast(str, self.roles[role]):
            case "visible":
                data[index.row()][1] = value
                self._config.set(*self._cfg_key, data)
                return True
            case "index":
                return False
            case _:
                return False

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles

    @Slot(int, int)
    def move(self, source_index: int, target_index: int) -> None:
        self.layoutAboutToBeChanged.emit()
        data = self._config.value(*self._cfg_key)
        item = data.pop(source_index)
        data.insert(target_index, item)
        self._config.set(*self._cfg_key, data)
        self.layoutChanged.emit()

    def _qml_path(self) -> str:
        return "file:///" + \
            QtCore.QFile("qml:OptionActionSequenceOrdering.qml").fileName()


@QtQml.QmlElement
class ProfileAutoLoadingModel(QtCore.QAbstractListModel, BaseMetaConfigOptionWidget):

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"profile"),
        QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"executable"),
        QtCore.Qt.ItemDataRole.UserRole + 3: QtCore.QByteArray(b"isEnabled"),
    }

    def __init__(self, parent: Optional[QtCore.QObject]=None) -> None:
        QtCore.QAbstractListModel.__init__(self, parent)
        BaseMetaConfigOptionWidget.__init__(self)

        self._config = gremlin.config.Configuration()
        self._cfg_key = ["profile", "automation", "entries-auto-loading"]

    @Slot()
    def newEntry(self) -> None:
        """Creates a new empty auto-load entry."""
        self.beginInsertRows(
            QtCore.QModelIndex(),
            self.rowCount(),
            self.rowCount()
        )
        data = self._config.value(*self._cfg_key)
        data.append(["", "", False])
        self._config.set(*self._cfg_key, data)
        self.endInsertRows()

    @Slot(int)
    def removeEntry(self, index: int) -> None:
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        data = self._config.value(*self._cfg_key)
        del data[index]
        self._config.set(*self._cfg_key, data)
        self.endRemoveRows()

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._config.value(*self._cfg_key))

    def data(
            self,
            index: ta.ModelIndex,
            role: int=QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        data = self._config.value(*self._cfg_key)[index.row()]
        match cast(str, self.roles[role]):
            case "profile":
                return data[0]
            case "executable":
                return data[1]
            case "isEnabled":
                return data[2]
            case _:
                raise GremlinError(f"Unknown role name {role}")

    def setData(
            self,
            index: ta.ModelIndex,
            value: Any,
            role: int=QtCore.Qt.ItemDataRole.EditRole
    ) -> bool:
        data = self._config.value(*self._cfg_key)
        match cast(str, self.roles[role]):
            case "profile":
                data[index.row()][0] = value
                self._config.set(*self._cfg_key, data)
                return True
            case "executable":
                data[index.row()][1] = value
                self._config.set(*self._cfg_key, data)
                return True
            case "isEnabled":
                data[index.row()][2] = value
                self._config.set(*self._cfg_key, data)
                return True
            case _:
                return False

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles

    def _qml_path(self) -> str:
        return "file:///" + \
            QtCore.QFile("qml:OptionProfileAutoLoading.qml").fileName()


@QtQml.QmlElement
class TTSVoiceSelectionModel(QtCore.QAbstractListModel, BaseMetaConfigOptionWidget):

    roles = {
        QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"name"),
    }

    currentIndexChanged = QtCore.Signal()

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        QtCore.QAbstractListModel.__init__(self, parent)
        BaseMetaConfigOptionWidget.__init__(self)

        TTSManager().start()
        self._voices = [voice.name() for voice in TTSManager().available_voices()]
        self._config = gremlin.config.Configuration()
        self._cfg_key = ["action", "text-to-speech", "voice"]

    def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._voices)

    def data(
            self,
            index: ta.ModelIndex,
            role: int = QtCore.Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == QtCore.Qt.ItemDataRole.UserRole + 1:
            return self._voices[index.row()]
        return None

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles

    def _qml_path(self) -> str:
        return "file:///" + \
            QtCore.QFile("qml:OptionTTSVoiceSelection.qml").fileName()

    def _get_current_index(self) -> int:
        try:
            return self._voices.index(self._config.value(*self._cfg_key))
        except ValueError:
            return 0

    def _set_current_index(self, index: int) -> None:
        if not (0 <= index < len(self._voices)):
            return
        self._config.set(*self._cfg_key, self._voices[index])
        TTSManager().update_voice(self._voices[index])
        self.currentIndexChanged.emit()

    currentIndex = QtCore.Property(
        int,
        fget=_get_current_index,
        fset=_set_current_index,
        notify=currentIndexChanged,
    )


class MetaConfigOption(metaclass=SingletonMetaclass):

    def __init__(self) -> None:
        self._options = {}

    def count(self) -> int:
        """Returns the number of registered options.

        Returns:
            Number of registered options.
        """
        return len(self._options)

    def register(
        self,
        section: str,
        group: str,
        name: str,
        description: str,
        qml_widget: type[BaseMetaConfigOptionWidget]
    ) -> None:
        """Registers an option that does not directly contain a value.

        This allows register option items of a more complex nature that have a
        dedicated QML UI widget to them which handles the UI configuring the
        content and also the logic to persist the data to the Configuration
        class.

        Args:
            section: overall section this option is associated with
            group: grouping into which the option belongs
            name: name by which the new option is shown
            description: description of the parameter's purpose
            qml_widget: QML widget class to use for this option
        """
        key = (section, group, name)
        if key in self._options:
            logging.getLogger("system").warning(
                f"Option {section}.{group}.{name} already registered."
            )
            return

        self._options[key] = {
            "description": description,
            "qml_widget": qml_widget
        }

    def sections(self) -> list[str]:
        """Returns the list of sections for which options have been registered.

        Returns:
            List of section names.
        """
        return list(set(section for section, _, _ in self._options.keys()))

    def groups(self, section: str) -> list[str]:
        """Returns the groups associated with the given section.

        Args:
            section: name of the section for which to find groups

        Returns:
            List of group names.
        """
        return list(set(
            group for sec, group, _ in self._options.keys() if sec == section
        ))

    def entries(self, section: str, group: str) -> list[str]:
        """Returns the entries associated with the given section and group.

        Args:
            section: name of the section for which to find entries
            group: name of the group for which to find entries

        Returns:
            List of entry names.
        """
        return list(
            name for sec, grp, name in self._options.keys()
            if sec == section and grp == group
        )

    def qml_widget(
            self,
            section: str,
            group: str,
            name: str
    ) -> type[BaseMetaConfigOptionWidget]:
        """Returns the QML widget class associated with the given option.

        Args:
            section: name of the section for which to find the option
            group: name of the group for which to find the option
            name: name of the option

        Returns:
            Class type of the QML widget to be used.
        """
        return cast(
            type[BaseMetaConfigOptionWidget],
            self._retrieve_value(section, group, name, "qml_widget")
        )

    def description(self, section: str, group: str, name: str) -> Optional[str]:
        """Returns the description associated with the given option.

        Args:
            section: name of the section for which to find the option
            group: name of the group for which to find the option
            name: name of the option

        Returns:
            Description string or None if not found.
        """
        return cast(
            str,
            self._retrieve_value(section, group, name, "description")
        )

    def _retrieve_value(
            self,
            section: str,
            group: str,
            name: str,
            entry: str
    ) -> str|type[BaseMetaConfigOptionWidget]:
        """Retrieves an entry from storage.

        Args:
            section: name of the section
            group: name of the group
            name: name of the option
            entry: which entry to retrieve

        Returns:
            Value of the requested entry.
        """
        key = (section, group, name)
        if key not in self._options:
            raise GremlinError(f"No option with key {key} exists.")

        match entry:
            case "description":
                return self._options[key]["description"]
            case "qml_widget":
                return self._options[key]["qml_widget"]
            case _:
                raise GremlinError(f"Unknown entry '{entry}' requested.")


MetaConfigOption().register(
    "action", "general", "action-list",
    "Reorder the order in which actions appear in the drop down menu as desired "
    "by dragging and dropping them in the list. Actions that are not desired "
    "can be turned off via the switch next to each action.",
    ActionSequenceOrdering
)

MetaConfigOption().register(
    "profile", "automation", "auto-loading",
    "Automatically load profiles based on the currently active executable. "
    "Each entry an executable and the profile to load with it. The executable "
    "can be changed manually if needed. This also allows specifying the path "
    "to an executable as a regular expression.",
    ProfileAutoLoadingModel
)

MetaConfigOption().register(
    "action", "text-to-speech", "voice-selection",
    "Voices available for use with Text to Speech actions.",
    TTSVoiceSelectionModel
)
