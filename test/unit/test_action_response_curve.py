# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib
import uuid
from xml.etree import ElementTree

import pytest
from PySide6 import QtCore

from action_plugins import response_curve
from action_plugins.root import RootData
from gremlin import spline, util
from gremlin.profile import (
    InputItem,
    InputItemBinding,
    Library,
    Profile,
)
from gremlin.types import InputType, PropertyType
from gremlin.ui.action_model import SequenceIndex
from gremlin.ui.profile import InputItemBindingModel

_PROFILE = "action_response_curve.xml"
_BEZIER_UUID = uuid.UUID("0f4b1c7e-58a1-4d0b-9b2e-6c1a4f5d3e21")
_LINEAR_UUID = uuid.UUID("7c2d5a19-3f84-42a7-8e6b-90d1c3b7e5f4")

_SAMPLE_POSITIONS = [-1.0, -0.77, -0.5, -0.25, -0.01, 0.0, 0.13, 0.5, 0.86, 1.0]


def _points(node: ElementTree.Element) -> list[str]:
    """Returns the control point coordinates of a serialized action."""
    cp_node = node.find("control-points")
    assert cp_node is not None
    return [
        p.to_string()
        for p in util.read_properties(cp_node, "point", PropertyType.Point2D)
    ]


def _symmetry_flags(node: ElementTree.Element) -> list[bool]:
    """Returns the handle symmetry entries of a serialized action."""
    cp_node = node.find("control-points")
    assert cp_node is not None
    return util.read_properties(cp_node, "symmetric-handles", PropertyType.Bool)


def _reload(
    action: response_curve.ResponseCurveData,
) -> response_curve.ResponseCurveData:
    """Returns the action after a serialization round trip."""
    restored = response_curve.ResponseCurveData(InputType.JoystickAxis)
    restored.from_xml(action.to_xml(), Library())
    return restored


class _RedrawLog:
    """Records the redraw signals a ResponseCurveModel emits."""

    SIGNALS = ["curveChanged", "controlPointChanged", "selectedPointChanged"]

    def __init__(self, model: response_curve.ResponseCurveModel) -> None:
        self.emitted: list[str] = []
        for name in _RedrawLog.SIGNALS:
            getattr(model, name).connect(lambda name=name: self.emitted.append(name))

    def reset(self) -> None:
        self.emitted = []


def _make_curve_model(
    data: response_curve.ResponseCurveData,
) -> response_curve.ResponseCurveModel:
    """Returns a QML model wrapping the given response curve action."""
    p = Profile()
    binding = InputItemBinding(InputItem(p.library))
    binding.root_action = RootData(InputType.JoystickAxis)
    binding.behavior = InputType.JoystickAxis
    p.library.add_action(binding.root_action)
    binding.root_action.insert_action(data, "children")

    return response_curve.ResponseCurveModel(
        data,
        InputItemBindingModel(binding),
        SequenceIndex(None, None, 0),
        SequenceIndex(None, None, 0),
        None,
    )


@pytest.fixture
def profile(xml_dir: pathlib.Path) -> Profile:
    p = Profile()
    p.from_xml(str(xml_dir / _PROFILE))
    return p


def test_from_xml(subtests: pytest.Subtests, profile: Profile) -> None:
    a = profile.library.get_action(_BEZIER_UUID)

    assert isinstance(a, response_curve.ResponseCurveData)
    with subtests.test("deadzone"):
        assert a.deadzone == [-0.9, -0.05, 0.05, 0.95]

    with subtests.test("control points"):
        assert isinstance(a.curve, spline.CubicBezierSpline)
        points = a.curve.control_points()
        assert len(points) == 3
        assert points[1].center.x == 0.0
        assert points[1].center.y == -0.3
        assert points[1].handle_left.x == -0.2
        assert points[1].handle_right.x == 0.25

    with subtests.test("handle symmetry defaults to off"):
        # A profile written before the option existed has to keep behaving
        # the way it did, which is with independently movable handles.
        assert [cp.symmetric_handles for cp in a.curve.control_points()] == [
            False,
            False,
            False,
        ]

    with subtests.test("other curve types"):
        b = profile.library.get_action(_LINEAR_UUID)
        assert isinstance(b.curve, spline.PiecewiseLinear)
        assert [(p.x, p.y) for p in b.curve.control_points()] == [
            (-1.0, -1.0),
            (-0.5, -0.1),
            (0.5, 0.4),
            (1.0, 1.0),
        ]


@pytest.mark.parametrize("action_uuid", [_BEZIER_UUID, _LINEAR_UUID])
def test_legacy_profile_serializes_unchanged(
    xml_dir: pathlib.Path, profile: Profile, action_uuid: uuid.UUID
) -> None:
    """An untouched profile has to be written back exactly as it was read."""
    source = ElementTree.parse(str(xml_dir / _PROFILE)).getroot()
    original = source.find(f"./library/action[@id='{str(action_uuid)}']")
    assert original is not None

    written = profile.library.get_action(action_uuid).to_xml()

    assert _points(written) == _points(original)
    assert _symmetry_flags(written) == []
    assert util.read_property(
        written, "curve-type", PropertyType.String
    ) == util.read_property(original, "curve-type", PropertyType.String)


def test_legacy_curve_evaluation_unchanged(profile: Profile) -> None:
    """A round trip must not alter what the curve actually does."""
    for action_uuid in [_BEZIER_UUID, _LINEAR_UUID]:
        a = profile.library.get_action(action_uuid)
        restored = _reload(a)
        assert restored.deadzone == a.deadzone
        for x in _SAMPLE_POSITIONS:
            assert restored.curve(x) == a.curve(x), (action_uuid, x)


def test_handle_symmetry_round_trip(profile: Profile) -> None:
    a = profile.library.get_action(_BEZIER_UUID)
    a.curve.set_symmetric_handles(1, True)
    geometry = [
        (a.curve.handle_geometry(i, side), i, side)
        for i in range(len(a.curve.control_points()))
        for side in ["left", "right"]
    ]

    restored = _reload(a)

    assert [cp.symmetric_handles for cp in restored.curve.control_points()] == [
        False,
        True,
        False,
    ]
    for expected, index, side in geometry:
        assert restored.curve.handle_geometry(index, side) == expected
    for x in _SAMPLE_POSITIONS:
        assert restored.curve(x) == a.curve(x), x


def test_numerical_edits_redraw_the_control_points(
    subtests: pytest.Subtests, profile: Profile
) -> None:
    """Editing a value numerically has to move the on-screen markers too.

    The curve line and the control point markers are driven by separate
    signals, so a change that only announces the former redraws the curve
    while leaving its handles behind.
    """
    model = _make_curve_model(profile.library.get_action(_BEZIER_UUID))
    model.selectedPoint = 1
    log = _RedrawLog(model)

    for name, value in [
        ("selectedRightSlope", 0.6),
        ("selectedRightLength", 0.4),
        ("selectedLeftSlope", 0.5),
        ("selectedLeftLength", 0.3),
    ]:
        with subtests.test(name):
            log.reset()
            model.setProperty(name, value)
            assert log.emitted != [], "no redraw at all"
            assert "curveChanged" in log.emitted
            assert "controlPointChanged" in log.emitted

    with subtests.test("point coordinates"):
        log.reset()
        model.updateSelectedPoint(0.1, -0.25)
        assert "curveChanged" in log.emitted
        assert "controlPointChanged" in log.emitted

    with subtests.test("dragging skips the marker rebuild"):
        # Dragging moves the markers in QML directly and rebuilds them once on
        # release, so the expensive signal must stay out of the drag path.
        log.reset()
        model.setControlHandle(0.3, -0.1, 1, "right", True)
        assert "curveChanged" in log.emitted
        assert "controlPointChanged" not in log.emitted


def test_control_point_handles_are_always_points(
    subtests: pytest.Subtests, profile: Profile
) -> None:
    """An end point's absent handle still has to read as a point.

    QML has no equivalent of a missing point, and handing it None makes every
    binding that touches the handle fail its type conversion at runtime.
    """
    model = _make_curve_model(profile.library.get_action(_BEZIER_UUID))
    points = model.controlPoints

    with subtests.test("handle presence"):
        assert [p.hasLeft for p in points] == [False, True, True]
        assert [p.hasRight for p in points] == [True, True, False]

    with subtests.test("handles are points"):
        for index, point in enumerate(points):
            for name in ["center", "handleLeft", "handleRight"]:
                value = getattr(point, name)
                assert value is not None, (index, name)
                assert isinstance(value, QtCore.QPointF), (index, name)


def test_handle_symmetry_ignored_by_older_readers(profile: Profile) -> None:
    """Older releases only read the point entries, so they have to describe
    the same curve whether or not handle symmetry is recorded alongside."""
    a = profile.library.get_action(_BEZIER_UUID)
    without_symmetry = _points(a.to_xml())

    a.curve.set_symmetric_handles(1, True)
    with_symmetry = a.to_xml()

    assert _symmetry_flags(with_symmetry) == [False, True, False]
    # Enabling symmetry mirrors the reference handle onto the opposing one, so
    # the left handle of the middle point is the only entry that may move.
    moved = [
        i
        for i, (before, after) in enumerate(
            zip(without_symmetry, _points(with_symmetry))
        )
        if before != after
    ]
    assert len(_points(with_symmetry)) == len(without_symmetry)
    assert moved == [2]

    # An older release ignores the unknown property and rebuilds the curve
    # from the points alone, arriving at exactly this curve.
    legacy = spline.CubicBezierSpline(
        [
            (p.x, p.y)
            for p in util.read_properties(
                with_symmetry.find("control-points"), "point", PropertyType.Point2D
            )
        ]
    )
    for x in _SAMPLE_POSITIONS:
        assert legacy(x) == a.curve(x), x
