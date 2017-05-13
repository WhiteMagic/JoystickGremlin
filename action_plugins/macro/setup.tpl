macro_${id} = gremlin.macro.Macro()
% for seq in entry.sequence:
    % if isinstance(seq, gremlin.macro.PauseAction):
macro_${id}.pause(${seq.duration})
    % elif isinstance(seq, gremlin.macro.KeyAction):
macro_${id}.action(gremlin.macro.key_from_code(${seq.key._scan_code}, ${seq.key._is_extended}), ${seq.is_pressed})
    % endif
% endfor