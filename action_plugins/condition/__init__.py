# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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

import enum
import logging
from typing import List, Optional
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from gremlin import actions, error, event_handler, plugin_manager, profile_library, util
from gremlin.base_classes import AbstractActionModel, AbstractFunctor
from gremlin.tree import TreeNode
from gremlin.types import InputType, PropertyType
from gremlin.ui.profile import ActionNodeModel



class AbstractCondition(QtCore.QObject):

    """Base class of all individual condition representations."""

    conditionTypeChanged = Signal()

    def __init__(self, parent: Optional[QtCore.QObject]=None):
        """Creates a new instance."""
        super().__init__(parent)

        self._condition_type = None

    def from_xml(self, node: ElementTree) -> None:
        """Populates the object with data from an XML node.

        Args:
            node: the XML node to parse for data
        """
        raise error.MissingImplementationError(
            "AbstractCondition.from_xml not implemented in subclass"
        )

    def to_xml(self) -> ElementTree:
        """Returns an XML node containing the objects data.

        Returns:
            XML node containing the object's data
        """
        raise error.MissingImplementationError(
            "AbstractCondition.to_xml not implemented in subclass"
        )

    def is_valid(self) -> bool:
        """Returns whether or not a condition is fully specified.

        Returns:
            True if the condition is properly specified, False otherwise
        """
        raise error.MissingImplementationError(
            "AbstractCondition.is_valid not implemented in subclass"
        )
    
    @Property(str, notify=conditionTypeChanged)
    def conditionType(self) -> str:
        return ConditionOperators.to_string(self._condition_type)


# class KeyboardCondition(AbstractCondition):

#     """Keyboard state based condition.

#     The condition is for a single key and as such contains the key's scan
#     code as well as the extended flag.
#     """

#     def __init__(self):
#         """Creates a new instance."""
#         super().__init__()
#         self.scan_code = None
#         self.is_extended = None

#     def from_xml(self, node: ElementTree) -> None:
#         """Populates the object with data from an XML node.

#         Args:
#             node: the XML node to parse for data
#         """
#         self.comparison = safe_read(node, "comparison")
#         self.scan_code = safe_read(node, "scan-code", int)
#         self.is_extended = parse_bool(safe_read(node, "extended"))

#     def to_xml(self) -> ElementTree:
#         """Returns an XML node containing the objects data.

#         Returns:
#             XML node containing the object's data
#         """
#         node = ElementTree.Element("condition")
#         node.set("condition-type", "keyboard")
#         node.set("input", "keyboard")
#         node.set("comparison", str(self.comparison))
#         node.set("scan-code", str(self.scan_code))
#         node.set("extended", str(self.is_extended))
#         return node

#     def is_valid(self) -> bool:
#         """Returns whether or not a condition is fully specified.

#         Returns:
#             True if the condition is properly specified, False otherwise
#         """
#         return super().is_valid() and \
#             self.scan_code is not None and \
#             self.is_extended is not None


# class JoystickCondition(AbstractCondition):

#     """Joystick state based condition.

#     This condition is based on the state of a joystick axis, button, or hat.
#     """

#     def __init__(self):
#         """Creates a new instance."""
#         super().__init__()
#         self.device_guid = 0
#         self.input_type = None
#         self.input_id = 0
#         self.range = [0.0, 0.0]
#         self.device_name = ""

#     def from_xml(self, node: ElementTree) -> None:
#         """Populates the object with data from an XML node.

#         Args:
#             node: the XML node to parse for data
#         """
#         self.comparison = safe_read(node, "comparison")

#         self.input_type = InputType.to_enum(safe_read(node, "input"))
#         self.input_id = safe_read(node, "id", int)
#         self.device_guid = parse_guid(node.get("device-guid"))
#         self.device_name = safe_read(node, "device-name")
#         if self.input_type == InputType.JoystickAxis:
#             self.range = [
#                 safe_read(node, "range-low", float),
#                 safe_read(node, "range-high", float)
#             ]

#     def to_xml(self) -> ElementTree:
#         """Returns an XML node containing the objects data.

#         Returns:
#             XML node containing the object's data
#         """
#         node = ElementTree.Element("condition")
#         node.set("comparison", str(self.comparison))
#         node.set("condition-type", "joystick")
#         node.set("input", InputType.to_string(self.input_type))
#         node.set("id", str(self.input_id))
#         node.set("device-guid", str(self.device_guid))
#         node.set("device-name", str(self.device_name))
#         if self.input_type == InputType.JoystickAxis:
#             node.set("range-low", str(self.range[0]))
#             node.set("range-high", str(self.range[1]))
#         return node

#     def is_valid(self) -> bool:
#         """Returns whether or not a condition is fully specified.

#         Returns:
#             True if the condition is properly specified, False otherwise
#         """
#         return super().is_valid() and self.input_type is not None


# class VJoyCondition(AbstractCondition):

#     """vJoy device state based condition.

#     This condition is based on the state of a vjoy axis, button, or hat.
#     """

#     def __init__(self):
#         """Creates a new instance."""
#         super().__init__()
#         self.vjoy_id = 0
#         self.input_type = None
#         self.input_id = 0
#         self.range = [0.0, 0.0]

#     def from_xml(self, node: ElementTree) -> None:
#         """Populates the object with data from an XML node.

#         Args
#             node: XML node to parse for data
#         """
#         self.comparison = safe_read(node, "comparison")

#         self.input_type = InputType.to_enum(safe_read(node, "input"))
#         self.input_id = safe_read(node, "id", int)
#         self.vjoy_id = safe_read(node, "vjoy-id", int)
#         if self.input_type == InputType.JoystickAxis:
#             self.range = [
#                 safe_read(node, "range-low", float),
#                 safe_read(node, "range-high", float)
#             ]

#     def to_xml(self) -> ElementTree:
#         """Returns an XML node containing the objects data.

#         Returns:
#             XML node containing the object's data
#         """
#         node = ElementTree.Element("condition")
#         node.set("comparison", str(self.comparison))
#         node.set("condition-type", "vjoy")
#         node.set("input", InputType.to_string(self.input_type))
#         node.set("id", str(self.input_id))
#         node.set("vjoy-id", str(self.vjoy_id))
#         if self.input_type == InputType.JoystickAxis:
#             node.set("range-low", str(self.range[0]))
#             node.set("range-high", str(self.range[1]))
#         return node

#     def is_valid(self) -> bool:
#         """Returns whether or not a condition is fully specified.

#         Returns:
#             True if the condition is properly specified, False otherwise
#         """
#         return super().is_valid() and self.input_type is not None


class InputStateCondition(AbstractCondition):

    """Input item press / release state based condition.

    The condition is for the current input item, triggering based on whether
    or not the input item is being pressed or released.
    """

    def __init__(self, parent=None):
        """Creates a new instance."""
        super().__init__(parent)

        self._condition_type = ConditionOperators.InputState
        self._comparator = None
        self.input_type = None

    def from_xml(self, node: ElementTree) -> None:
        """Populates the object with data from an XML node.

        Args:
            node: the XML node to parse for data
        """
        self.input_type = util.read_property(
            node, "input-type", PropertyType.InputType
        )
        if self.input_type in [InputType.JoystickButton, InputType.Keyboard]:
            self._comparator = InputStateCondition.ButtonComparator(
                util.read_property(node, "is-pressed", PropertyType.Bool)
            )
        elif self.input_type == InputType.JoystickAxis:
            self._comparator = InputStateCondition.AxisComparator(
                util.read_property(node, "low", PropertyType.Float),
                util.read_property(node, "high", PropertyType.Float)
            )
        elif self.input_type == InputType.JoystickHat:
            self._comparator = InputStateCondition.HatComparator(
                util.read_property(node, "direction", PropertyType.String)
            )
        else:
            raise error.ProfileError(
                f"Invalid condition type specified {self.input_type}"
            )

    def to_xml(self) -> ElementTree:
        """Returns an XML node containing the objects data.

        Returns:
            XML node containing the object's data
        """
        node = ElementTree.Element("condition")
        node.append(util.create_property_node(
            "condition-type",
            "input-state",
            PropertyType.String
        ))
        node.append(util.create_property_node(
            "input-type",
            self.input_type,
            PropertyType.InputType
        ))
        if self.input_type in [InputType.JoystickButton, InputType.Keyboard]:
            node.append(util.create_property_node(
                "is-pressed",
                self._comparator.is_pressed,
                PropertyType.Bool
            ))
        elif self.input_type == InputType.JoystickAxis:
            node.append(util.create_property_node(
                "low",
                self._comparator.low,
                PropertyType.Float
            ))
            node.append(util.create_property_node(
                "high",
                self._comparator.high,
                PropertyType.Float
            ))
        elif self.input_type == InputType.JoystickHat:
            node.append(util.create_property_node(
                "direction",
                self._comparator.direction,
                PropertyType.String
            ))
        else:
            raise error.ProfileError(
                f"Invalid condition type encountered {self.input_type}"
            )
        return node
    
    def is_valid(self) -> bool:
        return self._comparator != None

    @Property(str, constant=True)
    def inputType(self) -> str:
        return InputType.to_string(self.input_type)

    @Property(Comparator, notify=comparatorChanged)
    def comparator(self) -> Comparator:
        return self._comparator


class ConditionModel(AbstractActionModel):

    version = 1
    name = "Condition"
    tag = "condition"

    functor = ConditionFunctor
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    logicalOperatorChanged = Signal()
    conditionsChanged = Signal()
    actionsChanged = Signal()

    def __init__(
            self,
            action_tree: profile_library.ActionTree,
            input_type: InputType = InputType.JoystickButton,
            parent: Optional[QtCore.QObject] = None
    ):
        super().__init__(action_tree, input_type, parent)

        self._logical_operator = LogicalOperators.All
        self._true_action_ids = []
        self._false_action_ids = []
        self._conditions = []

    @Slot(int)
    def addCondition(self, condition: int) -> None:
        """Adds a new condition.

        Args:
            condition: Numerical value of the condition enum
        """
        #node = self._action_tree.root.nodes_matching(lambda x: x.value.id == self.id)

        if ConditionOperators(condition) == ConditionOperators.InputState:
            cond = InputStateCondition(self)
            cond.input_type = self.behavior_type
            cond._comparator = InputStateCondition.ButtonComparator(True)
            self._conditions.append(cond)

        self.conditionsChanged.emit()

    @Slot(str, str)
    def addAction(self, action_name: str, branch: str) -> None:
        """Adds a new action to one of the two condition branches.

        Args:
            action_name: name of the action to add
            branch: which of the two branches to add the action two, valid
                options are [if, else]
        """
        action = plugin_manager.ActionPlugins().get_class(action_name)(
            self._action_tree,
            self.behavior_type
        )

        predicate = lambda x: True if x.value and x.value.id == self.id else False
        nodes = self._action_tree.root.nodes_matching(predicate)
        if len(nodes) != 1:
            raise error.GremlinError(f"Node with ID {self.id} has invalid state")
        nodes[0].add_child(TreeNode(action))
        if branch == "if":
            self._true_action_ids.append(action.id)
        elif branch == "else":
            self._false_action_ids.append(action.id)
        else:
            raise error.GremlinError(f"Invalid branch specification: {branch}")

        self.actionsChanged.emit()

    @Slot(int)
    def removeCondition(self, index: int) -> None:
        if index >= len(self._conditions):
            raise error.GremlinError("Attempting to remove a non-existent condition.")

        del self._conditions[index]
        self.conditionsChanged.emit()

    @Property(list, constant=True)
    def logicalOperators(self) -> List[str]:
        return [
            {"value": str(e.value), "text": LogicalOperators.to_display(e)}
            for e in LogicalOperators
        ]

    @Property(list, constant=True)
    def conditionOperators(self) -> List[str]:
        return [
            {"value": str(e.value), "text": ConditionOperators.to_display(e)}
            for e in ConditionOperators
        ]

    @Property(list, notify=actionsChanged)
    def trueActionNodes(self) -> List[ActionNodeModel]:
        return self._create_node_list(self._true_action_ids)

    @Property(list, notify=actionsChanged)
    def falseActionNodes(self) -> List[ActionNodeModel]:
        return self._create_node_list(self._false_action_ids)

    @Property(list, notify=conditionsChanged)
    def conditions(self):
        return self._conditions

    def _get_logical_operator(self) -> str:
        return str(self._logical_operator.value)

    def _set_logical_operator(self, value: str) -> None:
        try:
            operator = LogicalOperators(int(value))
            if operator == self._logical_operator:
                return
            self._logical_operator = operator
            self.logicalOperatorChanged.emit()
        except ValueError as e:
            logging.getLogger("system").error(
                f"Invalid logical operator value obtained: \"{e}\"."
            )

    def from_xml(self, node: ElementTree.Element ) -> None:
        self._id = util.read_action_id(node)
        # Parse IF action ids
        self._true_action_ids = util.read_action_ids(node.find("if-actions"))
        # Parse ELSE action ids
        self._false_action_ids = util.read_action_ids(node.find("else-actions"))

        self._logical_operator = LogicalOperators.to_enum(
            util.read_property(node, "logical-operator", PropertyType.String)
        )
        
        self._conditions = []
        for entry in node.iter("condition"):
            condition_type = ConditionOperators.to_enum(
                util.read_property(entry, "condition-type", PropertyType.String)
            )
            if condition_type == ConditionOperators.InputState:
                condition = InputStateCondition()
                condition.from_xml(entry)
                self._conditions.append(condition)

    def to_xml(self) -> ElementTree:
        node = util.create_action_node(ConditionModel.tag, self._id)
        node.append(util.create_property_node(
            "logical-operator",
            LogicalOperators.to_string(self._logical_operator),
            PropertyType.String
        ))
        for condition in self._conditions:
            node.append(condition.to_xml())
        node.append(util.create_action_ids(
            "if-actions", self._true_action_ids
        ))
        node.append(util.create_action_ids(
            "else-actions", self._false_action_ids
        ))

        return node

    def is_valid(self) -> bool:
        return True

    def remove_action(self, action: AbstractActionModel) -> None:
        """Removes the provided action from this action.

        Args:
            action: the action to remove
        """
        self._remove_from_list(self._true_action_ids, action.id)
        self._remove_from_list(self._false_action_ids, action.id)

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
        self._insert_into_list(self._true_action_ids, anchor.id, action.id, True)
        self._insert_into_list(self._false_action_ids, anchor.id, action.id, True)

    def insert_action(self, container: str, action: AbstractActionModel) -> None:
        if container == "true":
            self._true_action_ids.insert(0, action.id)
        elif container == "false":
            self._false_action_ids.insert(0, action.id)
        else:
            raise error.GremlinError(
                f"Invalid container for a Condition action: '{container}`"
            )

    def qml_path(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:condition/ConditionAction.qml"
        ).fileName()

    logicalOperator = Property(
        str,
        fget=_get_logical_operator,
        fset=_set_logical_operator,
        notify=logicalOperatorChanged
    )


create = ConditionModel

QtQml.qmlRegisterType(
    InputStateCondition,
    "gremlin.action_plugins",
    1,
    0,
    "InputStateCondition"
)