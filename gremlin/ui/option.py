# -*- coding: utf-8; -*-

# Copyright (C) 2022 Lionel Ott
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

import logging
from typing import cast, Any, Dict, Optional, TYPE_CHECKING

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal

import gremlin.config
from gremlin.common import SingletonMetaclass
from gremlin.error import GremlinError, MissingImplementationError
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
        return list(sorted(
            set(self._config.sections() + self._option.sections())
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

            # TODO: Figure out if we need to retrieve an option or a config
            #       entry and handle it accordingly.
            # Special handling
            name = entries[index.row()]
            if self._config.exists(self._section_name, self._group_name, name):
                value = self._config.get(
                    self._section_name,
                    self._group_name,
                    entries[index.row()],
                    role_name
                )
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
                        print(value)
                    case "data_type":
                        value = "meta_option"
        return value

    def setData(
            self,
            index: ta.ModelIndex,
            value: Any,
            role: int=QtCore.Qt.ItemDataRole.EditRole
    ) -> bool:
        entries = self._config.entries(self._section_name, self._group_name)
        if not index.isValid() or index.row() >= len(entries):
            return False

        if self.roles[role] == "value":
            self._config.set(
                self._section_name,
                self._group_name,
                entries[index.row()],
                value
            )

            self.dataChanged.emit(index, index, {role})
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


# @QtQml.QmlElement
# class OptionTestWidget(BaseMetaConfigOptionWidget):

    timeChanged = Signal()

    def _qml_path(self) -> str:
        return "file:///" + QtCore.QFile("qml:OptionTest.qml").fileName()

    @Property(float, notify=timeChanged)
    def timeNow(self) -> float:
        import time
        return time.time()


@QtQml.QmlElement
class ActionSequenceOrdering(QtCore.QAbstractListModel, BaseMetaConfigOptionWidget):

    roles = {
        QtCore.Qt.UserRole + 1: QtCore.QByteArray(b"name"),
        QtCore.Qt.UserRole + 2: QtCore.QByteArray(b"visible"),
    }

    def __init__(self, parent: Optional[QtCore.QObject]=None) -> None:
        QtCore.QAbstractListModel.__init__(self, parent)
        BaseMetaConfigOptionWidget.__init__(self)

        self._config = gremlin.config.Configuration()
        self._cfg_key = ["global", "general", "action_priorities"]

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
                case _:
                    raise GremlinError(f"Unknown role name {role}")

        else:
            raise GremlinError("Invalid role encountered")

    def roleNames(self) -> Dict[int, QtCore.QByteArray]:
        return self.roles

    def _qml_path(self) -> str:
        return "file:///" + \
            QtCore.QFile("qml:OptionActionSequenceOrdering.qml").fileName()


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
    "global", "general", "action list",
    "Reorder actions as desired",
    ActionSequenceOrdering
)