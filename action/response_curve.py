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

from mako.template import Template
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree

from action.common import AbstractAction, AbstractActionWidget, DualSlider
import gremlin


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

    def _point_added_cb(self, idx, x, y):
        """Adds a new point to the scene.

        :param idx the id of the point in the model
        :param x the x coordinate of the point
        :param y the y coordinate of the point
        """
        self._points[idx] = ControlPointShapeItem(idx, x, y)
        self.addItem(self._points[idx])
        self._draw_control_points()
        self._draw_response_curve()

    def _point_removed_cb(self, idx):
        """Removes the given point from the scene.

        :param idx the model if of the point being removed
        """
        self.removeItem(self._points[idx])
        del self._points[idx]
        self._draw_control_points()
        self._draw_response_curve()

    def _point_moved_cb(self, idx, x, y):
        """Updates the position of the point in the scene and redraws
        the response curve.

        :param idx id of the point being changed
        :param x the new x coordinate
        :param y the new y coordinate
        """
        self._points[idx].setPos(x * 200.0, y * -200.0)
        self._draw_response_curve()

    def _point_selected_cb(self, idx):
        """Updates the point selection.

        :param idx the id of the newly selected point
        """
        # Remove highlight from all nodes
        for node in self._points.values():
            node.set_selected(node.identifier == idx)

    def _draw_control_points(self):
        """Updates the locations of all control points."""
        for idx, node in self._points.items():
            coords = self._model.get_coords(idx)
            node.setPos(coords[0] * 200, coords[1] * -200)

    def _draw_response_curve(self):
        """Redraws the entire response curve."""
        curve = self._model.curve_model(self._model.get_control_points())
        # Remove old path
        for item in self.items():
            if isinstance(item, QtWidgets.QGraphicsPathItem):
                self.removeItem(item)

        # Draw new curve
        if len(curve.x) > 1:
            path = QtGui.QPainterPath(QtCore.QPointF(-200, -200*curve(-1)))
            for x in range(-200, 201, 2):
                path.lineTo(x, -200 * curve(x / 200.0))
            self.addPath(path)

    def mousePressEvent(self, evt):
        """Informs the model about point selection if a point is clicked.

        :param evt the mouse event
        """
        item = self.itemAt(evt.scenePos(), QtGui.QTransform())
        is_control_point = isinstance(item, QtWidgets.QGraphicsEllipseItem)

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
                self._model.add_point(
                    evt.scenePos().x() / 200.0,
                    evt.scenePos().y() / -200.0
                )
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
            control_point.x() / 200.0,
            control_point.y() / -200.0
        )


class ControlPointModel(QtCore.QObject):

    """Model representing the control points of a response curve."""

    # Signals emitted by the model
    pointAdded = QtCore.pyqtSignal(int, float, float)
    pointRemoved = QtCore.pyqtSignal(int)
    pointMoved = QtCore.pyqtSignal(int, float, float)
    pointSelected = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent object
        """
        QtCore.QObject.__init__(self, parent)
        self._points = {}
        self._active_point = None
        self._next_id = 0
        self.curve_model = gremlin.cubic_spline.CubicSpline

    def get_control_points(self):
        """Returns the sorted list of all control points.

        :return sorted list of control points
        """
        return sorted(
            [(n[0], n[1]) for n in self._points.values()],
            key=lambda n: n[0]
        )

    def get_coords(self, idx):
        """Returns the coordinates of the specified control point.

        :param idx the id of the control point
        :return coordinates of the corresponding control point
        """
        return self._points[idx]

    def add_point(self, x, y):
        """Adds a new control point with the provided coordinates.

        :param x the x coordinate of the new control point
        :param y the y coordinate of the new control point
        """
        if -1 <= x <= 1 and -1 <= y <= 1:
            if not self._is_other_point_nearby(-1, x):
                self._points[self._next_id] = [x, y]
                self.pointAdded.emit(self._next_id, x, y)
                self._next_id += 1

    def move_point(self, idx, x, y):
        """Moves the specified control point to the new coordinates.

        :param idx the id of the control point to move
        :param x the new x coordinate of the control point
        :param y the new y coordinate of the control point
        """
        # Ensure points are in [-1, 1]
        x = gremlin.util.clamp(x, -1, 1)
        y = gremlin.util.clamp(y, -1, 1)

        point = self._points[idx]
        # Disallow points from being too close to each other
        if self._is_other_point_nearby(idx, x):
            pass
        # Edge points cannot be moved away from the edge
        elif point[0] in [-1, 1]:
            point[1] = y
        else:
            point = [x, y]
        self._points[idx] = point
        self.pointMoved.emit(idx, point[0], point[1])

    def remove_point(self, idx):
        """Removes the specified control point.

        :param idx the id of the control point to remove
        """
        del self._points[idx]
        self.pointRemoved.emit(idx)

    def select_point(self, idx):
        """Sets the specified control point as selected.

        :param idx the id of the point to be marked as selected
        """
        self._active_point = idx
        self.pointSelected.emit(idx)

    def _is_other_point_nearby(self, idx, x):
        """Returns whether or not another point is nearby to the given one.

        :param idx the id of the point for which the check is performed
        :param x the new x coordinate for the specified point
        :return True if another point is nearby, False otherwise
        """
        for pid, point in self._points.items():
            if pid == idx:
                continue
            if abs(point[0] - x) < 0.01:
                return True
        return False


class ControlPointShapeItem(QtWidgets.QGraphicsEllipseItem):

    """Represents a single control point within a GraphicsScene."""

    def __init__(self, identifier, x, y, parent=None):
        """Creates a new instance.

        :param x the x coordinate of the control point
        :param y the y coordinate of the control point
        :param identifier the id of this control point
        :param parent the parent widget
        """
        QtWidgets.QGraphicsEllipseItem.__init__(self, -4, -4, 8, 8, parent)
        self.setPos(x, y)
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

    def _point_removed_cb(self, idx):
        """Invalidates the current selection if it matches the
        removed point.

        :param idx the id of the removed point
        """
        if idx == self._current_selection:
            self._current_selection = None

    def _point_moved_cb(self, idx, x, y):
        """Updates the values of the input fields.

        :param idx the id of the moved point
        :param x the new x coordinate
        :param y the new y coordinate
        """
        self._disconnect_input_fields()
        self._current_selection = idx
        self.x_input.setValue(x)
        self.y_input.setValue(y)
        self._connect_input_fields()

    def _point_selected_cb(self, idx):
        """Updates the input field values with those of the selected point.

        :param idx the id of the newly selected point
        """
        self._disconnect_input_fields()
        self._current_selection = idx
        point = self._model.get_coords(idx)
        self.x_input.setValue(point[0])
        self.y_input.setValue(point[1])
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
        if self._current_selection is not None:
            x = value if index == 0 else self.x_input.value()
            y = value if index == 1 else self.y_input.value()
            self._model.move_point(self._current_selection, x, y)


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
        AbstractActionWidget.__init__(self, action_data, vjoy_devices, change_cb, parent)
        assert(isinstance(action_data, ResponseCurve))

    def _setup_ui(self):
        # Axis configuration storage
        self.deadzone = [-1, 0, 0, 1]
        self.is_inverted = False
        self.model = ControlPointModel()
        self.model.pointAdded.connect(self._point_added_cb)
        self.model.pointMoved.connect(self._point_added_cb)
        self.model.pointRemoved.connect(self._point_removed_cb)

        # Create widgets to edit the response curve
        # Graphical editor
        self.response_curve = ResponseCurveScene(self.model)
        self.view = QtWidgets.QGraphicsView(self.response_curve)
        self.view.setFixedSize(QtCore.QSize(410, 410))
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.view.setSceneRect(QtCore.QRectF(-200, -200, 400, 400))
        self.view_layout = QtWidgets.QHBoxLayout()
        self.view_layout.addStretch()
        self.view_layout.addWidget(self.view)
        self.view_layout.addStretch()
        # Text input field editor
        self.control_point_editor = ControlPointEditorWidget(self.model)

        # Deadzone configuration
        self.deadzone_label = QtWidgets.QLabel("Deadzone")
        self.deadzone = DeadzoneWidget(
            self.action_data.deadzone,
            self.change_cb
        )

        # Add all widgets to the layout
        self.main_layout.addLayout(self.view_layout)
        self.main_layout.addWidget(self.control_point_editor)
        self.main_layout.addWidget(self.deadzone_label)
        self.main_layout.addWidget(self.deadzone)

    def _invert_cb(self, state):
        """Callback for invert checkbox events.

        :param state the state of the checkbox
        """
        self.is_inverted = state != 0

    def _point_added_cb(self, idx, x, y):
        """Notifies the DeviceWidget about the addition of a point.

        :param idx id of the added or moved point
        :param x the new x coordinate
        :param y the new y coordinate
        """
        self.change_cb()

    def _point_removed_cb(self, idx):
        """Notifies the DeviceWidget about the removal of a point.

        :param idx the id of the removed point
        """
        self.change_cb()

    def initialize_from_profile(self, action_data):
        self.model.pointAdded.disconnect(self._point_added_cb)
        self.model.pointMoved.disconnect(self._point_added_cb)
        self.model.pointRemoved.disconnect(self._point_removed_cb)
        for point in action_data.control_points:
            self.model.add_point(point[0], point[1])
        self.model.pointAdded.connect(self._point_added_cb)
        self.model.pointMoved.connect(self._point_added_cb)
        self.model.pointRemoved.connect(self._point_removed_cb)

        self.deadzone.set_values(action_data.deadzone)

    def to_profile(self):
        self.action_data.mapping_type = "cubic-spline"
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
            elif child.tag == "mapping" and child.get("type") == "cubic-spline":
                self.mapping_type = "cubic-spline"
                self.control_points = []
                for point in child.iter("control-point"):
                    self.control_points.append((
                        float(point.get("x")),
                        float(point.get("y"))
                    ))
                self.control_points = sorted(self.control_points, key=lambda x: x[0])

    def _generate_xml(self):
        """Generates a XML node corresponding to this object.

        :return XML node representing the object's data
        """
        node = ElementTree.Element("response-curve")
        # Response curve mapping
        if len(self.control_points) > 0:
            mapping_node = ElementTree.Element("mapping")
            mapping_node.set("type", self.mapping_type)
            if self.mapping_type == "cubic-spline":
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
        body_code = Template(filename="templates/response_curve_body.tpl").render(
            entry=self,
            curve_name="curve_{:04d}".format(ResponseCurve.next_code_id)
        )
        global_code = Template(filename="templates/response_curve_global.tpl").render(
            entry=self,
            curve_name="curve_{:04d}".format(ResponseCurve.next_code_id),
            gremlin=gremlin
        )

        return {
            "body": body_code,
            "global": global_code,
        }