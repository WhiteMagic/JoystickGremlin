# -*- coding: utf-8; -*-

"""Profile settings management.

This module contains the Settings class for managing profile-wide
configuration settings.

Extracted from gremlin.profile for better organization.
"""

from xml.etree import ElementTree
from typing import Optional


class Settings:
    """Stores settings specific to a profile.

    This includes global profile configuration like mode behavior,
    activation settings, and other profile-wide options.
    """

    def __init__(self, parent):
        """Creates a new Settings instance.

        Args:
            parent: parent Profile instance
        """
        self._parent = parent
        self._default_mode = "Default"
        self._startup_mode = None
        self._autoload_mode = True

    @property
    def default_mode(self) -> str:
        """Returns the default mode name.

        Returns:
            Name of the default mode
        """
        return self._default_mode

    @default_mode.setter
    def default_mode(self, value: str) -> None:
        """Sets the default mode name.

        Args:
            value: new default mode name
        """
        self._default_mode = value

    @property
    def startup_mode(self) -> Optional[str]:
        """Returns the startup mode name.

        Returns:
            Name of the startup mode, or None
        """
        return self._startup_mode

    @startup_mode.setter
    def startup_mode(self, value: Optional[str]) -> None:
        """Sets the startup mode name.

        Args:
            value: new startup mode name
        """
        self._startup_mode = value

    @property
    def autoload_mode(self) -> bool:
        """Returns whether modes should be automatically loaded.

        Returns:
            True if autoload is enabled
        """
        return self._autoload_mode

    @autoload_mode.setter
    def autoload_mode(self, value: bool) -> None:
        """Sets the autoload mode flag.

        Args:
            value: new autoload setting
        """
        self._autoload_mode = value

    def from_xml(self, node: ElementTree.Element) -> None:
        """Initializes settings from XML node.

        Args:
            node: XML node containing settings data
        """
        settings_node = node.find("./settings")
        if settings_node is None:
            return

        # Parse default mode
        default_mode = settings_node.find("./default-mode")
        if default_mode is not None and default_mode.text:
            self._default_mode = default_mode.text

        # Parse startup mode
        startup_mode = settings_node.find("./startup-mode")
        if startup_mode is not None and startup_mode.text:
            self._startup_mode = startup_mode.text

        # Parse autoload setting
        autoload = settings_node.find("./autoload-mode")
        if autoload is not None and autoload.text:
            self._autoload_mode = autoload.text.lower() == "true"

    def to_xml(self) -> ElementTree.Element:
        """Converts settings to XML representation.

        Returns:
            XML element containing settings data
        """
        node = ElementTree.Element("settings")

        # Default mode
        default_mode = ElementTree.Element("default-mode")
        default_mode.text = self._default_mode
        node.append(default_mode)

        # Startup mode
        if self._startup_mode:
            startup_mode = ElementTree.Element("startup-mode")
            startup_mode.text = self._startup_mode
            node.append(startup_mode)

        # Autoload mode
        autoload = ElementTree.Element("autoload-mode")
        autoload.text = "true" if self._autoload_mode else "false"
        node.append(autoload)

        return node
