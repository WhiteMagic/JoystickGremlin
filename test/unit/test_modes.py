# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid

import pytest

import gremlin.mode_manager
import gremlin.plugin_manager
import gremlin.shared_state
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.mode_manager import (
    Mode,
    ModeManager,
)
from gremlin.profile import (
    ModeHierarchy,
    Profile,
)

_PROFILE_MODE_HIERARCHY = "profile_mode_hierarchy.xml"
_PROFILE_REALISTIC = "profile_realistic.xml"


class TestModeHierarchy:
    def test_ctor(self) -> None:
        p = Profile()
        mh = ModeHierarchy(p)

        assert mh.first_mode == "Default"
        assert mh.mode_names() == ["Default"]
        assert mh.mode_list()[0].value == "Default"
        assert mh.valid_parents("Default") == []
        assert mh.find_mode("Default") == mh.mode_list()[0]
        with pytest.raises(GremlinError):
            mh.find_mode("not there")

    def test_add(self) -> None:
        p = Profile()
        mh = ModeHierarchy(p)

        mh.add_mode("Second")
        mh.add_mode("Third")
        with pytest.raises(GremlinError):
            mh.add_mode("Second")

        assert set(mh.mode_names()) == {"Default", "Second", "Third"}
        assert mh.find_mode("Second").value == "Second"
        with pytest.raises(GremlinError):
            mh.find_mode("not there")

        assert mh.mode_exists("Second")
        assert not mh.mode_exists("Other")

    def test_delete(self) -> None:
        p = Profile()
        mh = ModeHierarchy(p)

        mh.add_mode("Second")
        mh.add_mode("Third")
        assert set(mh.mode_names()) == {"Default", "Second", "Third"}

        mh.delete_mode("Second")
        assert set(mh.mode_names()) == {"Default", "Third"}

        mh.add_mode("Second")
        assert set(mh.mode_names()) == {"Default", "Second", "Third"}

    def test_delete_moves_all_children_to_grandparent(
        self, tmp_path: pathlib.Path
    ) -> None:
        p = Profile()
        for name in ["Top", "Middle", "First", "Second"]:
            p.modes.add_mode(name)
        p.modes.set_parent("Middle", "Top")
        p.modes.set_parent("First", "Middle")
        p.modes.set_parent("Second", "Middle")

        p.modes.delete_mode("Middle")

        profile_path = tmp_path / "profile.xml"
        p.to_xml(profile_path)
        reloaded = Profile()
        reloaded.from_xml(profile_path)

        assert set(reloaded.modes.mode_names()) == {
            "Default",
            "Top",
            "First",
            "Second",
        }
        assert reloaded.modes.find_mode("First").parent.value == "Top"
        assert reloaded.modes.find_mode("Second").parent.value == "Top"

    def test_parents_survive_round_trip(
        self, xml_dir: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        p = Profile()
        p.from_xml(str(xml_dir / _PROFILE_MODE_HIERARCHY))

        profile_path = tmp_path / "profile.xml"
        p.to_xml(profile_path)
        reloaded = Profile()
        reloaded.from_xml(profile_path)

        assert {
            node.value: node.parent.value for node in reloaded.modes.mode_list()
        } == {
            "Default": "",
            "Child": "Default",
            "Separate": "",
            "Three": "",
            "Levels": "Three",
            "Deep": "Levels",
        }

    def test_valid_parents_excludes_self_and_descendants(self) -> None:
        p = Profile()
        for name in ["Top", "Middle", "Leaf", "Other"]:
            p.modes.add_mode(name)
        p.modes.set_parent("Middle", "Top")
        p.modes.set_parent("Leaf", "Middle")

        assert p.modes.valid_parents("Middle") == ["Default", "Other", "Top"]

    def test_rename(self) -> None:
        p = Profile()
        mh = ModeHierarchy(p)

        mh.add_mode("Second")
        mh.add_mode("Third")
        assert set(mh.mode_names()) == {"Default", "Second", "Third"}

        mh.rename_mode("Default", "Zeta")
        assert set(mh.mode_names()) == {"Zeta", "Second", "Third"}
        assert mh.first_mode == "Second"

    def test_first_mode_is_alphabetical_root(self) -> None:
        p = Profile()
        mh = ModeHierarchy(p)

        mh.add_mode("Charlie")
        mh.add_mode("Bravo")
        assert mh.first_mode == "Bravo"

        mh.add_mode("Alpha")
        mh.set_parent("Alpha", "Charlie")
        assert mh.first_mode == "Bravo"

    def test_parent(self) -> None:
        p = Profile()
        mh = ModeHierarchy(p)

        mh.add_mode("Second")
        mh.add_mode("Third")
        assert set(mh.mode_names()) == {"Default", "Second", "Third"}

        mh.set_parent("Default", "Second")
        assert mh.first_mode == "Second"
        assert mh.find_mode("Default").parent.value == "Second"
        assert mh.find_mode("Default").parent == mh.find_mode("Second")

    def test_complex_modifications(self, xml_dir: pathlib.Path) -> None:
        p = Profile()
        p.from_xml(str(xml_dir / _PROFILE_REALISTIC))
        mh = p.modes

        assert set(mh.mode_names()) == {"Default", "Second", "Child"}
        assert mh.find_mode("Child").parent == mh.find_mode("Default")

        child_input = p.inputs[uuid.UUID("684e9af0-03c4-11ef-8005-444553540000")][0]
        assert child_input.mode == "Child"
        assert len(p.inputs[uuid.UUID("684e9af0-03c4-11ef-8005-444553540000")]) == 3

        mh.rename_mode("Child", "Zeta")
        assert child_input.mode == "Zeta"

        mh.delete_mode("Zeta")
        assert len(p.inputs[uuid.UUID("684e9af0-03c4-11ef-8005-444553540000")]) == 2


class TestModeManager:
    def test_last_mode_skips_temporary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        p = Profile()
        p.fpath = pathlib.Path("C:/profiles/test.xml")
        gremlin.shared_state.current_profile = p

        cfg = Configuration()
        # Keep the per-profile map out of the real configuration file.
        stored: dict[str, str] = {}
        original_value = cfg.value
        original_set = cfg.set
        monkeypatch.setattr(
            cfg,
            "value",
            lambda section, group, name: (
                dict(stored)
                if name == "last-mode-per-profile"
                else original_value(section, group, name)
            ),
        )
        monkeypatch.setattr(
            cfg,
            "set",
            lambda section, group, name, value: (
                stored.update(value)
                if name == "last-mode-per-profile"
                else original_set(section, group, name, value)
            ),
        )

        mm = ModeManager()
        mm.reset()
        mm.switch_to(Mode("A", mm.current.name))
        assert stored == {str(p.fpath): "A"}

        mm.temporary(Mode("B", "A"))
        assert stored == {str(p.fpath): "A"}

    def test_mode_changed_reports_previous_mode(self) -> None:
        gremlin.shared_state.current_profile = Profile()

        mm = ModeManager()
        mm.reset()
        changes: list[tuple[str, str]] = []

        def record(mode_name: str, previous_mode: str) -> None:
            changes.append((mode_name, previous_mode))

        mm.modeChanged.connect(record)
        try:
            mm.switch_to(Mode("A", "Default"))
            mm.switch_to(Mode("B", "A"))
            mm.previous()
            mm.unwind()
        finally:
            mm.modeChanged.disconnect(record)

        assert changes == [("A", "Default"), ("B", "A"), ("A", "B"), ("B", "A")]

    def test_cycling(self) -> None:
        p = Profile()
        gremlin.shared_state.current_profile = p

        mm = ModeManager()
        cfg = Configuration()
        cfg.set("action", "change-mode", "resolution-mode", "Oldest")
        mm.reset()
        mm.switch_to(Mode("A", None))
        mm.switch_to(Mode("B", "A"))
        mm.switch_to(Mode("C", "B"))
        mm.switch_to(Mode("A", "C"))
        mm.switch_to(Mode("B", "A"))

        ml = mm._mode_stack
        assert ml[1].name == "A"
        assert ml[2].name == "B"

        cfg.set("action", "change-mode", "resolution-mode", "Newest")
        mm.reset()
        mm.switch_to(Mode("A", None))
        mm.switch_to(Mode("B", "A"))
        mm.switch_to(Mode("C", "B"))
        mm.switch_to(Mode("A", "C"))
        mm.switch_to(Mode("B", "A"))

        ml = mm._mode_stack
        assert ml[0].name == "C"
        assert ml[1].name == "A"
        assert ml[2].name == "B"

    def test_temporaries(self) -> None:
        p = Profile()
        gremlin.shared_state.current_profile = p

        mm = ModeManager()

        # Simple case with oldest mode retainment
        cfg = Configuration()
        cfg.set("action", "change-mode", "resolution-mode", "Oldest")
        mm.reset()
        mm.switch_to(Mode("A", None))
        mm.switch_to(Mode("B", "A"))
        mm.switch_to(Mode("C", "B", True))
        mm.switch_to(Mode("D", "C", True))
        mm.switch_to(Mode("E", "D", True))
        mm.switch_to(Mode("C", "E", True))
        mm.switch_to(Mode("D", "C", True))

        ml = mm._mode_stack
        assert len(ml) == 5
        assert ml[1].name == "A"
        assert ml[2].name == "B"
        assert ml[3].name == "C"
        assert ml[4].name == "D"
        assert ml[3].is_temporary
        assert ml[4].is_temporary

        # Newest mode retainment with requirement to keep some older modes
        cfg.set("action", "change-mode", "resolution-mode", "Newest")
        mm.reset()
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
