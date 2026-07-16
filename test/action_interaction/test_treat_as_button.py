# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.types import HatDirection

from . import input_definitions as inout
from .conftest import JoystickGremlinBot


def test_axis_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    assert not jgbot.button(inout.OUT_BUTTON_1)
    assert jgbot.axis(inout.IN_AXIS_1) == 0.0
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.20)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.30)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.80)
    assert not jgbot.button(inout.OUT_BUTTON_1)


def test_axis_edge_below(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.2499)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.25)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.75)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.75001)
    assert not jgbot.button(inout.OUT_BUTTON_1)


def test_axis_edge_above(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.7501)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.75)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.25)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.24999)
    assert not jgbot.button(inout.OUT_BUTTON_1)


def test_hat_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.North)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.East)
    assert not jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.South)
    assert jgbot.button(inout.OUT_BUTTON_1)
    jgbot.set_hat_direction(inout.IN_HAT_1, HatDirection.Center)
    assert not jgbot.button(inout.OUT_BUTTON_1)
