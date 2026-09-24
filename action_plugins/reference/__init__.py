# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import uuid
from typing import (
    TYPE_CHECKING,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import shared_state
from gremlin.base_classes import (
    AbstractActionData,
    UserFeedback,
)
from gremlin.common import natural_key
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    InputType,
)
from gremlin.ui.action_model import (
    ActionModel,
    SequenceIndex,
    _emit_input_item_changed_later,
)
from gremlin.ui.device import device_and_input_names
from gremlin.ui.profile import LabelValueSelectionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class ReferenceModel(ActionModel):
    modelChanged = QtCore.Signal()

    def __init__(
        self,
        data: AbstractActionData,
        binding_model: InputItemBindingModel,
        action_index: SequenceIndex,
        parent_index: SequenceIndex,
        parent: QtCore.QObject,
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)

    def _qml_path_impl(self) -> str:
        return (
            "file:///"
            + QtCore.QFile("core_plugins:reference/ReferenceAction.qml").fileName()
        )

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_actions(self) -> LabelValueSelectionModel:
        # Discover all actions that are an ancestor of the present action.
        ancestor_action_ids = []
        queue = [self._data.id]
        while len(queue) > 0:
            current_id = queue.pop(0)
            action_ids = [
                action.id
                for action in self.library.actions_by_predicate(
                    lambda candidate, child_id=current_id: (
                        child_id in [child.id for child in candidate.get_actions()[0]]
                    )
                )
            ]
            ancestor_action_ids.extend(action_ids)
            queue.extend(action_ids)

        # Predicate to select only valid actions to show in the reference
        # list. Excludes all actions that:
        # - result in circular inclusions
        # - are of an incompatible input type
        # - are a reference action
        # - are a root action
        def selector(action: AbstractActionData) -> bool:
            # Only consider actions that are of a valid type.
            if action.tag in ["reference", "root"]:
                return False
            if action.behavior_type != self.input_type:
                return False

            # Reject all actions that would result in a loop.
            return not (action.id in ancestor_action_ids)

        # Order bound inputs by mode, device, and input.
        input_entries = []
        for device_guid, input_items in shared_state.current_profile.inputs.items():
            for input_item in input_items:
                if not input_item.action_sequences:
                    continue
                device_name, input_name = device_and_input_names(
                    device_guid, input_item.input_type, input_item.input_id
                )
                input_entries.append(
                    (input_item.mode, device_guid, device_name, input_name, input_item)
                )
        input_entries.sort(
            key=lambda entry: (
                natural_key(entry[0]),
                natural_key(entry[2]),
                str(entry[1]),
                natural_key(entry[3]),
            )
        )

        # Each action is listed once, under the first input it is reachable from.
        labels = []
        actions = []
        seen_ids = set()
        for mode, _, device_name, input_name, input_item in input_entries:
            prefix = f"[{mode}] {device_name} - {input_name} › "
            for binding in input_item.action_sequences:
                # Children push order reversed so they pop in their original order.
                pending = [binding.root_action]
                while pending:
                    action = pending.pop()
                    pending.extend(reversed(action.get_actions()[0]))
                    if action.id in seen_ids or not selector(action):
                        continue
                    seen_ids.add(action.id)
                    labels.append(prefix + action.action_label)
                    actions.append(action)

        # Actions not reachable from any input go last.
        unbound_actions = sorted(
            self.library.actions_by_predicate(
                lambda action: action.id not in seen_ids and selector(action)
            ),
            key=lambda action: natural_key(action.action_label),
        )
        labels.extend(action.action_label for action in unbound_actions)
        actions.extend(unbound_actions)

        return LabelValueSelectionModel(
            labels,
            [str(action.id) for action in actions],
            bootstrap=[action.icon for action in actions],
            parent=self,
        )

    @QtCore.Slot(str)
    def referenceAction(self, value: str) -> None:
        self._replace_reference(self.library.get_action(uuid.UUID(value)))

    @QtCore.Slot(str)
    def duplicateAction(self, value: str) -> None:
        # Retrieve action and duplicate it before adding it to the tree.
        action = self.library.get_action(uuid.UUID(value)).clone()
        self.library.add_action(action)
        self._replace_reference(action)

    def _replace_reference(self, action: AbstractActionData) -> None:
        # Read before remove_action replaces every ActionModel behind this binding.
        enumeration_index = self._binding_model.parent().enumeration_index

        # Replace reference action with the provided action.
        self._binding_model.append_action(action, self.sequence_index)
        self._binding_model.remove_action(self.sequence_index)

        # Delete the reference action itself.
        self.library.delete_action(self._data.id)
        _emit_input_item_changed_later(enumeration_index)

    actions = QtCore.Property(
        LabelValueSelectionModel, fget=_get_actions, notify=modelChanged
    )


class ReferenceData(AbstractActionData):
    """Data for the library reference action."""

    version = 1
    name = "Reference"
    tag = "reference"
    icon = "\uf470"

    functor = None
    model = ReferenceModel

    properties = (ActionProperty.ActivateDisabled,)
    input_types = (
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard,
    )

    def __init__(self, behavior_type: InputType = InputType.JoystickButton) -> None:
        super().__init__(behavior_type)

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        pass

    @override
    def _to_xml(self) -> ElementTree.Element:
        return ElementTree.Element("")

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return [
            UserFeedback(
                UserFeedback.FeedbackType.Error,
                "Always invalid, use to insert an existing action into the profile.",
            )
        ]

    @override
    def _valid_selectors(self) -> list[str]:
        return []

    @override
    def _get_container(self, selector: str) -> list[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self, old_behavior: InputType, new_behavior: InputType
    ) -> None:
        pass


create = ReferenceData
