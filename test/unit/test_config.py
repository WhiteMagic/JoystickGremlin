# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

import sys
sys.path.append(".")

from collections.abc import Iterator
import tempfile
import pytest
from unittest import mock

import gremlin.config
import gremlin.error
import gremlin.types

from gremlin.common import SingletonMetaclass
from gremlin.types import PropertyType


@pytest.fixture
def cfg() -> Iterator[gremlin.config.Configuration]:
    """Returns a Configuration object other than the singleton, with file path
    modified."""
    # Remove the singleton instance if it exists and create a temporary file
    # to use as the config file. The old config file name is stored to be
    # restored when the fixutre is torn down.
    original_path = gremlin.config._config_file_path
    SingletonMetaclass._instances.pop(gremlin.config.Configuration, None)
    with mock.patch.object(
        gremlin.config, "_config_file_path", tempfile.mkstemp()[1]
    ):
        try:
            yield gremlin.config.Configuration()
        finally:
            # Restore original config file path and delete singleton instance.
            gremlin.config._config_file_path = original_path
            SingletonMetaclass._instances.pop(
                gremlin.config.Configuration, None
            )


def test_simple(cfg: gremlin.config.Configuration) -> None:
    cfg.register("test", "case", "1", PropertyType.Int, 42, "", {"min": 1, "max": 20})
    cfg.register("test", "case", "2", PropertyType.Bool, False, "", {})
    cfg.register(
        "test",
        "case",
        "3",
        PropertyType.HatDirection,
        gremlin.types.HatDirection.NorthEast,
        "",
        {},
    )
    assert cfg.value("test", "case", "1") == 42
    assert cfg.value("test", "case", "2") == False
    assert cfg.value("test", "case", "3") == gremlin.types.HatDirection.NorthEast

    cfg.set("test", "case", "1", 37)
    cfg.set("test", "case", "2", True)
    cfg.set("test", "case", "3", gremlin.types.HatDirection.SouthWest)
    assert cfg.value("test", "case", "1") == 37
    assert cfg.value("test", "case", "2") == True
    assert cfg.value("test", "case", "3") == gremlin.types.HatDirection.SouthWest


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
    assert cfg.expose("test", "case", "1") == False

    assert cfg.value("test", "case", "2") == False
    assert cfg.description("test", "case", "2") == "two"
    assert cfg.expose("test", "case", "2") == True

    assert cfg.value("test", "case", "3") == gremlin.types.HatDirection.NorthEast
    assert cfg.description("test", "case", "3") == ""
    assert cfg.expose("test", "case", "3") == False

    assert cfg.value("test", "case", "4") == [1, 2, 3, 4, 5]
    assert cfg.description("test", "case", "4") == ""
    assert cfg.expose("test", "case", "4") == False

    cfg.save()
    with mock.patch.object(
        cfg, cfg._should_skip_reload.__name__, return_value=False
    ):
        cfg.load()

    assert cfg.value("test", "case", "1") == 42
    assert cfg.expose("test", "case", "1") == False

    assert cfg.value("test", "case", "2") == False
    assert cfg.expose("test", "case", "2") == True

    assert cfg.value("test", "case", "3") == gremlin.types.HatDirection.NorthEast
    assert cfg.expose("test", "case", "3") == False

    assert cfg.value("test", "case", "4") == [1, 2, 3, 4, 5]
    assert cfg.expose("test", "case", "4") == False


def test_exceptions(cfg: gremlin.config.Configuration) -> None:
    cfg.register(
        "test", "case", "1", PropertyType.Int, 42, "", {"min": 1, "max": 20}
    )
    with pytest.raises(gremlin.error.GremlinError):
        cfg.set("test", "case", "1", 3.14)

    with pytest.raises(gremlin.error.GremlinError):
        cfg.set("test", "some", "other", "test")

    with pytest.raises(gremlin.error.GremlinError):
        cfg.value("does", "not", "exist")
