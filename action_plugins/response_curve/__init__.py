# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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


import enum
import logging
import os
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree

import gremlin
from gremlin.base_classes import AbstractAction, AbstractFunctor
from gremlin.common import InputType
from gremlin.ui.common import DualSlider, DynamicDoubleSpinBox
import gremlin.ui.input_item

g_scene_size = 250.0


class SymmetryMode(enum.Enum):

    """Symmetry modes for response curves."""

    NoSymmetry = 1
    Diagonal = 2


class Point2D:

    """Represents a 2D point with support for addition and subtraction."""

    def __init__(self, x=0.0, y=0.0):
        """Creates a new instance.

        :param x the x coordinate
        :param y the y coordinate
        """
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point2D(self.x - other.x, self.y - other.y)

    def __str__(self):
        return "[{:.2f}, {:.2f}]".format(self.x, self.y)


class ControlPoint:

    """Represents a single control point in a response curve.

    Each control point has at least a center point but can possibly have
    multiple handles which are used to control the shape of a curve segment.
    Each instance furthermore has a unique identifier used to distinguish
    and track different instances.
    """

    # Identifier of the next ControlPoint instance being created
    next_id = 0

    def __init__(self, model, center, handles=()):
        """Creates a new instance.

        :param model the model the control point is associated with
        :param center the center point of the control point
        :param handles optional list of handles to control curvature
        """
        self._model = model
        self._center = center
        self._handles = [hdl for hdl in handles]
        self._identifier = ControlPoint.next_id
        self._last_modified = time.time()
        ControlPoint.next_id += 1

    @property
    def last_modified(self):
        return self._last_modified

    @property
    def model(self):
        return self._model

    @property
    def center(self):
        """Returns the center point of the control point.

        :return center point of the control point
        """
        return self._center

    def set_center(self, point, emit_model_update=True):
        """Sets the center of the control point, if it is a valid point.

        This method uses the provided model to check if the provided location
        is valid.

        :param point the new center position of the control point
        :param emit_model_update if True a message will be emitted when the
            model changes
        """
        if self._model.is_valid_point(point, self.identifier):
            # Update handle locations if any are present
            delta = self.center - point
            for handle in self.handles:
                handle.x -= delta.x
                handle.y -= delta.y

            # Update center position
            self._center = point

            self._last_modified = time.time()
            if emit_model_update:
                self._model.model_updated()

    @property
    def identifier(self):
        return self._identifier

    @property
    def handles(self):
        return self._handles

    def set_handle(self, index, point):
        """Sets the location of the specified handle.

        :param index the id of the handle to modify
        :param point the new location of the handle
        """
        if len(self.handles) > index:
            self._last_modified = time.time()
            self.handles[index] = point
            if len(self.handles) == 2 and \
                    isinstance(self._model, CubicBezierSplineModel) and \
                    self._model.handle_symmetry_enabled:
                alt_point = self._center + (self._center - point)
                alt_index = 1 if index == 0 else 0
                self.handles[alt_index] = alt_point
            self._model.model_updated()

            self._last_modified = time.time()
            self._model.model_updated()

    def __eq__(self, other):
        """Compares two control points for identity.

        The unique identifier is used for the comparison.

        :param other the control point to compare with for identity
        :return True of the control points are the same, False otherwise
        """
        return self.identifier == other.identifier


class AbstractCurveModel(QtCore.QObject):

    """Abstract base class for all  curve models."""

    # Signal emitted when model data changes
    content_modified = QtCore.pyqtSignal()
    # Signal emitted when points are added or removed
    content_added = QtCore.pyqtSignal()

    def __init__(self, profile_data, parent=None):
        """Initializes an empty model.
        
        :param profile_data the data of this response curve
        """
        super().__init__(parent)
        self._control_points = []
        self._profile_data = profile_data
        self._init_from_profile_data()

        self.symmetry_mode = SymmetryMode.NoSymmetry

    def invert(self):
        for cp in self._control_points:
            cp.center.y = -cp.center.y
            for handle in cp.handles:
                handle.y = -handle.y
        self.save_to_profile()
        self.content_modified.emit()

    def model_updated(self):
        # If symmetry is enabled ensure that symmetry is preserved after
        # any changes
        if self.symmetry_mode == SymmetryMode.Diagonal:
            self._enforce_symmetry()
        self.save_to_profile()
        self.content_modified.emit()

    def get_curve_function(self):
        """Returns the curve function corresponding to the model.

        :return curve function corresponding to the model
        """
        raise gremlin.error.MissingImplementationError(
            "AbstractCurveModel::get_curve_function not implemented"
        )

    def get_control_points(self):
        """Returns the list of control points.

        :return list of control points
        """
        return self._control_points

    def add_control_point(self, point, handles=()):
        """Adds a new control point to the model.

        :param point the center of the control point
        :param handles list of potential handles
        :return the newly created control point
        """
        self._control_points.append(self._create_control_point(point, handles))

        if self.symmetry_mode == SymmetryMode.Diagonal:
            self._control_points.append(self._create_control_point(
                Point2D(-point.x, -point.y),
                handles
            ))
        self.save_to_profile()
        self.content_added.emit()

    def _create_control_point(self, point, handles=()):
        """Subclass specific implementation to add new control points.

        :param point the center of the control point
        :param handles list of potential handles
        :return the newly created control point
        """
        raise gremlin.error.MissingImplementationError(
            "AbstractCurveModel::_add_control_point not implemented"
        )

    def remove_control_point(self, control_point):
        """Removes the specified control point if it exists in the model.

        :param control_point the control point to remove
        """
        idx = self._control_points.index(control_point)
        if idx:
            del self._control_points[idx]
            self.save_to_profile()
            self.content_added.emit()

    def is_valid_point(self, point, identifier=None):
        """Checks is a point is valid in the model.

        :param point the point to check for validity
        :param identifier the identifier of a control point to ignore
        :return True if valid, False otherwise
        """
        raise gremlin.error.MissingImplementationError(
            "AbstractCurveModel::is_valid_point not implemented"
        )

    def _init_from_profile_data(self):
        """Initializes the control points based on profile data."""
        raise gremlin.error.MissingImplementationError(
            "AbstractCurveModel::_init_from_profile_data not implemented"
        )

    def save_to_profile(self):
        """Ensures that the control point data is properly recorded in
        the profile data."""
        raise gremlin.error.MissingImplementationError(
            "AbstractCurveModel::_update_profile_data not implemented"
        )

    def _enforce_symmetry(self):
        count = len(self._control_points)

        ordered_cp = sorted(self._control_points, key=lambda x: x.center.x)
        for i in range(int(count / 2.0)):
            cp1 = ordered_cp[i]
            cp2 = ordered_cp[-i - 1]
            if cp1.last_modified < cp2.last_modified:
                cp2, cp1 = cp1, cp2

            # cp1 is now the reference which is used to specify the values
            # of cp2
            cp2.set_center(Point2D(-cp1.center.x, -cp1.center.y), False)

            # Update handles
            if len(cp1.handles) == 2:
                cp2.handles[0] = cp2.center - (cp1.handles[1] - cp1.center)
                cp2.handles[1] = cp2.center - (cp1.handles[0] - cp1.center)
            elif len(cp1.handles) == 1:
                cp2.handles[0] = cp2.center - (cp1.handles[0] - cp1.center)

        if count % 2 != 0:
            ordered_cp[int(count / 2)].set_center(Point2D(0, 0), False)

    def set_symmetry_mode(self, mode):
        """Sets the symmetry mode of the curve model.

        :param mode the symmetry mode to use
        """
        if len(self._control_points) == 2:
            self.add_control_point(Point2D(0.0, 0.0))

        self._enforce_symmetry()
        self.symmetry_mode = mode
        self.content_added.emit()


class CubicSplineModel(AbstractCurveModel):

    """Represents a simple cubic spline model."""

    def __init__(self, profile_data):
        """Creates a new instance."""
        super().__init__(profile_data)

    def get_curve_function(self):
        """Returns the curve function corresponding to the model.

        :return curve function corresponding to the model
        """
        points = []
        for cp in sorted(self._control_points, key=lambda e: e.center.x):
            points.append((cp.center.x, cp.center.y))
        if len(points) < 2:
            return None
        else:
            return gremlin.spline.CubicSpline(points)

    def _create_control_point(self, point, handles=()):
        """Adds a new control point to the model.

        :param point the center of the control point
        :param handles list of potential handles
        :return the newly created control point
        """
        return ControlPoint(self, point)

    def is_valid_point(self, point, identifier=None):
        """Checks is a point is valid in the model.

        :param point the point to check for validity
        :param identifier the identifier of a control point to ignore
        :return True if valid, False otherwise
        """
        is_valid = True
        for other in self._control_points:
            if other.identifier == identifier:
                continue
            elif other.center.x == point.x:
                is_valid = False
        return is_valid

    def _init_from_profile_data(self):
        """Initializes the control points based on profile data."""
        for coord in self._profile_data.control_points:
            self._control_points.append(
                ControlPoint(self, Point2D(coord[0], coord[1]))
            )

    def save_to_profile(self):
        """Ensures that the control point data is properly recorded in
        the profile data."""
        self._profile_data.mapping_type = "cubic-spline"
        self._profile_data.control_points = []
        for cp in self._control_points:
            self._profile_data.control_points.append((cp.center.x, cp.center.y))


class CubicBezierSplineModel(AbstractCurveModel):

    """Represents a cubic bezier spline model."""

    def __init__(self, profile_data):
        """Creates a new model."""
        super().__init__(profile_data)
        self.handle_symmetry_enabled = False

    def get_curve_function(self):
        """Returns the curve function corresponding to the model.

        :return curve function corresponding to the model
        """
        points = []
        sorted_control_points = sorted(
            self._control_points, key=lambda e: e.center.x
        )
        for i, pt in enumerate(sorted_control_points):
            if i == 0:
                points.append((pt.center.x, pt.center.y))
                points.append((pt.handles[0].x, pt.handles[0].y))
            elif i == len(self._control_points) - 1:
                points.append((pt.handles[0].x, pt.handles[0].y))
                points.append((pt.center.x, pt.center.y))
            else:
                points.append((pt.handles[0].x, pt.handles[0].y))
                points.append((pt.center.x, pt.center.y))
                points.append((pt.handles[1].x, pt.handles[1].y))
        if len(points) < 4:
            return None
        else:
            return gremlin.spline.CubicBezierSpline(points)

    def set_handle_symmetry(self, is_enabled):
        """Enables and disables the handle symmetry mode.

        :param is_enabled whether or not the handle symmetry should be enabled
        """
        self.handle_symmetry_enabled = is_enabled

    def _create_control_point(self, point, handles=()):
        """Adds a new control point to the model.

        :param point the center of the control point
        :param handles list of potential handles
        :return the newly created control point
        """
        if len(handles) == 0:
            handles = (
                Point2D(point.x - 0.05, point.y),
                Point2D(point.x + 0.05, point.y)
            )
        return ControlPoint(self, point, handles)

    def is_valid_point(self, point, identifier=None):
        """Checks is a point is valid in the model.

        :param point the point to check for validity
        :param identifier the identifier of a control point to ignore
        :return True if valid, False otherwise
        """
        is_valid = True
        for other in self._control_points:
            if other.identifier == identifier:
                continue
            elif other.center.x == point.x:
                is_valid = False
        return is_valid

    def _init_from_profile_data(self):
        """Initializes the spline with profile data."""
        # If the data appears to be invalid insert a valid default
        if len(self._profile_data.control_points) < 4:
            self._profile_data.control_points = []
            self._profile_data.control_points.extend([
                (-1, -1),
                (-0.9, -0.9),
                (0.9, 0.9),
                (1, 1)
            ])
        coordinates = self._profile_data.control_points

        self._control_points.append(
            ControlPoint(
                self,
                Point2D(coordinates[0][0], coordinates[0][1]),
                [Point2D(coordinates[1][0], coordinates[1][1])]
            )
        )

        for i in range(3, len(coordinates)-3, 3):
            self._control_points.append(
                ControlPoint(
                    self,
                    Point2D(coordinates[i][0], coordinates[i][1]),
                    [
                        Point2D(coordinates[i-1][0], coordinates[i-1][1]),
                        Point2D(coordinates[i+1][0], coordinates[i+1][1])
                    ]
                )
            )
        self._control_points.append(
            ControlPoint(
                self,
                Point2D(coordinates[-1][0], coordinates[-1][1]),
                [Point2D(coordinates[-2][0], coordinates[-2][1])]
            )
        )

    def save_to_profile(self):
        """Ensure that UI and profile data are in sync."""
        control_points = sorted(
            self._control_points,
            key=lambda entry: entry.center.x
        )
        self._profile_data.control_points = []
        for cp in control_points:
            if cp.center.x == -1:
                self._profile_data.control_points.append(
                    [cp.center.x, cp.center.y]
                )
                self._profile_data.control_points.append(
                    [cp.handles[0].x, cp.handles[0].y]
                )
            elif cp.center.x == 1:
                self._profile_data.control_points.append(
                    [cp.handles[0].x, cp.handles[0].y]
                )
                self._profile_data.control_points.append(
                    [cp.center.x, cp.center.y]
                )
            else:
                self._profile_data.control_points.append(
                    [cp.handles[0].x, cp.handles[0].y]
                )
                self._profile_data.control_points.append(
                    [cp.center.x, cp.center.y]
                )
                self._profile_data.control_points.append(
                    [cp.handles[1].x, cp.handles[1].y]
                )


class ControlPointGraphicsItem(QtWidgets.QGraphicsEllipseItem):

    """UI Item representing the center of a control point."""

    def __init__(self, control_point, parent=None):
        """Creates a new instance.

        :param control_point the control point this element visualizes
        :param parent the parent of this widget
        """
        super().__init__(-4, -4, 8, 8, parent)
        assert(isinstance(control_point, ControlPoint))

        self.control_point = control_point

        self.setPos(
            g_scene_size * self.control_point.center.x,
            -g_scene_size * self.control_point.center.y
        )
        self.setZValue(2)
        self.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        self.handles = []

        if len(self.control_point.handles) > 0:
            for i, handle in enumerate(self.control_point.handles):
                dx = -(self.control_point.center.x - handle.x) * g_scene_size
                dy = -(self.control_point.center.y - handle.y) * g_scene_size
                item = CurveHandleGraphicsItem(i, Point2D(dx, dy), self)
                self.handles.append(item)

    def redraw(self):
        """Forces a position update of the ui element."""
        self.setPos(
            g_scene_size * self.control_point.center.x,
            -g_scene_size * self.control_point.center.y
        )

    def set_active(self, is_active):
        """Handles changing the selected state of an item

        :param is_active flag indicating if an item is selected or not
        """
        if is_active:
            self.setBrush(QtGui.QBrush(QtCore.Qt.red))
            if self.scene().mouseGrabberItem() != self:
                self.grabMouse()
        else:
            self.setBrush(QtGui.QBrush(QtCore.Qt.gray))
            if self.scene() and self.scene().mouseGrabberItem() == self:
                self.ungrabMouse()

    def mouseReleaseEvent(self, evt):
        """Releases the mouse grab when the mouse is released.

        :param evt the mouse even to process
        """
        self.ungrabMouse()
        # self.control_point.model.model_updated()

    def mouseMoveEvent(self, evt):
        """Updates the position of the control point based on mouse
        movements.

        :param evt the mouse event to process
        """
        # Create desired point
        new_point = Point2D(
            gremlin.util.clamp(evt.scenePos().x() / g_scene_size, -1.0, 1.0),
            gremlin.util.clamp(-evt.scenePos().y() / g_scene_size, -1.0, 1.0)
        )

        # Only allow movement along the y axis if the point is on either
        # end of the area
        if abs(self.control_point.center.x) == 1.0:
            new_point.x = self.control_point.center.x

        self.control_point.set_center(new_point)


class CurveHandleGraphicsItem(QtWidgets.QGraphicsRectItem):

    """UI Item representing a handle of a control point."""

    def __init__(self, index, point, parent):
        """Creates a new control point handle UI element.

        :param index the id of the handle
        :param point the location of the handle
        :param parent the parent of this widget
        """
        super().__init__(-4, -4, 8, 8, parent)
        self.setPos(point.x, point.y)
        self.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        self.parent = parent
        self.index = index
        self.line = QtWidgets.QGraphicsLineItem(point.x, point.y, 0, 0, parent)
        self.line.setZValue(0)
        self.setZValue(1)

    def redraw(self):
        """Forces a position update of the ui element."""
        center = self.parent.control_point.center
        point = self.parent.control_point.handles[self.index]
        delta = point - center

        self.setPos(delta.x*g_scene_size, -delta.y*g_scene_size)
        self.line.setLine(delta.x*g_scene_size, -delta.y*g_scene_size, 0, 0)

    def set_active(self, is_active):
        """Handles changing the selected state of an item

        :param is_active flag indicating if an item is selected or not
        """
        if self.scene() is None:
            return

        if is_active:
            self.setBrush(QtGui.QBrush(QtCore.Qt.red))
            if self.scene().mouseGrabberItem() != self:
                self.grabMouse()
        else:
            self.setBrush(QtGui.QBrush(QtCore.Qt.gray))
            if self.scene().mouseGrabberItem() == self:
                self.ungrabMouse()

    def mouseReleaseEvent(self, evt):
        """Releases the mouse grab when the mouse is released.

        :param evt the mouse event to process
        """
        self.ungrabMouse()

    def mouseMoveEvent(self, evt):
        """Updates the position of the control point based on mouse
        movements.

        :param evt the mouse event to process
        """
        # Create desired point
        new_point = Point2D(
            gremlin.util.clamp(evt.scenePos().x() / g_scene_size, -1.0, 1.0),
            gremlin.util.clamp(-evt.scenePos().y() / g_scene_size, -1.0, 1.0)
        )

        self.parent.control_point.set_handle(self.index, new_point)


class CurveView(QtWidgets.QGraphicsScene):

    """Visualization of the entire curve editor UI element."""

    def __init__(self, curve_model, point_editor, parent=None):
        """Creates a new instance.

        :param curve_model the model to visualize
        :param point_editor the point editor to use
        :param parent parent of this widget
        """
        super().__init__(parent)
        self.model = curve_model
        self.model.content_modified.connect(self.redraw_scene)
        self.model.content_added.connect(self._populate_from_model)
        self.point_editor = point_editor

        self.background_image = QtGui.QImage(
            "{}/grid.svg".format(os.path.dirname(os.path.realpath(__file__)))
        )

        # Connect editor widget signals
        self.point_editor.x_input.valueChanged.connect(self._editor_update)
        self.point_editor.y_input.valueChanged.connect(self._editor_update)

        self.current_item = None
        self._populate_from_model()

    def _populate_from_model(self):
        """Populates the UI based on content stored in the model."""
        # Remove old curve path and update control points
        for item in self.items():
            if type(item) in [
                ControlPointGraphicsItem,
                CurveHandleGraphicsItem
            ]:
                self.removeItem(item)

        for cp in self.model.get_control_points():
            self.addItem(ControlPointGraphicsItem(cp))
        self.redraw_scene()

    def add_control_point(self, point, handles=()):
        """Adds a new control point to the model and scene.

        :param point the center of the control point
        :param handles list of potential handles
        """
        self.model.add_control_point(point, handles)
        self._populate_from_model()

    def _editor_update(self, value):
        """Callback for changes in the point editor UI.

        :param value the new value entered using the editor UI
        """
        # We can only move control points around using the numerical inputs
        if not isinstance(self.current_item, ControlPointGraphicsItem):
            return

        if self.current_item:
            new_point = Point2D(
                self.point_editor.x_input.value(),
                self.point_editor.y_input.value()
            )
            if abs(self.current_item.control_point.center.x) == 1.0:
                new_point.x = self.current_item.control_point.center.x
            self.current_item.control_point.set_center(new_point)
            self.model.save_to_profile()
            # self.redraw_scene()

    def _select_item(self, item):
        """Handles drawing of an item being selected.

        :param item the item being selected
        """
        # Ensure we want / can select the provided item
        if isinstance(item, ControlPointGraphicsItem) or \
                isinstance(item, CurveHandleGraphicsItem):
            if self.current_item and item != self.current_item:
                self.current_item.set_active(False)
            self.current_item = item
            self.current_item.set_active(True)
        self.redraw_scene()

    def redraw_scene(self):
        """Updates the scene

        Need to update positions rather then recreating everything, as
        otherwise the state gets lost.
        """
        # Remove old curve path and update control points
        for item in self.items():
            if isinstance(item, QtWidgets.QGraphicsPathItem):
                self.removeItem(item)
            elif type(item) in [
                ControlPointGraphicsItem,
                CurveHandleGraphicsItem
            ]:
                item.redraw()

        # Redraw response curve
        curve_fn = self.model.get_curve_function()
        if curve_fn:
            path = QtGui.QPainterPath(
                QtCore.QPointF(-g_scene_size, -g_scene_size*curve_fn(-1))
            )
            for x in range(-int(g_scene_size), int(g_scene_size+1), 2):
                path.lineTo(x, -g_scene_size * curve_fn(x / g_scene_size))
            self.addPath(path, QtGui.QPen(QtGui.QColor(0, 200, 0)))

        # Update editor widget fields
        if self.current_item:
            if isinstance(self.current_item, ControlPointGraphicsItem):
                self.point_editor.set_values(
                    self.current_item.control_point.center
                )

    def mousePressEvent(self, evt):
        """Informs the model about point selection if a point is clicked.

        :param evt the mouse event to process
        """
        if evt.button() == QtCore.Qt.LeftButton:
            self._select_item(self.itemAt(evt.scenePos(), QtGui.QTransform()))

    def mouseDoubleClickEvent(self, evt):
        """Adds or removes a control point.

        A left double click on empty space creates a new control point.

        :param evt the mouse event to process
        """
        if evt.button() == QtCore.Qt.LeftButton:
            item = self.itemAt(evt.scenePos(), QtGui.QTransform())
            if not isinstance(item, ControlPointGraphicsItem):
                self.add_control_point(Point2D(
                    evt.scenePos().x() / g_scene_size,
                    evt.scenePos().y() / -g_scene_size
                ))

    def keyPressEvent(self, evt):
        """Removes the currently selected control point if the Del
        key is pressed.

        :param evt the keyboard event to process.
        """
        if evt.key() == QtCore.Qt.Key_Delete and \
                isinstance(self.current_item, ControlPointGraphicsItem):
            # Disallow removing edge points
            if abs(self.current_item.control_point.center.x) == 1.0:
                return

            # Otherwise remove the currently active control point
            self.model.remove_control_point(self.current_item.control_point)
            self._populate_from_model()
            self.current_item = None

    def drawBackground(self, painter, rect):
        """Draws the grid background image.

        :param painter the painter object
        :param rect the drawing rectangle
        """
        painter.drawImage(
            QtCore.QPoint(-g_scene_size, -g_scene_size),
            self.background_image
        )


class ControlPointEditorWidget(QtWidgets.QWidget):

    """Widgets allowing the control point coordinates to be changed
    via text fields."""

    # TODO: how does this synchronize with the points / model?

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent widget
        """
        super().__init__(parent)

        # Generate controls
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel("Control Point")
        self.x_label = QtWidgets.QLabel("X")
        self.y_label = QtWidgets.QLabel("Y")

        self.x_input = DynamicDoubleSpinBox()
        self.x_input.setRange(-1, 1)
        self.x_input.setDecimals(3)
        self.x_input.setSingleStep(0.1)

        self.y_input = DynamicDoubleSpinBox()
        self.y_input.setRange(-1, 1)
        self.y_input.setSingleStep(0.1)
        self.y_input.setDecimals(3)

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.x_label)
        self.main_layout.addWidget(self.x_input)
        self.main_layout.addWidget(self.y_label)
        self.main_layout.addWidget(self.y_input)

    def set_values(self, point):
        """Sets the values in the input fields to those of the provided point.

        :param point the point containing the new field values
        """
        self.x_input.setValue(point.x)
        self.y_input.setValue(point.y)


class DeadzoneWidget(QtWidgets.QWidget):

    """Widget visualizing deadzone settings as well as allowing the
    modification of these."""

    def __init__(self, profile_data, parent=None):
        """Creates a new instance.

        :param profile_data the data of this response curve
        :param parent the parent widget
        """
        super().__init__(parent)

        self.profile_data = profile_data

        self.main_layout = QtWidgets.QGridLayout(self)

        # Create the two sliders
        self.left_slider = DualSlider()
        self.left_slider.setRange(-100, 0)
        self.right_slider = DualSlider()
        self.right_slider.setRange(0, 100)

        # Create spin boxes for the left slider
        self.left_lower = DynamicDoubleSpinBox()
        self.left_lower.setMinimum(-1.0)
        self.left_lower.setMaximum(0.0)
        self.left_lower.setSingleStep(0.05)
        self.left_upper = DynamicDoubleSpinBox()
        self.left_upper.setMinimum(-1.0)
        self.left_upper.setMaximum(0.0)
        self.left_upper.setSingleStep(0.05)

        # Create spin boxes for the right slider
        self.right_lower = DynamicDoubleSpinBox()
        self.right_lower.setSingleStep(0.05)
        self.right_lower.setMinimum(0.0)
        self.right_lower.setMaximum(1.0)
        self.right_upper = DynamicDoubleSpinBox()
        self.right_upper.setSingleStep(0.05)
        self.right_upper.setMinimum(0.0)
        self.right_upper.setMaximum(1.0)

        self._normalizer =\
            self.left_slider.range()[1] - self.left_slider.range()[0]

        # Hook up all the required callbacks
        self.left_slider.valueChanged.connect(self._update_left)
        self.right_slider.valueChanged.connect(self._update_right)
        self.left_lower.valueChanged.connect(
            lambda value: self._update_from_spinner(
                value,
                DualSlider.LowerHandle,
                self.left_slider
            )
        )
        self.left_upper.valueChanged.connect(
            lambda value: self._update_from_spinner(
                value,
                DualSlider.UpperHandle,
                self.left_slider
            )
        )
        self.right_lower.valueChanged.connect(
            lambda value: self._update_from_spinner(
                value,
                DualSlider.LowerHandle,
                self.right_slider
            )
        )
        self.right_upper.valueChanged.connect(
            lambda value: self._update_from_spinner(
                value,
                DualSlider.UpperHandle,
                self.right_slider
            )
        )

        # Set slider positions
        self.set_values(self.profile_data.deadzone)

        # Put everything into the layout
        self.main_layout.addWidget(self.left_slider, 0, 0, 1, 2)
        self.main_layout.addWidget(self.right_slider, 0, 2, 1, 2)
        self.main_layout.addWidget(self.left_lower, 1, 0)
        self.main_layout.addWidget(self.left_upper, 1, 1)
        self.main_layout.addWidget(self.right_lower, 1, 2)
        self.main_layout.addWidget(self.right_upper, 1, 3)

    def set_values(self, values):
        """Sets the deadzone values.

        :param values the new deadzone values
        """
        self.left_slider.setLowerPosition(values[0] * self._normalizer)
        self.left_slider.setUpperPosition(values[1] * self._normalizer)
        self.right_slider.setLowerPosition(values[2] * self._normalizer)
        self.right_slider.setUpperPosition(values[3] * self._normalizer)

    def get_values(self):
        """Returns the current deadzone values.

        :return current deadzone values
        """
        return [
            self.left_lower.value(),
            self.left_upper.value(),
            self.right_lower.value(),
            self.right_upper.value()
        ]

    def _update_left(self, handle, value):
        """Updates the left spin boxes.

        :param handle the handle which was moved
        :param value the new value
        """
        if handle == DualSlider.LowerHandle:
            self.left_lower.setValue(value / self._normalizer)
            self.profile_data.deadzone[0] = value / self._normalizer
        elif handle == DualSlider.UpperHandle:
            self.left_upper.setValue(value / self._normalizer)
            self.profile_data.deadzone[1] = value / self._normalizer

    def _update_right(self, handle, value):
        """Updates the right spin boxes.

        :param handle the handle which was moved
        :param value the new value
        """
        if handle == DualSlider.LowerHandle:
            self.right_lower.setValue(value / self._normalizer)
            self.profile_data.deadzone[2] = value / self._normalizer
        elif handle == DualSlider.UpperHandle:
            self.right_upper.setValue(value / self._normalizer)
            self.profile_data.deadzone[3] = value / self._normalizer

    def _update_from_spinner(self, value, handle, widget):
        """Updates the slider position.

        :param value the new value
        :param handle the handle to move
        :param widget which slider widget to update
        """
        if handle == DualSlider.LowerHandle:
            widget.setLowerPosition(value * self._normalizer)
        elif handle == DualSlider.UpperHandle:
            widget.setUpperPosition(value * self._normalizer)


class ResponseCurveWidget(gremlin.ui.input_item.AbstractActionWidget):

    """Widget that allows configuring the response of an axis to
    user inputs."""

    def __init__(self, action_data, parent=None):
        """Creates a new instance.

        :param action_data the data associated with this specific action.
        :param parent parent widget
        """
        super().__init__(action_data, parent=parent)

        self.is_inverted = False
        self.symmetry_mode_on = False

    def _create_ui(self):
        """Creates the required UI elements."""
        # Dropdown menu for the different curve types
        self.curve_type_selection = QtWidgets.QComboBox()
        self.curve_type_selection.addItem("Cubic Spline")
        self.curve_type_selection.addItem("Cubic Bezier Spline")
        self.curve_type_selection.currentTextChanged.connect(
            self._change_curve_type
        )

        # Curve manipulation options
        self.curve_settings_layout = QtWidgets.QHBoxLayout()
        self.curve_settings_layout.addWidget(QtWidgets.QLabel("Curve Type:"))
        self.curve_settings_layout.addWidget(self.curve_type_selection)
        self.curve_settings_layout.addStretch(1)

        # Curve inversion
        self.curve_inversion = QtWidgets.QPushButton("Invert")
        self.curve_inversion.clicked.connect(self._invert_curve)
        self.curve_settings_layout.addWidget(self.curve_inversion)

        # Curve symmetry
        self.curve_symmetry = QtWidgets.QCheckBox("Diagonal Symmetry")
        self.curve_symmetry.stateChanged.connect(self._curve_symmetry_cb)
        self.curve_settings_layout.addWidget(self.curve_symmetry)

        # Handle symmetry
        self.handle_symmetry = None
        if self.action_data.mapping_type == "cubic-bezier-spline":
            self.handle_symmetry = QtWidgets.QCheckBox("Force smooth curves")
            self.handle_symmetry.stateChanged.connect(self._handle_symmetry_cb)
            self.curve_settings_layout.addWidget(self.handle_symmetry)

        # Create all objects required for the response curve UI
        self.control_point_editor = ControlPointEditorWidget()
        # Response curve model used
        if self.action_data.mapping_type == "cubic-spline":
            self.curve_model = CubicSplineModel(self.action_data)
        elif self.action_data.mapping_type == "cubic-bezier-spline":
            self.curve_model = CubicBezierSplineModel(self.action_data)
        else:
            raise gremlin.error.ProfileError("Invalid curve type")
        # Graphical curve editor
        self.curve_scene = CurveView(
            self.curve_model,
            self.control_point_editor
        )

        # Create view displaying the curve scene
        self.curve_view_layout = QtWidgets.QHBoxLayout()
        self.curve_view = QtWidgets.QGraphicsView(self.curve_scene)
        self._configure_response_curve_view()

        # Deadzone configuration
        self.deadzone_label = QtWidgets.QLabel("Deadzone")
        self.deadzone = DeadzoneWidget(self.action_data)

        # Add all widgets to the layout
        self.main_layout.addLayout(self.curve_settings_layout)
        self.main_layout.addLayout(self.curve_view_layout)
        self.main_layout.addWidget(self.control_point_editor)
        self.main_layout.addWidget(self.deadzone_label)
        self.main_layout.addWidget(self.deadzone)

    def _populate_ui(self):
        """Populates the UI elements."""
        self.curve_type_selection.currentTextChanged.disconnect(
            self._change_curve_type
        )

        # Create mapping from XML name to ui name
        name_map = {}
        for key, value in ResponseCurve.curve_name_map.items():
            name_map[value] = key

        # Setup correct response curve object
        self.curve_type_selection.setCurrentText(
            name_map[self.action_data.mapping_type]
        )
        self.curve_scene.redraw_scene()

        # Set deadzone values
        self.deadzone.set_values(self.action_data.deadzone)

        self.curve_type_selection.currentTextChanged.connect(
            self._change_curve_type
        )

    def _change_curve_type(self, curve_type):
        """Changes the type of curve used.

        :param curve_type the name of the new curve type
        """
        model_map = {
            "Cubic Spline": CubicSplineModel,
            "Cubic Bezier Spline": CubicBezierSplineModel
        }

        # Create new model
        if curve_type == "Cubic Spline":
            self.action_data.control_points = [(-1.0, -1.0), (1.0, 1.0)]
            self.action_data.mapping_type = "cubic-spline"
        elif curve_type == "Cubic Bezier Spline":
            self.action_data.control_points = [
                (-1.0, -1.0), (-0.8, -0.8), (0.8, 0.8), (1.0, 1.0)
            ]
            self.action_data.mapping_type = "cubic-bezier-spline"

        self.curve_model = model_map[curve_type](self.action_data)

        # Update curve settings UI
        if self.action_data.mapping_type == "cubic-spline":
            if self.handle_symmetry is not None:
                self.handle_symmetry.hide()
                self.handle_symmetry = None
        elif self.action_data.mapping_type == "cubic-bezier-spline":
            if self.handle_symmetry is None:
                self.handle_symmetry = QtWidgets.QCheckBox("Force smooth curves")
                self.handle_symmetry.stateChanged.connect(
                    self._handle_symmetry_cb
                )
                self.curve_settings_layout.addWidget(self.handle_symmetry)
        self.curve_symmetry.setChecked(False)

        # Recreate the UI components
        self.curve_scene = CurveView(
            self.curve_model,
            self.control_point_editor
        )
        self.curve_view = QtWidgets.QGraphicsView(self.curve_scene)
        self._configure_response_curve_view()

    def _curve_symmetry_cb(self, state):
        if state == QtCore.Qt.Checked:
            self.curve_model.set_symmetry_mode(SymmetryMode.Diagonal)
        else:
            self.curve_model.set_symmetry_mode(SymmetryMode.NoSymmetry)

        self.curve_scene.redraw_scene()

    def _handle_symmetry_cb(self, state):
        if not isinstance(self.curve_model, CubicBezierSplineModel):
            logging.getLogger("system").error(
                "Handle symmetry callback in non bezier curve attempted."
            )
            return

        self.curve_model.set_handle_symmetry(state == QtCore.Qt.Checked)

    def _configure_response_curve_view(self):
        """Initializes the response curve view components."""
        self.curve_view = QtWidgets.QGraphicsView(self.curve_scene)
        self.curve_view.setFixedSize(QtCore.QSize(510, 510))
        self.curve_view.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.curve_view.setSceneRect(QtCore.QRectF(
            -g_scene_size,
            -g_scene_size,
            2*g_scene_size,
            2*g_scene_size
        ))
        gremlin.ui.common.clear_layout(self.curve_view_layout)
        self.curve_view_layout.addStretch()
        self.curve_view_layout.addWidget(self.curve_view)
        self.curve_view_layout.addStretch()

    def _invert_curve(self):
        self.curve_model.invert()


class ResponseCurveFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)
        self.deadzone_fn = lambda value: gremlin.input_devices.deadzone(
            value,
            action.deadzone[0],
            action.deadzone[1],
            action.deadzone[2],
            action.deadzone[3]
        )
        if action.mapping_type == "cubic-spline":
            self.response_fn = gremlin.spline.CubicSpline(action.control_points)
        elif action.mapping_type == "cubic-bezier-spline":
            self.response_fn = \
                gremlin.spline.CubicBezierSpline(action.control_points)
        else:
            raise gremlin.error.GremlinError("Invalid curve type")

    def process_event(self, event, value):
        value.current = self.response_fn(self.deadzone_fn(value.current))
        return True


class ResponseCurve(AbstractAction):

    """Represents axis response curve mapping."""

    name = "Response Curve"
    tag = "response-curve"

    default_button_activation = (True, True)
    input_types = [
        InputType.JoystickAxis
    ]

    functor = ResponseCurveFunctor
    widget = ResponseCurveWidget

    curve_name_map = {
        "Cubic Spline": "cubic-spline",
        "Cubic Bezier Spline": "cubic-bezier-spline"
    }

    def __init__(self, parent):
        """Creates a new ResponseCurve instance.

        :param parent the parent profile.InputItem of this instance
        """
        super().__init__(parent)
        self.deadzone = [-1, 0, 0, 1]
        self.sensitivity = 1.0
        self.mapping_type = "cubic-spline"
        self.control_points = [(-1.0, -1.0), (1.0, 1.0)]

    def icon(self):
        """Returns the icon representing the action."""
        return "{}/icon.png".format(os.path.dirname(os.path.realpath(__file__)))

    def requires_virtual_button(self):
        """Returns whether or not an activation condition is needed.

        :return True if an activation condition is needed, False otherwise
        """
        return False

    def _parse_xml(self, node):
        """Parses the XML corresponding to a response curve.

        :param node the XML node to parse
        """
        self.control_points = []
        for child in node:
            if child.tag == "deadzone":
                self.deadzone = [
                    float(child.get("low")),
                    float(child.get("center-low")),
                    float(child.get("center-high")),
                    float(child.get("high"))
                ]
            elif child.tag == "mapping":
                self.mapping_type = child.get("type")
                self.control_points = []
                for point in child.iter("control-point"):
                    self.control_points.append((
                        float(point.get("x")),
                        float(point.get("y"))
                    ))

    def _generate_xml(self):
        """Generates a XML node corresponding to this object.

        :return XML node representing the object's data
        """
        node = ElementTree.Element("response-curve")
        # Response curve mapping
        if len(self.control_points) > 0:
            mapping_node = ElementTree.Element("mapping")
            mapping_node.set("type", self.mapping_type)
            for point in self.control_points:
                cp_node = ElementTree.Element("control-point")
                cp_node.set("x", str(point[0]))
                cp_node.set("y", str(point[1]))
                mapping_node.append(cp_node)
            node.append(mapping_node)

        # Deadzone settings
        deadzone_node = ElementTree.Element("deadzone")
        deadzone_node.set("low", str(self.deadzone[0]))
        deadzone_node.set("center-low", str(self.deadzone[1]))
        deadzone_node.set("center-high", str(self.deadzone[2]))
        deadzone_node.set("high", str(self.deadzone[3]))
        node.append(deadzone_node)

        return node

    def _is_valid(self):
        """Returns whether or not the action is configured correctly.

        :return True if the action is configured correctly, False otherwise
        """
        return True


version = 1
name = "response-curve"
create = ResponseCurve
