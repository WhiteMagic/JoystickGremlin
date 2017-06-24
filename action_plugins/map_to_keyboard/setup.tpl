macro_${id}_press = gremlin.macro.Macro()
% for key in entry.keys:
macro_${id}_press.action(gremlin.macro.key_from_code(${key[0]}, ${key[1]}), True)
% endfor

macro_${id}_release = gremlin.macro.Macro()
% for key in entry.keys:
macro_${id}_release.action(gremlin.macro.key_from_code(${key[0]}, ${key[1]}), False)
% endfor