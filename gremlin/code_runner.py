# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2017 Lionel Ott
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

import gremlin
from gremlin import actions, config, event_handler, input_devices, \
    joystick_handling, macro, util
import action_plugins.remap


class CodeRunner:

    """Runs the actual profile code."""

    def __init__(self):
        """Creates a new code runner instance."""
        self.event_handler = event_handler.EventHandler()
        self.event_handler.add_plugin(input_devices.JoystickPlugin())
        self.event_handler.add_plugin(input_devices.VJoyPlugin())
        self.event_handler.add_plugin(input_devices.KeyboardPlugin())

        self._inheritance_tree = None
        self._running = False

    def is_running(self):
        """Returns whether or not the code runner is executing code.

        :return True if code is being executed, False otherwise
        """
        return self._running

    def start(self, inheritance_tree, settings, start_mode, profile):
        """Starts listening to events and loads all existing callbacks.

        :param inheritance_tree tree encoding inheritance between the
            different modes
        :param settings profile settings to apply at launch
        """
        # Reset states to their default values
        self._inheritance_tree = inheritance_tree
        self._reset_state()

        # Load the generated code
        try:
            # Load generated python code
            gremlin_code = util.load_module("gremlin_code")

            # Create callbacks fom the user code
            callback_count = 0
            for dev_id, modes in input_devices.callback_registry.registry.items():
                for mode, callbacks in modes.items():
                    for event, callback_list in callbacks.items():
                        for callback in callback_list.values():
                            self.event_handler.add_callback(
                                dev_id,
                                mode,
                                event,
                                callback[0],
                                callback[1]
                            )
                            callback_count += 1

            # Generate code based on the profile's content
            for device in profile.devices.values():
                hid = device.hardware_id
                wid = device.windows_id
                dev_id = util.get_device_id(hid, wid)
                for mode in device.modes.values():
                    for input_items in mode.config.values():
                        for input_item in input_items.values():
                            # Only add callbacks for input items that actually
                            # contain actions
                            if len(input_item.containers) == 0:
                                continue

                            event = event_handler.Event(
                                event_type=input_item.input_type,
                                hardware_id=hid,
                                windows_id=wid,
                                identifier=input_item.input_id
                            )

                            self.event_handler.add_callback(
                                dev_id,
                                mode.name,
                                event,
                                InputItemCallback(input_item),
                                input_item.always_execute
                            )

            # Use inheritance to build input action lookup table
            self.event_handler.build_event_lookup(inheritance_tree)

            # Set vJoy axis default values
            for vid, data in settings.vjoy_initial_values.items():
                vjoy_proxy = joystick_handling.VJoyProxy()[vid]
                for aid, value in data.items():
                    vjoy_proxy.axis(aid).set_absolute_value(value)

            # Connect signals
            evt_listener = event_handler.EventListener()
            kb = input_devices.Keyboard()
            evt_listener.keyboard_event.connect(
                self.event_handler.process_event
            )
            evt_listener.joystick_event.connect(
                self.event_handler.process_event
            )
            evt_listener.keyboard_event.connect(kb.keyboard_event)

            input_devices.periodic_registry.start()
            macro.MacroManager().start()

            self.event_handler.change_mode(start_mode)
            self.event_handler.resume()
            self._running = True
        except ImportError as e:
            util.display_error(
                "Unable to launch due to missing custom modules: {}"
                .format(str(e))
            )

    def stop(self):
        """Stops listening to events and unloads all callbacks."""
        # Disconnect all signals
        if self._running:
            evt_lst = event_handler.EventListener()
            kb = input_devices.Keyboard()
            evt_lst.keyboard_event.disconnect(self.event_handler.process_event)
            evt_lst.joystick_event.disconnect(self.event_handler.process_event)
            evt_lst.keyboard_event.disconnect(kb.keyboard_event)
        self._running = False

        # Empty callback registry
        input_devices.callback_registry.clear()
        self.event_handler.clear()

        # Stop periodic events and clear registry
        input_devices.periodic_registry.stop()
        input_devices.periodic_registry.clear()

        macro.MacroManager().stop()

        # Remove all claims on VJoy devices
        joystick_handling.VJoyProxy.reset()

    def _reset_state(self):
        """Resets all states to their default values."""
        self.event_handler._active_mode =\
            list(self._inheritance_tree.keys())[0]
        self.event_handler._previous_mode =\
            list(self._inheritance_tree.keys())[0]


class InputItemCallback:

    """Callback object that can perform the actions associated with an input.

    The object uses the concept of a execution graph to handle conditional
    and chained actions.
    """

    def __init__(self, input_item):
        """Creates a new instance based according to the given input item.

        :param input_item a gremlin.profile.InputItem instance encoding
            settings and actions this callback will execute when executed
        """
        self.execution_graphs = []

        # Reorder containers such that if those containing remap actions are
        # executed last
        pre_containers = []
        post_containers = []
        for i, container in enumerate(input_item.containers):
            contains_remap = False
            for action_set in container.action_sets:
                for action in action_set:
                    if isinstance(action, action_plugins.remap.Remap):
                        contains_remap |= True
            if contains_remap:
                print("X")
                post_containers.append(i)
            else:
                pre_containers.append(i)

        ordered_containers = []
        for i in pre_containers:
            ordered_containers.append(input_item.containers[i])
        for i in post_containers:
            ordered_containers.append(input_item.containers[i])

        for container in ordered_containers:
            self.execution_graphs.append(ContainerExecutionGraph(container))

    def __call__(self, event):
        """Executes the callback based on the event's content.

        Creates a Value object from the event and passes the two through the
        execution graph until every entry has run or it is aborted.
        """
        if event.event_type in [
            gremlin.common.InputType.JoystickAxis,
            gremlin.common.InputType.JoystickHat
        ]:
            value = gremlin.actions.Value(event.value)
        elif event.event_type in [
            gremlin.common.InputType.JoystickButton,
            gremlin.common.InputType.Keyboard
        ]:
            value = gremlin.actions.Value(event.is_pressed)
        else:
            raise gremlin.error.GremlinError("Invalid event type")

        for graph in self.execution_graphs:
            graph.process_event(event, value)


class AbstractExecutionGraph(metaclass=ABCMeta):

    """Abstract base class for all execution graph type classes.

    An execution graph consists of nodes which represent actions to execute and
    links which are transitions between nodes. Each node's execution returns
    a boolean value, indicating success or failure. The links allow skipping
    of nodes based on the outcome of a node's execution.

    When there is no link for a given node and outcome combination the
    graph terminates.
    """

    def __init__(self, object):
        """Creates a new execution graph based on the provided data.

        :param the object to use in order to generate the graph
        """
        self.functors = []
        self.transitions = {}
        self.current_index = 0

        self._build_graph(object)

    def process_event(self, event, value):
        """Executes the graph with the provided data.

        :param event the raw event that caused the execution of this graph
        :param value the possibly modified value extracted from the event
        """
        while self.current_index is not None:
            result = self.functors[self.current_index].process_event(event, value)
            self.current_index = self.transitions.get(
                (self.current_index, result),
                None
            )
        self.current_index = 0

    @abstractmethod
    def _build_graph(self, object):
        """Builds the graph structure based on the given object's content.

        :param object the object to use in order to generate the graph
        """
        pass

    def _create_activation_condition(self, activation_condition):
        """Creates activation condition objects base on the given data.

        :param activation_condition data about activation condition to be
            used in order to generate executable nodes
        """
        conditions = []
        for condition in activation_condition.conditions:
            if isinstance(condition, gremlin.base_classes.KeyboardCondition):
                conditions.append(
                    gremlin.actions.KeyboardCondition(
                        condition.scan_code,
                        condition.is_extended,
                        condition.comparison
                    )
                )
            elif isinstance(condition, gremlin.base_classes.JoystickCondition):
                conditions.append(
                    gremlin.actions.JoystickCondition(
                        condition.windows_id,
                        condition.input_type,
                        condition.input_id,
                        condition.comparison
                    )
                )
            elif isinstance(condition, gremlin.base_classes.InputActionCondition):
                conditions.append(
                    gremlin.actions.InputActionCondition(condition.comparison)
                )
            else:
                raise gremlin.error.GremlinError("Invalid condition provided")

        return gremlin.actions.ActivationCondition(
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
                isinstance(cond, gremlin.base_classes.InputActionCondition)
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
                # Transition to the next node irrepsective of failure or success
                self.transitions[(i, True)] = i+1
                self.transitions[(i, False)] = i + 1


class ContainerExecutionGraph(AbstractExecutionGraph):

    """Execution graph for the content of a single container."""

    def __init__(self, container):
        """Creates a new instance for a specific container.

        :param container the container data from which to generate the
            execution graph
        """
        assert isinstance(container, gremlin.base_classes.AbstractContainer)
        super().__init__(container)

    def _build_graph(self, container):
        """Builds the graph structure based on the container's content.

        :param container data to use in order to generate the graph
        """
        sequence = []

        # Add virtual button transform as the first functor if present
        if container.virtual_button:
            self.functors.append(self._create_virtual_button(container))
            sequence.append("Condition")

        # If container based conditions exist add them beofre any actions
        if container.activation_condition_type == "container":
            self.functors.append(
                self._create_activation_condition(container.activation_condition)
            )
            sequence.append("Condition")

        self.functors.append(container.functor(container))
        sequence.append("Action")

        self._create_transitions(sequence)

    def _create_virtual_button(self, container):
        """Creates a VirtualButton object for the provided container.

        :param container data to use in order to generate the VirtualButton
        """
        input_type = container.get_input_type()
        if input_type == gremlin.common.InputType.JoystickAxis:
            return gremlin.actions.AxisButton(
                container.virtual_button.lower_limit,
                container.virtual_button.upper_limit
            )
        elif input_type == gremlin.common.InputType.JoystickHat:
            return gremlin.actions.HatButton(
                container.virtual_button.directions
            )
        else:
            raise gremlin.error.GremlinError("Invalid virtual button provided")


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
            if not isinstance(action, action_plugins.remap.Remap):
                ordered_action_set.append(action)
        for action in action_set:
            if isinstance(action, action_plugins.remap.Remap):
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
                condition = gremlin.base_classes.InputActionCondition()
                condition.comparison = ActionSetExecutionGraph.comparison_map[
                    action.default_button_activation
                ]
                activation_condition = gremlin.base_classes.ActivationCondition(
                    [condition],
                    gremlin.base_classes.ActivationRule.All
                )
                self.functors.append(
                    self._create_activation_condition(activation_condition)
                )
                sequence.append("Condition")

            # Create action functor
            self.functors.append(action.functor(action))
            sequence.append("Action")

        self._create_transitions(sequence)
