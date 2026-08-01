# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import enum
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    cast,
    override,
)
from xml.etree import ElementTree

from PySide6 import (
    QtCore,
    QtQml,
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
    ActionModel,
    SequenceIndex,
)

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta
    from gremlin.ui.profile import InputItemBindingModel


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
    value: float, low: float, low_center: float, high_center: float, high: float
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
        return min(
            1.0, max(0.0, (value - high_center) / max(0.01, abs(high - high_center)))
        )
    else:
        return max(
            -1.0, min(0.0, (value - low_center) / max(0.01, abs(low - low_center)))
        )


class ResponseCurveFunctor(AbstractFunctor):
    """Implements the function executed for the response curve at runtime."""

    def __init__(self, action: ResponseCurveData) -> None:
        super().__init__(action)

    @override
    def __call__(
        self,
        event: event_handler.Event,
        value: Value,
        properties: List[ActionProperty] = [],
    ) -> None:
        dz_value = deadzone(
            value.current,
            self.data.deadzone[DeadzoneIndex.LOW.value],
            self.data.deadzone[DeadzoneIndex.CENTER_LOW.value],
            self.data.deadzone[DeadzoneIndex.CENTER_HIGH.value],
            self.data.deadzone[DeadzoneIndex.HIGH.value],
        )
        value.current = self.data.curve(dz_value)


@QtQml.QmlElement
class Deadzone(QtCore.QObject):
    changed = QtCore.Signal()
    lowModified = QtCore.Signal(float)
    centerLowModified = QtCore.Signal(float)
    centerHighModified = QtCore.Signal(float)
    highModified = QtCore.Signal(float)

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
            DeadzoneIndex.HIGH: self.highModified,
        }
        if value != self._data.deadzone[index.value]:
            self._data.deadzone[index.value] = value
            lookup[index].emit(value)

    low = QtCore.Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, DeadzoneIndex.LOW),
        fset=lambda cls, value: Deadzone._set_value(cls, DeadzoneIndex.LOW, value),
        notify=lowModified,
    )

    centerLow = QtCore.Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, DeadzoneIndex.CENTER_LOW),
        fset=lambda cls, value: Deadzone._set_value(
            cls, DeadzoneIndex.CENTER_LOW, value
        ),
        notify=centerLowModified,
    )

    centerHigh = QtCore.Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, DeadzoneIndex.CENTER_HIGH),
        fset=lambda cls, value: Deadzone._set_value(
            cls, DeadzoneIndex.CENTER_HIGH, value
        ),
        notify=centerHighModified,
    )

    high = QtCore.Property(
        float,
        fget=lambda cls: Deadzone._get_value(cls, DeadzoneIndex.HIGH),
        fset=lambda cls, value: Deadzone._set_value(cls, DeadzoneIndex.HIGH, value),
        notify=highModified,
    )


class ControlPoint(QtCore.QObject):
    changed = QtCore.Signal()

    def __init__(
        self,
        center: Optional[QtCore.QPointF] = None,
        handle_left: Optional[QtCore.QPointF] = None,
        handle_right: Optional[QtCore.QPointF] = None,
        parent: Optional[QtCore.QPointF] = None,
        symmetric_handles: bool = False,
    ) -> None:
        super().__init__(parent)
        self._center = center
        self._handle_left = handle_left
        self._handle_right = handle_right
        self._symmetric_handles = symmetric_handles

    @QtCore.Property(QtCore.QPointF, notify=changed)
    def center(self) -> QtCore.QPointF:
        return self._center

    # The end points of a curve only possess a single handle. QML has no
    # equivalent of a missing point, so the absent one reads as the origin
    # and hasLeft/hasRight say whether it exists at all.
    @QtCore.Property(QtCore.QPointF, notify=changed)
    def handleLeft(self) -> QtCore.QPointF:
        return self._handle_left if self._handle_left is not None else QtCore.QPointF()

    @QtCore.Property(QtCore.QPointF, notify=changed)
    def handleRight(self) -> QtCore.QPointF:
        return (
            self._handle_right if self._handle_right is not None else QtCore.QPointF()
        )

    @QtCore.Property(bool, notify=changed)
    def hasHandles(self) -> bool:
        return self._handle_left is not None or self._handle_right is not None

    @QtCore.Property(bool, notify=changed)
    def hasLeft(self) -> bool:
        return self._handle_left is not None

    @QtCore.Property(bool, notify=changed)
    def hasRight(self) -> bool:
        return self._handle_right is not None

    @QtCore.Property(bool, notify=changed)
    def symmetricHandles(self) -> bool:
        return self._symmetric_handles


class ResponseCurveModel(ActionModel):
    changed = QtCore.Signal()
    deadzoneChanged = QtCore.Signal()
    curveChanged = QtCore.Signal()
    controlPointChanged = QtCore.Signal()
    selectedPointChanged = QtCore.Signal()

    def __init__(
        self,
        data: AbstractActionData,
        binding_model: InputItemBindingModel,
        action_index: SequenceIndex,
        parent_index: SequenceIndex,
        parent: QtCore.QObject,
    ) -> None:
        super().__init__(data, binding_model, action_index, parent_index, parent)

        self.widget_size = 400
        self._selected_point = 0
        # TODO: Find a better way, likely have the data class store symmetry
        #   mode information.
        # self._set_is_symmetric(True)

    def _qml_path_impl(self) -> str:
        return (
            "file:///"
            + QtCore.QFile(
                "core_plugins:response_curve/ResponseCurveAction.qml"
            ).fileName()
        )

    def _action_behavior(self) -> str:
        return self._binding_model.get_action_model_by_sidx(
            self._parent_sequence_index.index
        ).actionBehavior

    @QtCore.Property(Deadzone, notify=deadzoneChanged)
    def deadzone(self) -> Deadzone:
        return Deadzone(self._data, self)

    @QtCore.Property(QtCore.QPointF, notify=selectedPointChanged)
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

    @QtCore.Slot(float, float)
    def addControlPoint(self, x: float, y: float) -> None:
        self._data.curve.add_control_point(x, y)
        self.controlPointChanged.emit()
        self.curveChanged.emit()
        self.selectedPointChanged.emit()

    @QtCore.Slot(int)
    def removeControlPoint(self, idx: int) -> None:
        self._data.curve.remove_control_point(idx)
        self._set_selected_point(0)
        self.redrawElements()

    @QtCore.Slot(float, float, int, bool)
    def setControlPoint(
        self, x: float, y: float, idx: int, is_drag_event: bool
    ) -> None:
        self._data.curve.set_control_point(x, y, idx)
        self.curveChanged.emit()
        self.selectedPointChanged.emit()
        if not is_drag_event:
            self.controlPointChanged.emit()

    @QtCore.Slot(float, float, int, str, bool)
    def setControlHandle(
        self, x: float, y: float, idx: int, handle: str, is_drag_event: bool
    ) -> None:
        points = self._data.curve.control_points()
        control = points[idx]
        if handle == "center":
            dx = x - control.center.x
            dy = y - control.center.y
            self._move_control_center(control, dx, dy)
            if self._data.curve.is_symmetric:
                self._move_control_center(points[len(points) - idx - 1], -dx, -dy)
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
            self._mirror_handles(idx, "left")
        elif handle == "right" and control.handle_right:
            dx = x - control.handle_right.x
            dy = y - control.handle_right.y
            self._move_control_handle(control.handle_right, dx, dy)
            if self._data.curve.is_symmetric:
                self._move_control_handle(
                    points[len(points) - idx - 1].handle_left, -dx, -dy
                )
            self._mirror_handles(idx, "right")
        self._data.curve.fit()
        self.curveChanged.emit()
        if handle in ["left", "right"]:
            self.selectedPointChanged.emit()

    @QtCore.Slot(float, float)
    def updateSelectedPoint(self, x: float, y: float) -> None:
        if type(self._data.curve) in [spline.PiecewiseLinear, spline.CubicSpline]:
            self.setControlPoint(x, y, self._selected_point, False)
        elif isinstance(self._data.curve, spline.CubicBezierSpline):
            self.setControlHandle(x, y, self._selected_point, "center", False)

    @QtCore.Slot(float, result=list)
    def curveInfoAt(self, x: float) -> list[float]:
        """Returns the curve's output and slope at the given input position.

        Args:
            x: input position, in the [-1, 1] axis range

        Returns:
            Curve output at x followed by the curve's slope at x
        """
        x = util.clamp(x, -1.0, 1.0)
        delta = 0.001
        low = max(-1.0, x - delta)
        high = min(1.0, x + delta)
        slope = 0.0
        if high > low:
            slope = (self._data.curve(high) - self._data.curve(low)) / (high - low)
        return [self._data.curve(x), slope]

    @QtCore.Slot(int)
    def setWidgetSize(self, size: int) -> None:
        self.widget_size = size
        self.curveChanged.emit()
        self.controlPointChanged.emit()

    @QtCore.Slot()
    def invertCurve(self) -> None:
        self._data.curve.invert()
        self.curveChanged.emit()
        self.controlPointChanged.emit()
        self.selectedPointChanged.emit()

    @QtCore.Slot()
    def redrawElements(self) -> None:
        self.changed.emit()
        self.curveChanged.emit()
        self.controlPointChanged.emit()
        self.selectedPointChanged.emit()

    def _move_control_center(
        self, control: spline.CubicBezierSpline.ControlPoint, dx: float, dy: float
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
        self, handle: QtCore.QPointF, dx: float, dy: float
    ) -> None:
        """Modifies a control handle based on a delta movement.

        Args:
            handle: point representing the control handle
            dx: change in x direction
            dy: change in y direction
        """
        handle.x += dx
        handle.y += dy

    def _bezier_curve(self) -> spline.CubicBezierSpline | None:
        """Returns the curve if it is a Bezier spline and None otherwise.

        Returns:
            The Bezier spline being edited, None for any other curve type
        """
        if isinstance(self._data.curve, spline.CubicBezierSpline):
            return self._data.curve
        return None

    def _mirror_handles(self, idx: int, side: str) -> None:
        """Re-establishes handle symmetry after a handle has been moved.

        Args:
            idx: index of the control point whose handle was moved
            side: handle that was moved, "left" or "right"
        """
        curve = self._bezier_curve()
        if curve is None:
            return

        curve.enforce_handle_symmetry(idx, side)
        if curve.is_symmetric:
            curve.enforce_handle_symmetry(
                len(curve.control_points()) - idx - 1,
                "right" if side == "left" else "left",
            )

    def _handle_geometry(self, side: str) -> tuple[float, float]:
        """Returns slope and length of the selected point's handle.

        Args:
            side: "left" or "right" handle of the selected control point

        Returns:
            Slope and length of the handle, (0, 0) if there is no such handle
        """
        curve = self._bezier_curve()
        if curve is None:
            return (0.0, 0.0)
        return curve.handle_geometry(self._selected_point, side)

    def _set_handle_component(self, side: str, index: int, value: float) -> None:
        """Sets the slope or the length of the selected point's handle.

        Args:
            side: "left" or "right" handle of the selected control point
            index: 0 to set the slope, 1 to set the length
            value: new value for the given component
        """
        curve = self._bezier_curve()
        if curve is None:
            return

        geometry = list(self._handle_geometry(side))
        if geometry[index] == value:
            return
        geometry[index] = value

        idx = self._selected_point
        curve.set_handle_geometry(idx, side, geometry[0], geometry[1])
        # In symmetry mode the mirrored point's opposing handle has the very
        # same slope and length.
        if curve.is_symmetric:
            curve.set_handle_geometry(
                len(curve.control_points()) - idx - 1,
                "right" if side == "left" else "left",
                geometry[0],
                geometry[1],
            )
        self.curveChanged.emit()
        # The markers are not being dragged here, so they have to be rebuilt
        # for the handles to follow the values that were entered.
        self.controlPointChanged.emit()
        self.selectedPointChanged.emit()

    def _has_handle(self, side: str) -> bool:
        curve = self._bezier_curve()
        if curve is None:
            return False
        return curve.handle(self._selected_point, side) is not None

    def _get_selected_symmetric_handles(self) -> bool:
        curve = self._bezier_curve()
        if curve is None:
            return False
        return curve.control_points()[self._selected_point].symmetric_handles

    def _set_selected_symmetric_handles(self, is_symmetric: bool) -> None:
        curve = self._bezier_curve()
        if curve is None or self._get_selected_symmetric_handles() == is_symmetric:
            return

        curve.set_symmetric_handles(self._selected_point, is_symmetric)
        self.curveChanged.emit()
        self.controlPointChanged.emit()
        self.selectedPointChanged.emit()

    def _get_line_points(self) -> List[QtCore.QPointF]:
        points = []
        scaling_factor = self.widget_size / 2.0
        for i in range(-100, 101):
            points.append(
                QtCore.QPointF(
                    (i / 100.0 + 1) * scaling_factor,
                    self.widget_size
                    - (self._data.curve(i / 100.0) + 1) * scaling_factor,
                )
            )
        return points

    def _get_control_points(self) -> List[ControlPoint]:
        if type(self._data.curve) in [spline.PiecewiseLinear, spline.CubicSpline]:
            return [
                ControlPoint(center=QtCore.QPointF(p.x, p.y), parent=self)
                for p in self._data.curve.control_points()
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
                points.append(
                    ControlPoint(center, left, right, self, p.symmetric_handles)
                )
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
            spline.CubicBezierSpline: "Cubic Bezier Spline",
        }
        return lookup[type(self._data.curve)]

    def _set_curve_type(self, value: str) -> None:
        lookup = {
            "Piecewise Linear": spline.PiecewiseLinear,
            "Cubic Spline": spline.CubicSpline,
            "Cubic Bezier Spline": spline.CubicBezierSpline,
        }
        curve_type = lookup[value]
        if curve_type is not type(self._data.curve):
            self._data.curve = curve_type()
            self._set_selected_point(0)
            self.curveChanged.emit()
            self.controlPointChanged.emit()
            self.selectedPointChanged.emit()

    def _get_selected_point(self) -> int:
        return self._selected_point

    def _set_selected_point(self, index: int) -> None:
        if self._selected_point != index:
            self._selected_point = index
            self.selectedPointChanged.emit()

    linePoints = QtCore.Property(list, fget=_get_line_points, notify=curveChanged)

    controlPoints = QtCore.Property(
        list, fget=_get_control_points, notify=controlPointChanged
    )

    isSymmetric = QtCore.Property(
        bool, fget=_get_is_symmetric, fset=_set_is_symmetric, notify=changed
    )

    curveType = QtCore.Property(
        str, fget=_get_curve_type, fset=_set_curve_type, notify=curveChanged
    )

    selectedPoint = QtCore.Property(
        int,
        fget=_get_selected_point,
        fset=_set_selected_point,
        notify=selectedPointChanged,
    )

    hasControlHandles = QtCore.Property(
        bool,
        fget=lambda cls: ResponseCurveModel._bezier_curve(cls) is not None,
        notify=curveChanged,
    )

    selectedHasLeftHandle = QtCore.Property(
        bool,
        fget=lambda cls: ResponseCurveModel._has_handle(cls, "left"),
        notify=selectedPointChanged,
    )

    selectedHasRightHandle = QtCore.Property(
        bool,
        fget=lambda cls: ResponseCurveModel._has_handle(cls, "right"),
        notify=selectedPointChanged,
    )

    selectedSymmetricHandles = QtCore.Property(
        bool,
        fget=_get_selected_symmetric_handles,
        fset=_set_selected_symmetric_handles,
        notify=selectedPointChanged,
    )

    selectedLeftSlope = QtCore.Property(
        float,
        fget=lambda cls: ResponseCurveModel._handle_geometry(cls, "left")[0],
        fset=lambda cls, value: ResponseCurveModel._set_handle_component(
            cls, "left", 0, value
        ),
        notify=selectedPointChanged,
    )

    selectedLeftLength = QtCore.Property(
        float,
        fget=lambda cls: ResponseCurveModel._handle_geometry(cls, "left")[1],
        fset=lambda cls, value: ResponseCurveModel._set_handle_component(
            cls, "left", 1, value
        ),
        notify=selectedPointChanged,
    )

    selectedRightSlope = QtCore.Property(
        float,
        fget=lambda cls: ResponseCurveModel._handle_geometry(cls, "right")[0],
        fset=lambda cls, value: ResponseCurveModel._set_handle_component(
            cls, "right", 0, value
        ),
        notify=selectedPointChanged,
    )

    selectedRightLength = QtCore.Property(
        float,
        fget=lambda cls: ResponseCurveModel._handle_geometry(cls, "right")[1],
        fset=lambda cls, value: ResponseCurveModel._set_handle_component(
            cls, "right", 1, value
        ),
        notify=selectedPointChanged,
    )


class ResponseCurveData(AbstractActionData):
    """Model of a description action."""

    version = 1
    name = "Response Curve"
    tag = "response-curve"
    icon = "\uf18c"

    functor = ResponseCurveFunctor
    model = ResponseCurveModel

    properties = (ActionProperty.ActivateDisabled,)
    input_types = (InputType.JoystickAxis,)

    def __init__(self, behavior_type: InputType = InputType.JoystickAxis) -> None:
        super().__init__(behavior_type)

        # Model variables
        self.deadzone = [-1.0, 0.0, 0.0, 1.0]
        self.curve = spline.PiecewiseLinear()

    @override
    def _from_xml(self, node: ElementTree.Element, library: Library) -> None:
        lookup = {
            "PiecewiseLinear": spline.PiecewiseLinear,
            "CubicSpline": spline.CubicSpline,
            "CubicBezierSpline": spline.CubicBezierSpline,
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
            util.read_property(dz_node, "high", PropertyType.Float),
        ]

        # Create curve using XML values.
        cp_node = node.find("control-points")
        if cp_node is None:
            raise ProfileError("Missing control-points node")
        points = util.read_properties(cp_node, "point", PropertyType.Point2D)
        self.curve = lookup[
            util.read_property(node, "curve-type", PropertyType.String)
        ]([[p.x, p.y] for p in points])

        # Handle symmetry is optional, profiles written without it leave every
        # control point with freely movable handles.
        if isinstance(self.curve, spline.CubicBezierSpline):
            for cp, is_symmetric in zip(
                self.curve.control_points(),
                util.read_properties(cp_node, "symmetric-handles", PropertyType.Bool),
            ):
                cp.symmetric_handles = is_symmetric

    @override
    def _to_xml(self) -> ElementTree.Element:
        lookup = {
            spline.PiecewiseLinear: "PiecewiseLinear",
            spline.CubicSpline: "CubicSpline",
            spline.CubicBezierSpline: "CubicBezierSpline",
        }

        node = util.create_action_node(ResponseCurveData.tag, self._id)
        node.append(
            util.create_node_from_data(
                "deadzone",
                [
                    ("low", self.deadzone[DeadzoneIndex.LOW.value], PropertyType.Float),
                    (
                        "center-low",
                        self.deadzone[DeadzoneIndex.CENTER_LOW.value],
                        PropertyType.Float,
                    ),
                    (
                        "center-high",
                        self.deadzone[DeadzoneIndex.CENTER_HIGH.value],
                        PropertyType.Float,
                    ),
                    (
                        "high",
                        self.deadzone[DeadzoneIndex.HIGH.value],
                        PropertyType.Float,
                    ),
                ],
            )
        )

        points = []
        handle_symmetry = []
        match type(self.curve):
            case spline.PiecewiseLinear | spline.CubicSpline:
                points = self.curve.control_points()
            case spline.CubicBezierSpline:
                control_points = cast(
                    spline.CubicBezierSpline, self.curve
                ).control_points()
                for cp in control_points:
                    if cp.handle_left:
                        points.append(cp.handle_left)
                    points.append(cp.center)
                    if cp.handle_right:
                        points.append(cp.handle_right)
                # Only recorded when in use, so curves that don't rely on it
                # serialize exactly as they did before the option existed.
                if any(cp.symmetric_handles for cp in control_points):
                    handle_symmetry = [
                        ("symmetric-handles", cp.symmetric_handles, PropertyType.Bool)
                        for cp in control_points
                    ]

        node.append(
            util.create_node_from_data(
                "control-points",
                [("point", cp, PropertyType.Point2D) for cp in points]
                + handle_symmetry,
            )
        )
        node.append(
            util.create_property_node(
                "curve-type", lookup[type(self.curve)], PropertyType.String
            )
        )

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
        self, old_behavior: InputType, new_behavior: InputType
    ) -> None:
        pass


create = ResponseCurveData
