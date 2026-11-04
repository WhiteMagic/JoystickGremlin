# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.types import HatDirection

from .conftest import JoystickGremlinBot


def test_button_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert not jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")

    jgbot.press_button("Input Button 1")
    assert jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")
    jgbot.release_button("Input Button 1")
    assert not jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")


def test_button_hold(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert not jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")

    jgbot.hold_button("Input Button 1", 0.5)
    assert jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")
    jgbot.wait(0.4)
    assert jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")
    jgbot.wait(0.2)
    assert not jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")


def test_button_tap(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert not jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")

    # The duration of a tap is 0.1 seconds, thus the following checks ensure
    # that the button is held for approximately that long.
    jgbot.tap_button("Input Button 1")
    assert not jgbot.button("Input Button 1")
    assert not jgbot.button("Input Button 2")


def test_axis_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.axis("Input Axis 1") == 0.0
    assert jgbot.axis("Input Axis 2") == 0.0
    jgbot.set_axis_absolute("Input Axis 1", 0.5)
    assert jgbot.axis("Input Axis 1") == 0.5
    assert jgbot.axis("Input Axis 2") == 0.0


def test_axis_relative(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.axis("Input Axis 1") == 0.0
    assert jgbot.axis("Input Axis 2") == 0.0
    jgbot.set_axis_relative("Input Axis 1", 0.3)
    assert jgbot.axis("Input Axis 1") == 0.3
    assert jgbot.axis("Input Axis 2") == 0.0
    jgbot.set_axis_relative("Input Axis 1", -0.5)
    assert jgbot.axis("Input Axis 1") == -0.2
    assert jgbot.axis("Input Axis 2") == 0.0
    jgbot.set_axis_relative("Input Axis 1", -0.9)
    assert jgbot.axis("Input Axis 1") == -1.0
    assert jgbot.axis("Input Axis 2") == 0.0


def test_hat_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "template.xml")

    assert jgbot.hat("Input Hat 1") == HatDirection.Center
    assert jgbot.hat("Input Hat 2") == HatDirection.Center
    jgbot.set_hat_direction("Input Hat 1", HatDirection.North)
    assert jgbot.hat("Input Hat 1") == HatDirection.North
    assert jgbot.hat("Input Hat 2") == HatDirection.Center
