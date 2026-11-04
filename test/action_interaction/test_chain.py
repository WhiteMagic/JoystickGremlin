# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import (
    EventSpec,
    JoystickGremlinBot,
)


def test_cycling_wrap_around(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert EventSpec("out_1", True) == jgbot.next_event()
        assert jgbot.button("out_1")
        jgbot.release_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert EventSpec("out_1", False) == jgbot.next_event()
        assert not jgbot.button("out_1")

    with subtests.test("Chain 2"):
        jgbot.press_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert EventSpec("out_2", True) == jgbot.next_event()
        assert jgbot.button("out_2")
        jgbot.release_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert EventSpec("out_2", False) == jgbot.next_event()
        assert not jgbot.button("out_2")

    with subtests.test("Chain 3"):
        jgbot.press_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert EventSpec("out_3", True) == jgbot.next_event()
        assert jgbot.button("out_3")
        jgbot.release_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert EventSpec("out_3", False) == jgbot.next_event()
        assert not jgbot.button("out_3")

    with subtests.test("Chain 1"):
        jgbot.press_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert EventSpec("out_1", True) == jgbot.next_event()
        assert jgbot.button("out_1")
        jgbot.release_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert EventSpec("out_1", False) == jgbot.next_event()
        assert not jgbot.button("out_1")

    # Ensure no additional events are generated.
    with pytest.raises(jgbot.qtbot.TimeoutError):
        jgbot.next_event()


def test_no_early_timeout(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert jgbot.button("out_1")
        jgbot.release_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert not jgbot.button("out_1")

    # Wait but not long enough for the timeout to trigger.
    jgbot.wait(0.15)

    with subtests.test("Chain 2 after wait"):
        jgbot.press_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert jgbot.button("out_2")
        jgbot.release_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert not jgbot.button("out_2")


def test_timeout_reset(
    jgbot: JoystickGremlinBot, profile_dir: Path, subtests: pytest.Subtests
) -> None:
    jgbot.load_profile(profile_dir / "chain.xml")

    with subtests.test("Chain 1"):
        jgbot.press_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert jgbot.button("out_1")
        jgbot.release_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert not jgbot.button("out_1")

    # Wait for timeout to expire.
    jgbot.wait(0.3)

    with subtests.test("Chain 1 after timeout"):
        jgbot.press_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert jgbot.button("out_1")
        jgbot.release_button("Chain timeout 0.2 1: out_1 2: out_2 3: out_3")
        assert not jgbot.button("out_1")
