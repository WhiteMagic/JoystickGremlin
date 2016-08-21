% if entry.parent.input_type == InputType.JoystickAxis:
${helpers["format_condition"](entry.condition)}
    % if entry.condition and entry.condition.is_active:
        ${axis_button_name}.process(value, lambda x: ${axis_button_cb}(x))
    % endif
% else:
${helpers["format_condition"](entry.condition)}
        gremlin.control_action.cycle_modes(${mode_list_name})
% endif