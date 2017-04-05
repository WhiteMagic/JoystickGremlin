<%namespace file="../../templates/blocks.tpl" import="*"/>
mode_list_${id} = gremlin.control_action.ModeList([
    ${", ".join("\"{}\"".format(mode) for mode in entry.mode_list)}
])
cycle_modes_${id} = gremlin.action_containers.Basic(
    gremlin.action_containers.ActionFactory.cycle_modes(mode_list_${id})
)
${axis_button(
    id,
    input_type,
    InputType,
    entry,
    "cycle_mods_{:d}(is_pressed)".format(id)
)}