# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib
import uuid

import pytest

from action_plugins.description import DescriptionData
from action_plugins.root import RootData
from gremlin.error import GremlinError
from gremlin.profile import Profile
from gremlin.types import (
    DataInsertionMode,
    InputType,
)

_PROFILE_HIERARCHY = "profile_hierarchy.xml"


def test_ctor() -> None:
    a = RootData(InputType.JoystickButton)

    assert len(a.children) == 0
    assert a.is_valid()


def test_from_xml(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE_HIERARCHY))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    assert len(a.children) == 3
    assert a.children[0].id == uuid.UUID("0c905a47-9ad3-4b65-b702-fbae1d133600")
    assert a.children[1].id == uuid.UUID("0c905a47-9ad3-4b65-b702-fbae1d133601")
    assert a.children[2].id == uuid.UUID("0c905a47-9ad3-4b65-b702-fbae1d133603")


def test_action_methods(xml_dir: pathlib.Path) -> None:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE_HIERARCHY))

    a = p.library.get_action(uuid.UUID("ac905a47-9ad3-4b65-b702-fbae1d133609"))

    assert len(a.get_actions()[0]) == 3
    with pytest.raises(GremlinError):
        a.get_actions("invalid")
    assert len(a.get_actions("children")[0]) == 3

    d = DescriptionData()
    a.insert_action(d, "children", DataInsertionMode.Prepend)
    assert len(a.get_actions("children")[0]) == 4
    assert a.get_actions()[0][0].id == d.id
    with pytest.raises(GremlinError):
        a.remove_action(4, "children")
    a.remove_action(3, "children")
    assert len(a.get_actions("children")[0]) == 3
    assert d not in a.get_actions()
