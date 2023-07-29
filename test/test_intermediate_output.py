# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2023 Lionel Ott
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

import pytest

from gremlin.common import InputType
from gremlin.error import GremlinError
from gremlin.intermediate_output import IntermediateOutput


def test_creation():
    io = IntermediateOutput()

    io.create(InputType.JoystickButton, "TB 1")
    assert io.button("TB 1").label == "TB 1"
    assert io.button(0).label == "TB 1"
    assert io.button("TB 1").index == 0

    io.create(InputType.JoystickButton, "TB 2")
    io.create(InputType.JoystickButton, "TB 3")

    assert io.button(2).label == "TB 3"
    assert io.button("TB 3").index == 2

    io.create(InputType.JoystickAxis, "TA 1")
    io.create(InputType.JoystickButton, "TB 4")

    assert io.axis(0).label == "TA 1"
    assert io.axis("TA 1").index == 0
    assert io.button(3).label == "TB 4"
    assert io.button("TB 4").index == 3


def test_delete():
    io = IntermediateOutput()

    io.create(InputType.JoystickButton, "TB 1")
    io.create(InputType.JoystickButton, "TB 2")
    io.create(InputType.JoystickButton, "TB 3")
    
    assert len(io.all_keys()) == 3
    io.delete_by_label("TB 3")
    assert len(io.all_keys()) == 2

    with pytest.raises(GremlinError):
        assert io.button("TB 3")
    
    io.delete_by_index(InputType.JoystickButton, 0)
    assert len(io.all_keys()) == 1
    with pytest.raises(GremlinError):
        assert io.button("TB 1")
    assert io.button("TB 2").index == 1


def test_index_reuse():
    io = IntermediateOutput()

    io.create(InputType.JoystickButton, "TB 1")
    io.create(InputType.JoystickButton, "TB 2")
    io.create(InputType.JoystickButton, "TB 3")

    io.delete_by_label("TB 1")

    io.create(InputType.JoystickButton, "NEW")
    io.button(0).label == "NEW"


def test_relabel():
    io = IntermediateOutput()

    io.create(InputType.JoystickButton, "TB 1")
    io.create(InputType.JoystickButton, "TB 2")
    io.create(InputType.JoystickButton, "TB 3")

    assert io.button(1).label == "TB 2"
    assert io.button("TB 2").index == 1

    io.set_label("TB 2", "NEW")
    assert io.button(1).label == "NEW"
    assert io.button("NEW").index == 1

    assert "NEW" in io.all_keys()
    assert "TB 2" not in io.all_keys()
    assert len(io.all_keys()) == 3

    io.delete_by_label("NEW")
    assert len(io.all_keys()) == 2
    assert "NEW" not in io.all_keys()