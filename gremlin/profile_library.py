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


from abc import abstractmethod, ABCMeta
import uuid
from xml.etree import ElementTree

from . import base_classes, common, error, plugin_manager
from .tree import TreeNode


class ActionData(metaclass=ABCMeta):

    """Base class for all objects storing action information.

    This contains only input independent action infmration.
    """

    def __init__(self, parent):
        """Creates a new instance with a pointer to its parent.

        Args:
            parent: parent item of this instance in the profile tree
        """
        self.parent = parent

    def from_xml(self, node: ElementTree.Element) -> None:
        """Initializes this instance's content based on the provided XML node.

        Args:
            node : XML node used to populate this instance
        """
        self._parse_xml(node)

    def to_xml(self) -> ElementTree.Element:
        """Returns the XML representation of this instance.

        Returns:
            XML node representing this instance
        """
        return self._generate_xml()

    def is_valid(self) -> bool:
        """Returns whether or not an instance is fully specified.

        Returns:
            True if all required variables are set, False otherwise
        """
        return self._is_valid()

    @abstractmethod
    def _parse_xml(self, node: ElementTree.Element) -> None:
        """Implementation of the XML parsing.

        Args
        ==========:
            node: XML node used to populate this instance
        """
        pass

    @abstractmethod
    def _generate_xml(self) -> ElementTree.Element:
        """Implementation of the XML generation.

        Returns:
            XML node representing this instance
        """
        pass

    @abstractmethod
    def _is_valid(self) -> bool:
        """Returns whether or not an instance is fully specified.

        Returns:
            True if all required variables are set, False otherwise
        """
        pass

    @abstractmethod
    def _sanitize(self) -> None:
        """Processes the entries values to ensure they are consistent."""
        pass
from .util import safe_format, safe_read


# class LibraryReference:
#
#     """Holds the reference to a library entry inside an input item."""
#
#     virtual_button_lut = {
#         gremlin.types.InputType.JoystickAxis: VirtualAxisButton,
#         gremlin.types.InputType.JoystickHat: VirtualHatButton
#     }
#
#     def __init__(self, parent):
#         """Creates a new instance.
#
#         Parameters
#         ==========
#         parent
#             parent item of this instance in the profile tree
#         """
#         self.parent = parent
#         self.library_uuid = None
#         self.virtual_button = None
#         self.uuid = uuid.uuid4()
#
#     def configure_virtual_button_data(self):
#         """Creates or deletes virtual button data structures as needed.
#
#         This will create or remove the virtual button data structures
#         depending on whether or not the particular input this reference is
#         assigned to requires it.
#         """
#         need_virtual_button = False
#         action_sets = self.get_container().action_sets
#         for actions in [a for a in action_sets if a is not None]:
#             need_virtual_button = need_virtual_button or \
#                                   any([
#                                       a.requires_virtual_button(
#                                           self.parent.input_type)
#                                       for a in actions if a is not None
#                                   ])
#
#         if need_virtual_button:
#             if self.virtual_button is None:
#                 self.virtual_button = \
#                     LibraryReference.virtual_button_lut[
#                         self.parent.input_type]()
#             elif not isinstance(
#                     self.virtual_button,
#                     LibraryReference.virtual_button_lut[self.parent.input_type]()
#             ):
#                 self.virtual_button = \
#                     LibraryReference.virtual_button_lut[
#                         self.parent.input_type]()
#         else:
#             self.virtual_button = None
#
#     def from_xml(self, node):
#         """Initializes this instance's content based on the provided XML node.
#
#         Parameters
#         ==========
#         node : ElementTree.Element
#             XML node used to populate this instance
#         """
#         self.library_uuid = parse_guid(node.attrib["uuid"])
#
#         # Parse virtual button data
#         vb_node = node.find("virtual-button")
#         if vb_node is not None and \
#                 self.parent.input_type in LibraryReference.virtual_button_lut:
#             self.virtual_button = LibraryReference.virtual_button_lut[
#                 self.parent.input_type
#             ]()
#             self.virtual_button.from_xml(vb_node)
#         else:
#             self.virtual_button = None
#
#     def to_xml(self):
#         """Returns the XML representation of this instance.
#
#         Returns
#         =======
#         ElementTree.Element
#             XML node representing this instance
#         """
#         node = ElementTree.Element("library-reference")
#         node.set("uuid", str(self.library_uuid))
#         if self.virtual_button:
#             node.append(self.virtual_button.to_xml())
#         return node
#
#     def get_container(self):
#         """Returns the container associated with this reference.
#
#         Returns
#         =======
#         base_classes.AbstractContainer
#             The container being referenced
#         """
#         # Retrieve the root Profile node before getting the library instance
#         # from there
#         parent = self.parent
#         while parent.parent is not None:
#             parent = parent.parent
#
#         return parent.library.lookup(self.library_uuid)
#
#     def get_action_sets(self):
#         return self.get_container().action_sets
#
#     def get_settings(self):
#         """Returns the Settings data of the profile.
#
#         :return Settings object of this profile
#         """
#         item = self.parent
#         while not isinstance(item, Profile):
#             item = item.parent
#         return item.settings
#
#     def get_input_type(self):
#         return self.parent.input_type
#
#     def get_mode(self):
#         """Returns the Mode this data entry belongs to.
#
#         :return Mode instance this object belongs to
#         """
#         item = self.parent
#         while not isinstance(item, Mode):
#             item = item.parent
#         return item
#
#     def get_device_type(self):
#         """Returns the DeviceType of this data entry.
#
#         :return DeviceType of this entry
#         """
#         item = self.parent
#         while not isinstance(item, Device):
#             item = item.parent
#         return item.type


class ActionTree:

    """Represents a tree of actions.

    The tree contains both actions to execute as well as conditions controlling
    when and which actions will be executed.
    """

    def __init__(self):
        """Creates a new instance."""
        self.root = TreeNode()

    def from_xml(self, action_tree_node: ElementTree) -> None:
        """Populates the instance with the XML instance data.

        Args:
            action_tree_node: XML subtree which contains the information
        """
        root_id = safe_read(action_tree_node, "root", uuid.UUID)

        # Create the action tree nodes corresponding to each <action> XML
        # element
        action_nodes = []
        action_ids = {}
        parent_ids = {}
        for node in action_tree_node.findall("./action"):
            # Ensure all required attributes are present
            if not set(["id", "type", "parent"]).issubset(node.keys()):
                raise error.ProfileError(
                    f"Missing attribute in an action of tree with "
                    f"root: '{root_id}'"
                )

            # Ensure the action type is known
            type_key = node.get("type")
            if type_key not in plugin_manager.ActionPlugins().tag_map:
                action_id = safe_read(node, "id", uuid.UUID)
                raise error.ProfileError(
                    f"Unknown type '{type_key}' in action '{action_id}"
                )

            # Create action data object
            action_data = plugin_manager.ActionPlugins().tag_map[type_key]()
            action_data.from_xml(node)

            # Store node information
            action_node = TreeNode(action_data)
            action_nodes.append(action_node)
            action_ids[action_data.id] = len(action_nodes)
            parent_ids[action_data.id] = safe_read(node, "parent", uuid.UUID)

        # Reconstruct the action tree structure
        for node in action_nodes:
            parent_id = parent_ids[node.value.id]

            parent_node = None
            if parent_id in action_ids:
                parent_node = action_nodes[action_ids[parent_id]]
            elif parent_id == root_id:
                parent_node = self.root
            else:
                raise error.ProfileError(
                    f"Parent id '{parent_id}' of action "
                    f"'{node.value.id}' is invalid"
                )
            node.set_parent(parent_node)

    def to_xml(self) -> ElementTree:
        """Returns an XML subtree representing the tree's information.

        Returns:
            XML element containing the object's information
        """
        pass


class LibraryItem:

    """Stores information about an individual library item.

    Contains the actual action configuration and the unique id associated
    with the particular item.
    """

    def __init__(self):
        self.action_tree = None
        self._id = uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        """Returns the unique identifier of this instance.

        Returns:
            Unique id of this instance
        """
        return self._id

    def from_xml(self, node: ElementTree.Element) -> None:
        """Parses an library item to populate this instance.

        Args:
            node: XML node containing the library item information
        """
        self._id = safe_read(node, "id", uuid.UUID)
        at_node = node.find("action-tree")
        self.action_tree = ActionTree()
        self.action_tree.from_xml(at_node)

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the content of this library.

        Returns:
            XML node holding the instance's content
        """
        node = ElementTree.Element("library-item")
        node.set("id", safe_format(self._id, uuid.UUID))
        node.append(self.action_tree.to_xml())
        return node


class Library:

    """Stores library items which contain action configurations.

    Each item is a self contained entry with a UUID assigned to it which
    is used by the input items to reference the actual content.
    """

    def __init__(self):
        """Creates a new library instance."""

        # Each entry is a container with it's action sets but without
        # conditions or virtual button configuration
        self._items = {}

        self._container_name_map = plugin_manager.ContainerPlugins().tag_map

    def __contains__(self, key: uuid.UUID) -> bool:
        """Checks if an item exists for the given key.

        Args:
            key: the key to check for

        Returns:
            True if an item exists for the specific key, False otherwise
        """
        return key in self._items

    def __getitem__(self, key: uuid.UUID) -> LibraryItem:
        """Returns the item stored at the specified key.

        If there is no item with the specified key an exception is throw.

        Args:
            key: the key to return an item for

        Returns:
            The LibraryItem instance stored at the given key
        """
        if key not in self._items:
            raise error.GremlinError(f"Invalid uuid for library entry: {key}")
        return self._items[key]

    def add_item(self, item: LibraryItem) -> None:
        """Adds the provided item to the library.

        Args:
            item: the item to add
        """
        self._items[item.id] = item

    def delete_item(self, uuid: uuid.UUID) -> None:
        """Deletes the item with the provided identifier from the library.

        Args:
            uuid: unique identifier of the item to delete
        """
        if item.id in self._items:
            del self._items[item.id]

    def from_xml(self, node: ElementTree.Element) -> None:
        """Parses an library node to populate this instance.

        Args:
            node: XML node containing the library information
        """
        for item in node.findall("./library/library-item"):
            library_item = LibraryItem()
            library_item.from_xml(item)

            if library_item.id in self._items:
                raise error.ProfileError(
                    f"Duplicate library item guid: {library_item.id}"
                )

            self._items[library_item.id] = library_item

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node encoding the content of this library.

        Returns:
            XML node holding the instance's content
        """
        node = ElementTree.Element("library")



        return node