# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import uuid
from pathlib import Path

import pytest

import action_plugins.axis_delta as axis_delta
import gremlin.types as types
from action_plugins.description import DescriptionData
from gremlin.config import Configuration
from gremlin.error import GremlinError
from gremlin.profile import Profile
from gremlin.types import DataInsertionMode

_XML_PROFILE = "action_axis_delta_simple.xml"

_AXIS_DELTA_ID = uuid.UUID("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
_POSITIVE_CHILD_ID = uuid.UUID("11111111-2222-4333-8444-555555555555")
_NEGATIVE_CHILD_ID = uuid.UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")


def test_ctor() -> None:
    a = axis_delta.AxisDeltaData(types.InputType.JoystickAxis)
    c = Configuration()

    assert len(a.actions_positive) == 0
    assert len(a.actions_negative) == 0
    assert a.change_threshold == c.value("action", "axis-delta", "threshold")
    assert a.is_valid()


def test_from_xml(xml_dir: Path) -> None:
    p = Profile()
    p.from_xml(Path(xml_dir / _XML_PROFILE))

    a = p.library.get_action(_AXIS_DELTA_ID)

    assert isinstance(a, axis_delta.AxisDeltaData)
    assert a.change_threshold == pytest.approx(0.25)
    assert len(a.actions_positive) == 1
    assert len(a.actions_negative) == 1
    assert a.actions_positive[0].id == _POSITIVE_CHILD_ID
    assert a.actions_negative[0].id == _NEGATIVE_CHILD_ID


def test_to_xml() -> None:
    pos_child = DescriptionData()
    pos_child._id = uuid.UUID("11111111-2222-4333-8444-555555555555")

    neg_child = DescriptionData()
    neg_child._id = uuid.UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")

    a = axis_delta.AxisDeltaData(types.InputType.JoystickAxis)
    a.insert_action(pos_child, "positive")
    a.insert_action(neg_child, "negative")
    a.change_threshold = 0.42

    node = a._to_xml()

    assert node.find("./property/name[.='threshold']/../value").text == "0.42"
    assert (
        node.find("./positive-actions/action-id").text
        == "11111111-2222-4333-8444-555555555555"
    )
    assert (
        node.find("./negative-actions/action-id").text
        == "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    )


def test_action_methods(xml_dir: Path) -> None:
    p = Profile()
    p.from_xml(Path(xml_dir / _XML_PROFILE))

    a = p.library.get_action(_AXIS_DELTA_ID)

    # get_actions returns all actions across both containers
    assert len(a.get_actions()[0]) == 2
    assert len(a.get_actions("positive")[0]) == 1
    assert len(a.get_actions("negative")[0]) == 1

    with pytest.raises(GremlinError):
        a.get_actions("invalid")

    # insert and remove
    description_action = DescriptionData()
    a.insert_action(description_action, "positive")
    assert len(a.get_actions("positive")[0]) == 2

    a.remove_action(0, "positive")
    assert len(a.get_actions("positive")[0]) == 1
    assert a.get_actions("positive")[0][0].id == description_action.id

    a.insert_action(description_action, "negative", DataInsertionMode.Prepend)
    assert len(a.get_actions("negative")[0]) == 2
    assert a.get_actions("negative")[0][0].id == description_action.id
