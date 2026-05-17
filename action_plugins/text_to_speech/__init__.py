# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    List,
    override,
)
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtTextToSpeech import QTextToSpeech

from gremlin import event_handler, util
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
    ActionModel,
    SequenceIndex,
)

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


_tts_engine: QTextToSpeech | None = None


def _get_engine() -> QTextToSpeech:
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = QTextToSpeech()
        voice_name = Configuration().value("action", "tts", "voice")
        if voice_name:
            for voice in _tts_engine.availableVoices():
                if voice.name() == voice_name:
                    _tts_engine.setVoice(voice)
                    break
    return _tts_engine


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

        engine = _get_engine()
        if self.data.interrupt_running:
            engine.stop()
        engine.setRate(self.data.playback_rate / 10.0)
        engine.setVolume(self.data.playback_volume / 100.0)
        engine.setPitch(self.data.playback_pitch / 10.0)
        engine.say(self.data.text)


class TextToSpeechModel(ActionModel):
    textChanged = QtCore.Signal()
    interruptRunningChanged = QtCore.Signal()
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

    def _get_interrupt_running(self) -> bool:
        return self._data.interrupt_running

    def _set_interrupt_running(self, value: bool) -> None:
        if value != self._data.interrupt_running:
            self._data.interrupt_running = value
            self.interruptRunningChanged.emit()

    def _get_playback_rate(self) -> int:
        return self._data.playback_rate

    def _set_playback_rate(self, value: int) -> None:
        if value != self._data.playback_rate:
            self._data.playback_rate = value
            self.playbackRateChanged.emit()

    def _get_playback_volume(self) -> int:
        return self._data.playback_volume

    def _set_playback_volume(self, value: int) -> None:
        if value != self._data.playback_volume:
            self._data.playback_volume = value
            self.playbackVolumeChanged.emit()

    def _get_playback_pitch(self) -> int:
        return self._data.playback_pitch

    def _set_playback_pitch(self, value: int) -> None:
        if value != self._data.playback_pitch:
            self._data.playback_pitch = value
            self.playbackPitchChanged.emit()

    text = QtCore.Property(str, fget=_get_text, fset=_set_text, notify=textChanged)

    interruptRunning = QtCore.Property(
        bool,
        fget=_get_interrupt_running,
        fset=_set_interrupt_running,
        notify=interruptRunningChanged,
    )

    playbackRate = QtCore.Property(
        int,
        fget=_get_playback_rate,
        fset=_set_playback_rate,
        notify=playbackRateChanged,
    )

    playbackVolume = QtCore.Property(
        int,
        fget=_get_playback_volume,
        fset=_set_playback_volume,
        notify=playbackVolumeChanged,
    )

    playbackPitch = QtCore.Property(
        int,
        fget=_get_playback_pitch,
        fset=_set_playback_pitch,
        notify=playbackPitchChanged,
    )


class TextToSpeechData(AbstractActionData):
    version = 1
    name = "Text to Speech"
    tag = "text-to-speech"
    icon = "\uF484"

    functor = TextToSpeechFunctor
    model = TextToSpeechModel

    properties = (ActionProperty.ActivateOnPress,)
    input_types = (InputType.JoystickButton,)

    def __init__(self, behavior_type: InputType = InputType.JoystickButton) -> None:
        super().__init__(behavior_type)

        self.text: str = ""
        self.interrupt_running: bool = True
        self.playback_rate: int = 0
        self.playback_volume: int = 100
        self.playback_pitch: int = 0

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        self._id = util.read_action_id(node)
        self.text = util.read_property(node, "text", PropertyType.String)
        self.interrupt_running = util.read_property(
            node, "interrupt-running", PropertyType.Bool
        )
        self.playback_rate = util.read_property(node, "playback-rate", PropertyType.Int)
        self.playback_volume = util.read_property(
            node, "playback-volume", PropertyType.Int
        )
        self.playback_pitch = util.read_property(
            node, "playback-pitch", PropertyType.Int
        )

    @override
    def _to_xml(self) -> ElementTree.Element:
        node = util.create_action_node(TextToSpeechData.tag, self._id)
        util.append_property_nodes(
            node,
            [
                ["text", self.text, PropertyType.String],
                ["interrupt-running", self.interrupt_running, PropertyType.Bool],
                ["playback-rate", self.playback_rate, PropertyType.Int],
                ["playback-volume", self.playback_volume, PropertyType.Int],
                ["playback-pitch", self.playback_pitch, PropertyType.Int],
            ],
        )
        return node

    @override
    def user_feedback(self) -> List[UserFeedback]:
        if not self.text.strip():
            return [
                UserFeedback(
                    UserFeedback.FeedbackType.Error, "Text field must not be empty."
                )
            ]
        return []

    @override
    def _valid_selectors(self) -> List[str]:
        return []

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self, old_behavior: InputType, new_behavior: InputType
    ) -> None:
        pass


Configuration().register(
    "action",
    "tts",
    "voice",
    PropertyType.String,
    "",
    "Name of the TTS voice to use for all Text to Speech actions.",
    {},
    True,
)

create = TextToSpeechData
