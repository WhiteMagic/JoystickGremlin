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
import enum
import logging
from xml.etree import ElementTree

import dill

import gremlin
from . import common, error, execution_graph, plugin_manager, profile
from gremlin.profile import parse_guid, safe_read, write_guid


class ActivationRule(enum.Enum):

    """Activation rules for collections of conditions.

    All requires all the conditions in a collection to evaluate to True while
    Any only requires a single condition to be True.
    """

    All = 1
    Any = 2


class AbstractCondition(metaclass=ABCMeta):

    """Base class of all individual condition representations."""

    def __init__(self):
        """Creates a new condition."""
        self.comparison = ""

    @abstractmethod
    def from_xml(self, node):
        """Populates the object with data from an XML node.

        :param node the XML node to parse for data
        """
        pass

    @abstractmethod
    def to_xml(self):
        """Returns an XML node containing the objects data.

        :return XML node containing the object's data
        """
        pass

    def is_valid(self):
        """Returns whether or not a condition is fully specified.

        :return True if the condition is properly specified, False otherwise
        """
        return self.comparison != ""


class KeyboardCondition(AbstractCondition):

    """Keyboard state based condition.

    The condition is for a single key and as such contains the key's scan
    code as well as the extended flag.
    """

    def __init__(self):
        """Creates a new instance."""
        super().__init__()
        self.scan_code = None
        self.is_extended = None

    def from_xml(self, node):
        """Populates the object with data from an XML node.

        :param node the XML node to parse for data
        """
        self.comparison = safe_read(node, "comparison")
        self.scan_code = safe_read(node, "scan-code", int)
        self.is_extended = profile.parse_bool(safe_read(node, "extended"))

    def to_xml(self):
        """Returns an XML node containing the objects data.

        :return XML node containing the object's data
        """
        node = ElementTree.Element("condition")
        node.set("condition-type", "keyboard")
        node.set("input", "keyboard")
        node.set("comparison", str(self.comparison))
        node.set("scan-code", str(self.scan_code))
        node.set("extended", str(self.is_extended))
        return node

    def is_valid(self):
        """Returns whether or not a condition is fully specified.

        :return True if the condition is properly specified, False otherwise
        """
        return super().is_valid() and \
            self.scan_code is not None and \
            self.is_extended is not None


class JoystickCondition(AbstractCondition):

    """Joystick state based condition.

    This condition is based on the state of a joystick axis, button, or hat.
    """

    def __init__(self):
        """Creates a new instance."""
        super().__init__()
        self.device_guid = 0
        self.input_type = None
        self.input_id = 0
        self.range = [0.0, 0.0]
        self.device_name = ""

    def from_xml(self, node):
        """Populates the object with data from an XML node.

        :param node the XML node to parse for data
        """
        self.comparison = safe_read(node, "comparison")

        self.input_type = common.InputType.to_enum(safe_read(node, "input"))
        self.input_id = safe_read(node, "id", int)
        self.device_guid = parse_guid(node.get("device-guid"))
        self.device_name = safe_read(node, "device-name")
        if self.input_type == common.InputType.JoystickAxis:
            self.range = [
                safe_read(node, "range-low", float),
                safe_read(node, "range-high", float)
            ]

    def to_xml(self):
        """Returns an XML node containing the objects data.

        :return XML node containing the object's data
        """
        node = ElementTree.Element("condition")
        node.set("comparison", str(self.comparison))
        node.set("condition-type", "joystick")
        node.set("input", common.InputType.to_string(self.input_type))
        node.set("id", str(self.input_id))
        node.set("device-guid", write_guid(self.device_guid))
        node.set("device-name", str(self.device_name))
        if self.input_type == common.InputType.JoystickAxis:
            node.set("range-low", str(self.range[0]))
            node.set("range-high", str(self.range[1]))
        return node

    def is_valid(self):
        """Returns whether or not a condition is fully specified.

        :return True if the condition is properly specified, False otherwise
        """
        return super().is_valid() and self.input_type is not None


class VJoyCondition(AbstractCondition):

    """vJoy device state based condition.

    This condition is based on the state of a vjoy axis, button, or hat.
    """

    def __init__(self):
        """Creates a new instance."""
        super().__init__()
        self.vjoy_id = 0
        self.input_type = None
        self.input_id = 0
        self.range = [0.0, 0.0]

    def from_xml(self, node):
        """Populates the object with data from an XML node.

        Parameters
        ==========
        node : ElementTree.Element
            XML node to parse for data
        """
        self.comparison = safe_read(node, "comparison")

        self.input_type = common.InputType.to_enum(safe_read(node, "input"))
        self.input_id = safe_read(node, "id", int)
        self.vjoy_id = safe_read(node, "vjoy-id", int)
        if self.input_type == common.InputType.JoystickAxis:
            self.range = [
                safe_read(node, "range-low", float),
                safe_read(node, "range-high", float)
            ]

    def to_xml(self):
        """Returns an XML node containing the objects data.

        Return
        ======
        ElementTree.Element
            XML node containing the object's data
        """
        node = ElementTree.Element("condition")
        node.set("comparison", str(self.comparison))
        node.set("condition-type", "vjoy")
        node.set("input", common.InputType.to_string(self.input_type))
        node.set("id", str(self.input_id))
        node.set("vjoy-id", write_guid(self.vjoy_id))
        if self.input_type == common.InputType.JoystickAxis:
            node.set("range-low", str(self.range[0]))
            node.set("range-high", str(self.range[1]))
        return node

    def is_valid(self):
        """Returns whether or not a condition is fully specified.

        :return True if the condition is properly specified, False otherwise
        """
        return super().is_valid() and self.input_type is not None



class InputActionCondition(AbstractCondition):

    """Input item press / release state based condition.

    The condition is for the current input item, triggering based on whether
    or not the input item is being pressed or released.
    """

    def __init__(self):
        """Creates a new instance."""
        super().__init__()

    def from_xml(self, node):
        """Populates the object with data from an XML node.

        :param node the XML node to parse for data
        """
        self.comparison = safe_read(node, "comparison")

    def to_xml(self):
        """Returns an XML node containing the objects data.

        :return XML node containing the object's data
        """
        node = ElementTree.Element("condition")
        node.set("condition-type", "action")
        node.set("input", "action")
        node.set("comparison", str(self.comparison))
        return node


class ActivationCondition:

    """Dictates under what circumstances an associated code can be executed."""

    rule_lookup = {
        # String to enum
        "all": ActivationRule.All,
        "any": ActivationRule.Any,
        # Enum to string
        ActivationRule.All: "all",
        ActivationRule.Any: "any",
    }

    condition_lookup = {
        "keyboard": KeyboardCondition,
        "joystick": JoystickCondition,
        "vjoy": VJoyCondition,
        "action": InputActionCondition,
    }

    def __init__(self, conditions, rule):
        """Creates a new instance."""
        self.rule = rule
        self.conditions = conditions

    def from_xml(self, node):
        """Extracts activation condition data from an XML node.

        :param node the XML node to parse
        """
        self.rule = ActivationCondition.rule_lookup[safe_read(node, "rule")]
        for cond_node in node.findall("condition"):
            condition_type = safe_read(cond_node, "condition-type")
            condition = ActivationCondition.condition_lookup[condition_type]()
            condition.from_xml(cond_node)
            self.conditions.append(condition)

    def to_xml(self):
        """Returns an XML node containing the activation condition information.

        :return XML node containing information about the activation condition
        """
        node = ElementTree.Element("activation-condition")
        node.set("rule", ActivationCondition.rule_lookup[self.rule])

        for condition in self.conditions:
            if condition.is_valid():
                node.append(condition.to_xml())
        return node


class AbstractFunctor(metaclass=ABCMeta):

    """Abstract base class defining the interface for functor like classes.

    These classes are used in the internal code execution system.
    """

    def __init__(self, instance):
        """Creates a new instance, extracting needed information.

        :param instance the object which contains the information needed to
            execute it later on
        """
        pass

    @abstractmethod
    def process_event(self, event, value):
        """Processes the functor using the provided event and value data.

        :param event the raw event that caused the functor to be executed
        :param value the possibly modified value
        """
        pass


class AbstractAction(profile.LibraryData):

    """Base class for all actions that can be encoded via the XML and
    UI system."""

    def __init__(self, parent):
        """Creates a new instance.

        :parent the container which is the parent to this action
        """
        assert isinstance(parent, AbstractContainer)
        super().__init__(parent)

        self.activation_condition = None

    def from_xml(self, node):
        """Populates the instance with data from the given XML node.

        :param node the XML node to populate fields with
        """
        super().from_xml(node)

        for child in node.findall("activation-condition"):
            self.parent.activation_condition_type = "action"
            self.activation_condition = \
                gremlin.base_classes.ActivationCondition(
                    [],
                    ActivationRule.All
                )
            cond_node = node.find("activation-condition")
            if cond_node is not None:
                self.activation_condition.from_xml(cond_node)

    def to_xml(self):
        """Returns a XML node representing the instance's contents.

        :return XML node representing the state of this instance
        """
        node = super().to_xml()
        if self.activation_condition:
            node.append(self.activation_condition.to_xml())
        return node

    def icon(self):
        """Returns the icon to use when representing the action.

        :return icon to use
        """
        raise error.MissingImplementationError(
            "AbstractAction.icon not implemented in subclass"
        )

    def requires_virtual_button(self):
        """Returns whether or not the action requires the use of a
        virtual button.

        :return True if a virtual button has to be used, False otherwise
        """
        raise error.MissingImplementationError(
            "AbstractAction.requires_virtual_button not implemented"
        )


class AbstractContainer(profile.LibraryData):

    """Base class for action container related information storage."""

    # virtual_button_lut = {
    #     common.InputType.JoystickAxis: VirtualAxisButton,
    #     common.InputType.JoystickButton: None,
    #     common.InputType.JoystickHat: VirtualHatButton
    # }

    def __init__(self, parent):
        """Creates a new instance.

        :parent the InputItem which is the parent to this action
        """
        super().__init__(parent)
        self.action_sets = []
        self.activation_condition_type = None
        self.activation_condition = None
        # self.virtual_button = None
        # Storage for the currently active view in the UI
        # FIXME: This is ugly and shouldn't be done but for now the least
        #   terrible option
        # self.current_view_type = None

    def add_action(self, action, index=-1):
        """Adds an action to this container.

        :param action the action to add
        :param index the index of the action_set into which to insert the
            action. A value of -1 indicates that a new set should be
            created.
        """
        assert isinstance(action, AbstractAction)
        if index == -1:
            self.action_sets.append([])
            index = len(self.action_sets) - 1
        self.action_sets[index].append(action)

        # Create activation condition data if needed
        # self.create_or_delete_virtual_button()

    # TODO: This needs to become part of the library reference stuff
    # def create_or_delete_virtual_button(self):
    #     """Creates activation condition data as required."""
    #     need_virtual_button = False
    #     for actions in [a for a in self.action_sets if a is not None]:
    #         need_virtual_button = need_virtual_button or \
    #             any([a.requires_virtual_button() for a in actions if a is not None])
    #
    #     if need_virtual_button:
    #         if self.virtual_button is None:
    #             self.virtual_button = \
    #                 AbstractContainer.virtual_button_lut[self.parent.input_type]()
    #         elif not isinstance(
    #                 self.virtual_button,
    #                 AbstractContainer.virtual_button_lut[self.parent.input_type]
    #         ):
    #             self.virtual_button = \
    #                 AbstractContainer.virtual_button_lut[self.parent.input_type]()
    #     else:
    #         self.virtual_button = None

    # TODO: This should go somewhere in the code runner parts
    # def generate_callbacks(self):
    #     """Returns a list of callback data entries.
    #
    #     :return list of container callback entries
    #     """
    #     callbacks = []
    #
    #     # For a virtual button create a callback that sends VirtualButton
    #     # events and another callback that triggers of these events
    #     # like a button would.
    #     if self.virtual_button is not None:
    #         callbacks.append(execution_graph.CallbackData(
    #             execution_graph.VirtualButtonProcess(self.virtual_button),
    #             None
    #         ))
    #         callbacks.append(execution_graph.CallbackData(
    #             execution_graph.VirtualButtonCallback(self),
    #             gremlin.event_handler.Event(
    #                 gremlin.common.InputType.VirtualButton,
    #                 callbacks[-1].callback.virtual_button.identifier,
    #                 device_guid=dill.GUID_Virtual,
    #                 is_pressed=True,
    #                 raw_value=True
    #             )
    #         ))
    #     else:
    #         callbacks.append(execution_graph.CallbackData(
    #             execution_graph.ContainerCallback(self),
    #             None
    #         ))
    #
    #     return callbacks

    def from_xml(self, node):
        """Populates the instance with data from the given XML node.

        :param node the XML node to populate fields with
        """
        super().from_xml(node)
        self._parse_action_set_xml(node)
        # self._parse_virtual_button_xml(node)
        self._parse_activation_condition_xml(node)

    def to_xml(self):
        """Returns a XML node representing the instance's contents.

        :return XML node representing the state of this instance
        """
        node = super().to_xml()
        # Add activation condition if needed
        # if self.virtual_button:
        #     node.append(self.virtual_button.to_xml())
        if self.activation_condition:
            condition_node = self.activation_condition.to_xml()
            if condition_node:
                node.append(condition_node)
        return node

    def _parse_action_set_xml(self, node):
        """Parses the XML content related to actions.

        :param node the XML node to process
        """
        self.action_sets = []
        for child in node:
            # if child.tag == "virtual-button":
            #     continue
            if child.tag == "action-set":
                action_set = []
                self._parse_action_xml(child, action_set)
                self.action_sets.append(action_set)
            else:
                logging.getLogger("system").warning(
                    "Unknown node present: {}".format(child.tag)
                )

    def _parse_action_xml(self, node, action_set):
        """Parses the XML content related to actions in an action-set.

        :param node the XML node to process
        :param action_set storage for the processed action nodes
        """
        action_name_map = plugin_manager.ActionPlugins().tag_map
        for child in node:
            if child.tag not in action_name_map:
                logging.getLogger("system").warning(
                    "Unknown node present: {}".format(child.tag)
                )
                continue

            entry = action_name_map[child.tag](self)
            entry.from_xml(child)
            action_set.append(entry)

    # def _parse_virtual_button_xml(self, node):
    #     """Parses the virtual button part of the XML data.
    #
    #     :param node the XML node to process
    #     """
    #     vb_node = node.find("virtual-button")
    #
    #     self.virtual_button = None
    #     if vb_node is not None:
    #         self.virtual_button = AbstractContainer.virtual_button_lut[
    #             self.get_input_type()
    #         ]()
    #         self.virtual_button.from_xml(vb_node)

    def _parse_activation_condition_xml(self, node):
        for child in node.findall("activation-condition"):
            self.activation_condition_type = "container"
            self.activation_condition = \
                gremlin.base_classes.ActivationCondition([], ActivationRule.All)
            cond_node = node.find("activation-condition")
            if cond_node is not None:
                self.activation_condition.from_xml(cond_node)

    def _is_valid(self):
        """Returns whether or not this container is configured properly.

        :return True if configured properly, False otherwise
        """
        # Check state of the container
        state = self._is_container_valid()

        # Check state of all linked actions
        for actions in [a for a in self.action_sets if a is not None]:
            for action in actions:
                state = state & action.is_valid()
        return state

        # # Check that no action set is empty
        # for actions in [a for a in self.action_sets if a is not None]:
        #     if len(actions) == 0:
        #         state = False

        # # Check state of all linked actions
        # for actions in [a for a in self.action_sets if a is not None]:
        #     for action in actions:
        #         if action is None:
        #             state = False
        #         else:
        #             state = state & action.is_valid()
        # return state

    @abstractmethod
    def _is_container_valid(self):
        """Returns whether or not the container itself is valid.

        :return True container data is valid, False otherwise
        """
        pass
