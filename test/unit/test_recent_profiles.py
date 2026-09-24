# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

from pathlib import Path

from gremlin.ui.util import updated_recent_profiles


def test_empty_list(tmp_path: Path) -> None:
    profile = tmp_path / "a.xml"
    assert updated_recent_profiles([], profile, 5) == [str(profile.resolve())]


def test_new_entry_goes_to_front(tmp_path: Path) -> None:
    first = str((tmp_path / "a.xml").resolve())
    second = tmp_path / "b.xml"
    assert updated_recent_profiles([first], second, 5) == [
        str(second.resolve()),
        first,
    ]


def test_existing_entry_moves_to_front(tmp_path: Path) -> None:
    paths = [str((tmp_path / f"{name}.xml").resolve()) for name in "abc"]
    result = updated_recent_profiles(paths, Path(paths[2]), 5)
    assert result == [paths[2], paths[0], paths[1]]


def test_case_and_separator_variants_are_deduplicated(tmp_path: Path) -> None:
    stored = str((tmp_path / "Profile.xml").resolve())
    variant = Path(stored.upper().replace("\\", "/"))
    result = updated_recent_profiles([stored], variant, 5)
    assert len(result) == 1
    assert result[0] == str(variant.resolve())


def test_capped_at_limit(tmp_path: Path) -> None:
    paths = [str((tmp_path / f"{index}.xml").resolve()) for index in range(5)]
    new_profile = tmp_path / "new.xml"
    result = updated_recent_profiles(paths, new_profile, 5)
    assert result == [str(new_profile.resolve()), *paths[:4]]


def test_over_long_list_is_trimmed(tmp_path: Path) -> None:
    paths = [str((tmp_path / f"{index}.xml").resolve()) for index in range(8)]
    result = updated_recent_profiles(paths, Path(paths[0]), 5)
    assert result == paths[:5]
