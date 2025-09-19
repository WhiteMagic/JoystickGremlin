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

from collections.abc import Iterator
import logging
import sys
sys.path.append(".")

import pytest
from unittest import mock

import gremlin.error
import gremlin.types

from gremlin.ui.option import BaseMetaConfigOptionWidget, MetaConfigOption

from gremlin.common import SingletonMetaclass
from gremlin.types import PropertyType


class DummyWidget(BaseMetaConfigOptionWidget):

    def _qml_path(self) -> str:
        return "dummy.qml"


@pytest.fixture
def option() -> MetaConfigOption:
    SingletonMetaclass._instances.pop(MetaConfigOption, None)
    return MetaConfigOption()

def test_basic(option: MetaConfigOption) -> None:
    assert option.count() == 0

    option.register("some", "test", "option 1", "description 1", DummyWidget)
    option.register("some", "test", "option 2", "description 2", DummyWidget)

    assert option.count() == 2

    assert len(option.sections()) == 1
    assert len(option.groups("some")) == 1
    assert len(option.entries("some", "test")) == 2
    assert option.description("some", "test", "option 1") == "description 1"
    assert option.description("some", "test", "option 2") == "description 2"
    assert option.qml_widget("some", "test", "option 1") == DummyWidget
    assert option.qml_widget("some", "test", "option 2") == DummyWidget


def test_empty_entries(option: MetaConfigOption) -> None:
    assert option.count() == 0

    option.register("some", "test", "option 1", "description 1", DummyWidget)

    assert option.count() == 1

    assert len(option.sections()) == 1
    assert len(option.groups("some")) == 1
    assert len(option.entries("some", "test")) == 1
    assert option.entries("no", "such") == []
    assert option.entries("some", "no such") == []


def test_register_duplicate_logs_warning(option: MetaConfigOption, caplog) -> None:
    option.register("dup", "grp", "name", "desc", DummyWidget)
    option.register("dup", "grp", "name", "desc", DummyWidget)

    assert caplog.record_tuples == [
        ("system", logging.WARNING, "Option dup.grp.name already registered.")
    ]


def test_retrieve_nonexistent_raises(option: MetaConfigOption) -> None:
    with pytest.raises(gremlin.error.GremlinError):
        option.qml_widget("no", "such", "option")

    option.register("sec", "grp", "name", "desc", DummyWidget)
    with pytest.raises(gremlin.error.GremlinError):
        option.description("sec", "grp", "other")
