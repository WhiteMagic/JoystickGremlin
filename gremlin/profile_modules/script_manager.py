# -*- coding: utf-8; -*-

"""Script management for profiles.

This module contains the ScriptManager class for managing
user scripts associated with profiles.

Extracted from gremlin.profile for better organization.
"""

from pathlib import Path
from typing import List, Optional
from xml.etree import ElementTree

from gremlin import error


class Script:
    """Represents a single script instance.
    
    A script has a path (location on disk) and a name
    (for user identification when multiple instances exist).
    """

    def __init__(self, path: Optional[Path] = None, name: str = ""):
        """Creates a new script instance.

        Args:
            path: path to the script file
            name: user-friendly name for the script
        """
        self.path = path
        self.name = name

    def from_xml(self, node: ElementTree.Element) -> None:
        """Loads script data from XML.

        Args:
            node: XML element containing script data
        """
        path_node = node.find("./path")
        if path_node is not None and path_node.text:
            self.path = Path(path_node.text)

        name_node = node.find("./name")
        if name_node is not None and name_node.text:
            self.name = name_node.text

    def to_xml(self) -> ElementTree.Element:
        """Converts script to XML.

        Returns:
            XML element containing script data
        """
        node = ElementTree.Element("script")

        path_node = ElementTree.Element("path")
        path_node.text = str(self.path)
        node.append(path_node)

        name_node = ElementTree.Element("name")
        name_node.text = self.name
        node.append(name_node)

        return node


class ScriptManager:
    """Manages user scripts for a profile.
    
    Scripts can be assigned to profiles and executed during
    profile activation. Multiple instances of the same script
    can be added with different names.
    """

    def __init__(self, profile) -> None:
        """Creates a new instance.

        Each script is uniquely identified by the path to the script as well
        as its assigned name.

        Args:
            profile: the profile whose scripts to manage
        """
        self._profile = profile
        self._scripts: List[Script] = []

    @property
    def scripts(self) -> List[Script]:
        """Returns all managed scripts.

        Returns:
            List of all managed scripts
        """
        return self._scripts

    def add_script(self, path: Path) -> None:
        """Adds a new script to the manager.

        Args:
            path: path to the script's location
        """
        self._scripts.append(Script(path, self._default_name(path)))
        self._scripts.sort(key=lambda s: (s.path, s.name))

    def remove_script(self, path: Path, name: str) -> None:
        """Removes the specified script.

        Args:
            path: path to the script
            name: name of the script
        """
        script = self._find_instance(path, name)
        if script:
            self._scripts.remove(script)

    def rename_script(self, path: Path, old_name: str, new_name: str) -> None:
        """Renames the specified script.

        Args:
            path: path to the script
            old_name: current name of the script
            new_name: new name to use for the script
        """
        names = [s.name for s in self.scripts if s.path == path]
        if new_name not in names:
            script = self._find_instance(path, old_name)
            if script:
                script.name = new_name
                self._scripts.sort(key=lambda s: (s.path, s.name))

    def index_of(self, path: Path, name: str) -> int:
        """Returns the index of the specified script.

        Args:
            path: path to the script
            name: name of the script

        Returns:
            Index of the script in the list of scripts
        """
        instance = self._find_instance(path, name)
        if not instance:
            raise error.GremlinError(
                f"Unable to find script {path} with name '{name}'"
            )
        return self._scripts.index(instance)

    def _find_instance(self, path: Path, name: str) -> Script | None:
        """Finds a script instance by path and name.

        Args:
            path: path to the script
            name: name of the script

        Returns:
            Script instance if found, None otherwise
        """
        for script in self._scripts:
            if script.path == path and script.name == name:
                return script
        return None

    def _default_name(self, path: Path) -> str:
        """Generates a valid default name for the given script path.

        Args:
            path: path to the script

        Returns:
            Valid name to use for the script that doesn't clash with other
            existing scripts.
        """
        names = [s.name for s in self.scripts if s.path == path]
        for i in range(len(names) + 1):
            candidate = f"Instance {i+1}"
            if candidate not in names:
                return candidate
        raise error.GremlinError(
            f"Unable to find a valid default name for {path}"
        )

    def from_xml(self, root: ElementTree.Element) -> None:
        """Loads scripts from XML.

        Args:
            root: XML root element containing scripts
        """
        for node in root.findall("./scripts/script"):
            self._scripts.append(Script())
            self._scripts[-1].from_xml(node)
        self._scripts.sort(key=lambda s: (s.path, s.name))

    def to_xml(self) -> ElementTree.Element:
        """Converts scripts to XML.

        Returns:
            XML element containing all scripts
        """
        script_node = ElementTree.Element("scripts")
        for script in self._scripts:
            script_node.append(script.to_xml())
        return script_node
