# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import HatDirection

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_axis_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    assert not jgbot.button("out_button")
    assert jgbot.axis("Axis Button 0.25-0.75: out_button") == 0.0
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.20)
    assert not jgbot.button("out_button")
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.30)
    assert jgbot.button("out_button")
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.80)
    assert not jgbot.button("out_button")


def test_axis_edge_below(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.2499)
    assert not jgbot.button("out_button")
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.25)
    assert jgbot.button("out_button")
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.75)
    assert jgbot.button("out_button")
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.75001)
    assert not jgbot.button("out_button")


def test_axis_edge_above(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.7501)
    assert not jgbot.button("out_button")
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.75)
    assert jgbot.button("out_button")
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.25)
    assert jgbot.button("out_button")
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", 0.24999)
    assert not jgbot.button("out_button")


@pytest.mark.parametrize(
    ("start", "end"),
    [
        pytest.param(0.0, 1.0, id="from below"),
        pytest.param(1.0, 0.0, id="from above"),
    ],
)
def test_axis_skips_across_range_pulses(
    jgbot: JoystickGremlinBot, profile_dir: Path, start: float, end: float
) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", start)
    jgbot.set_axis_absolute("Axis Button 0.25-0.75: out_button", end)

    assert EventSpec("out_button", True) == jgbot.next_event()
    assert EventSpec("out_button", False) == jgbot.next_event()
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_hat_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "treat_as_button.xml")

    assert not jgbot.button("out_button")
    jgbot.set_hat_direction("Hat Button N,S: out_button", HatDirection.North)
    assert jgbot.button("out_button")
    jgbot.set_hat_direction("Hat Button N,S: out_button", HatDirection.East)
    assert not jgbot.button("out_button")
    jgbot.set_hat_direction("Hat Button N,S: out_button", HatDirection.South)
    assert jgbot.button("out_button")
    jgbot.set_hat_direction("Hat Button N,S: out_button", HatDirection.Center)
    assert not jgbot.button("out_button")
