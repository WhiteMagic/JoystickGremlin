${mode_list_name} = gremlin.control_action.ModeList([
    ${", ".join("\"{}\"".format(mode) for mode in entry.mode_list)}
])