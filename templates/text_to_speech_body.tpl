% if entry.parent.input_type == InputType.JoystickAxis:
% if entry.condition and entry.condition.is_active:
${helpers["format_condition"](entry.condition)}
        ${axis_button_name}.process(value, lambda x: ${axis_button_cb}(x))
    % endif
% else:
${helpers["format_condition"](entry.condition)}
        tts.speak(gremlin.util.text_substitution("${entry.text}"))
% endif