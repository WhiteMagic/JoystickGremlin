# -*- coding: utf-8; -*-

# Copyright (C) 2020 Lionel Ott
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
from typing import List, override, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import error, event_handler, plugin_manager, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.profile import Library
from gremlin.tree import TreeNode
from gremlin.types import ActionProperty, ConditionType, InputType, \
    LogicalOperator, PropertyType

from gremlin.ui.action_model import ActionModel

from . import condition as ca

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta
    from gremlin.ui.profile import InputItemBindingModel
    from gremlin.ui.action_model import SequenceIndex


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1


class ConditionFunctor(AbstractFunctor):

    def __init__(self, action: ConditionModel) -> None:
        super().__init__(action)

    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        if not self._should_execute(value):
            return

        actions = self.functors["true"] if \
            self._condition_truth_state(value) else self.functors["false"]
        for action in actions:
            action(event, value, properties)

    def _condition_truth_state(self, value: Value) -> bool:
        """Returns the truth value of the condition.

        Args:
            value: value of the event being evaluated

        Returns:
            True if the condition evaluates to True, False otherwise
        """
        outcomes = [cond(value) for cond in self.data.conditions]
        match self.data.logical_operator:
            case LogicalOperator.All:
                return all(outcomes)
            case LogicalOperator.Any:
                return any(outcomes)
            case _:
                raise error.GremlinError(
                    "ConditionAction: Invalid logical operator present " +
                    f"{self.data.logical_operator}"
                )


class ConditionModel(ActionModel):

    logicalOperatorChanged = Signal()
    conditionsChanged = Signal()
    actionsChanged = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:condition/ConditionAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @Slot(int)
    def addCondition(self, condition: int) -> None:
        """Adds a new condition.

        Args:
            condition: Numerical value of the condition enum
        """
        condition_lookup = {
            ConditionType.CurrentInput: ca.CurrentInputCondition,
            ConditionType.Joystick: ca.JoystickCondition,
            ConditionType.Keyboard: ca.KeyboardCondition,
            ConditionType.LogicalDevice: ca.LogicalDeviceCondition,
            ConditionType.VJoy: ca.VJoyCondition,
        }

        condition_type = ConditionType(condition)
        if condition_type in condition_lookup:
            cond = condition_lookup[condition_type](self)
            # If the condition is a CurrentInput one set the input type
            if condition_type == ConditionType.CurrentInput:
                cond.set_input_type(self._data.behavior_type)
            self._data.conditions.append(cond)
        self.conditionsChanged.emit()

    @Slot(str, str)
    def addAction(self, action_name: str, branch: str) -> None:
        """Adds a new action to one of the two condition branches.

        Args:
            action_name: name of the action to add
            branch: which of the two branches to add the action two, valid
                options are [if, else]
        """
        action = plugin_manager.PluginManager().get_class(action_name)(
            self._action_tree
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
        if index >= len(self._data.conditions):
            raise error.GremlinError("Attempting to remove a non-existent condition.")

        del self._data.conditions[index]
        self.conditionsChanged.emit()

    @Property(list, constant=True)
    def logicalOperators(self) -> List[dict[str, str]]:
        return [
            {"value": str(e.value), "text": LogicalOperator.to_display(e)}
            for e in LogicalOperator
        ]

    @Property(list, constant=True)
    def conditionOperators(self) -> List[dict[str, str]]:
        return [
            {"value": str(e.value), "text": ConditionType.to_display(e)}
            for e in ConditionType
        ]

    @Property(list, notify=conditionsChanged)
    def conditions(self) -> list[ca.AbstractCondition]:
        return self._data.conditions

    def _get_logical_operator(self) -> str:
        return str(self._data.logical_operator.value)

    def _set_logical_operator(self, value: str) -> None:
        try:
            operator = LogicalOperator(int(value))
            if operator == self._data.logical_operator:
                return
            self._data.logical_operator = operator
            self.logicalOperatorChanged.emit()
        except ValueError as e:
            logging.getLogger("system").error(
                f"Condition: Invalid logical operator value obtained: \"{e}\"."
            )

    logicalOperator = Property(
        str,
        fget=_get_logical_operator,
        fset=_set_logical_operator,
        notify=logicalOperatorChanged
    )


class ConditionData(AbstractActionData):

    version = 1
    name = "Condition"
    tag = "condition"
    icon = "\uF109"

    functor = ConditionFunctor
    model = ConditionModel

    properties = (
        ActionProperty.ActivateOnBoth,
    )
    input_types = (
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    )

    def __init__(
        self,
        behavior_type: InputType=InputType.JoystickButton
    ) -> None:
        super().__init__(behavior_type)

        self.logical_operator = LogicalOperator.All
        self.true_actions = []
        self.false_actions = []
        self.conditions = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        # Parse IF action ids
        true_ids = util.read_action_ids(node.find("true-actions"))
        self.true_actions = [library.get_action(aid) for aid in true_ids]
        # Parse ELSE action ids
        false_ids = util.read_action_ids(node.find("false-actions"))
        self.false_actions = [library.get_action(aid) for aid in false_ids]

        self.logical_operator = LogicalOperator.to_enum(
            util.read_property(node, "logical-operator", PropertyType.String)
        )

        self.conditions = []
        for entry in node.iter("condition"):
            condition_type = ConditionType.to_enum(
                util.read_property(entry, "condition-type", PropertyType.String)
            )
            cond_obj = None
            match condition_type:
                case ConditionType.CurrentInput:
                    cond_obj = ca.CurrentInputCondition()
                case ConditionType.Joystick:
                    cond_obj = ca.JoystickCondition()
                case ConditionType.Keyboard:
                    cond_obj = ca.KeyboardCondition()
                case ConditionType.LogicalDevice:
                    cond_obj = ca.LogicalDeviceCondition()
                case ConditionType.VJoy:
                    cond_obj = ca.VJoyCondition()
                case _:
                    logging.getLogger("system").error(
                        "ConditionAction: Unknown condition type "
                        f"{condition_type} encountered during XML parsing."
                    )
            if cond_obj is not None:
                cond_obj.from_xml(entry)
                self.conditions.append(cond_obj)

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(ConditionData.tag, self._id)
        node.append(util.create_property_node(
            "logical-operator",
            LogicalOperator.to_string(self.logical_operator),
            PropertyType.String
        ))
        for condition in self.conditions:
            node.append(condition.to_xml())
        node.append(util.create_action_ids(
            "true-actions", [action.id for action in self.true_actions]
        ))
        node.append(util.create_action_ids(
            "false-actions", [action.id for action in self.false_actions]
        ))

        return node

    @override
    def is_valid(self) -> bool:
        return True

    @override
    def _valid_selectors(self) -> List[str]:
        return ["true", "false"]

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        match selector:
            case "true":
                return self.true_actions
            case "false":
                return self.false_actions
            case _:
                raise error.GremlinError(
                    f"{self.name}: has no container with name {selector}"
                )

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        if old_behavior != new_behavior:
            for condition in self.conditions:
                condition.set_input_type(new_behavior)

    @override
    def swap_uuid(self, old_uuid: uuid.UUID, new_uuid: uuid.UUID) -> bool:
        performed_swap = False
        for condition in self.conditions:
            if condition.swap_uuid(old_uuid, new_uuid):
                performed_swap = True
        return performed_swap


create = ConditionData
