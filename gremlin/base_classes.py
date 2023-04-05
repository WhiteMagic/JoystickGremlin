# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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

from abc import abstractmethod, ABC

from typing import Any, Callable, List, Optional
import uuid
from xml.etree import ElementTree

from gremlin.error import MissingImplementationError
from gremlin.event_handler import Event
from gremlin.profile import Library
from gremlin.types import InputType


class Value:

    """Represents an input value, keeping track of raw and "seen" value."""

    def __init__(self, raw):
        """Creates a new value and initializes it.

        :param raw the initial raw data
        """
        self._raw = raw
        self._current = raw

    @property
    def raw(self):
        """Returns the raw unmodified value.

        :return raw unmodified value
        """
        return self._raw

    @property
    def current(self):
        """Returns the current, potentially, modified value.

        :return current and potentially modified value
        """
        return self._current

    @current.setter
    def current(self, current):
        """Sets the current value which may differ from the raw one.

        :param current the new current value
        """
        self._current = current


class AbstractActionData(ABC):

    """Base class holding the data of all action related data classes."""

    def __init__(self, behavior_type: InputType=InputType.JoystickButton):
        """Creates a new action data instance.

        Args:
            behavior_type: type of behavior of this action
        """
        self._id = uuid.uuid4()
        self._behavior_type = behavior_type

    @property
    def id(self) -> uuid.UUID:
        """Returns the identifier of this action.

        Returns:
            Unique identifier of this action
        """
        return self._id

    @property
    def behavior_type(self) -> InputType:
        """Returns the behavior type this action is configured for.
        
        Returns:
            InputType corresponding to the action's behavior
        """
        return self._behavior_type

    def set_behavior_type(self, new_behavior: InputType) -> None:
        """Sets the behavior type of the action.
        
        Args:
            new_behavior: new InputType corresponding to the behavior type
        """
        old_behavior = self._behavior_type
        self._behavior_type = new_behavior
        if old_behavior != new_behavior:
            self._handle_behavior_change(old_behavior, new_behavior)

    # Interface that all actions have to support, even if only an empty noop
    # implementation is provided.

    @abstractmethod
    def from_xml(self, node: ElementTree.Element, library: profile.Library) -> None:
        """Populates the instance's values with the content of the XML node.

        Args:
            node: the XML node to parse for content
        """
        raise MissingImplementationError(
            "AbstractActionModel.from_xml not implemented in subclass"
        )

    @abstractmethod
    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing the instance's contents.

        Returns:
            XML node containing the instance's contents
        """
        raise MissingImplementationError(
            "AbstractActionModel.to_xml not implemented in subclass"
        )

    @abstractmethod
    def is_valid(self) -> bool:
        """Returns whether or not the instance is in a valid state.

        Returns:
            True if the instance is in a valid state, False otherwise
        """
        raise MissingImplementationError(
            "AbstractActionModel.is_valid not implemented in subclass"
        )

    @abstractmethod
    def get_actions(
        self,
        selector: Optional[Any]=None
    )  -> List[AbstractActionData]:
        """Returns all actions matching the given selector.

        The selector can be used by implementations to only return parts
        of the actions present in an action. If no selector is provided all
        child actions have to be returned.

        Args:
            selector: information used by the implementation to select
                actions
        Returns:
            List of action instances based on the provided selector
        """
        raise MissingImplementationError(
            "AbstractActionModel.get_actions not implemented in subclass"
        )

    @abstractmethod
    def add_action(
        self,
        action: AbstractActionData,
        options: Optional[Any]=None
    ) -> None:
        """Adds a new action as a child of the current object.

        The specific handling of adding the child action is dependant on the
        particular action implementation. Additional information on how to
        perform the addition is encoded in the options parameter.
        
        Args:
            action: the action to insert as a child
            options: additional options to consider when adding the child
        """
        raise MissingImplementationError(
            "AbstractActionModel.add_child not implemented in subclass"
        )

    @abstractmethod
    def remove_action(self, action: AbstractActionData) -> None:
        """Removes the provided action from this action's children.

        Args:
            action: the action to remove
        """
        raise MissingImplementationError(
            "AbstractActionModel.remove_action not implemented in subclass"
        )

    @abstractmethod
    def insert_action(self, container: str, action: AbstractActionData) -> None:
        """Inserts the action into a specific container.

        Args:
            container: label of the container into which to insert the
                provided action
            action: the action to insert
        """
        raise MissingImplementationError(
            "AbstractActionModel.insert_action not implemented in subclass"
        )

    @abstractmethod
    def add_action_after(
        self,
        anchor: AbstractActionData,
        action: AbstractActionData
    ) -> None:
        """Adds the provided action after the specified anchor action.

        Args:
            anchor: action after which to insert the given action
            action: the action to remove
        """
        raise MissingImplementationError(
            "AbstractActionModel.add_action_after not implemented in subclass"
        )

    @abstractmethod
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        """Handles changing of the behavior type of the action.

        This function will only be called when the two behaviors are different.

        Args:
            old_behavior: type describing the old behavior
            new_behavior: type describing the new behavior
        """
        raise MissingImplementationError(
            "AbstractActionModel._handle_behavior_change not implemented "
            "in subclass"
        )

    # General utility functions, supporting the implementation of actions.

    # def _create_action_list(
    #     self,
    #     action_ids: List[uuid.UUID]
    # ) -> List[ActionModel]:
    #     """Returns a list containing actions with an id matching the provided
    #     ones.
        
    #     Args:
    #         action_ids: List of ids of actions to retrieve
        
    #     Returns:
    #         List of actions corresponding to the provided ids
    #     """
    #     actions = []
    #     # FIXME: this is outdated and needs replacing
    #     # for action in self._action_tree.root.nodes_matching(
    #     #     lambda x: x.value.id in action_ids
    #     # ):
    #     #     # Set parent relationship to handle object deletion properly
    #     #     action.setParent(self)
    #     #     # Create model instances representing the individual action
    #     #     actions.append(ActionModel(
    #     #         action,
    #     #         self.behavior_type,
    #     #         self._action_tree,
    #     #         parent=self
    #     #     ))
    #    return actions

    # def _find_actions_matching_predicate(
    #     self,
    #     predicate: Callable[[AbstractActionData], bool]
    # ) -> List[AbstractActionData]:
    #     pass

    def _remove_entry_from_list(self, storage: List[Any], value: Any) -> None:
        """Removes the provided value from the given container.

        Args:
            storage: list object from which to remove the value
            value: value to remove
        """
        if value in storage:
            storage.remove(value)

    def _insert_entry_into_list(
        self,
        storage: List[Any],
        anchor: Any,
        value: Any,
        append: bool=True
    ) -> None:
        """Inserts the provided value into the given storage.

        Args:
            storage: list container into which to insert the value
            anchor: value around which to insert the new value
            value: new value to insert into the list
            append: append if True, prepend if False
        """
        if anchor in storage:
            index = storage.index(anchor)
            index = index + 1 if append else index
            storage.insert(index, value)


class AbstractFunctor(ABC):

    """Abstract base class defining the interface for functor like classes.

    TODO: Rework this thing

    These classes are used in the internal code execution system.
    """

    def __init__(self, instance: AbstractActionData):
        """Creates a new instance, extracting needed information.

        :param instance the object which contains the information needed to
            execute it later on
        """
        self.data = instance

    @abstractmethod
    def process_event(self, event: Event, value: Value) -> None:
        """Processes the functor using the provided event and value data.

        :param event the raw event that caused the functor to be executed
        :param value the possibly modified value
        """
        pass
