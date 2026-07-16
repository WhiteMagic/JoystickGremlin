# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import InputType

from . import input_definitions as inout
from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_cycling_wrap_around(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button(inout.IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
            == jgbot.next_event()
        )
        assert jgbot.button(inout.OUT_BUTTON_1)
        jgbot.release_button(inout.IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
            == jgbot.next_event()
        )
        assert not jgbot.button(inout.OUT_BUTTON_1)

    with subtests.test("Chain 2"):
        jgbot.press_button(inout.IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, True)
            == jgbot.next_event()
        )
        assert jgbot.button(inout.OUT_BUTTON_2)
        jgbot.release_button(inout.IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_2, False)
            == jgbot.next_event()
        )
        assert not jgbot.button(inout.OUT_BUTTON_2)

    with subtests.test("Chain 3"):
        jgbot.press_button(inout.IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_3, True)
            == jgbot.next_event()
        )
        assert jgbot.button(inout.OUT_BUTTON_3)
        jgbot.release_button(inout.IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_3, False)
            == jgbot.next_event()
        )
        assert not jgbot.button(inout.OUT_BUTTON_3)

    with subtests.test("Chain 1"):
        jgbot.press_button(inout.IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, True)
            == jgbot.next_event()
        )
        assert jgbot.button(inout.OUT_BUTTON_1)
        jgbot.release_button(inout.IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, inout.OUT_BUTTON_1, False)
            == jgbot.next_event()
        )
        assert not jgbot.button(inout.OUT_BUTTON_1)

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_no_early_timeout(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button(inout.IN_BUTTON_1)
        assert jgbot.button(inout.OUT_BUTTON_1)
        jgbot.release_button(inout.IN_BUTTON_1)
        assert not jgbot.button(inout.OUT_BUTTON_1)

    # Wait but not long enough for the timeout to trigger.
    jgbot.wait(0.15)

    with subtests.test("Chain 2 after wait"):
        jgbot.press_button(inout.IN_BUTTON_1)
        assert jgbot.button(inout.OUT_BUTTON_2)
        jgbot.release_button(inout.IN_BUTTON_1)
        assert not jgbot.button(inout.OUT_BUTTON_2)


def test_timeout_reset(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button(inout.IN_BUTTON_1)
        assert jgbot.button(inout.OUT_BUTTON_1)
        jgbot.release_button(inout.IN_BUTTON_1)
        assert not jgbot.button(inout.OUT_BUTTON_1)

    # Wait for timeout to expire.
    jgbot.wait(0.3)

    with subtests.test("Chain 1 after timeout"):
        jgbot.press_button(inout.IN_BUTTON_1)
        assert jgbot.button(inout.OUT_BUTTON_1)
        jgbot.release_button(inout.IN_BUTTON_1)
        assert not jgbot.button(inout.OUT_BUTTON_1)
