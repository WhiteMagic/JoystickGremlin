# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib
from typing import cast

import pytest
import pytestqt.exceptions
from PySide6 import (
    QtCore,
    QtQuick,
)

import gremlin.ui.backend
from action_plugins.response_curve import ResponseCurveData
from gremlin import spline
from gremlin.types import Point2D
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_logical_input_with_action,
    reload_action,
    set_spin_box_value,
    typed_number,
)

ACTION = "Response Curve"
CURVE_TYPES: dict[str, type[spline.AbstractCurve]] = {
    "Piecewise Linear": spline.PiecewiseLinear,
    "Cubic Spline": spline.CubicSpline,
    "Cubic Bezier Spline": spline.CubicBezierSpline,
}

type Points = list[tuple[float, float]]


def _add_response_curve(ui: UiDriver) -> tuple[str, QtQuick.QQuickItem]:
    return add_logical_input_with_action(ui, "Axis", ACTION)


def _response_curve() -> ResponseCurveData:
    """Returns the profile's only Response Curve."""
    library = gremlin.ui.backend.Backend().profile.library
    (action,) = library.actions_by_type(ResponseCurveData)
    return cast(ResponseCurveData, action)


def _select_curve_type(
    ui: UiDriver, action: QtQuick.QQuickItem, curve_type: str
) -> None:
    combo = ui.find_item("curveTypeCombo", action)
    # Selecting the current type changes nothing.
    if combo.property("currentText") == curve_type:
        other_type = next(name for name in CURVE_TYPES if name != curve_type)
        ui.select(combo, other_type)
    ui.select(combo, curve_type)
    ui.wait_until(lambda: type(_response_curve().curve) is CURVE_TYPES[curve_type])


def _curve_position(area: QtQuick.QQuickItem, x: float, y: float) -> QtCore.QPointF:
    """Maps curve coordinates to coordinates of the curve's area."""
    return QtCore.QPointF((x + 1) / 2 * area.width(), (1 - y) / 2 * area.height())


def _add_point(ui: UiDriver, action: QtQuick.QQuickItem, x: float, y: float) -> None:
    area = ui.find_item("curveArea", action)
    ui.double_click(area, _curve_position(area, x, y))


def _drag_to(
    ui: UiDriver,
    action: QtQuick.QQuickItem,
    item: QtQuick.QQuickItem,
    x: float,
    y: float,
) -> None:
    """Drags a point or handle by its center to the curve coordinates x, y."""
    area = ui.find_item("curveArea", action)
    ui.drag_item_from_to(
        item,
        QtCore.QPointF(item.width() / 2, item.height() / 2),
        item.mapFromItem(area, _curve_position(area, x, y)),
    )


def _find_point(
    ui: UiDriver, action: QtQuick.QQuickItem, index: int
) -> QtQuick.QQuickItem:
    return ui.find_item(f"curvePoint_{index}", action)


def _select_point(ui: UiDriver, action: QtQuick.QQuickItem, index: int) -> None:
    """Clicks the point, then waits for the coordinate spinboxes to show it."""
    ui.click(_find_point(ui, action, index))
    x = _centers()[index][0]
    spin_box = ui.find_item("xCoordinateSpinBox", action)
    ui.wait_until(lambda: spin_box.property("value") == pytest.approx(x, abs=0.01))


def _coordinates(point: Point2D) -> tuple[float, float]:
    return point.x, point.y


def _centers() -> Points:
    return [
        _coordinates(
            point.center
            if isinstance(point, spline.CubicBezierSpline.ControlPoint)
            else point
        )
        for point in _response_curve().curve.control_points()
    ]


def _wait_for_points(ui: UiDriver, expected: Points) -> None:
    """Waits until the curve's control point centers are expected."""

    # One pixel of the curve is about 0.0044.
    def matches() -> bool:
        actual = _centers()
        return len(actual) == len(expected) and all(
            coordinate == pytest.approx(expected_coordinate, abs=0.01)
            for point, expected_point in zip(actual, expected, strict=True)
            for coordinate, expected_coordinate in zip(
                point, expected_point, strict=True
            )
        )

    try:
        ui.wait_until(matches)
    except pytestqt.exceptions.TimeoutError:
        pass
    assert matches(), f"Control points are {_centers()} instead of {expected}"


def _field_value(field: QtQuick.QQuickItem) -> float:
    value, is_valid = QtCore.QLocale().toDouble(field.property("text"))
    assert is_valid, f"Field shows '{field.property('text')}'"
    return value


def _set_field(ui: UiDriver, field: QtQuick.QQuickItem, value: float) -> None:
    ui.type_text(field, typed_number(value))
    ui.wait_for_value(lambda: _field_value(field), pytest.approx(value))


@pytest.mark.parametrize("curve_type", CURVE_TYPES)
def test_points(ui: UiDriver, empty_profile: pathlib.Path, curve_type: str) -> None:
    label, action = _add_response_curve(ui)
    _select_curve_type(ui, action, curve_type)
    _wait_for_points(ui, [(-1.0, -1.0), (1.0, 1.0)])

    _add_point(ui, action, -0.5, 0.2)
    _wait_for_points(ui, [(-1.0, -1.0), (-0.5, 0.2), (1.0, 1.0)])
    _add_point(ui, action, 0.5, -0.2)
    _wait_for_points(ui, [(-1.0, -1.0), (-0.5, 0.2), (0.5, -0.2), (1.0, 1.0)])

    _drag_to(ui, action, _find_point(ui, action, 1), -0.4, 0.6)
    _wait_for_points(ui, [(-1.0, -1.0), (-0.4, 0.6), (0.5, -0.2), (1.0, 1.0)])

    _select_point(ui, action, 2)
    set_spin_box_value(ui, ui.find_item("xCoordinateSpinBox", action), 0.3)
    set_spin_box_value(ui, ui.find_item("yCoordinateSpinBox", action), -0.5)
    _wait_for_points(ui, [(-1.0, -1.0), (-0.4, 0.6), (0.3, -0.5), (1.0, 1.0)])

    _select_point(ui, action, 1)
    ui.key_click(QtCore.Qt.Key.Key_Delete)
    _wait_for_points(ui, [(-1.0, -1.0), (0.3, -0.5), (1.0, 1.0)])

    ui.click(ui.find_item("invertCurveButton", action))
    _wait_for_points(ui, [(-1.0, 1.0), (0.3, 0.5), (1.0, -1.0)])

    action = reload_action(ui, empty_profile, label, ACTION)
    assert ui.find_item("curveTypeCombo", action).property("currentText") == curve_type
    _wait_for_points(ui, [(-1.0, 1.0), (0.3, 0.5), (1.0, -1.0)])
    # The reloaded editor selects the first point.
    assert ui.find_item("xCoordinateSpinBox", action).property(
        "value"
    ) == pytest.approx(-1.0)
    assert ui.find_item("yCoordinateSpinBox", action).property(
        "value"
    ) == pytest.approx(1.0)


@pytest.mark.parametrize("curve_type", CURVE_TYPES)
def test_symmetric(ui: UiDriver, empty_profile: pathlib.Path, curve_type: str) -> None:
    label, action = _add_response_curve(ui)
    _select_curve_type(ui, action, curve_type)

    ui.click(ui.find_item("symmetricCheckBox", action))
    _wait_for_points(ui, [(-1.0, -1.0), (0.0, 0.0), (1.0, 1.0)])

    _add_point(ui, action, -0.5, -0.2)
    _add_point(ui, action, -0.2, -0.6)
    _wait_for_points(
        ui,
        [
            (-1.0, -1.0),
            (-0.5, -0.2),
            (-0.2, -0.6),
            (0.0, 0.0),
            (0.2, 0.6),
            (0.5, 0.2),
            (1.0, 1.0),
        ],
    )

    _drag_to(ui, action, _find_point(ui, action, 1), -0.6, -0.4)
    _wait_for_points(
        ui,
        [
            (-1.0, -1.0),
            (-0.6, -0.4),
            (-0.2, -0.6),
            (0.0, 0.0),
            (0.2, 0.6),
            (0.6, 0.4),
            (1.0, 1.0),
        ],
    )

    _select_point(ui, action, 2)
    ui.key_click(QtCore.Qt.Key.Key_Delete)
    symmetric_points = [(-1.0, -1.0), (-0.6, -0.4), (0.0, 0.0), (0.6, 0.4), (1.0, 1.0)]
    _wait_for_points(ui, symmetric_points)

    # The symmetric flag isn't saved, the mirrored points are.
    reload_action(ui, empty_profile, label, ACTION)
    _wait_for_points(ui, symmetric_points)


def test_bezier_handles(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = _add_response_curve(ui)
    _select_curve_type(ui, action, "Cubic Bezier Spline")
    _add_point(ui, action, 0.2, 0.1)
    _wait_for_points(ui, [(-1.0, -1.0), (0.2, 0.1), (1.0, 1.0)])

    point = _find_point(ui, action, 1)
    _drag_to(ui, action, ui.find_item("leftHandle", point), 0.0, -0.2)
    point = _find_point(ui, action, 1)
    _drag_to(ui, action, ui.find_item("rightHandle", point), 0.4, 0.4)

    def handles() -> list[float]:
        middle_point = cast(
            spline.CubicBezierSpline.ControlPoint,
            _response_curve().curve.control_points()[1],
        )
        assert middle_point.handle_left is not None
        assert middle_point.handle_right is not None
        return [
            *_coordinates(middle_point.handle_left),
            *_coordinates(middle_point.handle_right),
        ]

    dragged_handles = pytest.approx([0.0, -0.2, 0.4, 0.4], abs=0.01)
    ui.wait_for_value(handles, dragged_handles)

    reload_action(ui, empty_profile, label, ACTION)
    _wait_for_points(ui, [(-1.0, -1.0), (0.2, 0.1), (1.0, 1.0)])
    assert handles() == dragged_handles


def test_deadzone(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    label, action = _add_response_curve(ui)
    lower_slider = ui.find_item("lowerDeadzoneSlider", action)
    upper_slider = ui.find_item("upperDeadzoneSlider", action)
    _set_field(ui, ui.find_item("firstValueField", lower_slider), -0.9)
    _set_field(ui, ui.find_item("secondValueField", lower_slider), -0.1)
    _set_field(ui, ui.find_item("firstValueField", upper_slider), 0.1)
    _set_field(ui, ui.find_item("secondValueField", upper_slider), 0.9)
    expected = [-0.9, -0.1, 0.1, 0.9]
    assert _response_curve().deadzone == pytest.approx(expected)

    action = reload_action(ui, empty_profile, label, ACTION)
    assert _response_curve().deadzone == pytest.approx(expected)
    lower_slider = ui.find_item("lowerDeadzoneSlider", action)
    upper_slider = ui.find_item("upperDeadzoneSlider", action)
    shown = [
        _field_value(ui.find_item(field, slider))
        for slider in [lower_slider, upper_slider]
        for field in ["firstValueField", "secondValueField"]
    ]
    assert shown == pytest.approx(expected)
