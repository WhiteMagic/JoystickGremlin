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
% if entry.parent.input_type == InputType.JoystickAxis:
    % if entry.input_type == InputType.JoystickAxis:
${helpers["format_condition"](entry.condition)}
        vjoy[${entry.vjoy_device_id}].axis[${axis_map[entry.vjoy_input_id]}].value = value
    % elif entry.condition.is_active == True:
${helpers["format_condition"](entry.condition)}
        ${axis_button_name}.process(value, lambda x: ${axis_button_cb}(x, vjoy))
    % endif
% elif entry.parent.input_type in [InputType.JoystickButton, InputType.Keyboard]:
    % if entry.condition.on_press and entry.condition.on_release:
    if is_pressed:
        tracker = gremlin.input_devices.AutomaticButtonRelease()
        tracker.register((${entry.vjoy_device_id}, ${entry.vjoy_input_id}), event)
    % endif
${helpers["format_condition"](entry.condition)}
        vjoy[${entry.vjoy_device_id}].button[${entry.vjoy_input_id}].is_pressed = is_pressed
% elif entry.parent.input_type == InputType.JoystickHat:
    vjoy[${entry.vjoy_device_id}].hat[${entry.vjoy_input_id}].direction = hat_direction_map[value]
% endif
