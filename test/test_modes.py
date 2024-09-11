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

import os
import pytest
import uuid
from xml.etree import ElementTree

import gremlin.plugin_manager
from gremlin.error import GremlinError
from gremlin.types import AxisMode, InputType

from gremlin.profile import Profile, ModeHierarchy


def test_ctor():
    p = Profile()
    mh = ModeHierarchy(p)

    assert mh.first_mode == "Default"
    assert mh.mode_names() == ["Default"]
    assert mh.mode_list()[0].value == "Default"
    assert mh.valid_parents("Default") == []
    assert mh.find_mode("Default") == mh.mode_list()[0]
    with pytest.raises(GremlinError):
        mh.find_mode("not there")


def test_add():
    p = Profile()
    mh = ModeHierarchy(p)

    mh.add_mode("Second")
    mh.add_mode("Third")
    with pytest.raises(GremlinError):
        mh.add_mode("Second")

    assert set(mh.mode_names()) == set(["Default", "Second", "Third"])
    assert mh.find_mode("Second").value == "Second"
    with pytest.raises(GremlinError):
        mh.find_mode("not there")

    assert mh.mode_exists("Second") == True
    assert mh.mode_exists("Other") == False


def test_delete():
    p = Profile()
    mh = ModeHierarchy(p)

    mh.add_mode("Second")
    mh.add_mode("Third")
    assert set(mh.mode_names()) == set(["Default", "Second", "Third"])

    mh.delete_mode("Second")
    assert set(mh.mode_names()) == set(["Default", "Third"])

    mh.add_mode("Second")
    assert set(mh.mode_names()) == set(["Default", "Second", "Third"])


def test_rename():
    p = Profile()
    mh = ModeHierarchy(p)

    mh.add_mode("Second")
    mh.add_mode("Third")
    assert set(mh.mode_names()) == set(["Default", "Second", "Third"])

    mh.rename_mode("Default", "Zeta")
    assert set(mh.mode_names()) == set(["Zeta", "Second", "Third"])
    assert mh.first_mode == "Zeta"


def test_parent():
    p = Profile()
    mh = ModeHierarchy(p)

    mh.add_mode("Second")
    mh.add_mode("Third")
    assert set(mh.mode_names()) == set(["Default", "Second", "Third"])

    mh.set_parent("Default", "Second")
    assert mh.first_mode == "Second"
    assert mh.find_mode("Default").parent.value == "Second"
    assert mh.find_mode("Default").parent == mh.find_mode("Second")


def test_complex_modifications():
    p = Profile()
    p.from_xml("test/xml/profile_realistic.xml")
    mh = p.modes

    assert set(mh.mode_names()) == set(["Default", "Second", "Child"])
    assert mh.find_mode("Child").parent == mh.find_mode("Default")

    child_input = p.inputs[uuid.UUID("684e9af0-03c4-11ef-8005-444553540000")][0]
    assert child_input.mode == "Child"
    assert len(p.inputs[uuid.UUID("684e9af0-03c4-11ef-8005-444553540000")]) == 3

    mh.rename_mode("Child", "Zeta")
    assert child_input.mode == "Zeta"

    mh.delete_mode("Zeta")
    assert len(p.inputs[uuid.UUID("684e9af0-03c4-11ef-8005-444553540000")]) == 2