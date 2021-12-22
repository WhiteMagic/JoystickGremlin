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

from abc import abstractmethod, ABCMeta
from collections import namedtuple
import copy
import logging
import time

from gremlin import actions, base_classes, common, error


CallbackData = namedtuple("ContainerCallback", ["callback", "event"])


class ContainerCallback:

    """Callback object that can perform the actions associated with an input.

    The object uses the concept of a execution graph to handle conditional
    and chained actions.
    """

    def __init__(self, container):
        """Creates a new instance based according to the given input item.

        :param container the container instance for which to build th
            execution graph base callback
        """
        self.execution_graph = ContainerExecutionGraph(container)

    def __call__(self, event):
        """Executes the callback based on the event's content.

        Creates a Value object from the event and passes the two through the
        execution graph until every entry has run or it is aborted.
        """
        if event.event_type in [
            common.InputType.JoystickAxis,
            common.InputType.JoystickHat
        ]:
            value = actions.Value(event.value)
        elif event.event_type in [
            common.InputType.JoystickButton,
            common.InputType.Keyboard,
            common.InputType.VirtualButton
        ]:
            value = actions.Value(event.is_pressed)
        else:
            raise error.GremlinError("Invalid event type")

        # Containers representing a virtual button get their individual
        # value instance, all others share one to propagate changes across
        shared_value = copy.deepcopy(value)

        if event == common.InputType.VirtualButton:
            # TODO: remove this at a future stage
            logging.getLogger("system").error(
                "Virtual button code path being used"
            )
        else:
            self.execution_graph.process_event(event, shared_value)


class VirtualButtonCallback:

    """VirtualButton event based callback class."""

    def __init__(self, container):
        """Creates a new instance.

        :param container the container to execute when called
        """
        self._execution_graph = ContainerExecutionGraph(container)

    def __call__(self, event):
        """Executes the container's content when called.

        :param event the event triggering the callback
        """
        self._execution_graph.process_event(
            event,
            actions.Value(event.is_pressed)
        )


class VirtualButtonProcess:

    """Callback that is responsible for emitting press and release events
    for a virtual button."""

    def __init__(self, data):
        """Creates a new instance for the given container.

        :param container the container using a virtual button configuration
        """
        self.virtual_button = None

        if isinstance(data, base_classes.VirtualAxisButton):
            self.virtual_button = actions.AxisButton(
                data.lower_limit,
                data.upper_limit,
                data.direction
            )
        elif isinstance(data, base_classes.VirtualHatButton):
            self.virtual_button = actions.HatButton(
                data.directions
            )
        else:
            raise error.GremlinError("Invalid virtual button data provided")

    def __call__(self, event):
        """Processes the provided event through the virtual button instance.

        :param event the input event being processed
        """
        self.virtual_button.process_event(event)


class AbstractExecutionGraph(metaclass=ABCMeta):

    """Abstract base class for all execution graph type classes.

    An execution graph consists of nodes which represent actions to execute and
    links which are transitions between nodes. Each node's execution returns
    a boolean value, indicating success or failure. The links allow skipping
    of nodes based on the outcome of a node's execution.

    When there is no link for a given node and outcome combination the
    graph terminates.
    """

    def __init__(self, instance):
        """Creates a new execution graph based on the provided data.

        :param instance the object to use in order to generate the graph
        """
        self.functors = []
        self.transitions = {}
        self.current_index = 0

        self._build_graph(instance)

    def process_event(self, event, value):
        """Executes the graph with the provided data.

        :param event the raw event that caused the execution of this graph
        :param value the possibly modified value extracted from the event
        """
        # Processing an event twice is needed when a virtual axis button has
        # "jumped" over it's activation region without triggering it. Once
        # this is detected the "press" event is sent and the second run ensures
        # a "release" event is sent.
        process_again = False

        while self.current_index is not None and len(self.functors) > 0:
            functor = self.functors[self.current_index]
            result = functor.process_event(event, value)

            if isinstance(functor, actions.AxisButton):
                process_again = functor.forced_activation

            self.current_index = self.transitions.get(
                (self.current_index, result),
                None
            )
        self.current_index = 0

        if process_again:
            time.sleep(0.05)
            self.process_event(event, value)

    @abstractmethod
    def _build_graph(self, instance):
        """Builds the graph structure based on the given object's content.

        :param instance the object to use in order to generate the graph
        """
        pass

    def _create_activation_condition(self, activation_condition):
        """Creates activation condition objects base on the given data.

        :param activation_condition data about activation condition to be
            used in order to generate executable nodes
        """
        conditions = []
        for condition in activation_condition.conditions:
            if isinstance(condition, base_classes.KeyboardCondition):
                conditions.append(
                    actions.KeyboardCondition(
                        condition.scan_code,
                        condition.is_extended,
                        condition.comparison
                    )
                )
            elif isinstance(condition, base_classes.JoystickCondition):
                conditions.append(
                    actions.JoystickCondition(condition)
                )
            elif isinstance(condition, base_classes.VJoyCondition):
                conditions.append(
                    actions.VJoyCondition(condition)
                )
            elif isinstance(condition, base_classes.InputActionCondition):
                conditions.append(
                    actions.InputActionCondition(condition.comparison)
                )
            else:
                raise error.GremlinError("Invalid condition provided")

        return actions.ActivationCondition(
            conditions,
            activation_condition.rule
        )

    def _contains_input_action_condition(self, activation_condition):
        """Returns whether or not an input action condition is present.

        :param activation_condition condition data to check for the existence
            of an input action
        :return return True if an input action is present, False otherwise
        """
        if activation_condition:
            return any([
                isinstance(cond, base_classes.InputActionCondition)
                for cond in activation_condition.conditions
            ])
        else:
            return False

    def _create_transitions(self, sequence):
        """Creates node transition based on the node type sequence information.

        :param sequence the sequence of nodes
        """
        seq_count = len(sequence)
        self.transitions = {}
        for i, seq in enumerate(sequence):
            if seq == "Condition":
                # On success, transition to the next node of any type in line
                self.transitions[(i, True)] = i+1
                offset = i + 1
                # On failure, transition to the condition node after the
                # next action node
                while offset < seq_count:
                    if sequence[offset] == "Action":
                        if offset+1 < seq_count:
                            self.transitions[(i, False)] = offset+1
                            break
                    offset += 1
            elif seq == "Action" and i+1 < seq_count:
                # Transition to the next node irrespective of failure or success
                self.transitions[(i, True)] = i+1
                self.transitions[(i, False)] = i + 1


class ContainerExecutionGraph(AbstractExecutionGraph):

    """Execution graph for the content of a single container."""

    def __init__(self, container):
        """Creates a new instance for a specific container.

        :param container the container data from which to generate the
            execution graph
        """
        assert isinstance(container, base_classes.AbstractContainer)
        super().__init__(container)

    def _build_graph(self, container):
        """Builds the graph structure based on the container's content.

        :param container data to use in order to generate the graph
        """
        sequence = []

        # Add virtual button transform as the first functor if present
        # if container.virtual_button:
        #     self.functors.append(self._create_virtual_button(container))
        #     sequence.append("Condition")

        # If container based conditions exist add them before any actions
        if container.activation_condition_type == "container":
            self.functors.append(
                self._create_activation_condition(container.activation_condition)
            )
            sequence.append("Condition")

        self.functors.append(container.functor(container))
        sequence.append("Action")

        self._create_transitions(sequence)


class ActionSetExecutionGraph(AbstractExecutionGraph):

    """Execution graph for the content of a set of actions."""

    comparison_map = {
        (True, True): "always",
        (True, False): "pressed",
        (False, True): "released"
    }

    def __init__(self, action_set):
        """Creates a new instance for a specific set of actions.

        :param action_set the set of actions from which to generate the
            execution graph
        """
        super().__init__(action_set)

    def _build_graph(self, action_set):
        """Builds the graph structure based on the content of the action set.

        :param action_set data to use in order to generate the graph
        """
        # The action set shouldn't be empty, but in case this happens
        # nonetheless we abort
        if len(action_set) == 0:
            return

        sequence = []

        condition_type = action_set[0].parent.activation_condition_type
        add_default_activation = True
        if condition_type is None:
            add_default_activation = True
        elif condition_type == "container":
            add_default_activation = not self._contains_input_action_condition(
                action_set[0].parent.activation_condition
            )

        # Reorder action set entries such that if any remap action is
        # present it is executed last
        ordered_action_set = []
        for action in action_set:
            # if not isinstance(action, action_plugins.remap.Remap):
            if not action.tag == "remap":
                ordered_action_set.append(action)
        for action in action_set:
            # if isinstance(action, action_plugins.remap.Remap):
            if action.tag == "remap":
                ordered_action_set.append(action)

        # Create functors
        for action in ordered_action_set:
            # Create conditions for each action if needed
            if action.activation_condition is not None:
                # Only add a condition if we truly have conditions
                if len(action.activation_condition.conditions) > 0:
                    self.functors.append(
                        self._create_activation_condition(
                            action.activation_condition
                        )
                    )
                    sequence.append("Condition")

            # Create default activation condition if needed
            has_input_action = self._contains_input_action_condition(
                action.activation_condition
            )

            if add_default_activation and not has_input_action:
                condition = base_classes.InputActionCondition()
                condition.comparison = ActionSetExecutionGraph.comparison_map[
                    action.default_button_activation
                ]
                activation_condition = base_classes.ActivationCondition(
                    [condition],
                    base_classes.ActivationRule.All
                )
                self.functors.append(
                    self._create_activation_condition(activation_condition)
                )
                sequence.append("Condition")

            # Create action functor
            self.functors.append(action.functor(action))
            sequence.append("Action")

        self._create_transitions(sequence)
