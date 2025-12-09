# -*- coding: utf-8; -*-

# Copyright (C) 2025 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


from __future__ import annotations

from pathlib import Path
import tempfile

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


def test_settings_defaults_roundtrip() -> None:
    p = Profile()
    assert p.settings.startup_mode == "Use Heuristic"
    assert p.settings.macro_default_delay == 0.05
    assert p.settings.vjoy_as_input == {}
    assert p.settings.vjoy_initial_values == {}

    p2 = _roundtrip_profile(p)
    assert p2.settings.startup_mode == "Use Heuristic"
    assert p2.settings.macro_default_delay == p.settings.macro_default_delay
    assert p2.settings.vjoy_as_input == {}
    assert p2.settings.vjoy_initial_values == {}


def test_settings_modifications_roundtrip() -> None:
    p = Profile()
    p.settings.startup_mode = "Default"
    p.settings.macro_default_delay = 0.1
    p.settings.vjoy_as_input = {1: True, 2: False}
    p.settings.set_initial_vjoy_axis_value(1, 0, 0.25)
    p.settings.set_initial_vjoy_axis_value(1, 1, -0.5)
    p.settings.set_initial_vjoy_axis_value(2, 0, 1.0)

    assert p.settings.startup_mode == "Default"
    assert p.settings.macro_default_delay == 0.1
    assert p.settings.vjoy_as_input.get(1) is True
    assert p.settings.vjoy_as_input.get(2, False) is False
    assert p.settings.get_initial_vjoy_axis_value(1, 0) == 0.25
    assert p.settings.get_initial_vjoy_axis_value(1, 1) == -0.5
    assert p.settings.get_initial_vjoy_axis_value(2, 0) == 1.0

    p2 = _roundtrip_profile(p)
    assert p2.settings.startup_mode == "Default"
    assert p2.settings.macro_default_delay == 0.1
    assert p2.settings.vjoy_as_input.get(1) is True
    assert p2.settings.vjoy_as_input.get(2, False) is False
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


def test_load_profile_settings_from_existing_xml(xml_dir: Path) -> None:
    xml_path = xml_dir / "profile_realistic.xml"
    assert xml_path.exists(), "Expected sample XML profile to exist"

    p = Profile()
    p.from_xml(str(xml_path))

    assert p.settings.startup_mode == "Default"
    assert p.settings.macro_default_delay == 0.05

    assert p.settings.vjoy_as_input == {}
    assert p.settings.vjoy_initial_values == {}
