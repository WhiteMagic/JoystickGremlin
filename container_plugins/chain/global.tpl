action_${id} = gremlin.abstract_containers.Chain([
% for action in entry.actions:
    ${action.to_code().static},
% endfor
])