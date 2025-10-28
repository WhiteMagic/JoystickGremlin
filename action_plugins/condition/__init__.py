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

from abc import abstractmethod, ABCMeta
import logging
from typing import Any, List, Optional, TYPE_CHECKING
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from vjoy.vjoy import VJoyProxy

from gremlin import error, event_handler, plugin_manager, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.input_cache import DeviceDatabase, Keyboard, Joystick
from gremlin.keyboard import key_from_code
from gremlin.logical_device import LogicalDevice
from gremlin.profile import Library
from gremlin.tree import TreeNode
from gremlin.types import ActionProperty, ConditionType, HatDirection, \
    InputType, LogicalOperator, PropertyType

from gremlin.ui.action_model import ActionModel
from gremlin.ui.device import InputIdentifier

from . import comparator


if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta
    from gremlin.ui.profile import InputItemBindingModel
    from gremlin.ui.action_model import SequenceIndex


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1


"""Overall design of the condition action.

A condition is comprised of two components:
- condition variable
- comparator

The condition variable represents the variable which is evaluated to true or
false by the comparator. The variable also defines which comparator is being
used.

A condition variable can capture various states of the Gremlin system, including
joystick state, keyboard state, vJoy state, logical device state, and in the
future possible even time, game state, or an internal state tracker system.

Comparators deal currently with three different styles of values: boolean,
range, and direction. In the future this could possibly be extended to
enumerations or text.

The condition variable(s) represent different information depending on the
type of the Condition they capture. They need to capture the information


Condition -> Input -> Value -> Comparator -> bool

"""

class AbstractState(metaclass=ABCMeta):

    """Represents a state against which a comparator can be evaluated.

    Stores the information erquired to evaluate the state's value as well
    as obtaining a human readable representation of the state.
    """

    @abstractmethod
    def get(self) -> Any:
        """Returns the current value of the state.

        Returns:
            Current value of the state.
        """
        pass

    @abstractmethod
    def display_name(self) -> str:
        """Returns a human readable representation of the state.

        Returns:
            Human readable representation of the state.
        """
        pass


class AbstractCondition(QtCore.QObject):

    """Base class of all individual condition representations."""

    conditionTypeChanged = Signal()
    comparatorChanged = Signal()
    statesChanged = Signal(list)

    def __init__(self, parent: ta.OQO=None) -> None:
        """Creates a new AbstractCondition instance."""
        super().__init__(parent)

        # Specific condition type needed for QT side of things. Every
        # subclass constructor sets this to the correct value.
        self._condition_type : ConditionType = ConditionType.CurrentInput
        # Comparator object implementing the condition.
        self._comparator : Optional[comparator.AbstractComparator] = None
        # States whose values will be compared within the comparator.
        self._states : List[AbstractState] = []

    def __call__(self, value: Value) -> bool:
        """Evaluates the truth state of the condition.

        Args:
            value: Value of the input event being evaluated.

        Returns:
            True if the condition is fulfilled, False otherwise.
        """
        if self._comparator is not None:
            return self._comparator(value, [s.get() for s in self._states])
        return False

    def from_xml(self, node: ElementTree.Element) -> None:
        """Populates the object with data from an XML node.

        Args:
            node: The XML node to parse for data.
        """
        raise error.MissingImplementationError(
            "AbstractCondition.from_xmT not implemented in subclass."
        )

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node containing the object's data.

        Returns:
            XML node containing the object's data.
        """
        raise error.MissingImplementationError(
            "AbstractCondition.to_xml not implemented in subclass."
        )

    def _comparator_from_xml(self, node: ElementTree.Element) -> None:
        """Creates the comparator from XML data.

        Args:
            node: The XML node to parse for data.
        """
        comp_node = node.find("comparator")
        if comp_node is None:
            raise error.ProfileError(
                "ConditionAction: JoystickCondition missing comparator."
            )
        self._comparator = comparator.create_comparator_from_xml(comp_node)

    def _create_condition_node(self) -> ElementTree.Element:
        """Creates the base condition XML node with comparator contents.

        Returns:
            Condition XML node for the uderlying type.
        """
        if self._comparator is None:
            raise error.GremlinError(
                "ConditionAction: Cannot serialize condition without comparator."
            )

        node = util.create_node_from_data(
            "condition",
            [(
                "condition-type",
                ConditionType.to_string(self._condition_type),
                PropertyType.String
            )]
        )
        node.append(self._comparator.to_xml())
        return node

    def is_valid(self) -> bool:
        """Returns whether or not a condition is validly specified.

        Returns:
            True if the condition is properly specified, False otherwise.
        """
        # TODO: Ensure condition type and comparator are compatible.
        return (self._comparator is not None) and (len(self._states) > 0)

    @Property(str, notify=conditionTypeChanged)
    def conditionType(self) -> str:
        """Returns the name of the condition type.

        Returns:
            String representation of the condition's type.
        """
        return ConditionType.to_string(self._condition_type)

    def set_input_type(self, input_type: InputType) -> None:
        """Sets the InputType of the input the condition is triggered within.

        This method forwards the change to each condition such that they can
        decide what, if any, change is needed.

        Args:
            input_type: New type of input the condition is based on.
        """
        self._update_comparator_if_needed(input_type)

    def _update_comparator_if_needed(self, input_type: InputType) -> None:
        """Updates the comparator if the current one is not adequate.

        Args:
            input_type: The InputType the comparator should support.
        """
        raise error.GremlinError(
            "AbstractCondition::_update_comparator_if_needed "
            "implementation missing."
        )

    def _create_comparator(self, input_type: InputType) -> None:
        """Creates the comparator based on the type of input.

        Args:
            input_type: Type of input the comparator is meant for.
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
        if not isinstance(self._comparator, type(comparator_map[input_type])):
            print("0")
            self._comparator = comparator.create_default_comparator(
                comparator_types[input_type]
            )
            print("1")
            self.comparatorChanged.emit()
            print("2")

    @Property(comparator.AbstractComparator, notify=comparatorChanged)
    def comparator(self) -> comparator.AbstractComparator | None:
        """Returns the current comparator instnace.

        Returns:
            Current comparator instance.
        """
        return self._comparator

    def _update_states(self, state_list: List[AbstractState]) -> None:
        """Updates the list of states used by the condition.

        Args:
            state_list: New list of states to use.
        """
        if set(state_list) != set(self._states):
            self._states = state_list
            self.statesChanged.emit(self._get_state_names())

    def _get_state_names(self) -> List[str]:
        """Returns a human readable textual representation for each state.

        Returns:
            List of human readable state names.
        """
        return [s.display_name() for s in self._states]

    states = Property(
        list,
        fget=_get_state_names,
        notify=statesChanged
    )


@QtQml.QmlElement
class KeyboardCondition(AbstractCondition):

    """Keyboard state based condition.

    The condition can contain a sequence of keys which will be treated as one
    for the purpose of determining truth value.
    """

    class State(AbstractState):

        def __init__(self, scan_code: int, is_extended: bool) -> None:
            self.key = key_from_code(scan_code, is_extended)
            self.keyboard = Keyboard()

        def get(self) -> bool:
            return self.keyboard.is_pressed(self.key)

        def display_name(self) -> str:
            return self.key.name

    def __init__(self, parent: ta.OQO=None) -> None:
        """Creates a new instance."""
        super().__init__(parent)

        self._condition_type = ConditionType.Keyboard

    def from_xml(self, node: ElementTree.Element) -> None:
        """Populates the object with data from an XML node.

        Args:
            node: the XML node to parse for data
        """
        self._comparator_from_xml(node)
        for item_node in node.findall("input"):
            self._states.append(self.State(
                util.read_property(item_node, "scan-code", PropertyType.Int),
                util.read_property(item_node, "is-extended", PropertyType.Bool)
            ))

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node containing the objects data.

        Returns:
            XML node containing the object's data
        """
        node = self._create_condition_node()
        for state in self._states:
            node.append(util.create_node_from_data(
                "input",
                [
                    ("scan-code", state.key.scan_code, PropertyType.Int),
                    ("is-extended", state.key.is_extended, PropertyType.Bool)
                ]
            ))
        return node

    @Slot(list)
    def updateFromUserInput(self, data: List[event_handler.Event]) -> None:
        # Verify the comparator type is still adequate and modify / warn as
        # needed. First determine the correct type and then check if changes
        # are needed.
        for evt in data:
            if evt.event_type != InputType.Keyboard:
                raise error.GremlinError(
                    f"ConditionAction: Invalid InputType {evt.event_type} in "
                    "KeyboardCondition."
                )

        # Check if the comparator type has to change
        if len(data) == 0:
            self._comparator = None
        else:
            if not isinstance(
                self._comparator, type(comparator.PressedComparator)
            ):
                self._comparator = \
                    comparator.create_default_comparator("pressed")

        self._update_states(
            [self.State(evt.identifier[0], evt.identifier[1]) for evt in data]
        )

    def _update_comparator_if_needed(self, input_type: InputType) -> None:
        pass


@QtQml.QmlElement
class JoystickCondition(AbstractCondition):

    """Joystick input state based condition.

    This condition is based on the state of a joystick axis, button, or hat.
    """

    class State(AbstractState):

        def __init__(
            self,
            device_uuid: uuid.UUID,
            input_type: InputType,
            input_id: int
        ) -> None:
            self.device_uuid = device_uuid
            self.input_type = input_type
            self.input_id = input_id
            self.joystick = Joystick()[self.device_uuid]
            self.device_lookup = DeviceDatabase().get_mapping_by_uuid(
                self.device_uuid
            )

        def get(self) -> bool | float | HatDirection:
            match self.input_type:
                case InputType.JoystickAxis:
                    return self.joystick.axis(self.input_id).value
                case InputType.JoystickButton:
                    return self.joystick.button(self.input_id).is_pressed
                case InputType.JoystickHat:
                    return self.joystick.hat(self.input_id).direction
                case _:
                    raise error.GremlinError(
                        f"ConditionAction: Invalid InputType {self.input_type} "
                        "in JoystickCondition."
                    )

        def display_name(self) -> str:
            input_name = ""
            match self.input_type:
                case InputType.JoystickAxis:
                    input_name = f"Axis: {self.input_id}"
                case InputType.JoystickButton:
                    input_name = f"Button: {self.input_id}"
                case InputType.JoystickHat:
                    input_name = f"Hat: {self.input_id}"
                case _:
                    raise error.GremlinError(
                        f"ConditionAction: Invalid InputType {self.input_type} "
                        "in JoystickCondition."
                    )
            if self.device_lookup is None:
                return input_name
            return self.device_lookup.input_name(input_name)

    def __init__(self, parent: ta.OQO=None) -> None:
        """Creates a new instance."""
        super().__init__(parent)

        self._condition_type = ConditionType.Joystick

    def from_xml(self, node: ElementTree.Element) -> None:
        """Populates the object with data from an XML node.

        Args:
            node: The XML node to parse for data.
        """
        self._comparator_from_xml(node)
        for entry in node.findall("input"):
            self._states.append(self.State(
                util.read_property(entry, "device-guid", PropertyType.UUID),
                util.read_property(entry, "input-type", PropertyType.InputType),
                util.read_property(entry, "input-id", PropertyType.Int)
            ))

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node containing the objects data.

        Returns:
            XML node containing the object's data.
        """
        node = self._create_condition_node()
        for state in self._states:
            node.append(util.create_node_from_data(
                "input",
                [
                    ("device-guid", state.device_guid, PropertyType.UUID),
                    ("input-type", state.event_type, PropertyType.InputType),
                    ("input-id", state.identifier, PropertyType.Int)
                ]
            ))
        return node

    @Slot(list)
    def updateFromUserInput(self, data: List[event_handler.Event]) -> None:
        # Verify the comparator type is still adequate and modify / warn as
        # needed. First determine the correct type and then check if changes
        # are needed.
        input_types = [evt.event_type for evt in data]
        if len(set(input_types)) > 1:
            # Should never happen for a condition to make sense
            raise error.GremlinError(
                "ConditionAction: Multiple InputType types present in a "
                "single condition."
            )

        # Check if the comparator type has to change
        if len(input_types) == 0:
            self._comparator = None
        else:
            self._create_comparator(input_types[0])

        # Create state objects and update.
        self._update_states([
            self.State(evt.device_guid, evt.event_type, evt.identifier)
            for evt in data
        ])

    def _update_comparator_if_needed(self, input_type: InputType) -> None:
        # No need to change the comparator as we don't rely on the input's
        # type for condition checks.
        pass


@QtQml.QmlElement
class CurrentInputCondition(AbstractCondition):

    class State(AbstractState):

        def __init__(self) -> None:
            pass

        def get(self) -> Any:
            return None

        def display_name(self) -> str:
            return "Current Input"

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        self._condition_type = ConditionType.CurrentInput

    def from_xml(self, node: ElementTree.Element) -> None:
        self._comparator_from_xml(node)

    def to_xml(self) -> ElementTree.Element:
        node = self._create_condition_node()
        node = util.create_node_from_data(
            "condition",
            [("condition-type", "current_input", PropertyType.String)]
        )
        return node

    def _update_comparator_if_needed(self, input_type: InputType) -> None:
        # Create a new comparator as the InputType of the selected input
        # itself changed, i.e. axis treated as button. Thus a different
        # comparator is required.
        self._create_comparator(input_type)


@QtQml.QmlElement
class VJoyCondition(AbstractCondition):

    vjoyConditionChanged = Signal()

    class State(AbstractState):

        def __init__(
            self,
            vjoy_id: int,
            input_type: InputType,
            input_id: int
        ) -> None:
            self.vjoy_id = vjoy_id
            self.input_type = input_type
            self.input_id = input_id
            self.vjoy = VJoyProxy()[self.vjoy_id]

        def get(self) -> bool | float | HatDirection:
            match self.input_type:
                case InputType.JoystickAxis:
                    return self.vjoy.axis(self.input_id).value
                case InputType.JoystickButton:
                    return self.vjoy.button(self.input_id).is_pressed
                case InputType.JoystickHat:
                    return self.vjoy.hat(self.input_id).direction
                case _:
                    raise error.GremlinError(
                        f"ConditionAction: Invalid InputType {self.input_type} "
                        "in VJoyCondition."
                    )

        def display_name(self) -> str:
            vjoy_name = f"vJoy {self.vjoy_id}"
            match self.input_type:
                case InputType.JoystickAxis:
                    return f"{vjoy_name} - Axis: {self.input_id}"
                case InputType.JoystickButton:
                    return f"{vjoy_name} - Button: {self.input_id}"
                case InputType.JoystickHat:
                    return f"{vjoy_name} - Hat: {self.input_id}"
                case _:
                    raise error.GremlinError(
                        f"ConditionAction: Invalid InputType {self.input_type} "
                        "in VJoyCondition."
                    )

    """vJoy input state based condition."""

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        self._states = [self.State(1, InputType.JoystickButton, 1)]
        self._condition_type = ConditionType.VJoy
        self._create_comparator(self._states[0].input_type)

    def from_xml(self, node: ElementTree.Element) -> None:
        self._comparator_from_xml(node)
        self._states = [self.State(
            util.read_property(node, "vjoy-id", PropertyType.Int),
            util.read_property(node, "input-type", PropertyType.InputType),
            util.read_property(node, "input-id", PropertyType.Int)
        )]

    def to_xml(self) -> ElementTree.Element[str]:
        node = self._create_condition_node()
        util.append_property_nodes(
            node,
            [
                ("vjoy-id", self._states[0].vjoy_id, PropertyType.Int),
                (
                    "input-type",
                    self._states[0].input_type,
                    PropertyType.InputType
                ),
                ("input-id", self._states[0].input_id, PropertyType.Int)
            ]
        )
        return node

    def _update_comparator_if_needed(self, input_type: InputType) -> None:
        pass

    def _get_vjoy_device_id(self) -> int:
        return self._states[0].vjoy_id

    def _set_vjoy_device_id(self, vjoy_device_id: int) -> None:
        if vjoy_device_id != self._states[0].vjoy_id:
            self._states[0].vjoy_id = vjoy_device_id
            self._create_comparator(self._states[0].input_type)
            self._update_states(self._states)

    def _get_vjoy_input_id(self) -> int:
        return self._states[0].input_id

    def _set_vjoy_input_id(self, vjoy_input_id: int) -> None:
        if vjoy_input_id != self._states[0].input_id:
            self._states[0].input_id = vjoy_input_id
            self._update_states(self._states)

    def _get_vjoy_input_type(self) -> str:
        return InputType.to_string(self._states[0].input_type)

    def _set_vjoy_input_type(self, input_type: str) -> None:
        input_type_tmp = InputType.to_enum(input_type)
        if input_type_tmp != self._states[0].input_type:
            self._states[0].input_type = input_type_tmp
            self._create_comparator(self._states[0].input_type)
            self._update_states(self._states)

    # Define properties
    vjoyDeviceId = Property(
        int,
        fget=_get_vjoy_device_id,
        fset=_set_vjoy_device_id,
        notify=vjoyConditionChanged
    )
    vjoyInputId = Property(
        int,
        fget=_get_vjoy_input_id,
        fset=_set_vjoy_input_id,
        notify=vjoyConditionChanged
    )
    vjoyInputType = Property(
        str,
        fget=_get_vjoy_input_type,
        fset=_set_vjoy_input_type,
        notify=vjoyConditionChanged
    )


@QtQml.QmlElement
class LogicalDeviceCondition(AbstractCondition):

    """Logical Device input state based condition."""

    logicalInputIdentifierChanged = Signal()

    class State(AbstractState):

        def __init__(self, input_type: InputType, input_id: int) -> None:
            self.input_type = input_type
            self.input_id = input_id
            self.input = LogicalDevice()[LogicalDevice.Input.Identifier(
                self.input_type,
                self.input_id
            )]

        def get(self) -> Any:
            match self.input_type:
                case InputType.JoystickAxis:
                    return self.input.value
                case InputType.JoystickButton:
                    return self.input.is_pressed
                case InputType.JoystickHat:
                    return self.input.direction
                case _:
                    raise error.GremlinError(
                        f"ConditionAction: Invalid InputType {self.input_type} "
                        "in LogicalDeviceCondition."
                    )

        def display_name(self) -> str:
            return self.input.label

    def __init__(self, parent: ta.OQO=None) -> None:
        super().__init__(parent)

        logical_input = LogicalDevice().inputs_of_type()[0]
        self._states = [self.State(logical_input.type, logical_input.id)]
        self._condition_type = ConditionType.LogicalDevice
        self._create_comparator(self._states[0].input_type)

    def from_xml(self, node: ElementTree.Element) -> None:
        self._comparator_from_xml(node)
        self._states = [self.State(
            util.read_property(node, "input-type", PropertyType.InputType),
            util.read_property(node, "input-id", PropertyType.Int)
        )]

    def to_xml(self) -> ElementTree.Element[str]:
        node = self._create_condition_node()
        util.append_property_nodes(
            node,
            [
                (
                    "input-type",
                    self._states[0].input_type,
                    PropertyType.InputType
                ),
                ("input-id", self._states[0].input_id, PropertyType.Int)
            ]
        )
        return node

    def _update_comparator_if_needed(self, input_type: InputType) -> None:
        pass

    def _get_logical_input_identifier(self) -> InputIdentifier:
        return InputIdentifier(
            LogicalDevice().device_guid,
            self._states[0].input_type,
            self._states[0].input_id,
            parent=self
        )

    def _set_logical_input_identifier(self, identifier: InputIdentifier) -> None:
        if (identifier.input_type != self._states[0].input_type) or \
                (identifier.input_id != self._states[0].input_id):
            self._states[0] = self.State(
                identifier.input_type,
                identifier.input_id
            )
            self.logicalInputIdentifierChanged.emit()
            self._create_comparator(self._states[0].input_type)

    logicalInputIdentifier = Property(
        InputIdentifier,
        fget=_get_logical_input_identifier,
        fset=_set_logical_input_identifier,
        notify=logicalInputIdentifierChanged
    )


class ConditionFunctor(AbstractFunctor):

    def __init__(self, action: ConditionModel) -> None:
        super().__init__(action)

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
                    "Invalid logical operator present " +
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
            ConditionType.Joystick: JoystickCondition,
            ConditionType.Keyboard: KeyboardCondition,
            ConditionType.CurrentInput: CurrentInputCondition,
            ConditionType.VJoy: VJoyCondition,
            ConditionType.LogicalDevice: LogicalDeviceCondition,
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
    def conditions(self) -> list[AbstractCondition]:
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
                case ConditionType.Joystick:
                    cond_obj = JoystickCondition()
                case ConditionType.Keyboard:
                    cond_obj = KeyboardCondition()
                case ConditionType.CurrentInput:
                    cond_obj = CurrentInputCondition()
                case ConditionType.VJoy:
                    cond_obj = VJoyCondition()
                case ConditionType.LogicalDevice:
                    cond_obj = LogicalDeviceCondition()
                case _:
                    logging.getLogger("system").error(
                        "ConditionAction: Unknown condition type "
                        f"{condition_type} encountered during XML parsing."
                    )
            if cond_obj is not None:
                cond_obj.from_xml(entry)
                self.conditions.append(cond_obj)

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

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return ["true", "false"]

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

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        if old_behavior != new_behavior:
            for condition in self.conditions:
                condition.set_input_type(new_behavior)

create = ConditionData