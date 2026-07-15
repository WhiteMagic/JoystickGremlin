# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.types import HatDirection

from .conftest import JoystickGremlinBot
from .input_definitions import *


def test_button_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.button(IN_BUTTON_1) == False
    assert jgbot.button(IN_BUTTON_2) == False

    jgbot.press_button(IN_BUTTON_1)
    assert jgbot.button(IN_BUTTON_1) == True
    assert jgbot.button(IN_BUTTON_2) == False
    jgbot.release_button(IN_BUTTON_1)
    assert jgbot.button(IN_BUTTON_1) == False
    assert jgbot.button(IN_BUTTON_2) == False


def test_button_hold(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.button(IN_BUTTON_1) == False
    assert jgbot.button(IN_BUTTON_2) == False

    jgbot.hold_button(IN_BUTTON_1, 0.5)
    assert jgbot.button(IN_BUTTON_1) == True
    assert jgbot.button(IN_BUTTON_2) == False
    jgbot.wait(0.4)
    assert jgbot.button(IN_BUTTON_1) == True
    assert jgbot.button(IN_BUTTON_2) == False
    jgbot.wait(0.2)
    assert jgbot.button(IN_BUTTON_1) == False
    assert jgbot.button(IN_BUTTON_2) == False


def test_button_tap(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.button(IN_BUTTON_1) == False
    assert jgbot.button(IN_BUTTON_2) == False

    # The duration of a tap is 0.1 seconds, thus the following checks ensure
    # that the button is held for approximately that long.
    jgbot.tap_button(IN_BUTTON_1)
    assert jgbot.button(IN_BUTTON_1) == False
    assert jgbot.button(IN_BUTTON_2) == False


def test_axis_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.axis(IN_AXIS_1) == 0.0
    assert jgbot.axis(IN_AXIS_2) == 0.0
    jgbot.set_axis_absolute(IN_AXIS_1, 0.5)
    assert jgbot.axis(IN_AXIS_1) == 0.5
    assert jgbot.axis(IN_AXIS_2) == 0.0


def test_axis_relative(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.axis(IN_AXIS_1) == 0.0
    assert jgbot.axis(IN_AXIS_2) == 0.0
    jgbot.set_axis_relative(IN_AXIS_1, 0.3)
    assert jgbot.axis(IN_AXIS_1) == 0.3
    assert jgbot.axis(IN_AXIS_2) == 0.0
    jgbot.set_axis_relative(IN_AXIS_1, -0.5)
    assert jgbot.axis(IN_AXIS_1) == -0.2
    assert jgbot.axis(IN_AXIS_2) == 0.0
    jgbot.set_axis_relative(IN_AXIS_1, -0.9)
    assert jgbot.axis(IN_AXIS_1) == -1.0
    assert jgbot.axis(IN_AXIS_2) == 0.0


def test_hat_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.hat(IN_HAT_1) == HatDirection.Center
    assert jgbot.hat(IN_HAT_2) == HatDirection.Center
    jgbot.set_hat_direction(IN_HAT_1, HatDirection.North)
    assert jgbot.hat(IN_HAT_1) == HatDirection.North
    assert jgbot.hat(IN_HAT_2) == HatDirection.Center
