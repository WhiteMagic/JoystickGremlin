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
    util,
)
from gremlin.audio_player import AudioPlayer
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    InputType,
    PropertyType,
)

from gremlin.ui.action_model import (
    SequenceIndex,
    ActionModel,
)

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


class PlaySoundFunctor(AbstractFunctor):

    """Executes a Play Sound action callback."""

    def __init__(self, action: PlaySoundData) -> None:
        super().__init__(action)

    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: List[ActionProperty]=[]
    ) -> None:
        if not self._should_execute(value):
            return

        AudioPlayer().enqueue(self.data.sound_filename, self.data.sound_volume)


class PlaySoundModel(ActionModel):

    soundFilenameChanged = QtCore.Signal()
    soundVolumeChanged = QtCore.Signal()

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
            "core_plugins:play_sound/PlaySoundAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_sound_filename(self) -> str:
        return self._data.sound_filename

    def _set_sound_filename(self, value: str) -> None:
        if str(value) != self._data.sound_filename:
            self._data.sound_filename = str(value)
            self.soundFilenameChanged.emit()

    def _get_sound_volume(self) -> int:
        return self._data.sound_volume

    def _set_sound_volume(self, value: int) -> None:
        if value != self._data.sound_volume:
            self._data.sound_volume = value
            self.soundVolumeChanged.emit()

    soundFilename = QtCore.Property(
        str,
        fget=_get_sound_filename,
        fset=_set_sound_filename,
        notify=soundFilenameChanged
    )

    soundVolume = QtCore.Property(
        int,
        fget=_get_sound_volume,
        fset=_set_sound_volume,
        notify=soundVolumeChanged
    )


class PlaySoundData(AbstractActionData):

    """Model for the play sound action."""

    version = 1
    name = "Play Sound"
    tag = "play-sound"
    icon = "\uF49E"

    functor = PlaySoundFunctor
    model = PlaySoundModel

    properties = (
        ActionProperty.ActivateOnPress,
    )
    input_types = (
        InputType.JoystickButton,
        InputType.Keyboard,
    )

    def __init__(
            self,
            behavior_type: InputType = InputType.JoystickButton
    ) -> None:
        super().__init__(behavior_type)

        # Model variables
        self.sound_filename: str = ""
        self.sound_volume: int = 50

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)

        self.sound_filename = util.read_property(
            node, "filename", PropertyType.String
        )
        self.sound_volume = util.read_property(
            node, "volume", PropertyType.Int
        )

        if not self.is_valid():
            raise GremlinError(
                f"{self.sound_filename} does not exists or is not accessible."
            )

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(PlaySoundData.tag, self._id)
        util.append_property_nodes(
            node,
            [
                ["filename", self.sound_filename, PropertyType.String],
                ["volume", self.sound_volume, PropertyType.Int],
            ]
        )
        return node

    @override
    def user_feedback(self) -> List[UserFeedback]:
        messages = []
        if not util.file_exists_and_is_accessible(self.sound_filename):
            messages.append(UserFeedback(
                UserFeedback.FeedbackType.Error,
                f"File '{self.sound_filename}' does not exist or is "
                f"not accessible.",
            ))
        return messages

    @override
    def _valid_selectors(self) -> list[str]:
        return []

    @override
    def _get_container(self, selector: str) -> list[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = PlaySoundData
