<%namespace name="util" module="templates.functions"/>

% if on_press and on_release:
${util.indent(code, 0)}
% elif on_press and not on_release:
if is_pressed:
    ${util.indent(code, 4)}
% elif not on_press and on_release:
if not is_pressed:
    ${util.indent(code, 4)}
% endif