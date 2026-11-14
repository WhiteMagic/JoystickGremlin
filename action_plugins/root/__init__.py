# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import (
    types,
    util,
)
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    InputType,
    PropertyType,
)
from gremlin.ui.action_model import ActionModel

if TYPE_CHECKING:
    from gremlin.ui.action_model import SequenceIndex
    from gremlin.ui.profile import ActionSequenceModel


class RootFunctor(AbstractFunctor):
    def __init__(self, action: RootData) -> None:
        super().__init__(action)

    @override
    def __call__(
        self,
        event: types.Event,
        value: Value,
        properties: list[ActionProperty] = [],
    ) -> bool:
        return self._process_event(self.functors["children"], event, value, properties)


class RootModel(ActionModel):
    def __init__(
        self,
        data: AbstractActionData,
        sequence_model: ActionSequenceModel,
        action_index: SequenceIndex,
        parent_index: SequenceIndex,
        parent: QtCore.QObject,
    ) -> None:
        super().__init__(data, sequence_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile("core_plugins:root/RootAction.qml").fileName()

    def _action_behavior(self) -> str:
        # Keyboard inputs share the actions of buttons.
        if self._data.input_type == InputType.Keyboard:
            return InputType.to_string(InputType.JoystickButton)
        return InputType.to_string(self._data.input_type)


class RootData(AbstractActionData):
    """Holds the actions of an action sequence and the input type it is made for."""

    version = 1
    name = "Root"
    tag = "root"
    icon = "\uf5e2"

    functor = RootFunctor
    model = RootModel

    properties = (ActionProperty.ActivateDisabled,)
    input_types = (
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard,
    )

    def __init__(self, behavior_type: InputType = InputType.JoystickButton) -> None:
        super().__init__(behavior_type)

        # Type of the inputs this action sequence can be bound to.
        self.input_type = behavior_type
        self.children = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.input_type = util.read_property(node, "input-type", PropertyType.InputType)
        child_ids = util.read_action_ids(node.find("actions"))
        self.children = [library.get_action(aid) for aid in child_ids]

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(RootData.tag, self._id)
        node.append(
            util.create_action_ids("actions", [child.id for child in self.children])
        )
        node.append(
            util.create_property_node(
                "input-type", self.input_type, PropertyType.InputType
            )
        )
        return node

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> list[str]:
        return ["children"]

    @override
    def _get_container(self, selector: str) -> list[AbstractActionData]:
        if selector == "children":
            return self.children


create = RootData
