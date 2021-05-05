# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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

from abc import abstractmethod, ABCMeta
from gremlin import actions

import logging
from typing import Any, List, Optional
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore

from . import actions, error
from .event_handler import Event
from .profile_library import ActionTree
from .types import InputType
from gremlin.ui.profile import ActionNodeModel


class AbstractActionModel(QtCore.QObject):

    """Base class for all action related data calsses."""

    modelChanged = QtCore.Signal()

    def __init__(
            self,
            action_tree: ActionTree,
            input_type: InputType=InputType.JoystickButton,
            parent: Optional[QtCore.QObject]=None
    ):
        super().__init__(parent)

        self._id = uuid.uuid4()
        self._action_tree = action_tree
        self._input_type = input_type

    @property
    def id(self) -> uuid.UUID:
        """Returns the identifier of this action.

        Returns:
            Unique identifier of this action
        """
        return self._id

    def qml_path(self) -> str:
        """Returns the path to the QML file visualizing the action.

        Returns:
            String representation of the QML file path
        """
        raise error.MissingImplementationError(
            "AbstractActionModel.qml_path not implemented in subclass"
        )

    def from_xml(self, node: ElementTree.Element) -> None:
        """Populates the instance's values with the content of the XML node.

        Args:
            node: the XML node to parse for content
        """
        raise error.MissingImplementationError(
            "AbstractActionModel.from_xml not implemented in subclass"
        )

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing the instance's contents.

        Returns:
            XML node containing the instance's contents
        """
        raise error.MissingImplementationError(
            "AbstractActionModel.to_xml not implemented in subclass"
        )

    def is_valid(self) -> bool:
        """Returns whether or not the instance is in a valid state.

        Returns:
            True if the instance is in a valid state, False otherwise
        """
        raise error.MissingImplementationError(
            "AbstractActionModel.is_valid not implemented in subclass"
        )

    def remove_action(self, action: AbstractActionModel) -> None:
        """Removes the provided action from this action.

        Args:
            action: the action to remove
        """
        pass

    def add_action_after(
        self,
        anchor: AbstractActionModel,
        action: AbstractActionModel
    ) -> None:
        """Adds the provided action after the specified anchor.

        Args:
            anchor: action after which to insert the given action
            action: the action to remove
        """
        pass

    def insert_action(self, container: str, action: AbstractActionModel) -> None:
        """Inserts the action into a specific container.

        Args:
            container: label of the container into which to insert the
                provided action
            action: the action to insert
        """
        raise error.MissingImplementationError(
            "AbstractActionModel.insert_action not implemented in subclass"
        )

    def _create_node_list(self, action_ids):
        nodes = []
        for node in self._action_tree.root.nodes_matching(lambda x: x.value.id in action_ids):
            node.value.setParent(self)
            nodes.append(ActionNodeModel(node, self._input_type, self._action_tree, parent=self))
        return nodes

    def _remove_from_list(self, storage: List[Any], value: Any) -> None:
        """Removes the provided value from the list storage.

        Args:
            storage: list object from which to remove the value
            value: value to remove
        """
        if value in storage:
            storage.remove(value)

    def _insert_into_list(
        self,
        storage: List[Any],
        anchor: Any,
        value: Any,
        append: bool=True
    ) -> None:
        """Inserts the given value into the storage.

        Args:
            storage: list object into which to insert the value
            anchor: value around which to insert the new value
            value: new value to insert into the list
            append: append if True, prepend if False
        """
        if anchor in storage:
            index = storage.index(anchor)
            index = index + 1 if append else index
            storage.insert(index, value)


# class ActivationCondition:

#     """Dictates under what circumstances an associated code can be executed."""

#     rule_lookup = {
#         # String to enum
#         "all": ActivationRule.All,
#         "any": ActivationRule.Any,
#         # Enum to string
#         ActivationRule.All: "all",
#         ActivationRule.Any: "any",
#     }

#     condition_lookup = {
#         "keyboard": KeyboardCondition,
#         "joystick": JoystickCondition,
#         "vjoy": VJoyCondition,
#         "action": InputActionCondition,
#     }

#     def __init__(self, conditions, rule):
#         """Creates a new instance."""
#         self.rule = rule
#         self.conditions = conditions

#     def from_xml(self, node):
#         """Extracts activation condition data from an XML node.

#         :param node the XML node to parse
#         """
#         self.rule = ActivationCondition.rule_lookup[safe_read(node, "rule")]
#         for cond_node in node.findall("condition"):
#             condition_type = safe_read(cond_node, "condition-type")
#             condition = ActivationCondition.condition_lookup[condition_type]()
#             condition.from_xml(cond_node)
#             self.conditions.append(condition)

#     def to_xml(self):
#         """Returns an XML node containing the activation condition information.

#         :return XML node containing information about the activation condition
#         """
#         node = ElementTree.Element("activation-condition")
#         node.set("rule", ActivationCondition.rule_lookup[self.rule])

#         for condition in self.conditions:
#             if condition.is_valid():
#                 node.append(condition.to_xml())
#         return node


class AbstractFunctor(metaclass=ABCMeta):

    """Abstract base class defining the interface for functor like classes.

    TODO: Rework this thing

    These classes are used in the internal code execution system.
    """

    def __init__(self, instance):
        """Creates a new instance, extracting needed information.

        :param instance the object which contains the information needed to
            execute it later on
        """
        self.data = instance

    @abstractmethod
    def process_event(self, event: Event, value: actions.Value) -> None:
        """Processes the functor using the provided event and value data.

        :param event the raw event that caused the functor to be executed
        :param value the possibly modified value
        """
        pass


# class AbstractAction(profile_library.ActionData):
#
#     """Base class for all actions that can be encoded via the XML and
#     UI system."""
#
#     def __init__(self, parent):
#         """Creates a new instance.
#
#         :parent the container which is the parent to this action
#         """
#         assert isinstance(parent, AbstractContainer)
#         super().__init__(parent)
#
#         self.activation_condition = None
#
#     def from_xml(self, node):
#         """Populates the instance with data from the given XML node.
#
#         :param node the XML node to populate fields with
#         """
#         super().from_xml(node)
#
#         for child in node.findall("activation-condition"):
#             self.parent.activation_condition_type = "action"
#             self.activation_condition = \
#                 ActivationCondition([], ActivationRule.All)
#             cond_node = node.find("activation-condition")
#             if cond_node is not None:
#                 self.activation_condition.from_xml(cond_node)
#
#     def to_xml(self):
#         """Returns a XML node representing the instance's contents.
#
#         :return XML node representing the state of this instance
#         """
#         node = super().to_xml()
#         if self.activation_condition:
#             node.append(self.activation_condition.to_xml())
#         return node
#
#     def icon(self):
#         """Returns the icon to use when representing the action.
#
#         :return icon to use
#         """
#         raise error.MissingImplementationError(
#             "AbstractAction.icon not implemented in subclass"
#         )
#
#     def requires_virtual_button(self):
#         """Returns whether or not the action requires the use of a
#         virtual button.
#
#         :return True if a virtual button has to be used, False otherwise
#         """
#         raise error.MissingImplementationError(
#             "AbstractAction.requires_virtual_button not implemented"
#         )
#
#
# class AbstractContainer(profile_library.ActionData):
#
#     """Base class for action container related information storage."""
#
#     def __init__(self, parent):
#         """Creates a new instance.
#
#         Parameters
#         ==========
#         parent : gremlin.profile.Library
#             Library instance this container belongs to
#         """
#         super().__init__(parent)
#         self.action_sets = []
#         self.activation_condition_type = None
#         self.activation_condition = None
#
#     def add_action(self, action, index=-1):
#         """Adds an action to this container.
#
#         :param action the action to add
#         :param index the index of the action_set into which to insert the
#             action. A value of -1 indicates that a new set should be
#             created.
#         """
#         assert isinstance(action, AbstractAction)
#         if index == -1:
#             self.action_sets.append([])
#             index = len(self.action_sets) - 1
#         self.action_sets[index].append(action)
#
#         # Create activation condition data if needed
#         # self.create_or_delete_virtual_button()
#
#     # TODO: This should go somewhere in the code runner parts
#     # def generate_callbacks(self):
#     #     """Returns a list of callback data entries.
#     #
#     #     :return list of container callback entries
#     #     """
#     #     callbacks = []
#     #
#     #     # For a virtual button create a callback that sends VirtualButton
#     #     # events and another callback that triggers of these events
#     #     # like a button would.
#     #     if self.virtual_button is not None:
#     #         callbacks.append(execution_graph.CallbackData(
#     #             execution_graph.VirtualButtonProcess(self.virtual_button),
#     #             None
#     #         ))
#     #         callbacks.append(execution_graph.CallbackData(
#     #             execution_graph.VirtualButtonCallback(self),
#     #             gremlin.event_handler.Event(
#     #                 gremlin.common.InputType.VirtualButton,
#     #                 callbacks[-1].callback.virtual_button.identifier,
#     #                 device_guid=dill.GUID_Virtual,
#     #                 is_pressed=True,
#     #                 raw_value=True
#     #             )
#     #         ))
#     #     else:
#     #         callbacks.append(execution_graph.CallbackData(
#     #             execution_graph.ContainerCallback(self),
#     #             None
#     #         ))
#     #
#     #     return callbacks
#
#     def from_xml(self, node):
#         """Populates the instance with data from the given XML node.
#
#         :param node the XML node to populate fields with
#         """
#         super().from_xml(node)
#         self._parse_action_set_xml(node)
#         # self._parse_virtual_button_xml(node)
#         self._parse_activation_condition_xml(node)
#
#     def to_xml(self):
#         """Returns a XML node representing the instance's contents.
#
#         :return XML node representing the state of this instance
#         """
#         node = super().to_xml()
#         if self.activation_condition:
#             condition_node = self.activation_condition.to_xml()
#             if condition_node:
#                 node.append(condition_node)
#         return node
#
#     def _parse_action_set_xml(self, node):
#         """Parses the XML content related to actions.
#
#         :param node the XML node to process
#         """
#         self.action_sets = []
#         for child in node:
#             if child.tag == "action-set":
#                 action_set = []
#                 self._parse_action_xml(child, action_set)
#                 self.action_sets.append(action_set)
#             else:
#                 logging.getLogger("system").warning(
#                     "Unknown node present: {}".format(child.tag)
#                 )
#
#     def _parse_action_xml(self, node, action_set):
#         """Parses the XML content related to actions in an action-set.
#
#         :param node the XML node to process
#         :param action_set storage for the processed action nodes
#         """
#         action_name_map = plugin_manager.ActionPlugins().tag_map
#         for child in node:
#             if child.tag not in action_name_map:
#                 logging.getLogger("system").warning(
#                     "Unknown node present: {}".format(child.tag)
#                 )
#                 continue
#
#             entry = action_name_map[child.tag](self)
#             entry.from_xml(child)
#             action_set.append(entry)
#
#     def _parse_activation_condition_xml(self, node):
#         for child in node.findall("activation-condition"):
#             self.activation_condition_type = "container"
#             self.activation_condition = \
#                 ActivationCondition([], ActivationRule.All)
#             cond_node = node.find("activation-condition")
#             if cond_node is not None:
#                 self.activation_condition.from_xml(cond_node)
#
#     def _is_valid(self):
#         """Returns whether or not this container is configured properly.
#
#         :return True if configured properly, False otherwise
#         """
#         # Check state of the container
#         state = self._is_container_valid()
#
#         # Check state of all linked actions
#         for actions in [a for a in self.action_sets if a is not None]:
#             for action in actions:
#                 state = state & action.is_valid()
#         return state
#
#         # # Check that no action set is empty
#         # for actions in [a for a in self.action_sets if a is not None]:
#         #     if len(actions) == 0:
#         #         state = False
#
#         # # Check state of all linked actions
#         # for actions in [a for a in self.action_sets if a is not None]:
#         #     for action in actions:
#         #         if action is None:
#         #             state = False
#         #         else:
#         #             state = state & action.is_valid()
#         # return state
#
#     @abstractmethod
#     def _is_container_valid(self):
#         """Returns whether or not the container itself is valid.
#
#         :return True container data is valid, False otherwise
#         """
#         pass
