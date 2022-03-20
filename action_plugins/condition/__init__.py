# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2022 Lionel Ott
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
from typing import List, Optional
from xml.etree import ElementTree

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from gremlin import error, event_handler, plugin_manager, \
    profile_library, util
from gremlin.base_classes import AbstractActionModel, AbstractFunctor, Value
from gremlin.input_devices import format_input
from gremlin.tree import TreeNode
from gremlin.types import ConditionType, InputType, LogicalOperator, \
    PropertyType
from gremlin.ui.profile import ActionNodeModel

from . import comparator


class AbstractCondition(QtCore.QObject):

    """Base class of all individual condition representations."""

    conditionTypeChanged = Signal()
    comparatorChanged = Signal()
    inputsChanged = Signal(list)

    def __init__(self, parent: Optional[QtCore.QObject]=None):
        """Creates a new instance."""
        super().__init__(parent)

        # Specific condition type needed for QT side of things
        self._condition_type = None
        # Comparator object implementing the condition
        self._comparator = None
        # Inputs used within the comparator
        self._inputs = []

    def __call__(self, value: Value) -> bool:
        """Evaluates the truth state of the condition.

        Args:
            value: value of the input event being evaluates

        Returns:
            True if the condition is fulfilled, False otherwise
        """
        return self._comparator(value)

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
        return self._condition_type is not None and \
            self._comparator is not None and \
            len(self._inputs) > 0

    @Property(str, notify=conditionTypeChanged)
    def conditionType(self) -> str:
        return ConditionType.to_string(self._condition_type)

    @Property(comparator.AbstractComparator, notify=comparatorChanged)
    def comparator(self) -> comparator.AbstractComparator:
        return self._comparator

    def _update_inputs(self, input_list: List[event_handler.Event]) -> None:
        if set(input_list) != set(self._inputs):
            self._inputs = input_list
            self.inputsChanged.emit(self._get_inputs())

    def _get_inputs(self) -> List[str]:
        return self._get_inputs_impl()

    def _get_inputs_impl(self) -> List[str]:
        raise error.GremlinError(
            "AbstractCondition::_get_inputs_impl implementation missing"
        )

    def _set_inputs(self, data: List) -> None:
        self._set_inputs_impl(data)

    def _set_inputs_impl(self, data: List) -> None:
        raise error.GremlinError(
            "AbstractCondition::_set_inputs_impl implementation missing"
        )

    inputs = Property(
        list,
        _get_inputs,
        _set_inputs,
        notify=inputsChanged
    )


class KeyboardCondition(AbstractCondition):

    """Keyboard state based condition.

    The condition is for a single key and as such contains the key's scan
    code as well as the extended flag.
    """

    class Input:

        def __init__(self) -> None:
            self.scan_code = 0
            self.is_extended = False

        def from_xml(self, node: ElementTree) -> None:
            self.scan_code = util.read_property(
                node, "scan-code", PropertyType.Int
            )
            self.is_extended = util.read_property(
                node, "is-extended", PropertyType.Bool
            )

        def to_xml(self) -> ElementTree:
            entries = [
                "scan-code", self.scan_code, PropertyType.Int,
                "is-extended", self.is_extended, PropertyType.Bool
            ]
            return util.create_node_from_data("input", entries)


    def __init__(self, parent=None):
        """Creates a new instance."""
        super().__init__(parent)

        self._condition_type = ConditionType.Keyboard

    def from_xml(self, node: ElementTree) -> None:
        """Populates the object with data from an XML node.

        Args:
            node: the XML node to parse for data
        """
        for item_node in node.findall("input"):
            i_node = KeyboardCondition.Input()
            i_node.from_xml(item_node)
            self._inputs.append(i_node)

        comp_node = node.find("comparator")
        if comp_node is None:
            raise error.ProfileError("Comparator node missing in condition.")
        self._comparator = comparator.create_comparator(comp_node)

    def to_xml(self) -> ElementTree:
        """Returns an XML node containing the objects data.

        Returns:
            XML node containing the object's data
        """
        entries = [
            ["condition-type", "keyboard", PropertyType.String]
        ]
        node = util.create_node_from_data("condition", entries)

        for entry in self._inputs:
            node.append(entry.to_xml())
        node.append(self._comparator.to_xml())

        return node


class JoystickCondition(AbstractCondition):

    """Joystick input state based condition.

    This condition is based on the state of a joystick axis, button, or hat.
    """

    def __init__(self, parent=None):
        """Creates a new instance."""
        super().__init__(parent)

        self._condition_type = ConditionType.Joystick

    def from_xml(self, node: ElementTree) -> None:
        """Populates the object with data from an XML node.

        Args:
            node: the XML node to parse for data
        """
        for entry in node.findall("input"):
            event = event_handler.Event(
                util.read_property(entry, "input-type", PropertyType.InputType),
                util.read_property(entry, "input-id", PropertyType.Int),
                util.parse_guid(str(
                    util.read_property(entry, "device-guid", PropertyType.GUID)
                ))
            )
            self._inputs.append(event)

        comp_node = node.find("comparator")
        if comp_node is None:
            raise error.ProfileError("Comparator node missing in condition.")
        self._comparator = comparator.create_comparator_from_xml(comp_node)

    def to_xml(self) -> ElementTree:
        """Returns an XML node containing the objects data.

        Returns:
            XML node containing the object's data
        """
        entries = [
            ["condition-type", "joystick", PropertyType.String]
        ]
        node = util.create_node_from_data("condition", entries)

        for entry in self._inputs:
            node.append(util.create_node_from_data(
                "input",
                [
                    ("device-guid", entry.device_guid, PropertyType.GUID),
                    ("input-type", entry.event_type, PropertyType.InputType),
                    ("input-id", entry.identifier, PropertyType.Int)
                ]
            ))
        node.append(self._comparator.to_xml())

        return node

    def _get_inputs_impl(self) -> List[str]:
        return [format_input(v) for v in self._inputs]

    def _set_inputs_impl(self, data: List[event_handler.Event]) -> None:
        self._update_inputs(data)

    @Slot(list)
    def updateInputs(self, data: List[event_handler.Event]) -> None:
        # Verify the comparator type is still adequate and modify / warn as
        # needed. First determine the correct type and then check if changes
        # are needed.
        input_types = [evt.event_type for evt in data]
        if len(set(input_types)) > 1:
            # Should never happen for a condition to make sense
            raise error.GremlinError(
                f"Multiple InputType types present in a single condition"
            )

        # Check if the comparator type has to change
        if len(input_types) == 0:
            self._comparator = None
        else:
            comparator_map = {
                InputType.JoystickAxis: comparator.RangeComparator,
                InputType.JoystickButton: comparator.PressedComparator,
                InputType.JoystickHat: comparator.DirectionComparator
            }
            comparator_types = {
                InputType.JoystickAxis: "range",
                InputType.JoystickButton: "button",
                InputType.JoystickHat: "direction"
            }
            if not isinstance(self._comparator, comparator_map[input_types[0]]):
                self._comparator = comparator.create_default_comparator(
                    comparator_types[input_types[0]]
                )

        self._update_inputs(data)


class ConditionFunctor(AbstractFunctor):

    def __init__(self, action: ConditionModel):
        super().__init__(action)

        self.true_actions = \
            [a.node.value.functor(a.node.value) for a in action.trueActionNodes]
        self.false_actions = \
            [a.node.value.functor(a.node.value) for a in action.falseActionNodes]

    def process_event(
        self,
        event: event_handler.Event,
        value: Value
    ) -> None:
        actions = self.true_actions if \
            self._condition_truth_state(value) else self.false_actions
        for action in actions:
            action.process_event(event, value)

    def _condition_truth_state(self, value: Value) -> bool:
        """Returns the truth value of the condition.

        Args:
            value: value of the event being evaluated

        Returns:
            True if the condition evaluates to True, False otherwise
        """
        outcomes = [cond(value) for cond in self.data.conditions]
        if self.data._logical_operator == LogicalOperator.All:
            return all(outcomes)
        elif self.data._logical_operator == LogicalOperator.Any:
            return any(outcomes)
        else:
            raise error.GremlinError(
                f"Invalid logical operator present {self.data._logical_operator}"
            )


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

        self._logical_operator = LogicalOperator.All
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

        if ConditionType(condition) == ConditionType.Joystick:
            cond = JoystickCondition(self)
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
            {"value": str(e.value), "text": LogicalOperator.to_display(e)}
            for e in LogicalOperator
        ]

    @Property(list, constant=True)
    def conditionOperators(self) -> List[str]:
        return [
            {"value": str(e.value), "text": ConditionType.to_display(e)}
            for e in ConditionType
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
            operator = LogicalOperator(int(value))
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

        self._logical_operator = LogicalOperator.to_enum(
            util.read_property(node, "logical-operator", PropertyType.String)
        )

        self._conditions = []
        for entry in node.iter("condition"):
            condition_type = ConditionType.to_enum(
                util.read_property(entry, "condition-type", PropertyType.String)
            )
            cond_obj = None
            if condition_type == ConditionType.Joystick:
                cond_obj = JoystickCondition()
            elif condition_type == ConditionType.Keyboard:
                cond_obj = KeyboardCondition()
            if cond_obj is not None:
                cond_obj.from_xml(entry)
                self._conditions.append(cond_obj)

    def to_xml(self) -> ElementTree:
        node = util.create_action_node(ConditionModel.tag, self._id)
        node.append(util.create_property_node(
            "logical-operator",
            LogicalOperator.to_string(self._logical_operator),
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
    JoystickCondition,
    "Gremlin.ActionPlugins",
    1,
    0,
    "JoystickCondition"
)
QtQml.qmlRegisterType(
    KeyboardCondition,
    "Gremlin.ActionPlugins",
    1,
    0,
    "KeyboardCondition"
)
QtQml.qmlRegisterType(
    JoystickCondition,
    "Gremlin.ActionPlugins",
    1,
    0,
    "JoystickCondition"
)