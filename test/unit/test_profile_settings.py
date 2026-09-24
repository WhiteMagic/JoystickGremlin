# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from gremlin.code_runner import resolve_start_mode
from gremlin.config import Configuration
from gremlin.profile import Profile


def _roundtrip_profile(profile: Profile) -> Profile:
    """Serialize profile to a temp file and load it back, then returning
    the new Profile.

    Args:
        profile: The Profile to serialize and reload.

    Returns:
        The reloaded Profile.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "roundtrip.xml"
        profile.to_xml(str(out))
        new_profile = Profile()
        new_profile.from_xml(str(out))
        return new_profile


def test_settings_modifications_roundtrip() -> None:
    p = Profile()
    p.settings.startup_mode = "Default"
    p.settings.macro_default_delay = 0.1
    p.settings.vjoy_as_input = {1: True, 2: False}
    p.settings.set_initial_vjoy_axis_value(1, 0, 0.25)
    p.settings.set_initial_vjoy_axis_value(1, 1, -0.5)
    p.settings.set_initial_vjoy_axis_value(2, 0, 1.0)

    p2 = _roundtrip_profile(p)
    assert p2.settings.startup_mode == "Default"
    assert p2.settings.macro_default_delay == 0.1
    assert p2.settings.vjoy_as_input.get(1) is True
    assert 2 not in p2.settings.vjoy_as_input
    assert p2.settings.get_initial_vjoy_axis_value(1, 0) == 0.25
    assert p2.settings.get_initial_vjoy_axis_value(1, 1) == -0.5
    assert p2.settings.get_initial_vjoy_axis_value(2, 0) == 1.0


def test_vjoy_initial_values_container_behavior() -> None:
    p = Profile()

    assert p.settings.get_initial_vjoy_axis_value(3, 5) == 0.0

    p.settings.set_initial_vjoy_axis_value(3, 5, 0.75)
    assert p.settings.get_initial_vjoy_axis_value(3, 5) == 0.75

    p.settings.set_initial_vjoy_axis_value(3, 5, -0.25)
    assert p.settings.get_initial_vjoy_axis_value(3, 5) == -0.25


def test_startup_mode_follows_rename() -> None:
    p = Profile()
    p.modes.add_mode("Flight")
    p.settings.startup_mode = "Flight"

    p.modes.rename_mode("Flight", "Cruise")
    assert p.settings.startup_mode == "Cruise"


def test_startup_mode_reset_on_delete() -> None:
    p = Profile()
    p.modes.add_mode("Flight")
    p.settings.startup_mode = "Flight"

    p.modes.delete_mode("Flight")
    assert p.settings.startup_mode == "Use Heuristic"


def _profile_with_modes() -> Profile:
    p = Profile()
    p.modes.add_mode("Alpha")
    p.modes.add_mode("Bravo")
    p.fpath = Path("C:/profiles/test.xml")
    return p


@pytest.fixture
def last_modes(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Replaces the stored per-profile last modes with a test-owned dict."""
    stored: dict[str, str] = {}
    cfg = Configuration()
    original_value = cfg.value
    monkeypatch.setattr(
        cfg,
        "value",
        lambda section, group, name: (
            stored
            if name == "last-mode-per-profile"
            else original_value(section, group, name)
        ),
    )
    return stored


def test_resolve_start_mode_explicit(last_modes: dict[str, str]) -> None:
    p = _profile_with_modes()
    p.settings.startup_mode = "Bravo"
    assert resolve_start_mode(p) == "Bravo"


def test_resolve_start_mode_heuristic(last_modes: dict[str, str]) -> None:
    p = _profile_with_modes()
    p.settings.startup_mode = "Use Heuristic"
    last_modes[str(p.fpath)] = "Bravo"
    assert resolve_start_mode(p) == "Alpha"


def test_resolve_start_mode_last_active(last_modes: dict[str, str]) -> None:
    p = _profile_with_modes()
    p.settings.startup_mode = "Last Active"
    last_modes[str(p.fpath)] = "Bravo"
    assert resolve_start_mode(p) == "Bravo"


def test_resolve_start_mode_last_active_fallbacks(
    last_modes: dict[str, str],
) -> None:
    p = _profile_with_modes()
    p.settings.startup_mode = "Last Active"
    assert resolve_start_mode(p) == "Alpha"

    last_modes[str(p.fpath)] = "Deleted"
    assert resolve_start_mode(p) == "Alpha"

    last_modes["None"] = "Bravo"
    p.fpath = None
    assert resolve_start_mode(p) == "Alpha"


def test_load_profile_settings_from_existing_xml(xml_dir: Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / "profile_realistic.xml"))

    assert p.settings.startup_mode == "Default"
