# -*- coding: utf-8; -*-

# Copyright (C) 2016 Lionel Ott
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING
from xml.etree import ElementTree

from PySide6 import QtCore, QtGui, QtQml
from PySide6.QtCore import Property, Signal, Slot, QCborTag

from gremlin import event_handler, spline, util
from gremlin.base_classes import AbstractActionData, AbstractFunctor, Value
from gremlin.error import GremlinError, ProfileError
from gremlin.profile import Library
from gremlin.types import ActionProperty, InputType, PropertyType
from gremlin.util import clamp

from gremlin.ui.action_model import SequenceIndex, ActionModel

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1


def deadzone(
        value: float,
        low: float,
        low_center: float,
        high_center: float,
        high: float
) -> float:
    """Returns the mapped value taking the provided deadzone into
    account.

    The following relationship between the limits has to hold.
    -1 <= low < low_center <= 0 <= high_center < high <= 1

    Args:
        value: the raw input value
        low: low deadzone limit
        low_center: lower center deadzone limit
        high_center: upper center deadzone limit
        high: high deadzone limit

    Returns:
        Corrected value
    """
    if value >= 0:
        return min(1.0, max(0.0, (value - high_center) / abs(high - high_center)))
    else:
        return max(-1.0, min(0.0, (value - low_center) / abs(low - low_center)))


class ResponseCurveFunctor(AbstractFunctor):

    """Implements the function executed for the response curve at runtime."""

    def __init__(self, action: ResponseCurveData):
        super().__init__(action)

    def __call__(
            self,
            event: Event,
            value: Value,
            properties: list[ActionProperty]=[]
    ) -> None:
        dz_value = deadzone(
            value.current,
            self.data.deadzone[0],
            self.data.deadzone[1],
            self.data.deadzone[2],
            self.data.deadzone[3]
        )
        value.current = self.data.curve(dz_value)


@QtQml.QmlElement
class Deadzone(QtCore.QObject):

    changed = Signal()
    lowModified = Signal(float)
    centerLowModified = Signal(float)
    centerHighModified = Signal(float)
    highModified = Signal(float)

    def __init__(self, data: AbstractActionData, parent=QtCore.QObject):
        super().__init__(parent)

        self._data = data

    def _get_value(self, index: int) -> float:
        return self._data.deadzone[index]

    def _set_value(self, index: int, value: float) -> None:
        lookup = {
            0: self.lowModified,
            1: self.centerLowModified,
            2: self.centerHighModified,
            3: self.highModified
        }
        if value != self._data.deadzone[index]:
            self._data.deadzone[index] = value
            lookup[index].emit(value)

    low = Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, 0),
        fset=lambda cls, value: Deadzone._set_value(cls, 0, value),
        notify=lowModified
    )

    centerLow = Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, 1),
        fset=lambda cls, value: Deadzone._set_value(cls, 1, value),
        notify=centerLowModified
    )

    centerHigh = Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, 2),
        fset=lambda cls, value: Deadzone._set_value(cls, 2, value),
        notify=centerHighModified
    )

    high = Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, 3),
        fset=lambda cls, value: Deadzone._set_value(cls, 3, value),
        notify=highModified
    )


class ControlPoint(QtCore.QObject):

    changed = Signal()

    def __init__(
            self,
            center: Optional[QtCore.QPointF]=None,
            handle_left: Optional[QtCore.QPointF]=None,
            handle_right: Optional[QtCore.QPointF]=None,
            parent: Optional[QtCore.QtCore.QPointF]=None
    ):
        super().__init__(parent)
        self._center = center
        self._handle_left = handle_left
        self._handle_right = handle_right

    @Property(QtCore.QPointF, notify=changed)
    def center(self) -> QtCore.QPointF:
        return self._center

    @Property(QtCore.QPointF, notify=changed)
    def handleLeft(self) -> QtCore.QPointF:
        return self._handle_left

    @Property(QtCore.QPointF, notify=changed)
    def handleRight(self) -> QtCore.QPointF:
        return self._handle_right

    @Property(bool, notify=changed)
    def hasHandles(self) -> bool:
        return self._handle_left is not None or self._handle_right is not None

    @Property(bool, notify=changed)
    def hasLeft(self) -> bool:
        return self._handle_left is not None

    @Property(bool, notify=changed)
    def hasRight(self) -> bool:
        return self._handle_right is not None


class ResponseCurveModel(ActionModel):

    changed = Signal()
    deadzoneChanged = Signal()
    curveChanged = Signal()
    controlPointChanged = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ):
        super().__init__(data, binding_model, action_index, parent_index, parent)

        self.widget_size = 400

    def _qml_path_impl(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:response_curve/ResponseCurveAction.qml"
        ).fileName()

    def _action_behavior(self) -> str:
        return  self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @Property(Deadzone, notify=deadzoneChanged)
    def deadzone(self) -> Deadzone:
        return Deadzone(self._data, self)

    @Slot(float, float)
    def addControlPoint(self, x: float, y: float) -> None:
        self._data.curve.add_control_point(x, y)
        self.controlPointChanged.emit()
        self.curveChanged.emit()

    @Slot(float, float, int)
    def setControlPoint(self, x: float, y: float, idx: int) -> None:
        self._data.curve.set_control_point(x, y, idx)
        self.curveChanged.emit()

    @Slot(float, float, int, str)
    def setControlHandle(self, x: float, y: float, idx: int, handle: str) -> None:
        points = self._data.curve.control_points()
        control = points[idx]
        if handle == "center":
            dx = x - control.center.x
            dy = y - control.center.y
            self._move_control_center(control, dx, dy)
            if self._data.curve.is_symmetric:
                self._move_control_center(points[len(points)-idx-1], -dx, -dy)
        if handle == "left" and control.handle_left:
            dx = x - control.handle_left.x
            dy = y - control.handle_left.y
            self._move_control_handle(control.handle_left, dx, dy)
            if self._data.curve.is_symmetric:
                self._move_control_handle(
                    points[len(points) - idx - 1].handle_right, -dx, -dy
                )
        elif handle == "right" and control.handle_right:
            dx = x - control.handle_right.x
            dy = y - control.handle_right.y
            self._move_control_handle(control.handle_right, dx, dy)
            if self._data.curve.is_symmetric:
                self._move_control_handle(
                    points[len(points)-idx-1].handle_left, -dx, -dy
                )
        self._data.curve.fit()
        self.curveChanged.emit()

    @Slot(int)
    def setWidgetSize(self, size: int) -> None:
        self.widget_size = size
        self.curveChanged.emit()
        self.controlPointChanged.emit()

    @Slot()
    def invertCurve(self) -> None:
        self._data.curve.invert()
        self.curveChanged.emit()
        self.controlPointChanged.emit()

    @Slot()
    def redrawElements(self):
        self.changed.emit()
        self.curveChanged.emit()
        self.controlPointChanged.emit()

    def _move_control_center(
            self,
            control: ControlPoint,
            dx: float,
            dy: float
    ) -> None:
        """Modifies a control point and it's handles based on a delta movement.

        Args:
            control: the control point to modify
            dx: change in x direction
            dy: change in y direction
        """
        # Move the handles such that they retain their relative position to
        # the center control
        if control.handle_left:
            control.handle_left.x += dx
            control.handle_left.y += dy
        if control.handle_right:
            control.handle_right.x += dx
            control.handle_right.y += dy
        control.center.x += dx
        control.center.y += dy

    def _move_control_handle(
            self,
            handle: QtCore.QPointF,
            dx: float,
            dy: float
    ) -> None:
        """Modifies a control handle based on a delta movement.

        Args:
            handle: point representing the control handle
            dx: change in x direction
            dy: change in y direction
        """
        handle.x += dx
        handle.y += dy

    def _get_line_points(self) -> List[QtCore.QPointF]:
        points = []
        scaling_factor = self.widget_size / 2.0
        for i in range(-100, 101):
            points.append(QtCore.QPointF(
                (i / 100.0 + 1) * scaling_factor,
                self.widget_size - (self._data.curve(i / 100.0) + 1) * scaling_factor
            ))
        return points

    def _get_control_points(self) -> List[ControlPoint]:
        if type(self._data.curve) in [spline.PiecewiseLinear, spline.CubicSpline]:
            return [
                ControlPoint(center=QtCore.QPointF(p.x, p.y), parent=self) for
                p in self._data.curve.control_points()
            ]
        elif isinstance(self._data.curve, spline.CubicBezierSpline):
            points = []
            for p in self._data.curve.control_points():
                center = QtCore.QPointF(p.center.x, p.center.y)
                left = None
                if p.handle_left is not None:
                    left = QtCore.QPointF(p.handle_left.x, p.handle_left.y)
                right = None
                if p.handle_right is not None:
                    right = QtCore.QPointF(p.handle_right.x, p.handle_right.y)
                points.append(ControlPoint(center, left, right, self))
            return points
        else:
            raise GremlinError(
                f"Invalid curve type encountered {str(type(self._data.curve))}"
            )

    def _get_is_symmetric(self) -> bool:
        return self._data.curve.is_symmetric

    def _set_is_symmetric(self, is_symmetric: bool) -> None:
        if self._data.curve.is_symmetric != is_symmetric:
            self._data.curve.is_symmetric = is_symmetric
            self.curveChanged.emit()
            self.controlPointChanged.emit()
            self.changed.emit()

    def _get_curve_type(self) -> str:
        lookup = {
            spline.PiecewiseLinear: "Piecewise Linear",
            spline.CubicSpline: "Cubic Spline",
            spline.CubicBezierSpline: "Cubic Bezier Spline"
        }
        return lookup[type(self._data.curve)]

    def _set_curve_type(self, value: str) -> None:
        lookup = {
            "Piecewise Linear": spline.PiecewiseLinear,
            "Cubic Spline": spline.CubicSpline,
            "Cubic Bezier Spline": spline.CubicBezierSpline
        }
        curve_type = lookup[value]
        if curve_type != type(self._data.curve):
            self._data.curve = curve_type()
            self.curveChanged.emit()
            self.controlPointChanged.emit()

    linePoints = Property(
        list,
        fget=_get_line_points,
        notify=curveChanged
    )

    controlPoints = Property(
        list,
        fget=_get_control_points,
        notify=controlPointChanged
    )

    isSymmetric = Property(
        bool,
        fget=_get_is_symmetric,
        fset=_set_is_symmetric,
        notify=changed
    )

    curveType = Property(
        str,
        fget=_get_curve_type,
        fset=_set_curve_type,
        notify=curveChanged
    )


class ResponseCurveData(AbstractActionData):

    """Model of a description action."""

    version = 1
    name = "Response Curve"
    tag = "response-curve"
    icon = "\uF18C"

    functor = ResponseCurveFunctor
    model = ResponseCurveModel

    properties = [
        ActionProperty.ActivateDisabled,
    ]
    input_types = [
        InputType.JoystickAxis,
    ]

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickAxis
    ):
        super().__init__(behavior_type)

        # Model variables
        self.deadzone = [-1.0, 0.0, 0.0, 1.0]
        self.curve = spline.PiecewiseLinear()

    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        lookup = {
            "PiecewiseLinear": spline.PiecewiseLinear,
            "CubicSpline": spline.CubicSpline,
            "CubicBezierSpline": spline.CubicBezierSpline
        }

        self._id = util.read_action_id(node)
        # Read deadzone values
        dz_node = node.find("deadzone")
        if dz_node is None:
            raise ProfileError("Missing deadzone node")
        self.deadzone = [
            util.read_property(dz_node, "low", PropertyType.Float),
            util.read_property(dz_node, "center-low", PropertyType.Float),
            util.read_property(dz_node, "center-high", PropertyType.Float),
            util.read_property(dz_node, "high", PropertyType.Float)
        ]
        # Create curve using XML values
        cp_node = node.find("control-points")
        if cp_node is None:
            raise ProfileError("Missing control-points node")
        points = util.read_properties(cp_node, "point", PropertyType.Point2D)
        self.curve = lookup[util.read_property(
            node, "curve-type", PropertyType.String
        )]([[p.x, p.y] for p in points])

    def _to_xml(self) -> ElementTree.Element:
        lookup = {
            spline.PiecewiseLinear: "PiecewiseLinear",
            spline.CubicSpline: "CubicSpline",
            spline.CubicBezierSpline: "CubicBezierSpline"
        }

        node = util.create_action_node(ResponseCurveData.tag, self._id)
        node.append(util.create_node_from_data(
            "deadzone",
            [
                ("low", self.deadzone[0], PropertyType.Float),
                ("center-low", self.deadzone[1], PropertyType.Float),
                ("center-high", self.deadzone[2], PropertyType.Float),
                ("high", self.deadzone[3], PropertyType.Float),
            ]
        ))
        points = []
        match type(self.curve):
            case spline.PiecewiseLinear | spline.CubicSpline:
                points = self.curve.control_points()
            case spline.CubicBezierSpline:
                for cp in self.curve.control_points():
                    if cp.handle_left:
                        points.append(cp.handle_left)
                    points.append(cp.center)
                    if cp.handle_right:
                        points.append(cp.handle_right)

        node.append(util.create_node_from_data(
            "control-points",
            [("point", cp, PropertyType.Point2D) for cp in points]
        ))
        node.append(util.create_property_node(
            "curve-type",
            lookup[type(self.curve)],
            PropertyType.String
        ))

        return node

    def is_valid(self) -> bool:
        return True

    def _valid_selectors(self) -> List[str]:
        return []

    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = ResponseCurveData
