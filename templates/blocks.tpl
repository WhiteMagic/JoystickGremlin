<%def name="axis_button(id, input_type, InputType, entry, code)">
% if input_type == InputType.JoystickAxis:
    % if entry.condition and entry.condition.is_active:
axis_button_${id} = gremlin.action_containers.AxisButton(${entry.condition.lower_limit}, ${entry.condition.upper_limit})
def axis_button_callback_${id}(is_pressed):
    if is_pressed:
        ${code}
    % endif
% endif
</%def>