# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
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

import copy
from mako.template import Template
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree

from action.common import AbstractAction, AbstractActionWidget, DualSlider, template_helpers
import gremlin


class BaseStorage(object):

    """Base class of all storage classes."""

    def __init__(self):
        """Creates a new instance."""
        self._points = {}

    def clear(self):
        """Empties the data storage."""
        self._points = {}

    def values(self):
        """Returns all stored data.

        :return list of all the stored data
        """
        return self._points.values()

    def items(self):
        """Returns the item representation of the stored data.

        :return item representation of the data
        """
        return self._points.items()

    def __setitem__(self, cpid, value):
        """Sets the value of the give id.

        :param cpid id of the entry to change
        :param value the new value for the given entry
        """
        self._points[cpid] = value

    def __getitem__(self, cpid):
        """Returns the value of the given entry.

        :param cpid id of the entry to return
        :return value of the given entry
        """
        return self._points[cpid]


class PointStorage(BaseStorage):

    """Storage for a simple point.

    This storage is used in conjunction with the cubic spline class.
    """

    def __init__(self):
        """Creates a new instance."""
        BaseStorage.__init__(self)

    def add(self, cpid, x, y):
        """Adds a new point with given id and coordinates.

        :param cpid the id of the new point
        :param x the x coordinate of the point
        :param y the y coordinate of the point
        """
        self._points[cpid] = Point2D(x, y)

    def remove(self, cpid):
        """Removes the specified point from the storage.

        :param cpid the id of the point to remove
        """
        del self._points[cpid]


class KnotStorage(BaseStorage):

    def __init__(self):
        """Creates a new instance."""
        BaseStorage.__init__(self)

    def add(self, cpid, x, y):
        """Adds a new point with given id and coordinates.

        :param cpid the id of the new point
        :param x the x coordinate of the point
        :param y the y coordinate of the point
        """
        self._points[cpid] = Point2D(x, y)
        self._points[ControlPointIdentifier(cpid.primary, 1)] = Point2D(x-0.05, y)
        self._points[ControlPointIdentifier(cpid.primary, 2)] = Point2D(x+0.05, y)

    def remove(self, cpid):
        """Removes the specified point from the storage.

        :param cpid the id of the point to remove
        """
        del self._points[cpid]
        del self._points[ControlPointIdentifier(cpid.primary, 1)]
        del self._points[ControlPointIdentifier(cpid.primary, 2)]


class Point2D(object):

    """Represents a 2D point."""

    def __init__(self, x=0, y=0):
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


class ResponseCurveScene(QtWidgets.QGraphicsScene):

    """Visualization of a response curve configuration."""

    def __init__(self, model, parent=None):
        """Creates a new instance.

        :param model the ControlPointModel this scene visualizes
        :param parent parent widget
        """
        QtWidgets.QGraphicsScene.__init__(self, parent)
        self._bg_image = QtGui.QImage("gfx/grid.svg")
        self._model = model

        # Storage for ControlPointShapeItem instances with
        # corresponding model ids
        self._points = {}

        # Connect to model signals
        self._model.pointAdded.connect(self._point_added_cb)
        self._model.pointRemoved.connect(self._point_removed_cb)
        self._model.pointMoved.connect(self._point_moved_cb)
        self._model.pointSelected.connect(self._point_selected_cb)

    def clear_points(self):
        """Removes all points from the scene."""
        for cpid, node in self._points.items():
            self.removeItem(node)
        self._points = {}

    def _point_added_cb(self, cpid, point):
        """Adds a new point to the scene.

        :param cpid the id of the point in the model
        :param point the coordinates of the point
        """
        if self._model.curve_model == gremlin.spline.CubicSpline:
            self._points[cpid] = ControlPointShapeItem(cpid, point)
        elif self._model.curve_model == gremlin.spline.CubicBezierSpline:
            self._points[cpid] = ControlPointShapeItem(
                cpid,
                self._model.get_coords(cpid)
            )
            tmp = ControlPointIdentifier(cpid.primary, 1)
            self._points[tmp] = CurvaturePointShapeItem(
                tmp,
                self._model.get_coords(tmp)
            )
            tmp = ControlPointIdentifier(cpid.primary, 2)
            self._points[tmp] = CurvaturePointShapeItem(
                tmp,
                self._model.get_coords(tmp)
            )
        for i in range(3):
            tmp = ControlPointIdentifier(cpid.primary, i)
            if tmp in self._points:
                self.addItem(self._points[tmp])
        self._draw_control_points()
        self._draw_response_curve()
        self._draw_handles()

    def _point_removed_cb(self, cpid):
        """Removes the given point from the scene.

        :param cpid the model if of the point being removed
        """
        self.removeItem(self._points[cpid])
        del self._points[cpid]
        if self._model.curve_model == gremlin.spline.CubicBezierSpline:
            cpid_1 = ControlPointIdentifier(cpid.primary, 1)
            cpid_2 = ControlPointIdentifier(cpid.primary, 2)
            self.removeItem(self._points[cpid_1])
            self.removeItem(self._points[cpid_2])
            del self._points[cpid_1]
            del self._points[cpid_2]
        self._draw_control_points()
        self._draw_response_curve()
        self._draw_handles()

    def _point_moved_cb(self, cpid, old_point, new_point):
        """Updates the position of the point in the scene and redraws
        the response curve.

        :param cpid the id of the item being changes
        :param old_point old coordinates of the item
        :param new_point new coordinates of the item
        """
        self._update_control_handle_locations(cpid, old_point, new_point)
        self._points[cpid].setPos(new_point.x * 200.0, new_point.y * -200.0)
        self._draw_response_curve()
        self._draw_handles()

    def _point_selected_cb(self, cpid):
        """Updates the point selection.

        :param cpid the id of the newly selected point
        """
        # Remove highlight from all nodes
        for node in self._points.values():
            node.set_selected(node.identifier == cpid)

    def _draw_control_points(self):
        """Updates the locations of all control points."""
        for cpid, node in self._points.items():
            coord = self._model.get_coords(cpid)
            node.setPos(coord.x * 200, coord.y * -200)

    def _draw_response_curve(self):
        """Redraws the entire response curve."""
        # Generate new curve
        curve = self._model.curve_model(self._model.get_control_points())

        # Remove old path
        for item in self.items():
            if isinstance(item, QtWidgets.QGraphicsPathItem):
                self.removeItem(item)
            elif isinstance(item, QtWidgets.QGraphicsLineItem):
                self.removeItem(item)

        # Draw new curve
        if len(curve.x) > 1:
            path = QtGui.QPainterPath(QtCore.QPointF(-200, -200*curve(-1)))
            for x in range(-200, 201, 2):
                path.lineTo(x, -200 * curve(x / 200.0))
            self.addPath(path)

    def _update_control_handle_locations(self, cpid, old_point, new_point):
        """Updates the location of control handles for bezier splines.

        :param cpid the identifier of the control point itself
        :param old_point coordinates of the point before motion
        :param new_point coordinates of the point after motion
        """
        if self._model.curve_model != gremlin.spline.CubicBezierSpline:
            return

        # Update handle location
        if cpid and cpid.secondary == 0:
            cpid_1 = ControlPointIdentifier(cpid.primary, 1)
            cpid_2 = ControlPointIdentifier(cpid.primary, 2)

            new_pt_1 = self._model.get_coords(cpid_1) + (new_point - old_point)
            new_pt_2 = self._model.get_coords(cpid_2) + (new_point - old_point)
            self._model.set_coords(cpid_1, new_pt_1)
            self._points[cpid_1].setPos(200 * new_pt_1.x, -200 * new_pt_1.y)
            self._model.set_coords(cpid_2, new_pt_2)
            self._points[cpid_2].setPos(200 * new_pt_2.x, -200 * new_pt_2.y)


    def _draw_handles(self):
        """Draws handles of control points fo bezier splines."""
        if self._model.curve_model != gremlin.spline.CubicBezierSpline:
            return

        # Update handle lines
        for cpid, point in self._model._storage.items():
            if cpid.secondary == 0:
                cpid_1 = ControlPointIdentifier(cpid.primary, 1)
                pt_1 = self._model.get_coords(cpid_1)
                self.addLine(
                    200*pt_1.x, -200*pt_1.y, 200*point.x, -200*point.y
                )
                cpid_2 = ControlPointIdentifier(cpid.primary, 2)
                pt_2 = self._model.get_coords(cpid_2)
                self.addLine(
                    200*pt_2.x, -200*pt_2.y, 200*point.x, -200*point.y
                )

    def mousePressEvent(self, evt):
        """Informs the model about point selection if a point is clicked.

        :param evt the mouse event
        """
        item = self.itemAt(evt.scenePos(), QtGui.QTransform())
        is_control_point = isinstance(item, ControlPointShapeItem) or \
            isinstance(item, CurvaturePointShapeItem)

        if evt.button() == QtCore.Qt.LeftButton:
            if is_control_point:
                self._model.select_point(item.identifier)

    def mouseDoubleClickEvent(self, evt):
        """Adds or removes a control point.

        A left double click on empty space creates a new control point,
        while a right double click on an existing control point removes
        the underlying control point.

        :param evt the mouse event
        """
        item = self.itemAt(evt.scenePos(), QtGui.QTransform())
        is_control_point = isinstance(item, QtWidgets.QGraphicsEllipseItem)

        # Create a new control point
        if evt.button() == QtCore.Qt.LeftButton:
            if not is_control_point:
                self._model.add_point(Point2D(
                    evt.scenePos().x() / 200.0,
                    evt.scenePos().y() / -200.0
                ))
        # Remove an existing control point
        elif evt.button() == QtCore.Qt.RightButton:
            if is_control_point:
                self._model.remove_point(item.identifier)

    def drawBackground(self, painter, rect):
        """Draws the grid background image.

        :param painter the painter object
        :param rect the drawing rectangle
        """
        painter.drawImage(QtCore.QPoint(-200, -200), self._bg_image)

    def update_model(self, control_point):
        """Updates the model with the given control point's location.

        :param control_point the point with which to update the model
        """
        self._model.move_point(
            control_point.identifier,
            Point2D(control_point.x() / 200.0, control_point.y() / -200.0)
        )


class ControlPointIdentifier(object):

    """Identifies a single control point.

    This can be the actual control point or a point that controls the
    shape of the actual spline. If the point is the primary one then
    the value of secondary is 0, otherwise it is a value > 0.
    """

    def __init__(self, primary,  secondary=0):
        """Creates a new instance.

        The secondary id is only used for Bezier splines.

        :param primary the primary id
        :param secondary the secondary id
        """
        self._primary = primary
        self._secondary = secondary

    @property
    def primary(self):
        return self._primary

    @property
    def secondary(self):
        return self._secondary

    def __hash__(self):
        return hash((self.primary, self.secondary))

    def __eq__(self, other):
        return (self.primary, self.secondary) == (other.primary, other.secondary)


class ControlPointModel(QtCore.QObject):

    """Model representing the control points of a response curve."""

    # Signals emitted by the model
    pointAdded = QtCore.pyqtSignal(ControlPointIdentifier, Point2D)
    pointRemoved = QtCore.pyqtSignal(ControlPointIdentifier)
    # id of the point, old position, new position
    pointMoved = QtCore.pyqtSignal(ControlPointIdentifier, Point2D, Point2D)
    pointSelected = QtCore.pyqtSignal(ControlPointIdentifier)

    def __init__(self, curve_model, parent=None):
        """Creates a new instance.

        :param curve_model the type of curve to use
        :param parent the parent object
        """
        QtCore.QObject.__init__(self, parent)
        self._active_point = None
        self._next_id = 1
        self.curve_model = curve_model

        storage_map = {
            gremlin.spline.CubicSpline: PointStorage,
            gremlin.spline.CubicBezierSpline: KnotStorage,
        }
        self._storage = storage_map[curve_model]()

    def get_control_points(self):
        """Returns the sorted list of all control points.

        :return sorted list of control points
        """
        if self.curve_model == gremlin.spline.CubicSpline:
            return sorted(
                [[pt.x, pt.y] for pt in self._storage.values()],
                key=lambda pt: pt[0]
            )
        elif self.curve_model == gremlin.spline.CubicBezierSpline:
            sequence = []
            for cpid, point in self._storage.items():
                if cpid.secondary == 0:
                    sequence.append((cpid.primary, point.x))
            sequence = sorted(sequence, key=lambda val: val[1])

            point_list = []
            for entry in sequence:
                for i in [1, 0, 2]:
                    point = self._storage[ControlPointIdentifier(entry[0], i)]
                    point_list.append([point.x, point.y])
            return point_list[1:-1]

    def get_coords(self, cpid):
        """Returns the coordinates of the specified control point.

        :param cpid the id of the control point
        :return coordinates of the corresponding control point
        """
        return self._storage[cpid]

    def set_coords(self, cpid, point):
        """Sets the coordinates of the specified control point.

        :param cpid the id of the control point
        :param point the new point location
        """
        self._storage[cpid] = point

    def add_point(self, point):
        """Adds a new control point with the provided coordinates.

        :param point the 2d point at which to add a new control point
        :return the index of the newly added point
        """
        if -1 <= point.x <= 1 and -1 <= point.y <= 1:
            if not self._is_other_point_nearby(
                    ControlPointIdentifier(-1, 0), point.x
            ):
                cpid = ControlPointIdentifier(self._next_id, 0)
                self._storage.add(cpid, point.x, point.y)
                self.pointAdded.emit(cpid, point)
                self._next_id += 1
            return cpid

    def move_point(self, cpid, point):
        """Moves the specified control point to the new coordinates.

        :param cpid the id of the control point to move
        :param point the new coordinates of the control point
        """
        # Ensure points are in [-1, 1]
        x = gremlin.util.clamp(point.x, -1, 1)
        y = gremlin.util.clamp(point.y, -1, 1)

        new_point = Point2D(self._storage[cpid].x, self._storage[cpid].y)
        # Disallow points from being too close to each other
        if self._is_other_point_nearby(cpid, x):
            pass
        # Edge points cannot be moved away from the edge
        elif new_point.x in [-1, 1]:
            new_point.y = y
        else:
            new_point = Point2D(x, y)
        old_point = Point2D(self._storage[cpid].x, self._storage[cpid].y)
        self._storage[cpid] = new_point
        self.pointMoved.emit(cpid, old_point, new_point)

    def remove_point(self, cpid):
        """Removes the specified control point.

        :param cpid the id of the control point to remove
        """
        point = self._storage[cpid]
        # Only allow removal of non edge points
        if -1 < point.x < 1:
            self._storage.remove(cpid)
            self.pointRemoved.emit(cpid)

    def select_point(self, cpid):
        """Sets the specified control point as selected.

        :param cpid the id of the point to be marked as selected
        """
        self._active_point = cpid
        self.pointSelected.emit(cpid)

    def clear_storage(self):
        """Removes all points from the storage object."""
        self._next_id = 1
        self._storage.clear()

    def _is_other_point_nearby(self, cpid, x):
        """Returns whether or not another point is nearby to the given one.

        :param cpid the id of the point for which the check is performed
        :param x the new x coordinate for the specified point
        :return True if another point is nearby, False otherwise
        """
        for pid, point in self._storage.items():
            if pid == cpid or pid.secondary != 0:
                continue
            if abs(point.x - x) < 0.01:
                return True
        return False


class ControlPointShapeItem(QtWidgets.QGraphicsEllipseItem):

    """Represents a single control point within a GraphicsScene."""

    def __init__(self, identifier, point, parent=None):
        """Creates a new instance.

        :param identifier the id of this control point
        :param point the coordinates of the control point
        :param parent the parent widget
        """
        QtWidgets.QGraphicsEllipseItem.__init__(self, -4, -4, 8, 8, parent)
        self.setPos(point.x, point.y)
        self.setZValue(1)
        self.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        self.identifier = identifier

    def set_selected(self, is_selected):
        """Sets the selected state of the point.

        Renders the point accordingly and grabs or releases the mouse
        as needed.

        :param is_selected the flag of whether or not the point is
            selected
        """
        if is_selected:
            self.setBrush(QtGui.QBrush(QtCore.Qt.red))
            if self.scene().mouseGrabberItem() != self:
                self.grabMouse()
        else:
            self.setBrush(QtGui.QBrush(QtCore.Qt.gray))
            if self.scene().mouseGrabberItem() == self:
                self.ungrabMouse()

    def mouseReleaseEvent(self, evt):
        """Releases the mouse grab when the mouse is released."""
        self.ungrabMouse()

    def mouseMoveEvent(self, evt):
        """Updates the position of the control point based on mouse
        movements.

        :param evt the mouse event
        """
        self.setPos(evt.scenePos().x(), evt.scenePos().y())
        self.scene().update_model(self)


class CurvaturePointShapeItem(QtWidgets.QGraphicsRectItem):

    """Represents a single curvature control point within a GraphicsScene."""

    def __init__(self, identifier, point, parent=None):
        """Creates a new instance.

        :param identifier the id of this control point
        :param point the coordinates of the control point
        :param parent the parent widget
        """
        QtWidgets.QGraphicsRectItem.__init__(self, -4, -4, 8, 8, parent)
        self.setPos(point.x, point.y)
        self.setZValue(1)
        self.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        self.identifier = identifier

    def set_selected(self, is_selected):
        """Sets the selected state of the point.

        Renders the point accordingly and grabs or releases the mouse
        as needed.

        :param is_selected the flag of whether or not the point is
            selected
        """
        if is_selected:
            self.setBrush(QtGui.QBrush(QtCore.Qt.red))
            if self.scene().mouseGrabberItem() != self:
                self.grabMouse()
        else:
            self.setBrush(QtGui.QBrush(QtCore.Qt.gray))
            if self.scene().mouseGrabberItem() == self:
                self.ungrabMouse()

    def mouseReleaseEvent(self, evt):
        """Releases the mouse grab when the mouse is released."""
        self.ungrabMouse()

    def mouseMoveEvent(self, evt):
        """Updates the position of the control point based on mouse
        movements.

        :param evt the mouse event
        """
        self.setPos(evt.scenePos().x(), evt.scenePos().y())
        self.scene().update_model(self)


class ControlPointEditorWidget(QtWidgets.QWidget):

    """Widgets allowing the control point coordinates to be changed
    via text fields."""

    def __init__(self, model, parent=None):
        """Creates a new instance.

        :param model the model this instance visualizes
        :param parent the parent widget
        """
        QtWidgets.QWidget.__init__(self, parent)
        self._model = model
        self._current_selection = None

        # Connect to model signals
        self._model.pointRemoved.connect(self._point_removed_cb)
        self._model.pointMoved.connect(self._point_moved_cb)
        self._model.pointSelected.connect(self._point_selected_cb)

        # Create input field callbacks
        self._update_x_value = lambda val: self._value_changed_cb(0, val)
        self._update_y_value = lambda val: self._value_changed_cb(1, val)

        # Generate controls
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel("Control Point")
        self.x_label = QtWidgets.QLabel("X")
        self.y_label = QtWidgets.QLabel("Y")

        self.x_input = QtWidgets.QDoubleSpinBox()
        self.x_input.setRange(-1, 1)
        self.x_input.setDecimals(3)
        self.x_input.setSingleStep(0.1)

        self.y_input = QtWidgets.QDoubleSpinBox()
        self.y_input.setRange(-1, 1)
        self.y_input.setSingleStep(0.1)
        self.y_input.setDecimals(3)

        self._connect_input_fields()

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.x_label)
        self.main_layout.addWidget(self.x_input)
        self.main_layout.addWidget(self.y_label)
        self.main_layout.addWidget(self.y_input)

    def set_model(self, model):
        """Changes the model of the widget.

        :param model the new model to use
        """
        self._model = model
        self._model.pointRemoved.connect(self._point_removed_cb)
        self._model.pointMoved.connect(self._point_moved_cb)
        self._model.pointSelected.connect(self._point_selected_cb)

    def _point_removed_cb(self, cpid):
        """Invalidates the current selection if it matches the
        removed point.

        :param cpid the id of the removed point
        """
        if self._current_selection and cpid == self._current_selection:
            self._current_selection = None

    def _point_moved_cb(self, cpid, old_point, new_point):
        """Updates the values of the input fields.

        :param cpid the id of the moved point
        :param old_point old coordinates of the point
        :param new_point new coordinates of the point
        """
        self._disconnect_input_fields()
        self._current_selection = cpid
        self.x_input.setValue(new_point.x)
        self.y_input.setValue(new_point.y)
        self._connect_input_fields()

    def _point_selected_cb(self, cpid):
        """Updates the input field values with those of the selected point.

        :param cpid the id of the newly selected point
        """
        self._disconnect_input_fields()
        self._current_selection = cpid
        point = self._model.get_coords(cpid)
        self.x_input.setValue(point.x)
        self.y_input.setValue(point.y)
        self._connect_input_fields()

    def _connect_input_fields(self):
        """Connects the handlers for the input fields."""
        self.x_input.valueChanged.connect(self._update_x_value)
        self.y_input.valueChanged.connect(self._update_y_value)

    def _disconnect_input_fields(self):
        """Disconnects the handlers of the input fields."""
        self.x_input.valueChanged.disconnect(self._update_x_value)
        self.y_input.valueChanged.disconnect(self._update_y_value)

    def _value_changed_cb(self, index, value):
        """Updates the value of a control point due to input field changes.

        :param index the index of the value, i.e. 0 for x, 1 for y
        :param value the new value
        """
        if self._current_selection is not None and \
                self._current_selection.secondary == 0:
            x = value if index == 0 else self.x_input.value()
            y = value if index == 1 else self.y_input.value()
            self._model.move_point(
                self._current_selection,
                Point2D(x, y)
            )


class DeadzoneWidget(QtWidgets.QWidget):

    """Widget visualizing deadzone settings as well as allowing the
    modification of these."""

    def __init__(self, values, change_cb, parent=None):
        """Creates a new instance.

        :param values the initial deadzone settings
        :param change_cb callback function to execute upon change
        :param parent the parent widget
        """
        QtWidgets.QWidget.__init__(self, parent)

        self.change_cb = change_cb

        self.main_layout = QtWidgets.QGridLayout(self)

        # Create the two sliders
        self.left_slider = DualSlider()
        self.left_slider.setRange(-100, 0)
        self.right_slider = DualSlider()
        self.right_slider.setRange(0, 100)

        # Create spin boxes for the left slider
        self.left_lower = QtWidgets.QDoubleSpinBox()
        self.left_lower.setMinimum(-1.0)
        self.left_lower.setMaximum(0.0)
        self.left_lower.setSingleStep(0.05)
        self.left_upper = QtWidgets.QDoubleSpinBox()
        self.left_upper.setMinimum(-1.0)
        self.left_upper.setMaximum(0.0)
        self.left_upper.setSingleStep(0.05)
        # Create spin boxes for the right slider
        self.right_lower = QtWidgets.QDoubleSpinBox()
        self.right_lower.setSingleStep(0.05)
        self.right_lower.setMinimum(0.0)
        self.right_lower.setMaximum(1.0)
        self.right_upper = QtWidgets.QDoubleSpinBox()
        self.right_upper.setSingleStep(0.05)
        self.right_upper.setMinimum(0.0)
        self.right_upper.setMaximum(1.0)

        self._normalizer = self.left_slider.range()[1] - self.left_slider.range()[0]

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
        self.set_values(values)

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
        elif handle == DualSlider.UpperHandle:
            self.left_upper.setValue(value / self._normalizer)
        self.change_cb()

    def _update_right(self, handle, value):
        """Updates the right spin boxes.

        :param handle the handle which was moved
        :param value the new value
        """
        if handle == DualSlider.LowerHandle:
            self.right_lower.setValue(value /  self._normalizer)
        elif handle == DualSlider.UpperHandle:
            self.right_upper.setValue(value / self._normalizer)
        self.change_cb()

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
        self.change_cb()


class AxisResponseCurveWidget(AbstractActionWidget):

    """Widget that allows configuring the response of an axis to
    user inputs."""

    def __init__(self, action_data, vjoy_devices, change_cb, parent=None):
        """Creates a new instance.

        :param action_data the data associated with this specific action.
        :param change_cb the callback to execute when changes occur
        :param parent parent widget
        """
        AbstractActionWidget.__init__(
            self,
            action_data,
            vjoy_devices,
            change_cb,
            parent
        )

    def _setup_ui(self):
        """Creates the required UI elements."""
        # Axis configuration storage
        self.deadzone = [-1, 0, 0, 1]
        self.is_inverted = False

        self.curve_selection = QtWidgets.QComboBox()
        self.curve_selection.addItem("Cubic Spline")
        self.curve_selection.addItem("Cubic Bezier Spline")
        self.curve_selection.currentTextChanged.connect(self._change_model)

        self.model = ControlPointModel(gremlin.spline.CubicSpline)
        self.model.pointAdded.connect(self._point_added_cb)
        self.model.pointMoved.connect(self._point_added_cb)
        self.model.pointRemoved.connect(self._point_removed_cb)

        # Create widgets to edit the response curve
        # Graphical editor
        self.response_curve = ResponseCurveScene(self.model)
        self.view_layout = QtWidgets.QHBoxLayout()
        self._create_response_curve_view()
        # Text input field editor
        self.control_point_editor = ControlPointEditorWidget(self.model)

        # Deadzone configuration
        self.deadzone_label = QtWidgets.QLabel("Deadzone")
        self.deadzone = DeadzoneWidget(
            self.action_data.deadzone,
            self.change_cb
        )

        # Add all widgets to the layout
        self.main_layout.addWidget(self.curve_selection)
        self.main_layout.addLayout(self.view_layout)
        self.main_layout.addWidget(self.control_point_editor)
        self.main_layout.addWidget(self.deadzone_label)
        self.main_layout.addWidget(self.deadzone)

    def _change_model(self, name):
        """Changes the type of curve used.

        :param name the name of the new curve type
        """
        model_map = {
            "Cubic Spline": gremlin.spline.CubicSpline,
            "Cubic Bezier Spline": gremlin.spline.CubicBezierSpline
        }
        # Create new model
        self.model.pointAdded.disconnect(self._point_added_cb)
        self.model.pointMoved.disconnect(self._point_added_cb)
        self.model.pointRemoved.disconnect(self._point_removed_cb)
        self.model = ControlPointModel(model_map[name])
        self.model.pointAdded.connect(self._point_added_cb)
        self.model.pointMoved.connect(self._point_added_cb)
        self.model.pointRemoved.connect(self._point_removed_cb)
        # Setup graph view and text fields
        self.response_curve = ResponseCurveScene(self.model)
        self._create_response_curve_view()
        self.control_point_editor.set_model(self.model)

        self.model.add_point(Point2D(-1.0, -1.0))
        self.model.add_point(Point2D(1.0, 1.0))

    def _create_response_curve_view(self):
        self.view = QtWidgets.QGraphicsView(self.response_curve)
        self.view.setFixedSize(QtCore.QSize(410, 410))
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.view.setSceneRect(QtCore.QRectF(-200, -200, 400, 400))
        gremlin.util.clear_layout(self.view_layout)
        self.view_layout.addStretch()
        self.view_layout.addWidget(self.view)
        self.view_layout.addStretch()

    def _invert_cb(self, state):
        """Callback for invert checkbox events.

        :param state the state of the checkbox
        """
        self.is_inverted = state != 0

    def _point_added_cb(self, cpid, point):
        """Notifies the DeviceWidget about the addition of a point.

        :param cpid id of the added or moved point
        :param point the new coordinates
        """
        self.change_cb()

    def _point_removed_cb(self, cpid):
        """Notifies the DeviceWidget about the removal of a point.

        :param cpid the id of the removed point
        """
        self.change_cb()

    def initialize_from_profile(self, action_data):
        # Create mapping from XML name to ui name
        name_map = {}
        for key, value in ResponseCurve.curve_name_map.items():
            name_map[value] = key

        # Setup correct response curve object
        self.curve_selection.setCurrentText(
            name_map[action_data.mapping_type]
        )

        # Disconnect all signals while adding points
        self.model.pointAdded.disconnect(self._point_added_cb)
        self.model.pointMoved.disconnect(self._point_added_cb)
        self.model.pointRemoved.disconnect(self._point_removed_cb)

        # Remove any existing points from the model
        self.model.clear_storage()
        self.response_curve.clear_points()

        # Add points to the curve
        if action_data.mapping_type == "cubic-spline":
            for point in action_data.control_points:
                self.model.add_point(Point2D(point[0], point[1]))
        elif action_data.mapping_type == "cubic-bezier-spline":
            points = copy.deepcopy(action_data.control_points)
            points.insert(0, (-1.05, points[0][1]))
            points.append((1.05, points[-1][1]))

            for i in range(1, len(points)-1, 3):
                cpid = self.model.add_point(
                    Point2D(points[i][0], points[i][1])
                )
                self.model.move_point(
                    ControlPointIdentifier(cpid.primary, 1),
                    Point2D(points[i-1][0], points[i-1][1])
                )
                self.model.move_point(
                    ControlPointIdentifier(cpid.primary, 2),
                    Point2D(points[i+1][0], points[i+1][1])
                )

        # Reconnect all signals
        self.model.pointAdded.connect(self._point_added_cb)
        self.model.pointMoved.connect(self._point_added_cb)
        self.model.pointRemoved.connect(self._point_removed_cb)

        self.deadzone.set_values(action_data.deadzone)

    def to_profile(self):
        self.action_data.mapping_type = \
            ResponseCurve.curve_name_map[self.curve_selection.currentText()]
        self.action_data.deadzone = self.deadzone.get_values()
        self.action_data.control_points = self.model.get_control_points()
        self.action_data.is_valid = True


class ResponseCurve(AbstractAction):

    """Represents axis response curve mapping."""

    icon = "gfx/icon_curve.svg"
    name = "Response Curve"
    widget = AxisResponseCurveWidget
    input_types = [
        gremlin.event_handler.InputType.JoystickAxis,
    ]

    curve_name_map = {
        "Cubic Spline": "cubic-spline",
        "Cubic Bezier Spline": "cubic-bezier-spline"
    }

    def __init__(self, parent):
        """Creates a new ResponseCurve instance.

        :param parent the parent profile.InputItem of this instance
        """
        AbstractAction.__init__(self, parent)
        self.deadzone = [-1, 0, 0, 1]
        self.sensitivity = 1.0
        self.mapping_type = "cubic-spline"
        self.control_points = [(-1.0, -1.0), (1.0, 1.0)]

    def _parse_xml(self, node):
        """Parses the XML corresponding to a response curve.

        :param node the XML node to parse
        """
        for child in node:
            if child.tag == "deadzone":
                self.deadzone = [
                    float(child.get("low")),
                    float(child.get("center_low")),
                    float(child.get("center_high")),
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
        deadzone_node.set("center_low", str(self.deadzone[1]))
        deadzone_node.set("center_high", str(self.deadzone[2]))
        deadzone_node.set("high", str(self.deadzone[3]))
        node.append(deadzone_node)

        return node

    def _generate_code(self):
        """Generates python code corresponding to this object."""
        body_code = Template(
            filename="templates/response_curve_body.tpl"
        ).render(
            entry=self,
            curve_name="curve_{:04d}".format(ResponseCurve.next_code_id),
            helpers=template_helpers
        )
        global_code = Template(
            filename="templates/response_curve_global.tpl"
        ).render(
            entry=self,
            curve_name="curve_{:04d}".format(ResponseCurve.next_code_id),
            gremlin=gremlin,
            helpers=template_helpers
        )

        return {
            "body": body_code,
            "global": global_code,
        }