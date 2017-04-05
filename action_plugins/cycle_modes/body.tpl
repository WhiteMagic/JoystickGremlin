% if input_type == InputType.JoystickAxis:
    % if entry.condition and entry.condition.is_active:
axis_button_${id}.process(value, lambda x: axis_button_callback_${id})(x))
    % endif
% elif input_type in [InputType.JoystickButton, InputType.Keyboard]:
cycle_modes_${id}(is_pressed)
% elif input_type == InputType.JoystickHat:
cycle_modes_${id}(True)
% endif