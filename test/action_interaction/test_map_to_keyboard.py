# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path

from gremlin.input_cache import Keyboard

from . import input_definitions as inout
from .conftest import JoystickGremlinBot

# def test_bm_key_press_rountrip(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
#     jgbot.load_profile(profile_dir / "map_to_keyboard.xml")

#     key = keyboard.key_from_name("esc")
#     timing_data = []
#     for _ in range(1000):
#         macro.send_key_down(key)
#         start_time = time.perf_counter()
#         while not Keyboard().is_pressed(key):
#             jgbot.wait(0.01)
#         timing_data.append(time.perf_counter() - start_time)
#         macro.send_key_up(key)

#     print(f"Min   : {min(timing_data)*1e6:.2f} us")
#     print(f"Median: {statistics.median(timing_data)*1e6:.2f} us")
#     print(f"Max   : {max(timing_data)*1e6:.2f} us")
#     print(f"Stddev: {statistics.stdev(timing_data)*1e6:.2f} us")

#     # assert False


def test_single_key(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "map_to_keyboard.xml")
    Keyboard()._keyboard_state = {}

    assert not Keyboard().is_pressed("k")
    jgbot.press_button(inout.IN_BUTTON_1)
    jgbot.wait(0.01)
    assert Keyboard().is_pressed("k")
    jgbot.release_button(inout.IN_BUTTON_1)
    jgbot.wait(0.01)
    assert not Keyboard().is_pressed("k")


def test_key_combination(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "map_to_keyboard.xml")

    assert not Keyboard().is_pressed("right shift2")
    assert not Keyboard().is_pressed("m")

    jgbot.press_button(inout.IN_BUTTON_2)
    jgbot.wait(0.01)
    assert Keyboard().is_pressed("right shift2")
    assert Keyboard().is_pressed("m")

    jgbot.release_button(inout.IN_BUTTON_2)
    jgbot.wait(0.01)
    assert not Keyboard().is_pressed("right shift2")
    assert not Keyboard().is_pressed("m")


def test_sequential(jgbot: JoystickGremlinBot, profile_dir: Path) -> None:
    jgbot.load_profile(profile_dir / "map_to_keyboard.xml")
    Keyboard()._keyboard_state = {}

    assert not Keyboard().is_pressed("o")
    jgbot.tap_button(inout.IN_BUTTON_3)
    jgbot.wait(0.01)
    print(Keyboard()._keyboard_state)
    assert Keyboard().is_pressed("o")
    jgbot.tap_button(inout.IN_BUTTON_3)
    jgbot.wait(0.01)
    assert not Keyboard().is_pressed("o")
    jgbot.tap_button(inout.IN_BUTTON_3)
    jgbot.wait(0.01)
    assert Keyboard().is_pressed("o")
    jgbot.tap_button(inout.IN_BUTTON_3)
    jgbot.wait(0.01)
    assert not Keyboard().is_pressed("o")
