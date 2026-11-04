# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.types import HatDirection

from .conftest import JoystickGremlinBot


def test_simple(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "remap_basic.xml")

    jgbot.press_button("Map to out_button")
    assert jgbot.button("out_button")
    jgbot.release_button("Map to out_button")
    assert not jgbot.button("out_button")

    jgbot.set_axis_absolute("Map to out_axis", 0.5)
    assert jgbot.axis("out_axis") == 0.5
    jgbot.set_axis_absolute("Map to out_axis", -0.5)
    assert jgbot.axis("out_axis") == -0.5

    jgbot.set_hat_direction("Map to out_hat", HatDirection.NorthWest)
    assert jgbot.hat("out_hat") == HatDirection.NorthWest
    jgbot.set_hat_direction("Map to out_hat", HatDirection.SouthEast)
    assert jgbot.hat("out_hat") == HatDirection.SouthEast


def test_button_advanced(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "remap_basic.xml")

    jgbot.tap_button("Map to out_button")
    assert not jgbot.button("out_button")

    jgbot.hold_button("Map to out_button", 0.5)
    assert jgbot.button("out_button")
    jgbot.wait(0.4)
    assert jgbot.button("out_button")
    jgbot.wait(0.2)
    assert not jgbot.button("out_button")

    jgbot.set_axis_absolute("Map to out_axis", 0.1)
    assert jgbot.axis("out_axis") == 0.1
    jgbot.set_axis_relative("Map to out_axis", -0.2)
    assert jgbot.axis("out_axis") == -0.1


def test_remap_inverse(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "remap_invert.xml")

    jgbot.press_button("Map inverted to out_button")
    assert not jgbot.button("out_button")
    jgbot.release_button("Map inverted to out_button")
    assert jgbot.button("out_button")
