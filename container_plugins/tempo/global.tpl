<%namespace name="util" module="templates.functions"/>
action_${id} = gremlin.actions.Tempo(
    [
% for actions in entry.action_sets:
        [
    % for action in actions:
            ${util.indent(action.to_code().container_action, 8, ",")}
    % endfor
        ],
% endfor
    ],
    ${util.indent(util.virtual_button(entry.virtual_button), 4, "")},
    ${entry.delay}
)