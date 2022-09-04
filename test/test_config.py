# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2022 Lionel Ott
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

import os
import tempfile
import pytest

import gremlin.config
import gremlin.error
import gremlin.util
import gremlin.types

from gremlin.types import PropertyType


@pytest.fixture
def modify_config():
    tmp = tempfile.mkstemp()
    gremlin.config._config_file_path = tmp[1]
    c = gremlin.config.Configuration()
    c._data = {}


def test_simple(modify_config):
    c = gremlin.config.Configuration()

    c.register("test.1", PropertyType.Int, 42)
    c.register("test.2", PropertyType.Bool, False)
    c.register("test.3", PropertyType.HatDirection, gremlin.types.HatDirection.NorthEast)
    assert c.get("test.1") == 42
    assert c.get("test.2") == False
    assert c.get("test.3") == gremlin.types.HatDirection.NorthEast

    c.set("test.1", 37)
    c.set("test.2", True)
    c.set("test.3", gremlin.types.HatDirection.SouthWest)
    assert c.get("test.1") == 37
    assert c.get("test.2") == True
    assert c.get("test.3") == gremlin.types.HatDirection.SouthWest

def test_load_save(modify_config):
    c = gremlin.config.Configuration()

    c.register("test.1", PropertyType.Int, 42)
    c.register("test.2", PropertyType.Bool, False)
    c.register("test.3", PropertyType.HatDirection, gremlin.types.HatDirection.NorthEast)
    c.register("test.4", PropertyType.List, [1,2,3,4,5])
    assert c.get("test.1") == 42
    assert c.get("test.2") == False
    assert c.get("test.3") == gremlin.types.HatDirection.NorthEast
    assert c.get("test.4") == [1,2,3,4,5]

    c.save()
    c.load()

    assert c.get("test.1") == 42
    assert c.get("test.2") == False
    assert c.get("test.3") == gremlin.types.HatDirection.NorthEast
    assert c.get("test.4") == [1,2,3,4,5]

def test_exceptions():
    c = gremlin.config.Configuration()

    c.register("test.1", PropertyType.Int, 42)
    with pytest.raises(gremlin.error.GremlinError):
        c.set("test.1", 3.14)
    
    with pytest.raises(gremlin.error.GremlinError):
        c.set("some.other", "test")

    with pytest.raises(gremlin.error.GremlinError):
        c.get("does.not.exist")