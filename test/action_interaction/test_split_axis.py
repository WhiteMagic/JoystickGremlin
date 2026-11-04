# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import JoystickGremlinBot


def test_split(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "split_axis.xml")

    jgbot.set_axis_absolute("Split 0.5: out_lower, out_upper", 0.0)
    assert jgbot.axis("out_lower") == pytest.approx(0.3333, abs=0.01)
    assert jgbot.axis("out_upper") == 0.0

    jgbot.set_axis_absolute("Split 0.5: out_lower, out_upper", 0.499)
    assert jgbot.axis("out_lower") == pytest.approx(1.0, abs=0.01)
    assert jgbot.axis("out_upper") == 0.0

    jgbot.set_axis_absolute("Split 0.5: out_lower, out_upper", 0.5)
    assert jgbot.axis("out_lower") == pytest.approx(1.0, abs=0.01)
    assert jgbot.axis("out_upper") == pytest.approx(1.0, abs=0.01)

    jgbot.set_axis_absolute("Split 0.5: out_lower, out_upper", 0.75)
    assert jgbot.axis("out_lower") == pytest.approx(1.0, abs=0.01)
    assert jgbot.axis("out_upper") == pytest.approx(0.0, abs=0.01)

    jgbot.set_axis_absolute("Split 0.5: out_lower, out_upper", 1.0)
    assert jgbot.axis("out_lower") == pytest.approx(1.0, abs=0.01)
    assert jgbot.axis("out_upper") == pytest.approx(-1.0, abs=0.01)
