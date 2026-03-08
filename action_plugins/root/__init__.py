# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import copy
import logging
import threading
import time
from typing import Any, List, Optional, TYPE_CHECKING, override
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import event_handler, plugin_manager, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, UserFeedback, \
    Value
from gremlin.error import GremlinError
from gremlin.config import Configuration
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType, DataInsertionMode, DataCreationMode

from gremlin.ui.action_model import ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel
    from gremlin.ui.action_model import SequenceIndex


class RootFunctor(AbstractFunctor):

    def __init__(self, action: RootData) -> None:
        super().__init__(action)

    @override
    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty] = []
    ) -> None:
        for functor in self.functors["children"]:
            functor(event, value, properties)


class RootModel(ActionModel):

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
            "core_plugins:root/RootAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return self._binding_model.behavior


class RootData(AbstractActionData):

    """Represents the root node of any action tree.

    This class mimicks the behavior of base_classes.AbstractActionModel but
    is not intended to be serialized. This is mainly needed to simplify the
    UI handling by providing a root-level container that holds all other
    actions.
    """

    version = 1
    name = "Root"
    tag = "root"
    icon = "\uF5E2"

    functor = RootFunctor
    model = RootModel

    properties = [
        ActionProperty.ActivateDisabled
    ]
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ):
        super().__init__(behavior_type)

        self.children = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        child_ids = util.read_action_ids(node.find("actions"))
        self.children = [library.get_action(aid) for aid in child_ids]

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(RootData.tag, self._id)
        node.append(util.create_action_ids(
            "actions",
            [child.id for child in self.children]
        ))
        return node

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> List[str]:
        return ["children"]

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        if selector == "children":
            return self.children

    @override
    def _handle_behavior_change(
            self,
            old_behavior: InputType,
            new_behavior: InputType
    ) -> None:
        pass

create = RootData