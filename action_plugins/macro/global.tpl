${macro_name} = gremlin.macro.Macro()
% for seq in entry.sequence:
% if isinstance(seq, gremlin.macro.Macro.Pause):
${macro_name}.pause(${seq.duration})
% elif isinstance(seq, gremlin.macro.Macro.KeyAction):
${macro_name}.action(gremlin.macro.key_from_code(${seq.key._scan_code}, ${seq.key._is_extended}), ${seq.is_pressed})
% endif
% endfor
#newline
% if entry.parent.input_type == InputType.JoystickAxis:
    % if entry.condition and entry.condition.is_active:

${axis_button_name} = gremlin.util.AxisButton(${entry.condition.lower_limit}, ${entry.condition.upper_limit})
def ${axis_button_cb}(is_pressed):
    if is_pressed:
        ${macro_name}.run()

    % endif
% endif
#newline