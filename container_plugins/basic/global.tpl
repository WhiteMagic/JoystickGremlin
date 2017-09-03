<%namespace name="util" module="templates.functions"/>
% for i, action in enumerate(entry.action_sets[0]):
action_${id}_${i} = gremlin.actions.Basic(
    ${util.indent(action.to_code().container_action, 4, "")},
    ${util.indent(util.virtual_button(entry.virtual_button), 4, "")}
)
%endfor
