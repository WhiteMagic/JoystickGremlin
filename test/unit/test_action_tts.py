# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid
from xml.etree import ElementTree

import pytest

from action_plugins.text_to_speech import TextToSpeechData
from gremlin.profile import Library
from gremlin.types import InputType

_ACTION_TTS_SIMPLE = "action_tts_simple.xml"
_TTS_UUID = uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609")


def test_ctor() -> None:
    a = TextToSpeechData(InputType.JoystickButton)

    assert a.text == ""
    assert a.queue_mode == "queue-back"
    assert a.playback_rate == 0.0
    assert a.playback_volume == 1.0
    assert a.playback_pitch == 0.0


def test_from_xml(xml_dir: pathlib.Path) -> None:
    library = Library()
    a = TextToSpeechData(InputType.JoystickButton)
    a.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_TTS_SIMPLE).read_text()),
        library,
    )

    assert a._id == _TTS_UUID
    assert a.text == "Gear up"
    assert a.queue_mode == "interrupt"
    assert a.playback_rate == pytest.approx(0.2)
    assert a.playback_volume == pytest.approx(0.8)
    assert a.playback_pitch == pytest.approx(-0.3)


def test_to_xml() -> None:
    a = TextToSpeechData(InputType.JoystickButton)
    a._id = _TTS_UUID
    a.text = "Gear up"
    a.queue_mode = "interrupt"
    a.playback_rate = 0.2
    a.playback_volume = 0.8
    a.playback_pitch = -0.3

    node = a._to_xml()

    assert node.attrib["type"] == "text-to-speech"
    assert node.attrib["id"] == str(_TTS_UUID)
    assert node.find("./property/name[.='text']/../value").text == "Gear up"
    assert node.find("./property/name[.='queue-mode']/../value").text == "interrupt"
    assert node.find("./property/name[.='playback-rate']/../value").text == "0.2"
    assert node.find("./property/name[.='playback-volume']/../value").text == "0.8"
    assert node.find("./property/name[.='playback-pitch']/../value").text == "-0.3"


def test_roundtrip(xml_dir: pathlib.Path) -> None:
    library = Library()
    a = TextToSpeechData(InputType.JoystickButton)
    a.from_xml(
        ElementTree.fromstring((xml_dir / _ACTION_TTS_SIMPLE).read_text()),
        library,
    )
    node = a.to_xml()
    assert node is not None

    b = TextToSpeechData(InputType.JoystickButton)
    b.from_xml(node, library)

    assert b.text == a.text
    assert b.queue_mode == a.queue_mode
    assert b.playback_rate == a.playback_rate
    assert b.playback_volume == a.playback_volume
    assert b.playback_pitch == a.playback_pitch


def test_whitespace_preserved() -> None:
    a = TextToSpeechData(InputType.JoystickButton)
    library = Library()
    a.text = "  hello\n  world  "

    node = a.to_xml()
    assert node is not None
    b = TextToSpeechData(InputType.JoystickButton)
    b.from_xml(node, library)

    assert b.text == "  hello\n  world  "


def test_user_feedback_empty_text() -> None:
    a = TextToSpeechData(InputType.JoystickButton)
    a.text = ""

    feedback = a.user_feedback()

    assert len(feedback) == 1
    assert feedback[0].feedback_type == feedback[0].FeedbackType.Error


def test_user_feedback_whitespace_only() -> None:
    a = TextToSpeechData(InputType.JoystickButton)
    a.text = "   \t\n"

    feedback = a.user_feedback()

    assert len(feedback) == 1


def test_user_feedback_valid() -> None:
    a = TextToSpeechData(InputType.JoystickButton)
    a.text = "hello"

    assert a.user_feedback() == []
