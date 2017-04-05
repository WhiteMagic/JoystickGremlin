macro_${id} = gremlin.macro.Macro()
% for seq in entry.sequence:
    % if isinstance(seq, gremlin.macro.Macro.Pause):
macro_${id}.pause(${seq.duration})
    % elif isinstance(seq, gremlin.macro.Macro.KeyAction):
macro_${id}.action(gremlin.macro.key_from_code(${seq.key._scan_code}, ${seq.key._is_extended}), ${seq.is_pressed})
    % endif
% endfor

% if entry.get_input_type() == InputType.JoystickAxis:
    % if entry.condition and entry.condition.is_active:
axis_button_${id} = gremlin.util.AxisButton(${entry.condition.lower_limit}, ${entry.condition.upper_limit})
def axis_button_callback_${id}(is_pressed):
    if is_pressed:
        macro_${id}.run()
    % endif
% endif