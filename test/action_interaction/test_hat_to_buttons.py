# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from gremlin.types import HatDirection

from .conftest import JoystickGremlinBot


def test_basic(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.North
    )
    assert jgbot.button("out_north_south")
    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.Center
    )
    assert not jgbot.button("out_north_south")
    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.East
    )
    assert jgbot.button("out_east")
    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.Center
    )
    assert not jgbot.button("out_east")

    # Ensure no additional events are generated.
    jgbot.clear_events()
    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.West
    )
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_transition(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.North
    )
    assert jgbot.button("out_north_south")
    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.East
    )
    assert not jgbot.button("out_north_south")
    assert jgbot.button("out_east")
    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.Center
    )
    assert not jgbot.button("out_north_south")
    assert not jgbot.button("out_east")


def test_transition_multiple(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "hat_to_buttons.xml")

    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.North
    )
    assert jgbot.button("out_north_south")
    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.South
    )
    assert jgbot.button("out_north_south")
    jgbot.set_hat_direction(
        "Hat Buttons - N,S: out_north_south, E: out_east", HatDirection.East
    )
    assert not jgbot.button("out_north_south")
    assert jgbot.button("out_east")
