<%namespace name="util" module="templates.functions"/>
action_${id} = gremlin.actions.Basic(
    [[
    % for action in entry.action_sets[0]:
        ${util.indent(action.to_code().container_action, 8, "")},
    % endfor
    ]],
    ${util.indent(util.virtual_button(entry.virtual_button), 4, "")}
)
