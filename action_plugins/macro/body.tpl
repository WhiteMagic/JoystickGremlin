% if entry.get_input_type() == InputType.JoystickAxis:
    % if entry.condition and entry.condition.is_active:
axis_button_${id}.process(value, lambda x: axis_button_callback_${id}(x))
    % endif
% else:
macro_${id}.run()
% endif