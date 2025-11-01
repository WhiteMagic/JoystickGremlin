from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, List, Optional, override, TYPE_CHECKING
import uuid
from xml.etree import ElementTree

from PySide6 import QtCore, QtQml
from PySide6.QtCore import Property, Signal, Slot

from vjoy.vjoy import VJoyProxy

from gremlin import error, event_handler, util
from gremlin.base_classes import Value
from gremlin.input_cache import DeviceDatabase, Joystick, Keyboard
from gremlin.keyboard import key_from_code
from gremlin.logical_device import LogicalDevice
from gremlin.types import ConditionType, HatDirection, InputType, PropertyType

from gremlin.ui.device import InputIdentifier

from action_plugins.condition.comparator import (
    AbstractComparator,
    AbstractComparatorModel,
    DirectionComparator,
    PressedComparator,
    RangeComparator,
)

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1


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
        # Comparator object implementing the condition and the accompanying
        # UI model.
        self._comparator : Optional[AbstractComparator] = None
        self._comparator_ui : Optional[AbstractComparatorModel] = None
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

    def is_valid(self) -> bool:
        """Returns whether or not a condition is validly specified.

        Returns:
            True if the condition is properly specified, False otherwise.
        """
        # TODO: Ensure condition type and comparator are compatible.
        return (self._comparator is not None) and (len(self._states) > 0)

    @Property(AbstractComparatorModel, notify=comparatorChanged)
    def comparator(self) -> AbstractComparatorModel | None:
        """Returns the current comparator instnace.

        Returns:
            Current comparator instance.
        """
        return self._comparator_ui

    @Property(str, notify=conditionTypeChanged)
    def conditionType(self) -> str:
        """Returns the name of the condition type.

        Returns:
            String representation of the condition's type.
        """
        return ConditionType.to_string(self._condition_type)

    @Property(list, notify=statesChanged)
    def states(self) -> List[str]:
        """Returns a human readable textual representation for each state.

        Returns:
            List of human readable state names.
        """
        return [s.display_name() for s in self._states]

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

    def _comparator_from_xml(self, node: ElementTree.Element) -> None:
        """Creates the comparator from XML data.

        Args:
            node: The XML node to parse for data.
        """
        comp_node = node.find("comparator")
        if comp_node is None:
            raise error.ProfileError(
                "ConditionAction: Missing comparator node in condition XML."
            )
        comparator_type = util.read_property(
            comp_node,
            "comparator-type",
            PropertyType.String
        )
        if comparator_type == "pressed":
            self._comparator = PressedComparator()
        elif comparator_type == "range":
            self._comparator = RangeComparator()
        elif comparator_type == "direction":
            self._comparator = DirectionComparator()
        else:
            raise error.ProfileError(
                "ConditionAction: Unable to create comparator of type "
                f"\"{comparator_type}\"."
            )
        self._comparator.from_xml(comp_node)
        self._comparator_ui = self._comparator.model(self._comparator)

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

    def _create_comparator(self, input_type: InputType) -> None:
        """Creates the comparator based on the type of input.

        Args:
            input_type: Type of input the comparator is meant for.
        """
        comparator_map = {
            InputType.JoystickAxis: RangeComparator,
            InputType.JoystickButton: PressedComparator,
            InputType.JoystickHat: DirectionComparator,
            InputType.Keyboard: PressedComparator,
        }

        if not isinstance(self._comparator, comparator_map[input_type]):
            self._comparator = comparator_map[input_type]()
            self._comparator_ui = self._comparator.model(self._comparator)
            self.comparatorChanged.emit()

    def _update_states(self, state_list: List[AbstractState]) -> None:
        """Updates the list of states used by the condition.

        Args:
            state_list: New list of states to use.
        """
        if set(state_list) != set(self._states):
            self._states = state_list
            self.statesChanged.emit(self.states)

    def swap_uuid(self, old_uuid: uuid.UUID, new_uuid: uuid.UUID) -> bool:
        """Swaps occurrences of the old UUID with the new one for this condition."""
        return False


@QtQml.QmlElement
class VJoyCondition(AbstractCondition):

    """vJoy input state based condition."""

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

        # If we have no data the user pressed Esc to cancel input recording.
        if len(data) == 0:
            self._comparator = None
            self._comparator_ui = None
        # If we have data but no comparator, create a default one.
        elif self._comparator is None:
            self._create_comparator(InputType.Keyboard)

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
            self.joystick = None
            self.update_for_device()
        
        def update_for_device(self):
            try:
                self.joystick = Joystick()[self.device_uuid]
            except error.GremlinError:
                pass
            self.device_lookup = DeviceDatabase().get_mapping_by_uuid(
                self.device_uuid
            )

        def get(self) -> bool | float | HatDirection:
            if self.joystick is None:
                raise error.GremlinError(
                    f"ConditionAction: Joystick with UUID {self.device_uuid} "
                    "not present."
                )
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
            if self.device_lookup:
                input_name = self.device_lookup.input_name(input_name)
            return f"{self.joystick.name} - {input_name}"

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
                    ("device-guid", state.device_uuid, PropertyType.UUID),
                    ("input-type", state.input_type, PropertyType.InputType),
                    ("input-id", state.input_id, PropertyType.Int)
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

        # If we have no data the user pressed Esc to cancel input recording.
        if len(input_types) == 0:
            self._comparator = None
            self._comparator_ui = None
        # With data present, create a new comparator based on the input type
        # if needed.
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

    @override
    def swap_uuid(self, old_uuid: uuid.UUID, new_uuid: uuid.UUID) -> bool:
        performed_swap = False
        for state in self._states:
            if state.device_uuid == old_uuid:
                state.device_uuid = new_uuid
                state.update_for_device()
                performed_swap = True
        return performed_swap


@QtQml.QmlElement
class CurrentInputCondition(AbstractCondition):

    """Condition based on the current input state."""

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
        return self._create_condition_node()

    def _update_comparator_if_needed(self, input_type: InputType) -> None:
        # Create a new comparator as the InputType of the selected input
        # itself changed, i.e. axis treated as button. Thus a different
        # comparator is required.
        self._create_comparator(input_type)


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
