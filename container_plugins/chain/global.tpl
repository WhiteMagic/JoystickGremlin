<%namespace name="util" module="templates.functions"/>
action_${id} = gremlin.actions.Chain([
% for action in entry.actions:
    ${util.indent(action.to_code().container_action, 4, ",")}
% endfor
])