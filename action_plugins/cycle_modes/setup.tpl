<%namespace file="../../templates/blocks.tpl" import="*"/>
mode_list_${id} = gremlin.control_action.ModeList([
    ${", ".join("\"{}\"".format(mode) for mode in entry.mode_list)}
])
${axis_button(
    id,
    input_type,
    InputType,
    entry,
    "cycle_mods_{:d}(is_pressed)".format(id)
)}