# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import enum
from typing import (
    override,
    Any,
    List,
    Optional,
    TYPE_CHECKING,
)
from xml.etree import ElementTree

from PySide6 import (
    QtCore,
    QtQml,
)
from PySide6.QtCore import (
    Property,
    Signal,
    Slot,
)

from gremlin import (
    event_handler,
    spline,
    util,
)
from gremlin.base_classes import (
    AbstractActionData,
    AbstractFunctor,
    UserFeedback,
    Value,
)
from gremlin.error import (
    GremlinError,
    ProfileError,
)
from gremlin.profile import Library
from gremlin.types import (
    ActionProperty,
    InputType,
    PropertyType,
)

from gremlin.ui.action_model import (
    SequenceIndex,
    ActionModel,
)

if TYPE_CHECKING:
    from gremlin.ui.profile import InputItemBindingModel
    import gremlin.ui.type_aliases as ta


QML_IMPORT_NAME = "Gremlin.ActionPlugins"
QML_IMPORT_MAJOR_VERSION = 1

class DeadzoneIndex(enum.Enum):

    """Index of a specific deadzone marker in the deadzone list in
    ResponseCurveData."""

    LOW = 0
    CENTER_LOW = 1
    CENTER_HIGH = 2
    HIGH = 3


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

    def __init__(self, action: ResponseCurveData) -> None:
        super().__init__(action)

    @override
    def __call__(
            self,
            event: event_handler.Event,
            value: Value,
            properties: List[ActionProperty]=[]
    ) -> None:
        dz_value = deadzone(
            value.current,
            self.data.deadzone[DeadzoneIndex.LOW.value],
            self.data.deadzone[DeadzoneIndex.CENTER_LOW.value],
            self.data.deadzone[DeadzoneIndex.CENTER_HIGH.value],
            self.data.deadzone[DeadzoneIndex.HIGH.value]
        )
        value.current = self.data.curve(dz_value)


@QtQml.QmlElement
class Deadzone(QtCore.QObject):

    changed = Signal()
    lowModified = Signal(float)
    centerLowModified = Signal(float)
    centerHighModified = Signal(float)
    highModified = Signal(float)

    def __init__(self, data: ResponseCurveData, parent: ta.OQO = None) -> None:
        super().__init__(parent)

        self._data = data

    def _get_value(self, index: DeadzoneIndex) -> float:
        return self._data.deadzone[index.value]

    def _set_value(self, index: DeadzoneIndex, value: float) -> None:
        lookup = {
            DeadzoneIndex.LOW: self.lowModified,
            DeadzoneIndex.CENTER_LOW: self.centerLowModified,
            DeadzoneIndex.CENTER_HIGH: self.centerHighModified,
            DeadzoneIndex.HIGH: self.highModified
        }
        if value != self._data.deadzone[index.value]:
            self._data.deadzone[index.value] = value
            lookup[index].emit(value)

    low = Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, DeadzoneIndex.LOW),
        fset=lambda cls, value: Deadzone._set_value(cls, DeadzoneIndex.LOW, value),
        notify=lowModified
    )

    centerLow = Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, DeadzoneIndex.CENTER_LOW),
        fset=lambda cls, value: Deadzone._set_value(cls, DeadzoneIndex.CENTER_LOW, value),
        notify=centerLowModified
    )

    centerHigh = Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, DeadzoneIndex.CENTER_HIGH),
        fset=lambda cls, value: Deadzone._set_value(cls, DeadzoneIndex.CENTER_HIGH, value),
        notify=centerHighModified
    )

    high = Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, DeadzoneIndex.HIGH),
        fset=lambda cls, value: Deadzone._set_value(cls, DeadzoneIndex.HIGH, value),
        notify=highModified
    )


class ControlPoint(QtCore.QObject):

    changed = Signal()

    def __init__(
            self,
            center: Optional[QtCore.QPointF]=None,
            handle_left: Optional[QtCore.QPointF]=None,
            handle_right: Optional[QtCore.QPointF]=None,
            parent: Optional[QtCore.QPointF]=None
    ) -> None:
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
    selectedPointChanged = Signal()

    def __init__(
            self,
            data: AbstractActionData,
            binding_model: InputItemBindingModel,
            action_index: SequenceIndex,
            parent_index: SequenceIndex,
            parent: QtCore.QObject
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)

        self.widget_size = 400
        self._selected_point = 0
        # TODO: Find a better way, likely have the data class store symmetry
        #   mode information.
        # self._set_is_symmetric(True)

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

    @Property(QtCore.QPointF, notify=selectedPointChanged)
    def selectedPointCoord(self) -> QtCore.QPointF:
        point = self._data.curve.control_points()[self._selected_point]
        if type(self._data.curve) in [spline.PiecewiseLinear, spline.CubicSpline]:
            return QtCore.QPointF(point.x, point.y)
        elif isinstance(self._data.curve, spline.CubicBezierSpline):
            return QtCore.QPointF(point.center.x, point.center.y)
        else:
            raise GremlinError(
                f"Invalid curve type encountered {str(type(self._data.curve))}"
            )

    @Slot(float, float)
    def addControlPoint(self, x: float, y: float) -> None:
        self._data.curve.add_control_point(x, y)
        self.controlPointChanged.emit()
        self.curveChanged.emit()
        self.selectedPointChanged.emit()

    @Slot(int)
    def removeControlPoint(self, idx: int) -> None:
        self._data.curve.remove_control_point(idx)
        self._set_selected_point(0)
        self.redrawElements()

    @Slot(float, float, int, bool)
    def setControlPoint(
        self,
        x: float,
        y: float,
        idx: int,
        is_drag_event: bool
    ) -> None:
        self._data.curve.set_control_point(x, y, idx)
        self.curveChanged.emit()
        self.selectedPointChanged.emit()
        if not is_drag_event:
            self.controlPointChanged.emit()

    @Slot(float, float, int, str, bool)
    def setControlHandle(
        self,
        x: float,
        y: float,
        idx: int,
        handle: str,
        is_drag_event: bool
    ) -> None:
        points = self._data.curve.control_points()
        control = points[idx]
        if handle == "center":
            dx = x - control.center.x
            dy = y - control.center.y
            self._move_control_center(control, dx, dy)
            if self._data.curve.is_symmetric:
                self._move_control_center(points[len(points)-idx-1], -dx, -dy)
            self.selectedPointChanged.emit()
            if not is_drag_event:
                self.controlPointChanged.emit()
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

    @Slot(float, float)
    def updateSelectedPoint(self, x: float, y: float) -> None:
        if type(self._data.curve) in [spline.PiecewiseLinear, spline.CubicSpline]:
            self.setControlPoint(x, y, self._selected_point, False)
        elif isinstance(self._data.curve, spline.CubicBezierSpline):
            self.setControlHandle(x, y, self._selected_point, "center", False)

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
        self.selectedPointChanged.emit()

    @Slot()
    def redrawElements(self):
        self.changed.emit()
        self.curveChanged.emit()
        self.controlPointChanged.emit()

    def _move_control_center(
            self,
            control: spline.CubicBezierSpline.ControlPoint,
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
            self.selectedPointChanged.emit()
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
            self._set_selected_point(0)
            self.curveChanged.emit()
            self.controlPointChanged.emit()

    def _get_selected_point(self) -> int:
        return self._selected_point

    def _set_selected_point(self, index: int) -> None:
        if self._selected_point != index:
            self._selected_point = index
            self.selectedPointChanged.emit()

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

    selectedPoint = Property(
        int,
        fget=_get_selected_point,
        fset=_set_selected_point,
        notify=selectedPointChanged
    )




class ResponseCurveData(AbstractActionData):

    """Model of a description action."""

    version = 1
    name = "Response Curve"
    tag = "response-curve"
    icon = "\uF18C"

    functor = ResponseCurveFunctor
    model = ResponseCurveModel

    properties = (
        ActionProperty.ActivateDisabled,
    )
    input_types = (
        InputType.JoystickAxis,
    )

    def __init__(
            self,
            behavior_type: InputType=InputType.JoystickAxis
    ) -> None:
        super().__init__(behavior_type)

        # Model variables
        self.deadzone = [-1.0, 0.0, 0.0, 1.0]
        self.curve = spline.PiecewiseLinear()

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        lookup = {
            "PiecewiseLinear": spline.PiecewiseLinear,
            "CubicSpline": spline.CubicSpline,
            "CubicBezierSpline": spline.CubicBezierSpline
        }

        self._id = util.read_action_id(node)

        # Read deadzone values.
        dz_node = node.find("deadzone")
        if dz_node is None:
            raise ProfileError("Missing deadzone node")
        self.deadzone = [
            util.read_property(dz_node, "low", PropertyType.Float),
            util.read_property(dz_node, "center-low", PropertyType.Float),
            util.read_property(dz_node, "center-high", PropertyType.Float),
            util.read_property(dz_node, "high", PropertyType.Float)
        ]

        # Create curve using XML values.
        cp_node = node.find("control-points")
        if cp_node is None:
            raise ProfileError("Missing control-points node")
        points = util.read_properties(cp_node, "point", PropertyType.Point2D)
        self.curve = lookup[util.read_property(
            node, "curve-type", PropertyType.String
        )]([[p.x, p.y] for p in points])

    @override
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
                (
                    "low",
                    self.deadzone[DeadzoneIndex.LOW.value],
                    PropertyType.Float
                ),
                (
                    "center-low",
                    self.deadzone[DeadzoneIndex.CENTER_LOW.value],
                    PropertyType.Float
                ),
                (
                    "center-high",
                    self.deadzone[DeadzoneIndex.CENTER_HIGH.value],
                    PropertyType.Float
                ),
                (
                    "high",
                    self.deadzone[DeadzoneIndex.HIGH.value],
                    PropertyType.Float
                ),
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

    @override
    def user_feedback(self) -> list[UserFeedback]:
        return []

    @override
    def _valid_selectors(self) -> list[str]:
        return []

    @override
    def _get_container(self, selector: str) -> List[AbstractActionData]:
        raise GremlinError(f"{self.name}: has no containers")

    @override
    def _handle_behavior_change(
        self,
        old_behavior: InputType,
        new_behavior: InputType
    ) -> None:
        pass


create = ResponseCurveData
