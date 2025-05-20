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
from typing import List, Optional, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from dill import GUID_Keyboard

from gremlin import error, event_handler, plugin_manager, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, \
    Value
from gremlin.keyboard import key_from_code
from gremlin.profile import Library
from gremlin.tree import TreeNode
from gremlin.types import ActionProperty, ConditionType, InputType, \
    LogicalOperator, PropertyType, DataCreationMode

from gremlin.ui.action_model import ActionModel
import gremlin.ui.util

from . import comparator


if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel
    from gremlin.ui.action_model import SequenceIndex


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1


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
        return self._comparator(value, self._inputs)

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
        """Returns the name of the condition type.

        Returns:
            String representation of the condition's type
        """
        return ConditionType.to_string(self._condition_type)

    def set_condition_type(self, condition_type: ConditionType):
        """Sets the condition type to the provided one.

        This allows modifying the condition type from within code without
        UI based intervetion. The UI should cause input type changes by
        setting the inputs.

        Args:
            condition_type: type of condition to use
        """
        self._set_condition_type_impl(condition_type)

    def _set_condition_type_impl(self, condition_type: ConditionType) -> None:
        raise error.GremlinError(
            "AbstractCondition::_set_condition_type_impl implementation missing"
        )

    def _create_comparator(self, input_type: InputType):
        """Creates the comparator based on the current condition type.

        Args:
            input_type: type of input the comparator is meant for
        """
        comparator_map = {
            InputType.JoystickAxis: comparator.RangeComparator,
            InputType.JoystickButton: comparator.PressedComparator,
            InputType.JoystickHat: comparator.DirectionComparator,
            InputType.Keyboard: comparator.PressedComparator,
        }
        comparator_types = {
            InputType.JoystickAxis: "range",
            InputType.JoystickButton: "pressed",
            InputType.JoystickHat: "direction",
            InputType.Keyboard: "pressed",
        }
        if not isinstance(self._comparator, comparator_map[input_type]):
            self._comparator = comparator.create_default_comparator(
                comparator_types[input_type]
            )
            self.comparatorChanged.emit()

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


@QtQml.QmlElement
class KeyboardCondition(AbstractCondition):

    """Keyboard state based condition.

    The condition is for a single key and as such contains the key's scan
    code as well as the extended flag.
    """

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
            key_id = (
                util.read_property(item_node, "scan-code", PropertyType.Int),
                util.read_property(item_node, "is-extended", PropertyType.Bool)
            )
            event = event_handler.Event(
                InputType.Keyboard,
                key_id,
                GUID_Keyboard,
                "None"
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
            ["condition-type", "keyboard", PropertyType.String]
        ]
        node = util.create_node_from_data("condition", entries)

        for event in self._inputs:
            node.append(util.create_node_from_data(
                "input",
                [
                    ("scan-code", event.identifier[0], PropertyType.Int),
                    ("is-extended", event.identifier[1], PropertyType.Bool)
                ]
            ))
        node.append(self._comparator.to_xml())

        return node

    def _get_inputs_impl(self) -> List[str]:
        return [key_from_code(*v.identifier).name for v in self._inputs]

    def _set_inputs_impl(self, data: List[event_handler.Event]) -> None:
        self._update_inputs(data)

    def _set_condition_type_impl(self, condition_type: ConditionType) -> None:
        pass

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
        elif input_types[0] != InputType.Keyboard:
            raise error.GremlinError(
                f"Found non Keyboard input type" + \
                f"({InputType.to_string(input_types[0])}) " + \
                f"in a keyboard condition."
            )

        # Check if the comparator type has to change
        if len(input_types) == 0:
            self._comparator = None
        else:
            if not isinstance(self._comparator, comparator.PressedComparator):
                self._comparator = \
                    comparator.create_default_comparator("pressed")

        self._update_inputs(data)


@QtQml.QmlElement
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
                util.read_property(entry, "device-guid", PropertyType.UUID),
                "None"
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

        for event in self._inputs:
            node.append(util.create_node_from_data(
                "input",
                [
                    ("device-guid", event.device_guid, PropertyType.UUID),
                    ("input-type", event.event_type, PropertyType.InputType),
                    ("input-id", event.identifier, PropertyType.Int)
                ]
            ))
        node.append(self._comparator.to_xml())

        return node

    def _get_inputs_impl(self) -> List[event_handler.Event]:
        return [v.display_name() for v in self._inputs]

    def _set_inputs_impl(self, data: List[event_handler.Event]) -> None:
        self._update_inputs(data)

    def _set_condition_type_impl(self, condition_type: ConditionType) -> None:
        pass

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
            self._create_comparator(input_types[0])

        self._update_inputs(data)


@QtQml.QmlElement
class CurrentInputCondition(AbstractCondition):

    def __init__(self, parent: Optional[QtCore.QObject]=None):
        super().__init__(parent)

        self._condition_type = ConditionType.CurrentInput

    def from_xml(self, node: ElementTree) -> None:
        comp_node = node.find("comparator")
        if comp_node is None:
            raise error.ProfileError("Comparator node missing in condition.")
        self._comparator = comparator.create_comparator_from_xml(comp_node)

    def to_xml(self) -> ElementTree:
        entries = [
            ["condition-type", "current_input", PropertyType.String]
        ]
        node = util.create_node_from_data("condition", entries)
        node.append(self._comparator.to_xml())
        return node

    def _get_inputs_impl(self) -> List[str]:
        return ["Current Input"]

    def _set_inputs_impl(self, data: List[event_handler.Event]) -> None:
        self._update_inputs(data)

    def set_input_type(self, input_type: InputType):
        self._create_comparator(input_type)

    def _set_condition_type_impl(self, condition_type: ConditionType) -> None:
        if self._condition_type != condition_type:
            self._condition_type = condition_type
            self.conditionTypeChanged.emit()


class ConditionFunctor(AbstractFunctor):

    def __init__(self, action: ConditionModel):
        super().__init__(action)

    def __call__(
            self,
            event: Event,
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
        if self.data.logical_operator == LogicalOperator.All:
            return all(outcomes)
        elif self.data.logical_operator == LogicalOperator.Any:
            return any(outcomes)
        else:
            raise error.GremlinError(
                f"Invalid logical operator present {self.data._logical_operator}"
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
    ):
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
            ConditionType.Joystick: JoystickCondition,
            ConditionType.Keyboard: KeyboardCondition,
            ConditionType.CurrentInput: CurrentInputCondition,
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
        if index >= len(self._data.conditions):
            raise error.GremlinError("Attempting to remove a non-existent condition.")

        del self._data.conditions[index]
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

    @Property(list, notify=conditionsChanged)
    def conditions(self):
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

    properties = [
        ActionProperty.ActivateOnBoth
    ]
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    def __init__(self, behavior_type: InputType=InputType.JoystickButton):
        super().__init__(behavior_type)

        self.logical_operator = LogicalOperator.All
        self.true_actions = []
        self.false_actions = []
        self.conditions = []

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
            if condition_type == ConditionType.Joystick:
                cond_obj = JoystickCondition()
            elif condition_type == ConditionType.Keyboard:
                cond_obj = KeyboardCondition()
            elif condition_type == ConditionType.CurrentInput:
                cond_obj = CurrentInputCondition()
            if cond_obj is not None:
                cond_obj.from_xml(entry)
                self.conditions.append(cond_obj)

    def _to_xml(self) -> ElementTree:
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

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return ["true", "false"]

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        if selector == "true":
            return self.true_actions
        elif selector == "false":
            return self.false_actions

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass

create = ConditionData