# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from . import input_definitions as inout
from .conftest import JoystickGremlinBot


def test_split(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "split_axis.xml")

    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.0)
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(0.3333, abs=0.01)
    assert jgbot.axis(inout.OUT_AXIS_2) == 0.0

    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.499)
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(1.0, abs=0.01)
    assert jgbot.axis(inout.OUT_AXIS_2) == 0.0

    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.5)
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(1.0, abs=0.01)
    assert jgbot.axis(inout.OUT_AXIS_2) == pytest.approx(1.0, abs=0.01)

    jgbot.set_axis_absolute(inout.IN_AXIS_1, 0.75)
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(1.0, abs=0.01)
    assert jgbot.axis(inout.OUT_AXIS_2) == pytest.approx(0.0, abs=0.01)

    jgbot.set_axis_absolute(inout.IN_AXIS_1, 1.0)
    assert jgbot.axis(inout.OUT_AXIS_1) == pytest.approx(1.0, abs=0.01)
    assert jgbot.axis(inout.OUT_AXIS_2) == pytest.approx(-1.0, abs=0.01)
