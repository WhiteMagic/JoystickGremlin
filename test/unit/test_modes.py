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
import gremlin.shared_state
from gremlin.config import Configuration
from gremlin.error import GremlinError
import gremlin.mode_manager
from gremlin.mode_manager import Mode, ModeManager
from gremlin.types import AxisMode, InputType

from gremlin.profile import Profile, ModeHierarchy

import action_plugins.tempo as tempo

_PROFILE_REALISTIC = "profile_realistic.xml"


class TestModeHierarchy:

    def test_ctor(self):
        p = Profile()
        mh = ModeHierarchy(p)

        assert mh.first_mode == "Default"
        assert mh.mode_names() == ["Default"]
        assert mh.mode_list()[0].value == "Default"
        assert mh.valid_parents("Default") == []
        assert mh.find_mode("Default") == mh.mode_list()[0]
        with pytest.raises(GremlinError):
            mh.find_mode("not there")

    def test_add(self):
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

    def test_delete(self):
        p = Profile()
        mh = ModeHierarchy(p)

        mh.add_mode("Second")
        mh.add_mode("Third")
        assert set(mh.mode_names()) == set(["Default", "Second", "Third"])

        mh.delete_mode("Second")
        assert set(mh.mode_names()) == set(["Default", "Third"])

        mh.add_mode("Second")
        assert set(mh.mode_names()) == set(["Default", "Second", "Third"])

    def test_rename(self):
        p = Profile()
        mh = ModeHierarchy(p)

        mh.add_mode("Second")
        mh.add_mode("Third")
        assert set(mh.mode_names()) == set(["Default", "Second", "Third"])

        mh.rename_mode("Default", "Zeta")
        assert set(mh.mode_names()) == set(["Zeta", "Second", "Third"])
        assert mh.first_mode == "Zeta"

    def test_parent(self):
        p = Profile()
        mh = ModeHierarchy(p)

        mh.add_mode("Second")
        mh.add_mode("Third")
        assert set(mh.mode_names()) == set(["Default", "Second", "Third"])

        mh.set_parent("Default", "Second")
        assert mh.first_mode == "Second"
        assert mh.find_mode("Default").parent.value == "Second"
        assert mh.find_mode("Default").parent == mh.find_mode("Second")

    def test_complex_modifications(self, xml_dir: str):
        p = Profile()
        p.from_xml(os.path.join(xml_dir, _PROFILE_REALISTIC))
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


class TestModeManager:

    def test_cycling(self):
        p = Profile()
        gremlin.shared_state.current_profile = p

        mm = ModeManager()
        cfg = Configuration()
        cfg.set("action", "change-mode", "resolution-mode", "oldest")
        mm.reset()
        del mm._mode_stack[0]
        mm.switch_to(Mode("A", None))
        mm.switch_to(Mode("B", "A"))
        mm.switch_to(Mode("C", "B"))
        mm.switch_to(Mode("A", "C"))
        mm.switch_to(Mode("B", "A"))

        ml = mm._mode_stack
        assert ml[0].name == "A"
        assert ml[1].name == "B"

        cfg.set("action", "change-mode", "resolution-mode", "newest")
        mm.reset()
        del mm._mode_stack[0]
        mm.switch_to(Mode("A", None))
        mm.switch_to(Mode("B", "A"))
        mm.switch_to(Mode("C", "B"))
        mm.switch_to(Mode("A", "C"))
        mm.switch_to(Mode("B", "A"))

        ml = mm._mode_stack
        assert ml[0].name == "C"
        assert ml[1].name == "A"
        assert ml[2].name == "B"

    def test_temporaries(self):
        p = Profile()
        gremlin.shared_state.current_profile = p

        mm = ModeManager()

        # Simple case with oldest mode retainment
        cfg = Configuration().set("action", "change-mode", "resolution-mode", "oldest")
        mm.reset()
        del mm._mode_stack[0]
        mm.switch_to(Mode("A", None))
        mm.switch_to(Mode("B", "A"))
        mm.switch_to(Mode("C", "B", True))
        mm.switch_to(Mode("D", "C", True))
        mm.switch_to(Mode("E", "D", True))
        mm.switch_to(Mode("C", "E", True))
        mm.switch_to(Mode("D", "C", True))

        ml = mm._mode_stack
        assert len(ml) == 4
        assert ml[0].name == "A"
        assert ml[1].name == "B"
        assert ml[2].name == "C"
        assert ml[3].name == "D"
        assert ml[2].is_temporary
        assert ml[3].is_temporary

        # Newest mode retainment with requirement to keep some older modes
        cfg = Configuration().set("action", "change-mode", "resolution-mode", "newest")
        mm.reset()
        del mm._mode_stack[0]
        mm.switch_to(Mode("A", None))
        mm.switch_to(Mode("B", "A"))
        mm.switch_to(Mode("C", "B", True))
        mm.switch_to(Mode("D", "C", True))
        mm.switch_to(Mode("E", "D", True))
        mm.switch_to(Mode("C", "E", True))
        mm.switch_to(Mode("D", "C", True))

        ml = mm._mode_stack
        assert len(ml) == 5
        assert ml[0].name == "B"
        assert ml[1].name == "C"
        assert ml[2].name == "E"
        assert ml[3].name == "C"
        assert ml[4].name == "D"
        assert ml[1].is_temporary
        assert ml[2].is_temporary
        assert ml[3].is_temporary
        assert ml[4].is_temporary
