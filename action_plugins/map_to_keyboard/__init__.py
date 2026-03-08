# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import (
    override,
    List,
    TYPE_CHECKING,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import (
    event_handler,
    keyboard,
    macro,
    util,
)
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    InputType,
    PropertyType,
)

from gremlin.ui.action_model import (
    ActionModel,
    SequenceIndex,
)

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class MapToKeyboardFunctor(AbstractFunctor):

    def __init__(self, action: MapToKeyboardData) -> None:
        super().__init__(action)

        self.press = macro.Macro()
        for key in self.data.keys:
            self.press.press(key)
            self.press.pause(0.0)
        self.release = macro.Macro()
        for key in reversed(self.data.keys):
            self.release.release(key)
            self.release.pause(0.0)
    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        if self._should_execute(value):
            if value.current:
                macro.MacroManager().queue_macro(self.press)
            else:
                macro.MacroManager().queue_macro(self.release)


class MapToKeyboardModel(ActionModel):

    # Signal emitted when the description variable's content changes
    changed = QtCore.Signal()

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
            "core_plugins:map_to_keyboard/MapToKeyboardAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @QtCore.Property(str, notify=changed)
    def keyCombination(self) -> str:
        return " + ".join([key.name for key in self._data.keys])

    @QtCore.Slot(list)
    def updateInputs(self, data: List[event_handler.Event]) -> None:
        """Receives the events corresponding to mouse button presses.

        We only expect to receive a single button press and thus store the
        button identifier.

        Args:
            data: list of mouse button presses to store
        """
        # Sort keys such that modifiers are first
        all_keys = [keyboard.key_from_code(*evt.identifier) for evt in data]
        modifier_keys = []
        normal_keys = []
        for key in all_keys:
            if key in keyboard.modifier_keys():
                modifier_keys.append(key)
            else:
                normal_keys.append(key)
        self._data.keys = modifier_keys + normal_keys
        self.changed.emit()
        super().actionChanged.emit()


class MapToKeyboardData(AbstractActionData):

    """Model of a map to keyboard action."""

    version = 1
    name = "Map to Keyboard"
    tag = "map-to-keyboard"
    icon = "\uF451"

    functor = MapToKeyboardFunctor
    model = MapToKeyboardModel

    properties = (
        ActionProperty.ActivateOnBoth,
    )
    input_types = (
        InputType.JoystickButton,
        InputType.Keyboard,
    )

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickButton
    ) -> None:
        super().__init__(behavior_type)

        self.keys = []

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        for key_node in node.findall("input"):
            key = keyboard.key_from_code(
                util.read_property(key_node, "scan-code", PropertyType.Int),
                util.read_property(key_node, "is-extended", PropertyType.Bool)
            )
            self.keys.append(key)

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(MapToKeyboardData.tag, self._id)
        for key in self.keys:
            node.append(util.create_node_from_data(
                "input",
                [
                    ("scan-code", key.scan_code, PropertyType.Int),
                    ("is-extended", key.is_extended, PropertyType.Bool)
                ]
            ))
        return node

    @override
    def user_feedback(self) -> List[UserFeedback]:
        messages = []
        if len(self.keys) == 0:
            messages.append(UserFeedback(
                UserFeedback.FeedbackType.Error,
                "Mapping has no keys assigned to it."
            ))
        return messages

    @override
    def _valid_selectors(self) -> List[str]:
        return []

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = MapToKeyboardData
