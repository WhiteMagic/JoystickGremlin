<%namespace name="util" module="templates.functions"/>
action_${id} = gremlin.actions.Chain(
    [
% for action in entry.actions:
        ${util.indent(action.to_code().container_action, 8, ",")}
% endfor
    ],
    ${util.indent(util.condition(entry.activation_condition), 4, "")},
    ${entry.timeout}
)