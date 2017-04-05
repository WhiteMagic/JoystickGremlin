<%namespace file="../../templates/blocks.tpl" import="*"/>
pause_${id} = gremlin.action_containers.Basic(
    gremlin.action_containers.ActionFactory.pause()
)
${axis_button(
    id,
    input_type,
    InputType,
    entry,
    "pause_{:d}(is_pressed)".format(id)
)}