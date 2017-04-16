<%namespace name="util" module="templates.functions"/>
action_${id} = gremlin.actions.Tempo([
% for action in entry.actions:
    ${util.indent(action.to_code().container_action, 4, ",")}
% endfor
], ${entry.delay})