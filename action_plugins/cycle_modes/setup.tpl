mode_list_${id} = gremlin.control_action.ModeList([
    ${", ".join("\"{}\"".format(mode) for mode in entry.mode_list)}
])