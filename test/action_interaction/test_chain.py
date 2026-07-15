# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import InputType

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)
from .input_definitions import *


def test_cycling_wrap_around(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button(IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, OUT_BUTTON_1, True)
            == jgbot.next_event()
        )
        assert jgbot.button(OUT_BUTTON_1) == True
        jgbot.release_button(IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, OUT_BUTTON_1, False)
            == jgbot.next_event()
        )
        assert jgbot.button(OUT_BUTTON_1) == False

    with subtests.test("Chain 2"):
        jgbot.press_button(IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, OUT_BUTTON_2, True)
            == jgbot.next_event()
        )
        assert jgbot.button(OUT_BUTTON_2) == True
        jgbot.release_button(IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, OUT_BUTTON_2, False)
            == jgbot.next_event()
        )
        assert jgbot.button(OUT_BUTTON_2) == False

    with subtests.test("Chain 3"):
        jgbot.press_button(IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, OUT_BUTTON_3, True)
            == jgbot.next_event()
        )
        assert jgbot.button(OUT_BUTTON_3) == True
        jgbot.release_button(IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, OUT_BUTTON_3, False)
            == jgbot.next_event()
        )
        assert jgbot.button(OUT_BUTTON_3) == False

    with subtests.test("Chain 1"):
        jgbot.press_button(IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, OUT_BUTTON_1, True)
            == jgbot.next_event()
        )
        assert jgbot.button(OUT_BUTTON_1) == True
        jgbot.release_button(IN_BUTTON_1)
        assert (
            EventSpec(InputType.JoystickButton, OUT_BUTTON_1, False)
            == jgbot.next_event()
        )
        assert jgbot.button(OUT_BUTTON_1) == False

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_no_early_timeout(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == False

    # Wait but not long enough for the timeout to trigger.
    jgbot.wait(0.15)

    with subtests.test("Chain 2 after wait"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_2) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_2) == False


def test_timeout_reset(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == False

    # Wait for timeout to expire.
    jgbot.wait(0.3)

    with subtests.test("Chain 1 after timeout"):
        jgbot.press_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == True
        jgbot.release_button(IN_BUTTON_1)
        assert jgbot.button(OUT_BUTTON_1) == False
