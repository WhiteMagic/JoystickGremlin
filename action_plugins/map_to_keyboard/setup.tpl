macro_${id} = gremlin.macro.Macro()
% for key in entry.keys:
macro_${id}.action(gremlin.macro.key_from_code(${key[0]}, ${key[1]}), True)
% endfor
macro_${id}.pause(0.05)
% for key in entry.keys:
macro_${id}.action(gremlin.macro.key_from_code(${key[0]}, ${key[1]}), False)
% endfor