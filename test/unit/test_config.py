# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import tempfile
from collections.abc import Iterator
from unittest import mock

import pytest

import gremlin.config
import gremlin.error
import gremlin.types
from gremlin.common import SingletonMetaclass
from gremlin.types import PropertyType

# Regular expressions are tried sorted by executable, the order listed here.
AUTO_LOADING_ENTRIES = [
    ["unassigned.xml", "", True, False],
    ["typo.xml", "*Squadrons.exe", True, False],
    ["desktop.xml", "C:/Games/Elite/EliteDangerous64.exe", True, True],
    ["dcs.xml", r"DCS World.*/bin/DCS\.exe$", True, False],
    ["star_citizen.xml", r"StarCitizen/\w+/Bin64/StarCitizen\.exe$", True, False],
]


@pytest.fixture
def cfg() -> Iterator[gremlin.config.Configuration]:
    """Returns a Configuration object other than the singleton, with file path
    modified."""
    # Remove the singleton instance if it exists and create a temporary file
    # to use as the config file. The old config file name and instance are
    # stored to be restored when the fixutre is torn down.
    original_path = gremlin.config._config_file_path
    original_instance = SingletonMetaclass._instances.pop(
        gremlin.config.Configuration, None
    )
    with mock.patch.object(gremlin.config, "_config_file_path", tempfile.mkstemp()[1]):
        try:
            yield gremlin.config.Configuration()
        finally:
            # A fresh instance lacks import-time registrations and gets purged.
            gremlin.config._config_file_path = original_path
            SingletonMetaclass._instances.pop(gremlin.config.Configuration, None)
            if original_instance is not None:
                SingletonMetaclass._instances[gremlin.config.Configuration] = (
                    original_instance
                )


def _register_auto_loading_entries(
    cfg: gremlin.config.Configuration, entries: list[list[str | bool]]
) -> None:
    """Stores entries of the form [profile, executable, enabled, is_default]."""
    cfg.register(
        "profile",
        "automation",
        "entries-auto-loading",
        PropertyType.List,
        entries,
        "",
        {},
    )


def test_load_save(cfg: gremlin.config.Configuration) -> None:
    cfg.register(
        "test", "case", "1", PropertyType.Int, 42, "one", {"min": 1, "max": 20}
    )
    cfg.register("test", "case", "2", PropertyType.Bool, False, "two", {}, True)
    cfg.register(
        "test",
        "case",
        "3",
        PropertyType.HatDirection,
        gremlin.types.HatDirection.NorthEast,
        "",
        {},
    )
    cfg.register("test", "case", "4", PropertyType.List, [1, 2, 3, 4, 5], "", {})
    assert cfg.value("test", "case", "1") == 42
    assert cfg.description("test", "case", "1") == "one"
    assert not cfg.expose("test", "case", "1")

    assert not cfg.value("test", "case", "2")
    assert cfg.description("test", "case", "2") == "two"
    assert cfg.expose("test", "case", "2")

    assert cfg.value("test", "case", "3") == gremlin.types.HatDirection.NorthEast
    assert cfg.description("test", "case", "3") == ""
    assert not cfg.expose("test", "case", "3")

    assert cfg.value("test", "case", "4") == [1, 2, 3, 4, 5]
    assert cfg.description("test", "case", "4") == ""
    assert not cfg.expose("test", "case", "4")

    cfg.save()
    with mock.patch.object(cfg, cfg._should_skip_reload.__name__, return_value=False):
        cfg.load()

    assert cfg.value("test", "case", "1") == 42
    assert not cfg.expose("test", "case", "1")

    assert not cfg.value("test", "case", "2")
    assert cfg.expose("test", "case", "2")

    assert cfg.value("test", "case", "3") == gremlin.types.HatDirection.NorthEast
    assert not cfg.expose("test", "case", "3")

    assert cfg.value("test", "case", "4") == [1, 2, 3, 4, 5]
    assert not cfg.expose("test", "case", "4")


def test_dict_roundtrip(cfg: gremlin.config.Configuration) -> None:
    cfg.register("test", "case", "dict", PropertyType.Dict, {}, "", {})
    assert cfg.value("test", "case", "dict") == {}

    cfg.set("test", "case", "dict", {"C:/profile.xml": "Flight"})
    cfg.save()
    with mock.patch.object(cfg, cfg._should_skip_reload.__name__, return_value=False):
        cfg.load()

    assert cfg.value("test", "case", "dict") == {"C:/profile.xml": "Flight"}
    assert cfg.data_type("test", "case", "dict") == PropertyType.Dict
    with pytest.raises(gremlin.error.GremlinError):
        cfg.set("test", "case", "dict", ["not", "a", "dict"])


def test_exceptions(cfg: gremlin.config.Configuration) -> None:
    cfg.register("test", "case", "1", PropertyType.Int, 42, "", {"min": 1, "max": 20})
    with pytest.raises(gremlin.error.GremlinError):
        cfg.set("test", "case", "1", 3.14)

    with pytest.raises(gremlin.error.GremlinError):
        cfg.set("test", "some", "other", "test")

    with pytest.raises(gremlin.error.GremlinError):
        cfg.value("does", "not", "exist")


@pytest.mark.parametrize(
    ("executable", "expected"),
    [
        ("C:/Games/DCS World OpenBeta/bin/DCS.exe", "dcs.xml"),
        ("D:/RSI/StarCitizen/PTU/Bin64/StarCitizen.exe", "star_citizen.xml"),
        ("C:/Games/Elite/EliteDangerous64.exe", None),
        ("C:/Windows/explorer.exe", None),
    ],
    ids=[
        "after-invalid-regex",
        "after-non-matching-regex",
        "executable-of-default-entry",
        "no-matching-entry",
    ],
)
def test_profile_lookup_by_executable(
    cfg: gremlin.config.Configuration, executable: str, expected: str | None
) -> None:
    _register_auto_loading_entries(cfg, AUTO_LOADING_ENTRIES)

    assert gremlin.config.get_profile_with_regex(executable) == expected


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        (["default.xml", "", True, True], "default.xml"),
        (["default.xml", "", False, True], None),
        (["", "", True, True], None),
        (["other.xml", "", True, False], None),
    ],
    ids=["enabled", "disabled", "no-profile", "not-default"],
)
def test_default_profile_lookup(
    cfg: gremlin.config.Configuration,
    entry: list[str | bool],
    expected: str | None,
) -> None:
    _register_auto_loading_entries(cfg, [entry])

    assert gremlin.config.get_default_profile() == expected
