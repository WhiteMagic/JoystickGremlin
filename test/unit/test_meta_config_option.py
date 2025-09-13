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

import logging
import sys
sys.path.append(".")

import pytest

import gremlin.error
import gremlin.types

from gremlin.ui.option import MetaConfigOption

from gremlin.types import PropertyType


def test_basic():
    option = MetaConfigOption()

    assert option.count() == 0

    option.register("some", "test", "option 1", "description 1", "ui/test1.qml")
    option.register("some", "test", "option 2", "description 2", "ui/test2.qml")

    assert option.count() == 2

    assert len(option.sections()) == 1
    assert len(option.groups("some")) == 1
    assert len(option.entries("some", "test")) == 2
    assert option.description("some", "test", "option 1") == "description 1"
    assert option.description("some", "test", "option 2") == "description 2"
    assert option.qml_element("some", "test", "option 1") == "ui/test1.qml"
    assert option.qml_element("some", "test", "option 2") == "ui/test2.qml"


def test_register_duplicate_logs_warning(caplog):
    option = MetaConfigOption()
    option.register("dup", "grp", "name", "desc", "ui/elem.qml")
    option.register("dup", "grp", "name", "desc", "ui/elem.qml")

    assert caplog.record_tuples == [
        ("system", logging.WARNING, "Option dup.grp.name already registered.")
    ]


def test_retrieve_nonexistent_raises():
    option = MetaConfigOption()
    with pytest.raises(gremlin.error.GremlinError):
        option.qml_element("no", "such", "option")

    option.register("sec", "grp", "name", "desc", "ui/elem.qml")
    with pytest.raises(gremlin.error.GremlinError):
        option.description("sec", "grp", "other")
