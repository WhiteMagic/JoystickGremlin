% if entry.parent.input_type == InputType.JoystickAxis:
    % if entry.condition and entry.condition.is_active:

${axis_button_name} = gremlin.util.AxisButton(${entry.condition.lower_limit}, ${entry.condition.upper_limit})
def ${axis_button_cb}(is_pressed, vjoy):
    vjoy[${entry.vjoy_device_id}].button(${entry.vjoy_input_id}).is_pressed = is_pressed

    % endif
% endif
#newline