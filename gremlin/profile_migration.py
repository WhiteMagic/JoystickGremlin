# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from xml.etree import ElementTree

from gremlin import (
    error,
    util,
)
from gremlin.types import (
    ActionActivationMode,
    AxisButtonDirection,
    InputType,
    PropertyType,
)


def _upgrade_from_14(root: ElementTree.Element) -> None:
    """Upgrades a version 14 profile to version 17 in place.

    - Special handling of virtual button configurations removed and replaced by a
      virtual button action.
    - Items directly hold Root action references rather than an input binding.

    Args:
        root: root element of the profile's XML document
    """
    library = root.find("library")
    if library is None:
        raise error.ProfileError("Profile has no library")

    referenced_root_ids = set()
    for input_node in root.findall("./inputs/input"):
        input_type = util.read_subelement(input_node, "input-type")
        for configuration in input_node.findall("action-configuration"):
            root_id = util.read_subelement(configuration, "root-action")
            root_action = _library_action(library, root_id)
            root_action.append(
                util.create_property_node(
                    "input-type", input_type, PropertyType.InputType
                )
            )
            if (
                input_type in (InputType.JoystickAxis, InputType.JoystickHat)
                and util.read_subelement(configuration, "behavior")
                == InputType.JoystickButton
            ):
                _v14_insert_virtual_button(
                    library,
                    root_action,
                    _v14_virtual_button_properties(configuration, input_type),
                )
            referenced_root_ids.add(root_id)

            configuration.clear()
            configuration.tag = "root-action"
            configuration.text = str(root_id)

    for action in library.findall("./action[@type='root']"):
        if util.read_action_id(action) not in referenced_root_ids:
            library.remove(action)


def _library_action(
    library: ElementTree.Element, action_id: uuid.UUID
) -> ElementTree.Element:
    """Returns the library's action node with the given id.

    Args:
        library: library element of the profile
        action_id: id of the action to return

    Returns:
        Action node with the given id
    """
    action = library.find(f"./action[@id='{action_id}']")
    if action is None:
        raise error.ProfileError(f"Action {action_id} is missing from the library")
    return action


def _v14_virtual_button_properties(
    configuration: ElementTree.Element, input_type: InputType
) -> list[list]:
    """Returns the Virtual Button action's property data for the configuration.

    Args:
        configuration: action configuration holding a virtual-button node
        input_type: type of the input the configuration belongs to

    Returns:
        Name, value, and type of each of the virtual button's settings
    """
    virtual_button = configuration.find("virtual-button")
    if virtual_button is None:
        raise error.ProfileError(
            "Action configuration with button behavior has no virtual-button entry"
        )

    if input_type == InputType.JoystickAxis:
        return [
            [
                "lower-limit",
                util.read_subelement(virtual_button, "lower-limit"),
                PropertyType.Float,
            ],
            [
                "upper-limit",
                util.read_subelement(virtual_button, "upper-limit"),
                PropertyType.Float,
            ],
            [
                "axis-button-direction",
                AxisButtonDirection.to_string(
                    util.read_subelement(virtual_button, "axis-button-direction")
                ),
                PropertyType.String,
            ],
        ]
    return [
        ["hat-direction", direction, PropertyType.HatDirection]
        for direction in util.read_subelements(virtual_button, "hat-direction")
    ]


def _v14_insert_virtual_button(
    library: ElementTree.Element,
    root_action: ElementTree.Element,
    virtual_button_properties: list[list],
) -> None:
    """Moves the root action's children into a new Virtual Button action.

    Args:
        library: library element of the profile
        root_action: root action node receiving the Virtual Button action
        properties: name, value, and type of each of the virtual button's settings
    """
    root_children = root_action.find("actions")
    if root_children is None:
        raise error.ProfileError(
            f"Root action {root_action.get('id')} has no actions entry"
        )

    virtual_button_id = uuid.uuid4()
    virtual_button = util.create_action_node("virtual-button", virtual_button_id)
    root_action.remove(root_children)
    virtual_button.append(root_children)
    util.append_property_nodes(
        virtual_button,
        [
            *virtual_button_properties,
            ["action-label", "Virtual Button", PropertyType.String],
            [
                "activation-mode",
                ActionActivationMode.Disallowed,
                PropertyType.ActionActivationMode,
            ],
        ],
    )

    root_action.insert(0, util.create_action_ids("actions", [virtual_button_id]))
    library.insert(list(library).index(root_action) + 1, virtual_button)


# Sequentially ordered list of profile upgrades, each turning a profile of the
# first version into one of the second.
_UPGRADES = [
    (14, 17, _upgrade_from_14),
]


def migrate_profile(root: ElementTree.Element, fpath: Path) -> None:
    """Upgrades a profile's XML document to the current format in place.

    Profiles of a version without an upgrade path are left unchanged.

    Args:
        root: root element of the profile's XML document
    """
    version = int(root.get("version", "0"))
    for source_version, target_version, upgrade in _UPGRADES:
        if version == source_version:
            upgrade(root)
            # Update version value and attribute such that the next part in the upgrade
            # chain can run.
            version = target_version
            root.set("version", str(version))
            logging.getLogger("system").info(
                f"Upgraded profile {fpath} from version {source_version} "
                f"to {target_version}"
            )
