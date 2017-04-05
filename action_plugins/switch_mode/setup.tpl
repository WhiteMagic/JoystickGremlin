switch_mode_${id} = gremlin.action_containers.Basic(
    gremlin.action_containers.ActionFactory.switch_mode("${entry.mode_name}")
)