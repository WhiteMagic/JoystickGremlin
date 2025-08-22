# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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

import sys
sys.path.append(".")

from collections.abc import Iterator
import tempfile
import pytest
from unittest import mock

import gremlin.config
import gremlin.error
import gremlin.types

from gremlin.types import PropertyType


@pytest.fixture
def cfg() -> Iterator[gremlin.config.Configuration]:
    """Returns a Configuration object other than the singleton, with file path modified."""
    tmp = tempfile.mkstemp()
    with mock.patch.object(gremlin.config, "_config_file_path", tmp[1]):
        yield gremlin.config.Configuration.klass()


def test_simple(cfg: gremlin.config.Configuration):
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


def test_load_save(cfg: gremlin.config.Configuration):
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
    with mock.patch.object(cfg, cfg._should_skip_reload.__name__, return_value=False):
        cfg.load()

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


def test_exceptions(cfg: gremlin.config.Configuration):
    cfg.register("test", "case", "1", PropertyType.Int, 42, "", {"min": 1, "max": 20})
    with pytest.raises(gremlin.error.GremlinError):
        cfg.set("test", "case", "1", 3.14)

    with pytest.raises(gremlin.error.GremlinError):
        cfg.set("test", "some", "other", "test")

    with pytest.raises(gremlin.error.GremlinError):
        cfg.value("does", "not", "exist")
