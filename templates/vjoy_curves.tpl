from PyQt5 import QtCore

from gremlin.event_handler import EventHandler
from gremlin.input_devices import VJoyProxy


class VJoyCurves(QtCore.QObject):

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        EventHandler().mode_changed.connect(self._mode_changed_cb)

    def _mode_changed_cb(self, new_mode):
    % for vid in vjoy_ids:
        self._handle_vjoy_${vid}(new_mode)
    % endfor


    % for device in vjoy_devices.values():
    def _handle_vjoy_${device.windows_id}(self, new_mode):
        vjoy = VJoyProxy()[${device.windows_id}]

        % for name, mode in device.modes.items():
        if new_mode == "${name}":
            % for aid, entry in mode.config[UiInputType.JoystickAxis].items():
            % if len(entry.actions) > 0:
            if vjoy.is_axis_valid(${aid}):
                % for action in entry.actions:
                vjoy.axis(${aid}).set_deadzone(${action.deadzone[0]}, ${action.deadzone[1]}, ${action.deadzone[2]}, ${action.deadzone[3]})
                vjoy.axis(${aid}).set_response_curve(
                    "${action.mapping_type}",
                    ${action.control_points}
                )
                % endfor
            % endif
            % endfor
            pass
        % endfor
    % endfor

vjoy_curves = VJoyCurves()
