# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from string import Template
from typing import (
    TYPE_CHECKING,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore

from gremlin import (
    event_handler,
    mode_manager,
    tts,
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


class TextToSpeechFunctor(AbstractFunctor):
    def __init__(self, action: TextToSpeechData) -> None:
        super().__init__(action)

    @override
    def __call__(
        self,
        event: event_handler.Event,
        value: Value,
        properties: list[ActionProperty] = [],
    ) -> None:
        if not self._should_execute(value):
            return

        substitutions = {"current_mode": mode_manager.ModeManager().current.name}
        tts.TTSManager().enqueue(
            tts.TTSRequest(
                text=Template(self.data.text).safe_substitute(substitutions),
                rate=self.data.playback_rate,
                volume=self.data.playback_volume,
                pitch=self.data.playback_pitch,
            ),
            tts.TTSQueueMode(self.data.queue_mode),
        )


class TextToSpeechModel(ActionModel):
    textChanged = QtCore.Signal()
    queueModeChanged = QtCore.Signal()
    playbackRateChanged = QtCore.Signal()
    playbackVolumeChanged = QtCore.Signal()
    playbackPitchChanged = QtCore.Signal()

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
            + QtCore.QFile(
                "core_plugins:text_to_speech/TextToSpeechAction.qml"
            ).fileName()
        )

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    def _get_text(self) -> str:
        return self._data.text

    def _set_text(self, value: str) -> None:
        if value != self._data.text:
            self._data.text = value
            self.textChanged.emit()

    def _get_queue_mode(self) -> str:
        return self._data.queue_mode

    def _set_queue_mode(self, value: str) -> None:
        if value != self._data.queue_mode:
            self._data.queue_mode = value
            self.queueModeChanged.emit()

    def _get_playback_rate(self) -> float:
        return self._data.playback_rate

    def _set_playback_rate(self, value: float) -> None:
        if value != self._data.playback_rate:
            self._data.playback_rate = value
            self.playbackRateChanged.emit()

    def _get_playback_volume(self) -> float:
        return self._data.playback_volume

    def _set_playback_volume(self, value: float) -> None:
        if value != self._data.playback_volume:
            self._data.playback_volume = value
            self.playbackVolumeChanged.emit()

    def _get_playback_pitch(self) -> float:
        return self._data.playback_pitch

    def _set_playback_pitch(self, value: float) -> None:
        if value != self._data.playback_pitch:
            self._data.playback_pitch = value
            self.playbackPitchChanged.emit()

    text = QtCore.Property(str, fget=_get_text, fset=_set_text, notify=textChanged)

    queueMode = QtCore.Property(
        str,
        fget=_get_queue_mode,
        fset=_set_queue_mode,
        notify=queueModeChanged,
    )

    playbackRate = QtCore.Property(
        float,
        fget=_get_playback_rate,
        fset=_set_playback_rate,
        notify=playbackRateChanged,
    )

    playbackVolume = QtCore.Property(
        float,
        fget=_get_playback_volume,
        fset=_set_playback_volume,
        notify=playbackVolumeChanged,
    )

    playbackPitch = QtCore.Property(
        float,
        fget=_get_playback_pitch,
        fset=_set_playback_pitch,
        notify=playbackPitchChanged,
    )


class TextToSpeechData(AbstractActionData):
    version = 1
    name = "Text to Speech"
    tag = "text-to-speech"
    icon = "\uf484"

    functor = TextToSpeechFunctor
    model = TextToSpeechModel

    properties = (ActionProperty.ActivateOnPress,)
    input_types = (InputType.JoystickButton,)

    def __init__(self, behavior_type: InputType = InputType.JoystickButton) -> None:
        super().__init__(behavior_type)

        self.text: str = ""
        self.queue_mode: str = tts.TTSQueueMode.QueueBack
        self.playback_rate: float = 0.0
        self.playback_volume: float = 1.0
        self.playback_pitch: float = 0.0

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.text = util.read_property(node, "text", PropertyType.String)
        self.queue_mode = util.read_property(
            node, "queue-mode", PropertyType.String
        )
        self.playback_rate = util.read_property(
            node, "playback-rate", PropertyType.Float
        )
        self.playback_volume = util.read_property(
            node, "playback-volume", PropertyType.Float
        )
        self.playback_pitch = util.read_property(
            node, "playback-pitch", PropertyType.Float
        )

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(TextToSpeechData.tag, self._id)
        util.append_property_nodes(
            node,
            [
                ["text", self.text, PropertyType.String],
                ["queue-mode", self.queue_mode, PropertyType.String],
                ["playback-rate", self.playback_rate, PropertyType.Float],
                ["playback-volume", self.playback_volume, PropertyType.Float],
                ["playback-pitch", self.playback_pitch, PropertyType.Float],
            ],
        )
        return node

    @override
    def user_feedback(self) -> list[UserFeedback]:
        if not self.text.strip():
            return [
                UserFeedback(
                    UserFeedback.FeedbackType.Error, "Text field must not be empty."
                )
            ]
        return []

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


create = TextToSpeechData
