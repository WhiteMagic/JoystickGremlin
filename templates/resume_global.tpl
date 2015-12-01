% if entry.parent.input_type == InputType.JoystickAxis:
    % if entry.condition and entry.condition.is_active:

${axis_button_name} = gremlin.util.AxisButton(${entry.condition.lower_limit}, ${entry.condition.upper_limit})
def ${axis_button_cb}(is_pressed):
    if is_pressed:
        gremlin.control_action.resume()

    % endif
% endif
#newline