# -*- coding: utf-8; -*-

# Copyright (C) 2017 Lionel Ott
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

import typing
from abc import abstractmethod, ABC
import copy
import time
from typing import Any, List, Tuple, Optional
import uuid
from xml.etree import ElementTree

from gremlin import util, event_handler
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import ActionActivationMode, ActionProperty, InputType, \
    PropertyType, DataInsertionMode, DataCreationMode

if typing.TYPE_CHECKING:
    from gremlin.event_handler import Event


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

    # Fields expected to be present in every action plugin. These define
    # information required by the plugin manager as well as UI and behavior
    # logic.
    version = None
    name = None
    tag = None
    icon = None
    functor = None
    model = None
    properties = []
    input_types: List[InputType] = []

    def __init__(self, behavior_type: InputType=InputType.JoystickButton) -> None:
        """Creates a new action data instance.

        Args:
            behavior_type: type of behavior of this action
        """
        self._id = uuid.uuid4()
        self._behavior_type = behavior_type
        self._action_label = ""

        self._activation_mode = ActionActivationMode.Deactivated
        for prop in self.properties:
            match prop:
                case ActionProperty.ActivateOnPress:
                    self._activation_mode = ActionActivationMode.Press
                case ActionProperty.ActivateOnRelease:
                    self._activation_mode = ActionActivationMode.Release
                case ActionProperty.ActivateOnBoth:
                    self._activation_mode = ActionActivationMode.Both
                case ActionProperty.ActivateDisabled:
                    self._activation_mode = ActionActivationMode.Disallowed

    @classmethod
    def create(
            cls,
            mode: DataCreationMode,
            behavior_type: InputType=InputType.JoystickButton
    ) -> AbstractActionData:
        """Creates a new instance with the given creation mode.

        Args:
            mode: defines how to create the new instance
            behavior_type: type of behavior of this action

        Returns:
            The newly created instance
        """
        if mode == DataCreationMode.Create:
            obj = cls(behavior_type)
            obj.action_label = cls.name
            return obj
        else:
            obj =  cls._do_create(mode, behavior_type)
            obj.action_label = cls.name
            if obj is None:
                raise GremlinError(f"Unable to create an object")
            return obj

    @classmethod
    def can_create(cls) -> bool:
        """Returns if requirements to create his action are met.

        By default this always returns True, however, subclasses can override
        this method to implement logic that checks specific requirements.
        """
        return True

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

    @property
    def action_label(self) -> str:
        return self._action_label

    @action_label.setter
    def action_label(self, value: str) -> None:
        self._action_label = value

    @property
    def activation_mode(self) -> ActionActivationMode:
        return self._activation_mode

    @activation_mode.setter
    def activation_mode(self, value: ActionActivationMode) -> None:
        self._activation_mode = value

    def from_xml(
            self,
            node: ElementTree.Element,
            library: Library
    ) -> None:
        """Populates the instance's values with the content of the XML node.

        Calls the implementation specific serialization routine.

        Args:
            node: the XML node to parse for content
            library: Library instance containing all actions
        """
        self.action_label = util.read_property(
            node, "action-label", PropertyType.String
        )
        self.activation_mode = util.read_property(
            node, "activation-mode", PropertyType.ActionActivationMode
        )
        self._from_xml(node, library)

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing the instance's contents.

        Calls the implementation specific serialization routine.

        Returns:
            XML node containing the instance's contents
        """
        if not self.is_valid():
            print(f"This node is invalid {self.id}")
            return None

        node = self._to_xml()
        if node is not None:
            node.append(util.create_property_node(
                "action-label", self.action_label, PropertyType.String
            ))
            node.append(util.create_property_node(
                "activation-mode",
                self.activation_mode,
                PropertyType.ActionActivationMode
            ))
        else:
            print(f"Received invalid node in {self.id}")
        return node

    # Interface that all actions have to support, even if only an empty noop
    # implementation is provided.

    @abstractmethod
    def _from_xml(
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
    def _to_xml(self) -> ElementTree.Element:
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
            mode: DataInsertionMode = DataInsertionMode.Append,
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

    def clone(self) -> AbstractActionData:
        """Returns a copy of this action with a novel unique id.

        Returns:
            Copy of the action with a new unique id
        """
        clone = copy.deepcopy(self)
        clone._id = uuid.uuid4()
        return clone

    @classmethod
    def _do_create(
            cls,
            mode: DataCreationMode,
            behavior_type: InputType
    ) -> AbstractActionData:
        """Allows customization of instance creation in derived classes.

        Args:
            mode: mode to use when creating the new instance
            behavior_type: type of behavior of this action

        Returns:
            Newly created instance
        """
        pass

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

    """Abstract base class defining the interface for functor like classes."""

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
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        """Processes the functor using the provided event and value data.

        Args:
            event: the raw event that caused the functor to be executed
            value: the possibly modified value
            properties: additional property information to pass to child
                functors
        """
        pass

    def _process_event(
        self,
        functors: List[AbstractFunctor],
        event: event_handler.Event,
        value: Value,
        properties: list[ActionProperty]=[]
    ):
        """Processes the provided event data with every provided functor.

        Args:
            functors: List of functors to process the event with
            event: event to process
            value: value of the event
            properties: additional property information to pass to child
                functors
        """
        for functor in functors:
            functor(event, value, properties)

    def _pulse_event(
            self,
            functors: List[AbstractFunctor],
            event_press: event_handler.Event,
            value_press: Value,
            properties: list[ActionProperty] = []
    ):
        """Processes the provided event as a pulse with every provided functor.

        This assumes that the provided event and value correspond to an input
        "press" event as the event data will then be modified to a release one
        in order to emit the pulse.

        Args:
            functors: List of functors to process the event with
            event: press event to use
            value: press value to use
            properties: additional property information to pass to child
                functors
        """
        self._process_event(functors, event_press, value_press, properties)
        time.sleep(0.05)
        value_release = Value(False)
        event_release = event_press.clone()
        event_release.is_pressed = False
        event_release.raw_value = None
        self._process_event(functors, event_release, value_release, properties)

    def _should_execute(self, value: Value) -> bool:
        """Checks if the action should execute based on the value and
        internal activation behavior.

        Args:
            value: the current input value to consider

        Returns:
            True if the action should execute, False otherwise
        """
        match self.data.activation_mode:
            case ActionActivationMode.Both:
                return True
            case ActionActivationMode.Deactivated:
                return False
            case ActionActivationMode.Press:
                return value.current
            case ActionActivationMode.Release:
                return not value.current
            case _:
                raise GremlinError(
                    f"Invalid activation mode encountered when executing " +
                    f"action '{self.data.id}'"
                )