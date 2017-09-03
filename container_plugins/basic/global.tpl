<%namespace name="util" module="templates.functions"/>
action_${id} = gremlin.actions.Basic(
    ${util.indent(entry.actions[0].to_code().container_action, 4, "")},
    ${util.indent(util.virtual_button(entry.virtual_button), 4, "")}
)
