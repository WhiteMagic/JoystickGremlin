# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING,
    List,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import (
    event_handler,
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


class RunCommandFunctor(AbstractFunctor):
    """Launches an external program in a fire-and-forget manner."""

    def __init__(self, action: RunCommandData) -> None:
        super().__init__(action)

    @override
    def __call__(
        self,
        event: event_handler.Event,
        value: Value,
        properties: List[ActionProperty] = [],
    ) -> None:
        if not self._should_execute(value):
            return

        if not self.data.executable:
            return

        arguments = QtCore.QProcess.splitCommand(self.data.arguments)
        try:
            QtCore.QProcess.startDetached(self.data.executable, arguments)
        except Exception as exception:
            logging.getLogger("system").error(
                f"Failed to run command '{self.data.executable}': {exception}"
            )


class RunCommandModel(ActionModel):
    executableChanged = QtCore.Signal()
    argumentsChanged = QtCore.Signal()

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
            + QtCore.QFile("core_plugins:run_command/RunCommandAction.qml").fileName()
        )

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_executable(self) -> str:
        return self._data.executable

    def _set_executable(self, value: str) -> None:
        if str(value) != self._data.executable:
            self._data.executable = str(value)
            self.executableChanged.emit()

    def _get_arguments(self) -> str:
        return self._data.arguments

    def _set_arguments(self, value: str) -> None:
        if str(value) != self._data.arguments:
            self._data.arguments = str(value)
            self.argumentsChanged.emit()

    executable = QtCore.Property(
        str,
        fget=_get_executable,
        fset=_set_executable,
        notify=executableChanged,
    )

    arguments = QtCore.Property(
        str,
        fget=_get_arguments,
        fset=_set_arguments,
        notify=argumentsChanged,
    )


class RunCommandData(AbstractActionData):
    """Model for the run command action."""

    version = 1
    name = "Run Command"
    tag = "run-command"
    icon = ""

    functor = RunCommandFunctor
    model = RunCommandModel

    properties = (ActionProperty.ActivateOnPress,)
    input_types = (
        InputType.JoystickButton,
        InputType.Keyboard,
    )

    def __init__(self, behavior_type: InputType = InputType.JoystickButton) -> None:
        super().__init__(behavior_type)

        # Model variables
        self.executable: str = ""
        self.arguments: str = ""

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.executable = util.read_property(node, "executable", PropertyType.String)
        self.arguments = util.read_property(node, "arguments", PropertyType.String)

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(RunCommandData.tag, self._id)
        util.append_property_nodes(
            node,
            [
                ["executable", self.executable, PropertyType.String],
                ["arguments", self.arguments, PropertyType.String],
            ],
        )
        return node

    @override
    def user_feedback(self) -> List[UserFeedback]:
        messages = []
        if not self.executable.strip():
            messages.append(
                UserFeedback(
                    UserFeedback.FeedbackType.Error,
                    "No executable specified.",
                )
            )
        return messages

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


create = RunCommandData
