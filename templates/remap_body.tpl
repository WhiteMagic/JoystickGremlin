<%!
    from vjoy.vjoy import AxisName
    axis_map = {
        1: AxisName.X,
        2: AxisName.Y,
        3: AxisName.Z,
        4: AxisName.RX,
        5: AxisName.RY,
        6: AxisName.RZ,
        7: AxisName.SL0,
        8: AxisName.SL1
    }
%>\
${helpers["format_condition"](entry.condition)}
% if entry.input_type == InputType.JoystickAxis:
        vjoy[${entry.vjoy_device_id}].axis[${axis_map[entry.vjoy_input_id]}].value = value
% elif entry.input_type in [InputType.JoystickButton, InputType.Keyboard]:
        vjoy[${entry.vjoy_device_id}].button[${entry.vjoy_input_id}].is_pressed = is_pressed
% elif entry.input_type == InputType.JoystickHat:
        vjoy[${entry.vjoy_device_id}].hat[${entry.vjoy_input_id}].direction = hat_direction_map[value]
% endif