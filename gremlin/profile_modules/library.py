# -*- coding: utf-8; -*-

"""Action library management for profiles.

This module contains the Library class which stores and manages
all action configurations that can be referenced by input bindings.

Extracted from gremlin.profile for better organization.
"""

import logging
import uuid
from typing import Dict, List, Optional, Callable
from xml.etree import ElementTree

from gremlin import error, plugin_manager
from gremlin.base_classes import ILibrary, IActionData
from gremlin.util import safe_read


def read_action_ids(node: ElementTree.Element) -> List[uuid.UUID]:
    """Extract all action IDs referenced in an XML node.
    
    Args:
        node: XML element to search for action references
        
    Returns:
        List of UUIDs found in the node
    """
    action_ids = []
    for child in node.findall(".//action-ref"):
        try:
            action_ids.append(uuid.UUID(child.text))
        except (ValueError, AttributeError):
            pass
    return action_ids


class Library(ILibrary):
    """Stores actions in order to be referenced by input binding instances.

    Each item is a self-contained entry with a UUID assigned to it which
    is used by the input items to reference the actual content.
    
    Implements ILibrary interface to break circular dependency with base_classes.
    """

    def __init__(self):
        """Creates a new library instance.

        The library contains both the individual action configurations as well
        as the items composed of them.
        """
        self._actions: Dict[uuid.UUID, IActionData] = {}

    def add_action(self, action: IActionData) -> None:
        """Add an action to the library.
        
        Args:
            action: The action to add to the library
        """
        if action.id in self._actions:
            logging.getLogger("system").warning(
                f"Action with id {action.id} already exists, skipping."
            )
        self._actions[action.id] = action

    def delete_action(self, key: uuid.UUID) -> None:
        """Deletes the action with the given key from the library.

        Args:
            key: the key of the action to delete
        """
        if key not in self._actions:
            logging.getLogger("system").warning(
                f"Attempting to remove non-existant action with id {key}."
            )
        if key in self._actions:
            del self._actions[key]
    
    def remove_action(self, action_id: uuid.UUID) -> None:
        """Remove action from library (implements ILibrary interface).
        
        Args:
            action_id: UUID of action to remove
        """
        self.delete_action(action_id)

    def remove_unused(
        self,
        action: IActionData,
        recursive: bool = True
    ) -> None:
        """Removes the provided action and all its children if unused.

        Args:
            action: the action to remove
            recursive: if true all children of the action will be subjected
                to the same removal check
        """
        # If the action occurs in another action we can abort any further
        # processing
        for entry in self._actions.values():
            child_actions, _ = entry.get_actions()
            if action in child_actions:
                return

        # Build a list of all actions linked to the provided action and then
        # attempt to remove them one after the other
        if recursive:
            all_actions = [action]
            index = 0
            while index < len(all_actions):
                child_actions, _ = all_actions[index].get_actions()
                all_actions.extend(child_actions)
                index += 1
            all_actions.pop(0)

            for entry in reversed(all_actions):
                self.remove_unused(entry, True)

        del self._actions[action.id]

    def actions_by_type(
            self,
            action_type: type[IActionData]
    ) -> List[IActionData]:
        """Returns all actions in the library matching the given type.

        Args:
            action_type: type of the action to return

        Returns:
            All actions of the given type
        """
        return [a for a in self._actions.values() if isinstance(a, action_type)]

    def actions_by_predicate(
            self,
            predicate: Callable[[IActionData], bool]
    ) -> List[IActionData]:
        """Returns the list of actions fulfilling the given predicate.

        Args:
            predicate: the predicate to evaluate on each action

        Returns:
            List of all actions fulfilling the given predicate
        """
        actions = []
        for action in self._actions.values():
            if predicate(action):
                actions.append(action)
        return actions

    def get_action(self, action_id: uuid.UUID) -> Optional[IActionData]:
        """Returns the action specified by the action_id.

        Args:
            action_id: the UUID to return an action for

        Returns:
            The action instance stored at the given key, or None if not found
        """
        return self._actions.get(action_id, None)

    def has_action(self, key: uuid.UUID) -> bool:
        """Checks if an action exists with the given key.

        Args:
            key: the key to check for

        Returns:
            True if an action exists for the specific key, False otherwise
        """
        return key in self._actions

    def _validate_action_entry(self, entry: ElementTree.Element) -> None:
        """Validate required attributes for action entry.
        
        Args:
            entry: XML action entry
            
        Raises:
            ProfileError: If entry is invalid
        """
        if not set(["id", "type"]).issubset(entry.keys()):
            raise error.ProfileError(
                "Incomplete library action specification"
            )
        
        type_key = entry.get("type")
        if type_key not in plugin_manager.PluginManager().tag_map:
            action_id = safe_read(entry, "id", uuid.UUID)
            raise error.ProfileError(
                f"Unknown type '{type_key}' in action with id '{action_id}'"
            )

    def _parse_immediate_actions(
        self,
        node: ElementTree.Element,
        can_parse: Callable
    ) -> List[ElementTree.Element]:
        """Parse actions that can be parsed immediately.
        
        Args:
            node: XML node containing actions
            can_parse: Callable to check if action can be parsed
            
        Returns:
            List of actions that need delayed parsing
        """
        parse_later = []
        for entry in node.findall("./library/action"):
            self._validate_action_entry(entry)
            
            if can_parse(entry):
                self._parse_xml_action(entry)
            else:
                parse_later.append(entry)
        
        return parse_later

    def _parse_delayed_actions(
        self,
        parse_later: List[ElementTree.Element],
        can_parse: Callable
    ) -> None:
        """Parse actions with dependencies.
        
        Args:
            parse_later: List of actions to parse
            can_parse: Callable to check if action can be parsed
        """
        iterations = 0
        action_set = None
        
        while len(parse_later) > 0:
            entry = parse_later.pop(0)
            if can_parse(entry):
                self._parse_xml_action(entry)
                iterations = 0
            else:
                parse_later.append(entry)

            new_action_set = set(parse_later)
            if new_action_set != action_set:
                new_action_set = action_set
            else:
                iterations += 1
                if iterations > 5:
                    logging.getLogger("system").error(
                        "Loading profile failed due to action resolution chain"
                    )
                    break

    def from_xml(self, node: ElementTree.Element) -> None:
        """Parses a library node to populate this instance.

        Args:
            node: XML node containing the library information
        """
        can_parse = lambda entry: all([
            aid in self._actions for aid in read_action_ids(entry)
        ])

        parse_later = self._parse_immediate_actions(node, can_parse)
        self._parse_delayed_actions(parse_later, can_parse)

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the content of this library.

        Returns:
            XML node holding the instance's content
        """
        # Process the entire library, removing links to invalid actions
        invalid_aids = [n.id for n in self._actions.values() if not n.is_valid()]
        for action in self._actions.values():
            for selector in action._valid_selectors():
                to_remove = []
                for i, child in enumerate(action.get_actions(selector)[0]):
                    if child.id in invalid_aids:
                        to_remove.append(i)
                for i in to_remove:
                    action.remove_action(i, selector)

        # Generate library subtree
        node = ElementTree.Element("library")
        for action in [n for n in self._actions.values() if n.is_valid()]:
            node.append(action.to_xml())
        return node

    def _parse_xml_action(self, action: ElementTree.Element) -> None:
        """Parses an action XML node and stores it within the library.

        Args:
            action: XML node to parse
        """
        type_key = action.get("type")
        action_obj = plugin_manager.PluginManager().tag_map[type_key]()
        action_obj.from_xml(action, self)
        if action_obj.id in self._actions:
            raise error.ProfileError(
                f"Duplicate library action entry with id '{action_obj.id}'"
            )
        self._actions[action_obj.id] = action_obj
