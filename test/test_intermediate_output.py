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
import uuid

sys.path.append(".")

import pytest

from gremlin.common import InputType
from gremlin.error import GremlinError
from gremlin.intermediate_output import IntermediateOutput


@pytest.fixture(autouse=True)
def reset_io():
    IntermediateOutput().reset()


def test_creation():
    io = IntermediateOutput()

    io.create(InputType.JoystickButton, label="TB 1")
    assert io["TB 1"].label == "TB 1"
    assert io["TB 1"].type == InputType.JoystickButton
    assert isinstance(io["TB 1"].guid, uuid.UUID)

    io.create(InputType.JoystickButton, label="TB 2")
    io.create(InputType.JoystickButton, label="TB 3")

    for key in ["TB 1", "TB 2", "TB 3"]:
        assert key in io.labels_of_type([InputType.JoystickButton])

    io.create(InputType.JoystickAxis, label="TA 1")
    io.create(InputType.JoystickButton, label="TB 4")

    assert len(io.labels_of_type([InputType.JoystickButton])) == 4
    assert len(io.labels_of_type([InputType.JoystickAxis])) == 1


def test_delete():
    io = IntermediateOutput()

    io.create(InputType.JoystickButton, label="TB 1")
    io.create(InputType.JoystickButton, label="TB 2")
    tb2_guid = io["TB 2"].guid
    io.create(InputType.JoystickButton, label="TB 3")

    assert len(io.labels_of_type()) == 3
    io.delete("TB 3")
    assert len(io.labels_of_type()) == 2

    with pytest.raises(GremlinError):
        assert io["TB 3"]

    io.delete(io["TB 1"].guid)
    assert len(io.labels_of_type()) == 1
    with pytest.raises(GremlinError):
        assert io["TB 1"]
    assert io["TB 2"].guid == tb2_guid


def test_index_reuse():
    io = IntermediateOutput()

    io.create(InputType.JoystickButton, label="TB 1")
    tb1_guid = io["TB 1"]
    io.create(InputType.JoystickButton, label="TB 2")
    io.create(InputType.JoystickButton, label="TB 3")

    io.delete("TB 1")

    io.create(InputType.JoystickButton, label="NEW")
    io["NEW"].guid != tb1_guid


def test_relabel():
    io = IntermediateOutput()

    io.create(InputType.JoystickButton, label="TB 1")
    io.create(InputType.JoystickButton, label="TB 2")
    tb2_guid = io["TB 2"].guid
    io.create(InputType.JoystickButton, label="TB 3")

    io.set_label("TB 2", "NEW")
    assert io[tb2_guid].label == "NEW"
    assert io["NEW"].guid == tb2_guid

    assert "NEW" in io.labels_of_type()
    assert "TB 2" not in io.labels_of_type()
    assert len(io.labels_of_type()) == 3

    io.delete("NEW")
    assert len(io.labels_of_type()) == 2
    assert "NEW" not in io.labels_of_type()