# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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
from enum import Enum
from typing import Any, Dict, List, Tuple, Optional
import uuid
from xml.etree import ElementTree

from gremlin.error import GremlinError
from gremlin.event_handler import Event
from gremlin.profile import Library
from gremlin.types import InputType


class DataInsertionMode(Enum):

    """Specifies to insertion type to be performed."""

    Append = 0
    Prepend = 1


class Value:

    """Represents an input value, keeping track of raw and "seen" value."""

    def __init__(self, raw: Any) -> None:
        """Creates a new value and initializes it.

        Args:
            raw: the initial raw data
        """
        self._raw = raw
        self._current = raw

    @property
    def raw(self) -> Any:
        """Returns the raw unmodified value.

        Returns:
            raw unmodified value
        """
        return self._raw

    @property
    def current(self) -> Any:
        """Returns the current, potentially, modified value.

        Returns:
            current and potentially modified value
        """
        return self._current

    @current.setter
    def current(self, current: Any) -> None:
        """Sets the current value which may differ from the raw one.

        Args:
            current: the new current value
        """
        self._current = current


class AbstractActionData(ABC):

    """Base class holding the data of all action related data classes."""

    def __init__(self, behavior_type: InputType=InputType.JoystickButton) -> None:
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
    def from_xml(
            self,
            node: ElementTree.Element,
            library: Library
    ) -> None:
        """Populates the instance's values with the content of the XML node.

        Args:
            node: the XML node to parse for content
            library: Library instance containing all actions
        """
        pass

    @abstractmethod
    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing the instance's contents.

        Returns:
            XML node containing the instance's contents
        """
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """Returns whether the instance is in a valid state.

        Returns:
            True if the instance is in a valid state, False otherwise
        """
        pass

    def get_actions(
            self,
            selector: Optional[str]=None
    )  -> Tuple[List[AbstractActionData], List[str]]:
        """Returns all actions matching the given selector.

        The selector indicates the container from which to return actions. If
        no selector, or None, is provided all child actions are returned.

        Args:
            selector: name of the container to return actions from
        Returns:
            Tuple containing a list of action instances and their
            corresponding selector.
        """
        self._validate_selector(selector)

        actions = []
        selectors = []
        if selector is None:
            for entry in self._valid_selectors():
                new_actions = self._get_container(entry)
                actions.extend(new_actions)
                selectors.extend([entry] * len(new_actions))
        else:
            actions = self._get_container(selector)
            selectors = [selector]  * len(actions)
        return (actions, selectors)

    def insert_action(
            self,
            action: AbstractActionData,
            selector: str,
            mode: DataInsertionMode=DataInsertionMode.Append,
            anchor: Optional[int]=None
    ) -> None:
        """Inserts an action as a child of the current object.

        Inserts the given action into the container specified by the selector
        parameter. When no anchor is provided, appending inserts the action
        at the end of the container while prepending inserts it as the first
        element. If an anchor action is provided, appending inserts it after
        the anchor while prepending inserts it before.

        Args:
            action: the action to insert as a child
            selector: name of the container into which to insert the action
            mode: insertion mode to use when adding the action
            anchor: offset into the container that specifies where to perform
                the insertion
        """
        self._validate_selector(selector, False)

        container = self._get_container(selector)
        if anchor is None:
            anchor = 0 if mode == DataInsertionMode.Prepend else len(container)
        else:
            if not (0 <= anchor <= len(container)):
                raise GremlinError(
                    f"{self.name}: specified anchor index '{anchor.id}' is " +
                    f"not present in container '{selector}'"
                )
            if mode == DataInsertionMode.Append:
                anchor += 1

        container.insert(anchor, action)

    def remove_action(self, index: int, selector: str) -> None:
        """Removes the provided action from this action's children.

        Args:
            index: index of the action in the container to remove
            selector: the container in which the action is located
        """
        self._validate_selector(selector)

        container = self._get_container(selector)
        if 0 <= index < len(container):
            del container[index]
        else:
            raise GremlinError(
                f"{self.name}: attempting to remove action with invalid " +
                f"index ({index}) from container '{selector}'"
            )

    @abstractmethod
    def _valid_selectors(self) -> List[str]:
        """Returns the list of valid selectors.

        Returns:
            List of valid selectors
        """
        pass

    @abstractmethod
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        """Returns the list corresponding to the selector.

        Args:
            selector: string representing the container to return

        Returns:
            List container with actions referenced by the selector
        """
        pass

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
        pass

    # General utility functions, supporting the implementation of actions.

    def _validate_selector(
            self,
            selector: Optional[str],
            none_is_valid: bool=True
    ) -> None:
        """Verifies that a provided selector is valid.

        If the provided selector is not supported by the action then an
        exception is raised. A selector of None is valid as it implies that
        all valid selectors should be used.

        Args:
            selector: string representing the selector
            none_is_valid: if True, None selector values are accepted
        """
        valid_selector = selector in self._valid_selectors()
        valid_none = selector is None if none_is_valid else False
        if not (valid_selector or valid_none):
            raise GremlinError(
                f"{self.name}: provided selector '{selector}' is invalid"
            )

    def _remove_entry_from_list(self, storage: List[Any], value: Any) -> None:
        """Removes the provided value from the given container.

        Args:
            storage: list object from which to remove the value
            value: the value to remove
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

    def __init__(self, instance: AbstractActionData) -> None:
        """Creates a new instance, extracting needed information.

        Args:
            instance the object which contains the information needed to
            execute it later on
        """
        self.data = instance
        self.functors = {}

        # Recursively generate all functors
        for selector in instance._valid_selectors():
            self.functors[selector] = []
        for action, selector in zip(*instance.get_actions()):
            self.functors[selector].append(action.functor(action))

    @abstractmethod
    def __call__(self, event: Event, value: Value) -> None:
        """Processes the functor using the provided event and value data.

        Args:
            event: the raw event that caused the functor to be executed
            value: the possibly modified value
        """
        pass
