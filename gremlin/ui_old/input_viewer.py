# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2020 Lionel Ott
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
import enum
import time

from PyQt5 import QtCore, QtGui, QtWidgets

import dill

import gremlin
from . import common


class VisualizationType(enum.Enum):

    """Enumeration of possible visualization types."""

    AxisTemporal = 1
    AxisCurrent = 2
    ButtonHat = 3


class VisualizationSelector(QtWidgets.QWidget):

    """Presents a list of possibly device and visualization widgets."""

    # Event emitted when the visualization configuration changes
    changed = QtCore.pyqtSignal(
        dill.DeviceSummary,
        VisualizationType,
        bool
    )

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        devices = gremlin.joystick_handling.joystick_devices()

        self.main_layout = QtWidgets.QVBoxLayout(self)
        for dev in sorted(devices, key=lambda x: (x.name, x.vjoy_id)):
            if dev.is_virtual:
                box = QtWidgets.QGroupBox("{} #{:d}".format(
                    dev.name,
                    dev.vjoy_id
                ))
            else:
                box = QtWidgets.QGroupBox(dev.name)

            at_cb = QtWidgets.QCheckBox("Axes - Temporal")
            at_cb.stateChanged.connect(
                self._create_callback(dev, VisualizationType.AxisTemporal)
            )

            ac_cb = QtWidgets.QCheckBox("Axes - Current")
            ac_cb.stateChanged.connect(
                self._create_callback(dev, VisualizationType.AxisCurrent)
            )
            bh_cb = QtWidgets.QCheckBox("Buttons + Hats")
            bh_cb.stateChanged.connect(
                self._create_callback(dev, VisualizationType.ButtonHat)
            )

            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(at_cb)
            layout.addWidget(ac_cb)
            layout.addWidget(bh_cb)

            box.setLayout(layout)

            self.main_layout.addWidget(box)

    def _create_callback(self, device, vis_type):
        """Creates the callback to trigger visualization updates.

        :param device the device being updated
        :param vis_type visualization type being updated
        """
        return lambda state: self.changed.emit(
                device,
                vis_type,
                state == QtCore.Qt.Checked
            )


class InputViewerUi(common.BaseDialogUi):

    """Main UI dialog for the input viewer."""

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        self._widget_storage = {}

        self.devices = gremlin.joystick_handling.joystick_devices()
        self.setLayout(QtWidgets.QHBoxLayout())

        self.vis_selector = VisualizationSelector()
        self.vis_selector.changed.connect(self._add_remove_visualization_widget)

        self.views = InputViewerArea()

        self.layout().addWidget(self.vis_selector)
        self.layout().addWidget(self.views)

    def _add_remove_visualization_widget(self, device, vis_type, is_active):
        """Adds or removes a visualization widget.

        :param device the device which is being updated
        :param vis_type the visualization type being updated
        :param is_active if True the visualization is added, if False it is
            removed
        """
        key = device, vis_type
        widget = JoystickDeviceWidget(device, vis_type)
        if is_active:
            self.views.add_widget(widget)
            self._widget_storage[key] = widget
        elif key in self._widget_storage:
            self.views.remove_widget(self._widget_storage[key])
            del self._widget_storage[key]


class InputViewerArea(QtWidgets.QScrollArea):

    """Holds individual input visualization widgets."""

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.widgets = []
        self.setWidgetResizable(True)
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout()
        self.scroll_layout.addStretch()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.setWidget(self.scroll_widget)

    def add_widget(self, widget):
        """Adds the specified widget to the visualization area.

        :param widget the widget to add
        """
        self.widgets.append(widget)
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, widget)
        widget.show()

        width = 0
        height = 0
        for widget in self.widgets:
            hint = widget.minimumSizeHint()
            height = max(height, hint.height())
            width = max(width, hint.width())
        self.setMinimumSize(QtCore.QSize(width+40, height))

    def remove_widget(self, widget):
        """Removes a widget from the visualization area.

        :param widget the widget to remove
        """
        self.scroll_layout.removeWidget(widget)
        widget.hide()
        del self.widgets[self.widgets.index(widget)]
        del widget


class JoystickDeviceWidget(QtWidgets.QWidget):

    """Widget visualization joystick data."""

    def __init__(self, device_data, vis_type, parent=None):
        """Creates a new instance.

        :param device_data information about the device itself
        :param vis_type the visualization type to use
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.device_data = device_data
        self.device_guid = device_data.device_guid
        self.vis_type = vis_type
        self.widgets = []
        self.setLayout(QtWidgets.QHBoxLayout())

        el = gremlin.event_handler.EventListener()
        if vis_type == VisualizationType.AxisCurrent:
            self._create_current_axis()
            el.joystick_event.connect(self._current_axis_update)
        elif vis_type == VisualizationType.AxisTemporal:
            self._create_temporal_axis()
            el.joystick_event.connect(self._temporal_axis_update)
        elif vis_type == VisualizationType.ButtonHat:
            self._create_button_hat()
            el.joystick_event.connect(self._button_hat_update)

    def minimumSizeHint(self):
        """Returns the minimum size of this widget.

        :return minimum size of this widget
        """
        width = 0
        height = 0
        for widget in self.widgets:
            hint = widget.minimumSizeHint()
            height = max(height, hint.height())
            width += hint.width()
        return QtCore.QSize(width, height)

    def _create_button_hat(self):
        """Creates display for button and hat data."""
        self.widgets = [
            ButtonState(self.device_data),
            HatState(self.device_data)
        ]
        for widget in self.widgets:
            self.layout().addWidget(widget)
        self.layout().addStretch(1)

    def _create_current_axis(self):
        """Creates display for current axes data."""
        self.widgets = [AxesCurrentState(self.device_data)]
        for widget in self.widgets:
            self.layout().addWidget(widget)

    def _create_temporal_axis(self):
        """Creates display for temporal axes data."""
        self.widgets = [AxesTimeline(self.device_data)]
        for widget in self.widgets:
            self.layout().addWidget(widget)

    def _button_hat_update(self, event):
        """Updates the button and hat display.

        :param event the event to use in the update
        """
        if self.device_guid != event.device_guid:
            return

        for widget in self.widgets:
            widget.process_event(event)

    def _current_axis_update(self, event):
        if self.device_guid != event.device_guid:
            return

        for widget in self.widgets:
            widget.process_event(event)

    def _temporal_axis_update(self, event):
        """Updates the temporal axes display.

        :param event the event to use in the update
        """
        if self.device_guid != event.device_guid:
            return

        if event.event_type == gremlin.common.InputType.JoystickAxis:
            for widget in self.widgets:
                widget.add_point(event.value, event.identifier)


class ButtonState(QtWidgets.QGroupBox):

    """Widget representing the state of a device's buttons."""

    style_sheet = """
        QPushButton {
            border: 2px solid #8f8f91;
            border-radius: 15px;
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #f6f7fa, stop: 1 #dadbde);
            min-width: 30px;
            min-height: 30px;
            max-width: 30px;
            max-height: 30px;
        }

        QPushButton:pressed {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #e5342d, stop: 1 #b22823);
            border-color: #661714;
        }

        QPushButton:flat {
            border: none; /* no border for a flat push button */
        }

        QPushButton:!enabled
        {
             color: #000000;
        }
        """

    def __init__(self, device, parent=None):
        """Creates a new instance.

        :param device the device of which to display the button sate
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self._event_times = {}

        if device.is_virtual:
            self.setTitle("{} #{:d} - Buttons".format(device.name, device.vjoy_id))
        else:
            self.setTitle("{} - Buttons".format(device.name))

        self.buttons = [None]
        button_layout = QtWidgets.QGridLayout()
        for i in range(device.button_count):
            btn = QtWidgets.QPushButton(str(i+1))
            btn.setStyleSheet(ButtonState.style_sheet)
            btn.setDisabled(True)
            self.buttons.append(btn)
            button_layout.addWidget(btn, int(i / 10), int(i % 10))
        button_layout.setColumnStretch(10, 1)
        self.setLayout(button_layout)

    def process_event(self, event):
        """Updates state visualization based on the given event.

        :param event the event with which to update the state display
        """
        if event.event_type == gremlin.common.InputType.JoystickButton:
            state = event.is_pressed if event.is_pressed is not None else False
            self.buttons[event.identifier].setDown(state)
            self._event_times[event.identifier] = time.time()


class HatState(QtWidgets.QGroupBox):

    """Visualizes the sate of a device's hats."""

    def __init__(self, device, parent=None):
        """Creates a new instance.

        :param device the device of which to display the hat sate
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self._event_times = {}

        if device.is_virtual:
            self.setTitle("{} #{:d} - Hats".format(device.name, device.vjoy_id))
        else:
            self.setTitle("{} - Hats".format(device.name))

        self.hats = [None]
        hat_layout = QtWidgets.QGridLayout()
        for i in range(device.hat_count):
            hat = HatWidget()
            self.hats.append(hat)
            hat_layout.addWidget(hat, int(i / 2), int(i % 2))

        self.setLayout(hat_layout)

    def process_event(self, event):
        """Updates state visualization based on the given event.

        :param event the event with which to update the state display
        """
        if event.event_type == gremlin.common.InputType.JoystickHat:
            self.hats[event.identifier].set_angle(event.value)
            self._event_times[event.identifier] = time.time()


class AxesTimeline(QtWidgets.QGroupBox):

    """Visualizes axes state as a timeline."""

    color_list = {
        1: "#e41a1c",
        2: "#377eb8",
        3: "#4daf4a",
        4: "#984ea3",
        5: "#ff7f00",
        6: "#ffff33",
        7: "#a65628",
        8: "#f781bf"
    }

    def __init__(self, device, parent=None):
        """Creates a new instance.

        :param device the device of which to display the axes sate
        :param parent the parent of this widget
        """
        super().__init__(parent)

        if device.is_virtual:
            self.setTitle("{} #{:d} - Axes".format(device.name, device.vjoy_id))
        else:
            self.setTitle("{} - Axes".format(device.name))

        self.setLayout(QtWidgets.QVBoxLayout())
        self.plot_widget = TimeLinePlotWidget()
        self.legend_layout = QtWidgets.QHBoxLayout()
        self.legend_layout.addStretch()
        for i in range(device.axis_count):
            label = QtWidgets.QLabel(
                "Axis {:d}".format(device.axis_map[i].axis_index)
            )
            label.setStyleSheet(
                "QLabel {{ color: {}; font-weight: bold }}".format(
                    AxesTimeline.color_list.get(
                        device.axis_map[i].axis_index,
                        "#000000"
                    )
                )
            )
            self.legend_layout.addWidget(label)
        self.layout().addWidget(self.plot_widget)
        self.layout().addLayout(self.legend_layout)

    def add_point(self, value, series_id):
        """Adds a new point to the timline.

        :param value the value to add
        :param series_id id of the axes to which to add the value
        """
        self.plot_widget.add_point(value, series_id)


class AxesCurrentState(QtWidgets.QGroupBox):

    """Displays the current state of all axes on a device."""

    def __init__(self, device, parent=None):
        """Creates a new instance.

        :param device the device of which to display the axes sate
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.device = device
        if device.is_virtual:
            self.setTitle("{} #{:d} - Axes".format(device.name, device.vjoy_id))
        else:
            self.setTitle("{} - Axes".format(device.name))

        self.axes = [None]
        axes_layout = QtWidgets.QHBoxLayout()
        for i in range(device.axis_count):
            axis = AxisStateWidget(i+1)
            axis.set_value(0.0)
            self.axes.append(axis)
            axes_layout.addWidget(axis)
        axes_layout.addStretch()
        self.setLayout(axes_layout)

    def process_event(self, event):
        """Updates state visualization based on the given event.

        :param event the event with which to update the state display
        """
        if event.event_type == gremlin.common.InputType.JoystickAxis:
            axis_id = gremlin.joystick_handling.linear_axis_index(
                self.device.axis_map,
                event.identifier
            )
            self.axes[axis_id].set_value(event.value)


class AxisStateWidget(QtWidgets.QWidget):

    """Visualizes the current state of an axis."""

    # Scaling factor for the [-1, 1] input to make ensure proper visualization
    scale_factor = 10000

    def __init__(self, axis_id, parent=None):
        """Creates a new instance.

        :param axis_id id of the axis, used in the label
        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(
            -AxisStateWidget.scale_factor,
            AxisStateWidget.scale_factor
        )
        self.progress.setOrientation(QtCore.Qt.Vertical)

        self.readout = QtWidgets.QLabel()
        self.label = QtWidgets.QLabel("Axis {}".format(axis_id))

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.progress)
        self.main_layout.addWidget(self.readout)

    def set_value(self, value):
        """Sets the value shown by the widget.

        :param value new value to show
        """
        self.progress.setValue(AxisStateWidget.scale_factor * value)
        self.readout.setText("{:d} %".format(int(round(100 * value))))


class HatWidget(QtWidgets.QWidget):

    """Widget visualizing the state of a hat."""

    # Polygon path for a triangle
    triangle = QtGui.QPolygon(
        [QtCore.QPoint(-10, 0), QtCore.QPoint(10, 0), QtCore.QPoint(0, 15)]
    )

    # Mapping from event values to rotation angles
    lookup = {
        (0, 0): -1,
        (0, 1): 180,
        (1, 1): 225,
        (1, 0): 270,
        (1, -1): 315,
        (0, -1): 0,
        (-1, -1): 45,
        (-1, 0): 90,
        (-1, 1): 135
    }

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        self.angle = -1

    def minimumSizeHint(self):
        """Returns the minimum size of the widget.

        :return the widget's minimum size
        """
        return QtCore.QSize(120, 120)

    def set_angle(self, state):
        """Sets the current direction of the hat.

        :param state the direction of the hat
        """
        self.angle = HatWidget.lookup.get(state, -1)
        self.update()

    def paintEvent(self, event):
        """Draws the entire hat state visualization.

        :param event the paint event
        """
        # Define pens and brushes
        pen_default = QtGui.QPen(QtGui.QColor("#8f8f91"))
        pen_default.setWidth(2)
        pen_active = QtGui.QPen(QtGui.QColor("#661714"))
        pen_active.setWidth(2)
        brush_default = QtGui.QBrush(QtGui.QColor("#f6f7fa"))
        brush_active = QtGui.QBrush(QtGui.QColor("#b22823"))

        # Prepare painter instance
        painter = QtGui.QPainter(self)
        painter.setRenderHint(int(
            QtGui.QPainter.Antialiasing |
            QtGui.QPainter.SmoothPixmapTransform
        ))
        painter.setPen(pen_default)
        painter.setBrush(brush_default)

        painter.translate(50, 50)

        # Center dot
        if self.angle == -1:
            painter.setBrush(brush_active)
        painter.drawEllipse(-8, -8, 16, 16)
        painter.setBrush(brush_default)
        # Directions
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            painter.save()
            painter.rotate(angle)
            painter.translate(0, 35)

            if angle == self.angle:
                painter.setBrush(brush_active)
                painter.setPen(pen_active)

            painter.drawPolygon(HatWidget.triangle)
            painter.restore()


class TimeLinePlotWidget(QtWidgets.QWidget):

    """Visualizes temporal data as a line graph."""

    # Pre-defined colors for eight time series
    pens = {
        1: QtGui.QPen(QtGui.QColor("#e41a1c")),
        2: QtGui.QPen(QtGui.QColor("#377eb8")),
        3: QtGui.QPen(QtGui.QColor("#4daf4a")),
        4: QtGui.QPen(QtGui.QColor("#984ea3")),
        5: QtGui.QPen(QtGui.QColor("#ff7f00")),
        6: QtGui.QPen(QtGui.QColor("#ffff33")),
        7: QtGui.QPen(QtGui.QColor("#a65628")),
        8: QtGui.QPen(QtGui.QColor("#f781bf")),
    }
    for pen in pens.values():
        pen.setWidth(2)
    pens[0] = QtGui.QPen(QtGui.QColor("#c0c0c0"))
    pens[0].setWidth(1)

    def __init__(self, parent=None):
        """Creates a new instance.

        :param parent the parent of this widget
        """
        super().__init__(parent)

        self._render_flags = int(
            QtGui.QPainter.Antialiasing |
            QtGui.QPainter.SmoothPixmapTransform
        )

        # Plotting canvas
        self._pixmap = QtGui.QPixmap(1000, 200)
        self._pixmap.fill()

        # Grid drawing variables
        self._horizontal_steps = 0
        self._vertical_timestep = time.time()

        # Last recorded value for a data series
        self._series = {}

        # Step size per update
        self._step_size = 1

        # Update the plot
        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(self._update_pixmap)
        self._update_timer.start(1000/60)

        # Redrawing of the widget
        self._repaint_timer = QtCore.QTimer(self)
        self._repaint_timer.timeout.connect(self.update)
        self._repaint_timer.start(1000/60)

    def resizeEvent(self, event):
        """Handles resizing this widget.

        :param event the resize event
        """
        self._pixmap = QtGui.QPixmap(event.size())
        self._pixmap.fill()
        self._horizontal_steps = 0
        self._vertical_timestep = time.time()

    def minimumSizeHint(self):
        """Returns the minimum size of this widget.

        :return the widget's minimum size
        """
        return QtCore.QSize(400, 150)

    def paintEvent(self, event):
        """Refreshes the timeline view.

        :param event the paint event
        """
        widget_painter = QtGui.QPainter(self)
        widget_painter.drawPixmap(0, 0, self._pixmap)

    def add_point(self, value, series_id=0):
        """Adds a data point to a time series.

        :param value the value to add
        :param series_id the series to which to add the value
        """
        if series_id not in self._series:
            self._series[series_id] = [value, value]
        self._series[series_id][1] = value

    def _update_pixmap(self):
        """Updates the pixmap that contains the moving timeline."""
        pixmap_painter = QtGui.QPainter(self._pixmap)
        pixmap_painter.setRenderHint(self._render_flags)

        self._pixmap.scroll(
            -self._step_size,
            0,
            QtCore.QRect(0, 0, self._pixmap.width(), self._pixmap.height())
        )
        pixmap_painter.eraseRect(
            self._pixmap.width() - self._step_size,
            0,
            1,
            self._pixmap.height()
        )

        # Draw vertical line in one second intervals
        pixmap_painter.setPen(TimeLinePlotWidget.pens[0])
        if self._vertical_timestep < time.time()-1:
            pixmap_painter.drawLine(
                self._pixmap.width()-1,
                0,
                self._pixmap.width() - 1,
                self._pixmap.height()
            )
            self._vertical_timestep = time.time()
        self._horizontal_steps += 1
        if self._horizontal_steps <= 5:
            quarter = self._pixmap.height() / 4
            x = self._pixmap.width()-1
            pixmap_painter.drawPoint(x, quarter)
            pixmap_painter.drawPoint(x, 2*quarter)
            pixmap_painter.drawPoint(x, 3*quarter)
        elif self._horizontal_steps > 10:
            self._horizontal_steps = 0

        # Draw onto the pixmap all series data that has been accumulated
        for key, value in self._series.items():
            pixmap_painter.setPen(TimeLinePlotWidget.pens[key])
            pixmap_painter.drawLine(
                self._pixmap.width()-self._step_size-1,
                2 + (self._pixmap.height()-4) * (value[0] + 1) / 2.0,
                self._pixmap.width()-1,
                2 + (self._pixmap.height()-4) * (value[1] + 1) / 2.0
            )
            value[0] = value[1]
